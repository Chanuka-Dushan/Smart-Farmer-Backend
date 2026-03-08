"""
Tyre Damage Detection Module using YOLOv8
Detects various types of tyre damage including treadwear, cracks, bulging, etc.
"""

import logging
from pathlib import Path
from typing import Dict
import numpy as np
from datetime import datetime

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
    logger.warning(f"⚠ Ultralytics YOLO not available: {e}")


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
            model_path = Path(__file__).parent / "models" / "tyremodel" / "tyremodel.pt"

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
                return

            logger.info(f"📦 Loading YOLO model from: {self.model_path}")

            self.model = YOLO(str(self.model_path))
            self.model_loaded = True

            logger.info("✅ YOLO model loaded successfully")

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
            return self._simulate_detection(image_path)

        try:

            logger.info(f"🔍 Detecting damage in: {image_path}")

            results = self.model(image_path, conf=confidence_threshold, verbose=False)

            detections = []
            highest_severity_damage = None
            max_severity_score = 0.0

            for result in results:

                boxes = result.boxes

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

                    severity_score = damage_info["lifespan_reduction"] * confidence

                    if severity_score > max_severity_score:
                        max_severity_score = severity_score
                        highest_severity_damage = detection

            annotated_path = None

            if save_annotated and len(results) > 0 and CV2_AVAILABLE:
                annotated_path = self._save_annotated_image(results[0], image_path)

            response = {
                "success": True,
                "image_path": str(image_path),
                "detections_count": len(detections),
                "detections": detections,
                "primary_damage": highest_severity_damage,
                "annotated_image_path": annotated_path,
                "model": "YOLOv8",
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info(f"✅ Detection complete: {len(detections)} damage(s) found")

            return response

        except Exception as e:

            logger.error(f"❌ Detection failed: {e}", exc_info=True)

            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _save_annotated_image(self, result, original_path: str):

        if not CV2_AVAILABLE:
            logger.warning("⚠ Cannot save annotated image because OpenCV is not available")
            return None

        try:

            annotated_dir = Path(original_path).parent / "annotated"
            annotated_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"annotated_{timestamp}.jpg"

            save_path = annotated_dir / filename

            annotated_img = result.plot()

            cv2.imwrite(str(save_path), annotated_img)

            logger.info(f"💾 Annotated image saved: {save_path}")

            return str(save_path)

        except Exception as e:

            logger.error(f"❌ Failed to save annotated image: {e}")

            return None

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