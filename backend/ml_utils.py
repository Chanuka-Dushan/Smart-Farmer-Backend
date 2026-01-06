"""
Machine Learning Utilities for Smart Farmer
Handles model evaluation, validation, and prediction with proper error handling
"""
import numpy as np
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Optional, Any
from PIL import Image
from io import BytesIO

try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
    import matplotlib.pyplot as plt
    import seaborn as sns
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logging.warning("TensorFlow or sklearn not available - ML features will be limited")

logger = logging.getLogger(__name__)

class ModelEvaluator:
    """Handles model evaluation and metrics generation"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.evaluation_results = {}
        
    def load_model(self) -> bool:
        """Load the trained model"""
        try:
            if not TENSORFLOW_AVAILABLE:
                logger.error("TensorFlow not available")
                return False
                
            self.model = load_model(self.model_path)
            logger.info(f"Model loaded successfully from {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def evaluate_on_generator(self, data_generator) -> Dict[str, Any]:
        """Evaluate model on a data generator"""
        if not self.model:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Get predictions
        logger.info("Generating predictions...")
        predictions = self.model.predict(data_generator, verbose=1)
        
        # Get true labels
        true_labels = data_generator.classes
        predicted_labels = (predictions > 0.5).astype(int).flatten()
        
        # Calculate metrics
        results = {
            "accuracy": np.mean(predicted_labels == true_labels),
            "total_samples": len(true_labels),
            "true_positives": np.sum((predicted_labels == 1) & (true_labels == 1)),
            "true_negatives": np.sum((predicted_labels == 0) & (true_labels == 0)),
            "false_positives": np.sum((predicted_labels == 1) & (true_labels == 0)),
            "false_negatives": np.sum((predicted_labels == 0) & (true_labels == 1)),
        }
        
        # Calculate precision, recall, F1
        tp = results["true_positives"]
        fp = results["false_positives"]
        fn = results["false_negatives"]
        
        results["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0
        results["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0
        results["f1_score"] = 2 * (results["precision"] * results["recall"]) / \
                             (results["precision"] + results["recall"]) \
                             if (results["precision"] + results["recall"]) > 0 else 0
        
        # ROC AUC
        try:
            results["roc_auc"] = roc_auc_score(true_labels, predictions)
        except Exception as e:
            logger.warning(f"Could not calculate ROC AUC: {e}")
            results["roc_auc"] = None
        
        # Classification report
        class_names = list(data_generator.class_indices.keys())
        results["classification_report"] = classification_report(
            true_labels, predicted_labels, 
            target_names=class_names,
            output_dict=True
        )
        
        # Confusion matrix
        results["confusion_matrix"] = confusion_matrix(true_labels, predicted_labels).tolist()
        
        self.evaluation_results = results
        return results
    
    def save_evaluation_report(self, output_dir: str = "evaluation_reports"):
        """Save evaluation results to JSON and generate visualizations"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True) # Changed to parents=True
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_path / f"evaluation_report_{timestamp}.json"
        
        # Convert NumPy types to Python native types for JSON serialization
        def convert_to_native(obj):
            """Recursively convert NumPy types to Python native types"""
            if isinstance(obj, dict):
                return {key: convert_to_native(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            elif isinstance(obj, (np.integer, np.int32, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        # Convert evaluation results
        serializable_results = convert_to_native(self.evaluation_results)
        
        # Save JSON report
        with open(json_path, 'w', encoding='utf-8') as f: # Added encoding
            json.dump(serializable_results, f, indent=2) # Dump serializable_results
        logger.info(f"Evaluation report saved to {json_path}")
        
        # Generate confusion matrix visualization
        if TENSORFLOW_AVAILABLE:
            self._plot_confusion_matrix(output_path / f"confusion_matrix_{timestamp}.png")
            logger.info(f"Confusion matrix saved")
        
        return json_path
    
    def _plot_confusion_matrix(self, save_path: Path):
        """Plot and save confusion matrix"""
        cm = np.array(self.evaluation_results["confusion_matrix"])
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=['Good', 'Damaged'],
                   yticklabels=['Good', 'Damaged'])
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()


class PredictionValidator:
    """Validates model predictions and ensures quality"""
    
    def __init__(self, min_confidence: float = 0.7):
        self.min_confidence = min_confidence
        self.prediction_log = []
    
    def validate_prediction(self, prediction: float, confidence: Optional[float] = None) -> Tuple[bool, str]:
        """
        Validate a prediction value
        Returns: (is_valid, message)
        """
        # Check range
        if not (0.0 <= prediction <= 1.0):
            return False, f"Prediction out of range: {prediction}"
        
        # Check confidence if provided
        if confidence is not None and confidence < self.min_confidence:
            return False, f"Low confidence: {confidence:.2f} < {self.min_confidence}"
        
        return True, "Valid prediction"
    
    def calculate_confidence(self, prediction: float) -> float:
        """
        Calculate confidence score for a prediction
        Confidence is higher when prediction is closer to 0 or 1
        """
        # Distance from decision boundary (0.5)
        distance_from_boundary = abs(prediction - 0.5)
        # Normalize to 0-1 range
        confidence = distance_from_boundary * 2
        return confidence
    
    def log_prediction(self, prediction_data: Dict[str, Any]):
        """Log prediction for monitoring"""
        prediction_data["timestamp"] = datetime.now().isoformat()
        self.prediction_log.append(prediction_data)
    
    def get_prediction_stats(self) -> Dict[str, Any]:
        """Get statistics about recent predictions"""
        if not self.prediction_log:
            return {"total_predictions": 0}
        
        predictions = [p.get("prediction", 0) for p in self.prediction_log]
        confidences = [p.get("confidence", 0) for p in self.prediction_log]
        
        return {
            "total_predictions": len(predictions),
            "mean_prediction": np.mean(predictions),
            "std_prediction": np.std(predictions),
            "mean_confidence": np.mean(confidences),
            "low_confidence_count": sum(1 for c in confidences if c < self.min_confidence),
        }


class ImagePreprocessor:
    """Handles image preprocessing for model inference"""
    
    def __init__(self, target_size: Tuple[int, int] = (224, 224)):
        self.target_size = target_size
    
    def preprocess_image(self, image_data: bytes) -> Optional[np.ndarray]:
        """
        Preprocess image for model inference
        Returns: Preprocessed image array or None if error
        """
        try:
            # Load image
            img = Image.open(BytesIO(image_data)).convert('RGB')
            
            # Resize
            img = img.resize(self.target_size)
            
            # Convert to array and normalize
            img_array = np.array(img) / 255.0
            
            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)
            
            return img_array
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return None
    
    def validate_image(self, image_data: bytes) -> Tuple[bool, str]:
        """
        Validate image before processing
        Returns: (is_valid, message)
        """
        try:
            img = Image.open(BytesIO(image_data))
            
            # Check format
            if img.format not in ['JPEG', 'PNG', 'BMP']:
                return False, f"Unsupported format: {img.format}"
            
            # Check size
            if img.size[0] < 50 or img.size[1] < 50:
                return False, f"Image too small: {img.size}"
            
            # Check mode
            if img.mode not in ['RGB', 'L', 'RGBA']:
                return False, f"Unsupported mode: {img.mode}"
            
            return True, "Valid image"
            
        except Exception as e:
            return False, f"Invalid image: {str(e)}"


def clip_prediction(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Safely clip prediction values to valid range"""
    return float(np.clip(value, min_val, max_val))


def load_model_metadata(model_path: str) -> Optional[Dict[str, Any]]:
    """Load metadata associated with a model"""
    metadata_path = Path(model_path).with_suffix('.json')
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            return json.load(f)
    return None


def save_model_metadata(model_path: str, metadata: Dict[str, Any]):
    """Save metadata for a model"""
    metadata_path = Path(model_path).with_suffix('.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Model metadata saved to {metadata_path}")
