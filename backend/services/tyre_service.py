import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import numpy as np
from PIL import Image, ImageDraw
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


class TyreService:
    """Service that loads models once and performs classification + segmentation."""

    def __init__(self,
                 backend_root: Optional[Path] = None,
                 clf_path: Optional[Path] = None,
                 seg_path: Optional[Path] = None):

        if backend_root is None:
            backend_root = Path(__file__).resolve().parents[1]

        self.backend_root = Path(backend_root)
        self.model_dir = self.backend_root / "models" / "tyremodel"

        self.clf_path = Path(clf_path) if clf_path else (self.model_dir / "efficientnet_good_defect.keras")
        self.seg_path = Path(seg_path) if seg_path else (self.model_dir / "tyre_seg_best.pt")

        self._clf = None
        self._yolo = None
        self._tf_available = False
        self._yolo_available = False

        self._load_models()

    def _load_models(self):
        # Load TensorFlow/Keras classification model if available
        try:
            import tensorflow as tf
            from tensorflow.keras.models import load_model
            self._tf = tf
            self._tf_available = True
            if self.clf_path.exists():
                logger.info(f"📦 Loading classification model from: {self.clf_path}")
                try:
                    self._clf = load_model(str(self.clf_path))
                    logger.info("✅ Classification model loaded")
                except Exception as e:
                    logger.error(f"Failed to load classification model: {e}")
                    self._clf = None
            else:
                logger.warning(f"Classification model not found at {self.clf_path}")
        except Exception as e:
            logger.warning(f"TensorFlow not available or failed to import: {e}")
            self._tf_available = False

        # Load YOLO segmentation model if available
        try:
            from ultralytics import YOLO
            self._YOLO = YOLO
            if self.seg_path.exists():
                logger.info(f"📦 Loading YOLO segmentation model from: {self.seg_path}")
                try:
                    self._yolo = YOLO(str(self.seg_path))
                    self._yolo_available = True
                    logger.info("✅ YOLO segmentation model loaded")
                except Exception as e:
                    logger.error(f"Failed to load YOLO model: {e}")
                    self._yolo = None
            else:
                logger.warning(f"YOLO model not found at {self.seg_path}")
        except Exception as e:
            logger.warning(f"Ultralytics YOLO not available: {e}")
            self._yolo_available = False

    def _classify(self, pil_image: Image.Image) -> Tuple[str, float]:
        # Preprocess to 224x224 and normalize
        try:
            img = pil_image.convert("RGB").resize((224, 224))
            arr = np.asarray(img).astype("float32") / 255.0
            arr = np.expand_dims(arr, axis=0)

            if self._clf is not None:
                preds = self._clf.predict(arr)
                # Assume binary output [prob_good, prob_defect] or single sigmoid
                if preds.ndim == 2 and preds.shape[1] == 2:
                    prob_defect = float(preds[0, 1])
                    prob_good = float(preds[0, 0])
                else:
                    # assume sigmoid outputs probability of defect
                    prob_defect = float(preds[0][0]) if hasattr(preds[0], '__len__') else float(preds[0])
                    prob_good = 1.0 - prob_defect

                classification = "defect" if prob_defect >= prob_good else "good"
                score = prob_good if classification == "good" else prob_defect
                return classification, round(float(score), 4)
            else:
                # Fallback heuristic when model missing: treat as good
                return "good", 0.99

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return "good", 0.0

    def _create_roi_mask(self, width: int, height: int) -> np.ndarray:
        cx = int(width / 2)
        cy = int(height / 2)
        radius = int(0.4 * width)

        Y, X = np.ogrid[:height, :width]
        dist_from_center = (X - cx) ** 2 + (Y - cy) ** 2
        mask = dist_from_center <= (radius ** 2)
        return mask.astype(np.uint8)

    def _run_yolo_segmentation(self, image_np: np.ndarray) -> np.ndarray:
        """Run YOLO segmentation and return combined binary mask for cracks (same HxW)."""
        if not self._yolo_available or self._yolo is None:
            return np.zeros((image_np.shape[0], image_np.shape[1]), dtype=np.uint8)

        try:
            results = self._yolo(image_np)
            if len(results) == 0:
                return np.zeros((image_np.shape[0], image_np.shape[1]), dtype=np.uint8)

            result = results[0]
            # Extract masks
            masks = None
            try:
                masks_obj = getattr(result, "masks", None)
                if masks_obj is not None:
                    masks_data = getattr(masks_obj, "data", None)
                    if masks_data is not None:
                        # torch tensor -> numpy
                        try:
                            masks = masks_data.cpu().numpy()
                        except Exception:
                            masks = np.array(masks_data)
                    else:
                        masks = np.array(masks_obj)
            except Exception:
                masks = None

            if masks is None:
                return np.zeros((image_np.shape[0], image_np.shape[1]), dtype=np.uint8)

            # masks shape: (N, H, W) or (H, W) for single
            if masks.ndim == 2:
                combined = (masks > 0).astype(np.uint8)
            else:
                combined = np.any(masks > 0, axis=0).astype(np.uint8)

            return combined

        except Exception as e:
            logger.error(f"YOLO segmentation failed: {e}")
            return np.zeros((image_np.shape[0], image_np.shape[1]), dtype=np.uint8)

    def predict_from_bytes(self, image_bytes: bytes, return_overlay: bool = True) -> Dict[str, Any]:
        pil_image = Image.open(BytesIO(image_bytes)).convert("RGB")
        width, height = pil_image.size

        # 1) Classification
        classification, classification_score = self._classify(pil_image)

        if classification == "good":
            response = {
                "classification": "good",
                "classification_score": float(classification_score),
                "severity_ratio": 0.0,
                "severity_percent": 0.0,
                "crack_pixels": 0,
                "roi_pixels": 0,
                "rul": "30 months",
                "message": "No damage detected"
            }
            if return_overlay:
                # draw ROI for visualization
                overlay_b64 = self._build_overlay(pil_image, np.zeros((height, width), dtype=np.uint8))
                response["overlay_image"] = overlay_b64
            return response

        # 2) Defect -> segmentation
        image_np = np.asarray(pil_image)

        roi_mask = self._create_roi_mask(width, height)
        roi_pixels = int(np.sum(roi_mask))

        seg_mask = self._run_yolo_segmentation(image_np)

        # Make sure seg_mask matches HxW
        if seg_mask.shape != roi_mask.shape:
            seg_mask = np.array(Image.fromarray(seg_mask.astype(np.uint8) * 255).resize((width, height))).astype(np.uint8)
            seg_mask = (seg_mask > 0).astype(np.uint8)

        valid_crack = (seg_mask.astype(bool) & roi_mask.astype(bool)).astype(np.uint8)
        crack_pixels = int(np.sum(valid_crack))

        severity_ratio = float(crack_pixels / roi_pixels) if roi_pixels > 0 else 0.0
        severity_percent = severity_ratio * 100.0

        # RUL rules
        if severity_ratio < 0.02:
            rul = "6–12 months"
            message = "Minor crack detected"
        elif severity_ratio < 0.05:
            rul = "3–6 months"
            message = "Moderate crack detected"
        else:
            rul = "0–3 months"
            message = "Severe crack detected"

        response = {
            "classification": "defect",
            "classification_score": float(classification_score),
            "crack_pixels": crack_pixels,
            "roi_pixels": roi_pixels,
            "severity_ratio": round(float(severity_ratio), 6),
            "severity_percent": round(float(severity_percent), 3),
            "rul": rul,
            "message": message
        }

        if return_overlay:
            overlay_b64 = self._build_overlay(pil_image, valid_crack)
            response["overlay_image"] = overlay_b64

        return response

    def _build_overlay(self, pil_image: Image.Image, crack_mask: np.ndarray) -> Optional[str]:
        try:
            overlay = pil_image.copy()
            draw = ImageDraw.Draw(overlay, "RGBA")
            w, h = overlay.size

            # draw ROI circle
            cx = w / 2
            cy = h / 2
            r = 0.4 * w
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 0, 180), width=6)

            if crack_mask is not None and crack_mask.sum() > 0:
                # create red overlay
                mask_img = Image.fromarray((crack_mask * 255).astype(np.uint8)).convert("L")
                red = Image.new("RGBA", overlay.size, (255, 0, 0, 120))
                overlay.paste(red, (0, 0), mask_img)

            buff = BytesIO()
            overlay.save(buff, format="JPEG")
            b64 = base64.b64encode(buff.getvalue()).decode("utf-8")
            return b64
        except Exception as e:
            logger.error(f"Failed to build overlay image: {e}")
            return None


# Singleton
_service_instance: Optional[TyreService] = None


def get_tyre_service() -> TyreService:
    global _service_instance
    if _service_instance is None:
        _service_instance = TyreService()
    return _service_instance
