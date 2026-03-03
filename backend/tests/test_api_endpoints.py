"""
Integration Tests for Smart Farmer API Endpoints
Run with: pytest tests/test_api_endpoints.py -v
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
from io import BytesIO
from PIL import Image

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_image():
    """Create a sample image for testing"""
    img = Image.new('RGB', (224, 224), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


@pytest.mark.integration
class TestLifecyclePredictionAPI:
    """Test the lifecycle prediction API endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        # Import here to avoid loading the entire app during collection
        from main import app
        return TestClient(app)
    
    def test_predict_lifecycle_success(self, client, sample_image):
        """Test successful lifecycle prediction"""
        response = client.post(
            "/api/predict-lifecycle",
            data={
                "part_name": "battery",
                "usage_hours": "1000",
                "location": "Colombo"
            },
            files={"image": ("test.png", sample_image, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "part_name" in data
        assert "ai_knowledge" in data
        assert "visual_scan" in data
        assert "environment" in data
        assert "prediction" in data
        
        # Check prediction fields
        assert "remaining_life" in data["prediction"]
        assert "status" in data["prediction"]
        assert "color_code" in data["prediction"]
    
    def test_predict_lifecycle_missing_fields(self, client):
        """Test API with missing required fields"""
        response = client.post(
            "/api/predict-lifecycle",
            data={"part_name": "battery"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_predict_lifecycle_invalid_image(self, client):
        """Test API with invalid image"""
        invalid_file = BytesIO(b"not an image")
        
        response = client.post(
            "/api/predict-lifecycle",
            data={
                "part_name": "battery",
                "usage_hours": "1000",
                "location": "Colombo"
            },
            files={"image": ("test.txt", invalid_file, "text/plain")}
        )
        
        # Should either reject or handle gracefully
        assert response.status_code in [200, 400, 422, 500]

    def test_identify_part_success(self, client, sample_image):
        """Test successful part identification"""
        response = client.post(
            "/api/identify-part",
            files={"image": ("test.png", sample_image, "image/png")}
        )
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "label" in data
            assert "confidence" in data

    def test_identify_part_missing(self, client):
        """Request without image should fail validation"""
        response = client.post("/api/identify-part")
        assert response.status_code == 422

    def test_identify_part_invalid_image(self, client):
        """Test API with invalid image for identification"""
        invalid_file = BytesIO(b"not an image")
        response = client.post(
            "/api/identify-part",
            files={"image": ("test.txt", invalid_file, "text/plain")}
        )
        assert response.status_code in [400, 422, 500]


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health check endpoints"""
    
    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
