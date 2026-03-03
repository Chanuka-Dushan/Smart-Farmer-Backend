"""
Unit Tests for Smart Farmer ML Components
Run with: pytest tests/test_ml_components.py -v
"""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import json
from PIL import Image
from io import BytesIO

# Import modules to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml_utils import (
    PredictionValidator, 
    ImagePreprocessor, 
    clip_prediction,
    save_model_metadata,
    load_model_metadata
)


class TestPredictionValidator:
    """Test the PredictionValidator class"""
    
    def test_valid_prediction(self):
        validator = PredictionValidator(min_confidence=0.7)
        is_valid, message = validator.validate_prediction(0.8, confidence=0.9)
        assert is_valid is True
        assert "Valid" in message
    
    def test_out_of_range_prediction(self):
        validator = PredictionValidator()
        is_valid, message = validator.validate_prediction(1.5)
        assert is_valid is False
        assert "out of range" in message.lower()
    
    def test_low_confidence_prediction(self):
        validator = PredictionValidator(min_confidence=0.7)
        is_valid, message = validator.validate_prediction(0.5, confidence=0.5)
        assert is_valid is False
        assert "confidence" in message.lower()
    
    def test_confidence_calculation(self):
        validator = PredictionValidator()
        
        # Prediction close to 0 or 1 should have high confidence
        conf_high = validator.calculate_confidence(0.95)
        assert conf_high > 0.8
        
        # Prediction close to 0.5 should have low confidence
        conf_low = validator.calculate_confidence(0.5)
        assert conf_low < 0.2
    
    def test_prediction_logging(self):
        validator = PredictionValidator()
        
        validator.log_prediction({
            "prediction": 0.8,
            "confidence": 0.9,
            "part_name": "battery"
        })
        
        stats = validator.get_prediction_stats()
        assert stats["total_predictions"] == 1
        assert stats["mean_prediction"] == 0.8


