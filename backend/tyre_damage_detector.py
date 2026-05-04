"""
Tyre Damage Detection Module using YOLOv8
Detects various types of tyre damage including treadwear, cracks, bulging, etc.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
from datetime import datetime
import base64

logger = logging.getLogger(__name__)

# Safe OpenCV import (cloud compatible)
try:
    import cv2
    CV2_AVAILABLE = True
    logger.info("✓ OpenCV (cv2) imported successfully")
except Exception as e:
    CV2_AVAILABLE = False
    cv2 = None
    logger.warning(f"⚠ OpenCV not available: {e}")

# YOLO import
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    logger.info("✓ Ultralytics YOLO available")
except Exception as e:
    YOLO_AVAILABLE = False
    logger.error(f"❌ Ultralytics YOLO import failed: {e}", exc_info=True)
    # Check for common missing dependencies
    try:
        import torch
        logger.info(f"  - PyTorch is available: {torch.__version__}")
    except ImportError:
        logger.error("  - PyTorch is MISSING")
    
    try:
        import numpy
        logger.info(f"  - NumPy is available: {numpy.__version__}")
    except ImportError:
        logger.error("  - NumPy is MISSING")
    
    logger.warning("⚠ Tyre damage detection will run in simulation mode due to YOLO unavailability")


class TyreDamageDetector:
    """YOLOv8-based tyre damage detection system"""

    DAMAGE_SEVERITY = {
        "crack_1": {"severity": "minor", "lifespan_reduction": 0.15},
        "crack_2": {"severity": "severe", "lifespan_reduction": 0.50},
        "treadwear_1": {"severity": "minor", "lifespan_reduction": 0.10},
        "treadwear_2": {"severity": "moderate", "lifespan_reduction": 0.30},
    }

    def __init__(self, model_path: str = None):

        if model_path is None:
            model_path = Path(__file__).parent / "models" / "tyremodel" / "tyre_seg_best.pt"

        self.model_path = Path(model_path)
        self.model = None
        self.model_loaded = False

        if YOLO_AVAILABLE:
            self._load_model()
        else:
            logger.warning("⚠ YOLO not available - running in simulation mode")

    def _load_model(self):

        try:
            if not self.model_path.exists():
                logger.error(f"❌ Model file not found: {self.model_path}")
                logger.error(f"   Expected at: {self.model_path.absolute()}")
                return

            logger.info(f"📦 Loading YOLO model from: {self.model_path}")
            logger.info(f"   File size: {self.model_path.stat().st_size / 1024 / 1024:.2f} MB")

            self.model = YOLO(str(self.model_path))
            self.model_loaded = True

            logger.info("✅ YOLO model loaded successfully")
            logger.info(f"   Model type: {type(self.model)}")
            logger.info(f"   Model task: {self.model.task if hasattr(self.model, 'task') else 'N/A'}")

        except Exception as e:
            logger.error(f"❌ Failed to load YOLO model: {e}")
            self.model_loaded = False

    def detect_damage(
        self,
        image_path: str,
        confidence_threshold: float = 0.25,
        save_annotated: bool = True
    ) -> Dict:

        if not self.model_loaded or not YOLO_AVAILABLE:
            logger.warning("⚪ Model not loaded, running in simulation mode")
            return self._simulate_detection(image_path)

        try:

            logger.info(f"🔍 Detecting damage in: {image_path}")
            logger.info(f"   Confidence threshold: {confidence_threshold}")

            results = self.model(image_path, conf=confidence_threshold, verbose=False)

            detections = []
            highest_severity_damage = None
            max_severity_score = 0.0

            for result in results:

                boxes = result.boxes
                logger.info(f"   Boxes found: {len(boxes)}")

                for box in boxes:

                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    bbox = box.xyxy[0].cpu().numpy().tolist()

                    class_name = result.names[class_id]

                    damage_info = self.DAMAGE_SEVERITY.get(
                        class_name,
                        {"severity": "unknown", "lifespan_reduction": 0.5}
                    )

                    detection = {
                        "damage_type": class_name,
                        "confidence": round(confidence, 3),
                        "severity": damage_info["severity"],
                        "lifespan_reduction": damage_info["lifespan_reduction"],
                        "bounding_box": {
                            "x1": round(bbox[0], 2),
                            "y1": round(bbox[1], 2),
                            "x2": round(bbox[2], 2),
                            "y2": round(bbox[3], 2)
                        }
                    }

                    detections.append(detection)
                    logger.info(f"   ✓ Detected: {class_name} (confidence: {confidence:.3f}, severity: {damage_info['severity']})")

                    severity_score = damage_info["lifespan_reduction"] * confidence

                    if severity_score > max_severity_score:
                        max_severity_score = severity_score
                        highest_severity_damage = detection

            annotated_path = None
            annotated_base64 = None

            if save_annotated and len(results) > 0 and CV2_AVAILABLE:
                annotated_path, annotated_base64 = self._save_annotated_image(results[0], image_path)

            response = {
                "success": True,
                "image_path": str(image_path),
                "detections_count": len(detections),
                "detections": detections,
                "primary_damage": highest_severity_damage,
                "annotated_image_path": annotated_path,
                "annotated_image_base64": annotated_base64,
                "model": "YOLOv8 (tyre_seg_best)",
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info(f"✅ Detection complete: {len(detections)} damage(s) found")
            logger.info(f"   Primary damage: {highest_severity_damage['damage_type'] if highest_severity_damage else 'None'}")

            return response

        except Exception as e:

            logger.error(f"❌ Detection failed: {e}", exc_info=True)

            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _save_annotated_image(self, result, original_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Save annotated image and return both file path and base64 encoding
        
        Returns:
            Tuple of (file_path, base64_string) or (None, None) if fails
        """
        if not CV2_AVAILABLE:
            logger.warning("⚠ Cannot save annotated image because OpenCV is not available")
            return None, None

        try:

            annotated_dir = Path(original_path).parent / "annotated"
            annotated_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"annotated_{timestamp}.jpg"

            save_path = annotated_dir / filename

            # Generate annotated image
            annotated_img = result.plot()

            # Save to filesystem
            cv2.imwrite(str(save_path), annotated_img)

            # Encode to base64 for mobile app
            _, buffer = cv2.imencode('.jpg', annotated_img)
            image_base64 = base64.b64encode(buffer).decode('utf-8')

            logger.info(f"💾 Annotated image saved: {save_path} (base64 encoded for mobile)")

            return str(save_path), image_base64

        except Exception as e:

            logger.error(f"❌ Failed to save annotated image: {e}")

            return None, None

    def _simulate_detection(self, image_path: str) -> Dict:

        logger.warning("⚪ Running in simulation mode")

        return {
            "success": True,
            "image_path": str(image_path),
            "detections_count": 1,
            "detections": [
                {
                    "damage_type": "treadwear_2",
                    "confidence": 0.82,
                    "severity": "moderate",
                    "lifespan_reduction": 0.30,
                    "bounding_box": {
                        "x1": 100.0,
                        "y1": 150.0,
                        "x2": 400.0,
                        "y2": 450.0
                    }
                }
            ],
            "primary_damage": {
                "damage_type": "treadwear_2",
                "confidence": 0.82,
                "severity": "moderate",
                "lifespan_reduction": 0.30
            },
            "annotated_image_path": None,
            "model": "Simulation Mode",
            "timestamp": datetime.utcnow().isoformat()
        }


_detector_instance = None


def get_detector() -> TyreDamageDetector:

    global _detector_instance

    if _detector_instance is None:
        _detector_instance = TyreDamageDetector()

    return _detector_instance