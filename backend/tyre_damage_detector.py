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

    def _calculate_rul_from_masks(
        self,
        image: np.ndarray,
        masks: Optional[np.ndarray],
        classification: str = "defect"
    ) -> Dict:
        """
        Calculate Remaining Useful Life (RUL) from YOLO segmentation masks.
        
        Steps:
        1. Create fixed circular ROI mask (tyre region approximation)
        2. Extract crack pixels from YOLO masks
        3. Compute severity ratio (crack_pixels / roi_pixels)
        4. Map severity to RUL using predefined rules
        
        Args:
            image: Input image as numpy array
            masks: YOLO segmentation masks (None if no damage)
            classification: "good" or "defect" from EfficientNet
            
        Returns:
            Dict with crack_pixels, roi_pixels, severity_ratio, severity_percent, rul, message
        """
        try:
            h, w = image.shape[:2]
            logger.info(f"📏 Image size: {w}x{h}")
            
            # STEP 1: Create fixed circular ROI mask
            cx, cy = w / 2, h / 2
            r = 0.4 * w  # ROI radius
            
            y, x = np.ogrid[:h, :w]
            roi_mask = (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2
            roi_pixels = np.sum(roi_mask)
            
            logger.info(f"   ROI center: ({cx:.1f}, {cy:.1f}), radius: {r:.1f}")
            logger.info(f"   ROI pixels: {roi_pixels}")
            
            # STEP 2 & 3: Handle classification and extract crack pixels
            if classification.lower() == "good":
                logger.info("✅ EfficientNet classified: GOOD (no damage)")
                return {
                    "crack_pixels": 0,
                    "roi_pixels": int(roi_pixels),
                    "severity_ratio": 0.0,
                    "severity_percent": 0.0,
                    "rul": "30 months",
                    "message": "No damage detected - tyre is in good condition"
                }
            
            # Extract crack pixels from YOLO masks
            crack_pixels = 0
            if masks is not None and len(masks) > 0:
                logger.info(f"   Processing {len(masks)} mask(s)")
                
                for idx, mask in enumerate(masks):
                    # Resize mask to image dimensions
                    if mask.shape != (h, w):
                        mask_resized = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
                    else:
                        mask_resized = mask
                    
                    # Threshold to binary
                    binary_mask = (mask_resized > 0.5).astype(np.uint8)
                    
                    # Filter crack pixels inside ROI
                    crack_in_roi = binary_mask * roi_mask.astype(np.uint8)
                    crack_pixels += np.sum(crack_in_roi)
                    
                    logger.info(f"   Mask {idx}: {np.sum(crack_in_roi)} crack pixels")
            
            # STEP 4: Compute severity ratio
            severity_ratio = crack_pixels / roi_pixels if roi_pixels > 0 else 0.0
            severity_percent = severity_ratio * 100
            
            logger.info(f"   Total crack pixels: {crack_pixels}")
            logger.info(f"   Severity ratio: {severity_ratio:.4f} ({severity_percent:.2f}%)")
            
            # STEP 5: Map severity to RUL
            if severity_ratio < 0.02:
                rul = "6–12 months"
                message = "Minor crack detected - monitor regularly"
                severity_label = "minor"
            elif severity_ratio < 0.05:
                rul = "3–6 months"
                message = "Moderate crack detected - recommend maintenance soon"
                severity_label = "moderate"
            else:
                rul = "0–3 months"
                message = "Severe crack detected - replace tyre immediately"
                severity_label = "severe"
            
            result = {
                "crack_pixels": int(crack_pixels),
                "roi_pixels": int(roi_pixels),
                "severity_ratio": round(severity_ratio, 4),
                "severity_percent": round(severity_percent, 2),
                "rul": rul,
                "message": message,
                "severity_label": severity_label
            }
            
            logger.info(f"   RUL: {rul}")
            logger.info(f"   Message: {message}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ RUL calculation failed: {e}", exc_info=True)
            return {
                "crack_pixels": 0,
                "roi_pixels": 0,
                "severity_ratio": 0.0,
                "severity_percent": 0.0,
                "rul": "Unknown",
                "message": f"RUL calculation error: {str(e)}"
            }

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

            # Read image for RUL calculation
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to read image: {image_path}")

            results = self.model(image_path, conf=confidence_threshold, verbose=False)

            detections = []
            highest_severity_damage = None
            max_severity_score = 0.0
            
            # Extract masks and classification
            masks = None
            classification = "good"

            for result in results:
                boxes = result.boxes
                logger.info(f"   Boxes found: {len(boxes)}")

                # Extract masks if available (segmentation model)
                if hasattr(result, 'masks') and result.masks is not None:
                    masks = result.masks.data.cpu().numpy()
                    logger.info(f"   Segmentation masks found: {masks.shape}")
                    classification = "defect" if len(masks) > 0 else "good"

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

            # CALCULATE RUL FROM MASKS
            rul_data = self._calculate_rul_from_masks(image, masks, classification)

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
                # Add RUL calculation data
                "crack_pixels": rul_data["crack_pixels"],
                "roi_pixels": rul_data["roi_pixels"],
                "severity_ratio": rul_data["severity_ratio"],
                "severity_percent": rul_data["severity_percent"],
                "rul": rul_data["rul"],
                "message": rul_data["message"],
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info(f"✅ Detection complete: {len(detections)} damage(s) found")
            logger.info(f"   Primary damage: {highest_severity_damage['damage_type'] if highest_severity_damage else 'None'}")
            logger.info(f"   RUL: {rul_data['rul']}")

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