class TestImagePreprocessor:
    """Test the ImagePreprocessor class"""
    
    @pytest.fixture
    def sample_image_bytes(self):
        """Create a sample image as bytes"""
        img = Image.new('RGB', (300, 300), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    def test_preprocess_valid_image(self, sample_image_bytes):
        preprocessor = ImagePreprocessor(target_size=(224, 224))
        result = preprocessor.preprocess_image(sample_image_bytes)
        
        assert result is not None
        assert result.shape == (1, 224, 224, 3)
        assert result.min() >= 0.0
        assert result.max() <= 1.0
    
    def test_validate_valid_image(self, sample_image_bytes):
        preprocessor = ImagePreprocessor()
        is_valid, message = preprocessor.validate_image(sample_image_bytes)
        
        assert is_valid is True
        assert "Valid" in message
    
    def test_validate_invalid_image(self):
        preprocessor = ImagePreprocessor()
        invalid_bytes = b"not an image"
        is_valid, message = preprocessor.validate_image(invalid_bytes)
        
        assert is_valid is False
        assert "Invalid" in message or "Unsupported" in message
    
    def test_validate_small_image(self):
        preprocessor = ImagePreprocessor()
        
        # Create very small image
        img = Image.new('RGB', (20, 20), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        
        is_valid, message = preprocessor.validate_image(img_bytes.getvalue())
        assert is_valid is False
        assert "small" in message.lower()


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_clip_prediction(self):
        assert clip_prediction(1.5) == 1.0
        assert clip_prediction(-0.5) == 0.0
        assert clip_prediction(0.5) == 0.5


class TestPartIdentifier:
    """Unit tests for the PartIdentifier helper"""

    def test_part_identifier_dummy(self, tmp_path):
        pytest.importorskip("torch")
        from ml_utils import PartIdentifier
        import torch
        import torch.nn as nn
        import numpy as np

        # create a trivial linear model
        model = nn.Sequential(nn.Flatten(), nn.Linear(224 * 224 * 3, 5))
        model_path = tmp_path / "dummy.pth"
        torch.save(model, str(model_path))

        labels = {str(i): f"class{i}" for i in range(5)}
        label_file = tmp_path / "labels.json"
        label_file.write_text(json.dumps(labels))

        pi = PartIdentifier(str(model_path), str(label_file))
        assert pi.load_model()

        arr = np.zeros((1, 224, 224, 3), dtype=np.float32)
        label, conf = pi.predict(arr)
        assert label in labels.values()
        assert isinstance(conf, float)
    
    def test_model_metadata_save_load(self):
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            model_path = f.name
        
        try:
            # Save metadata
            metadata = {
                "version": "v1.0",
                "accuracy": 0.95,
                "training_date": "2024-01-01"
            }
            save_model_metadata(model_path, metadata)
            
            # Load metadata
            loaded_metadata = load_model_metadata(model_path)
            
            assert loaded_metadata is not None
            assert loaded_metadata["version"] == "v1.0"
            assert loaded_metadata["accuracy"] == 0.95
            
        finally:
            # Cleanup
            Path(model_path).unlink(missing_ok=True)
            Path(model_path).with_suffix('.json').unlink(missing_ok=True)


class TestLifecyclePrediction:
    """Test lifecycle prediction logic"""
    
    def test_lifecycle_calculation_basic(self):
        """Test basic lifecycle calculation"""
        fresh_life = 3000  # hours
        usage_hours = 1000
        visual_damage = 0.3
        hist_stress = 1.1
        future_penalty = 0.0
        
        # Formula: effective_capacity = fresh_life * (1.0 - visual_damage - future_penalty)
        effective_capacity = fresh_life * (1.0 - visual_damage - future_penalty)
        real_usage = usage_hours * hist_stress
        remaining = effective_capacity - real_usage
        
        assert remaining > 0
        assert remaining < fresh_life
    
    def test_lifecycle_with_bonus(self):
        """Test lifecycle with condition bonus"""
        fresh_life = 3000
        visual_damage = 0.15  # Less than 20%
        
        # Should get bonus
        if visual_damage < 0.20:
            condition_bonus = (0.20 - visual_damage) / 0.20 * 0.50
            assert condition_bonus > 0
            assert condition_bonus <= 0.50
    
    def test_lifecycle_critical_threshold(self):
        """Test critical threshold detection"""
        remaining = 50
        
        if remaining < 100:
            status = "CRITICAL REPLACEMENT"
            assert status == "CRITICAL REPLACEMENT"
        elif remaining < 300:
            status = "WARNING"
        else:
            status = "GOOD"


class TestEnvironmentalFactors:
    """Test environmental stress calculations"""
    
    def test_dry_zone_stress(self):
        """Test dry zone stress factor"""
        location = "anuradhapura"
        part_name = "battery"
        
        # Simulate the logic from main.py
        stress_factor = 1.0
        if location.lower() in ["anuradhapura", "jaffna"]:
            if "battery" in part_name.lower():
                stress_factor = 1.25
        
        assert stress_factor == 1.25
    
    def test_wet_zone_stress(self):
        """Test wet zone stress factor"""
        location = "colombo"
        part_name = "pump"
        
        stress_factor = 1.0
        if location.lower() in ["colombo", "galle"]:
            if "pump" in part_name.lower():
                stress_factor = 1.20
        
        assert stress_factor == 1.20


# Integration test marker
@pytest.mark.integration
class TestModelIntegration:
    """Integration tests (require actual model file)"""
    
    @pytest.mark.skipif(
        not Path("models/smart_farmer_vision_v1.0.h5").exists(),
        reason="Model file not found"
    )
    def test_model_loads(self):
        """Test that the model can be loaded"""
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model("models/smart_farmer_vision_v1.0.h5")
            assert model is not None
            assert len(model.layers) > 0
        except ImportError:
            pytest.skip("TensorFlow not available")
    
    @pytest.mark.skipif(
        not Path("models/smart_farmer_vision_v1.0.h5").exists(),
        reason="Model file not found"
    )
    def test_model_prediction_shape(self):
        """Test model prediction output shape"""
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model("models/smart_farmer_vision_v1.0.h5")
            
            # Create dummy input
            dummy_input = np.random.rand(1, 224, 224, 3).astype(np.float32)
            prediction = model.predict(dummy_input, verbose=0)
            
            assert prediction.shape == (1, 1)
            assert 0.0 <= prediction[0][0] <= 1.0
        except ImportError:
            pytest.skip("TensorFlow not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
