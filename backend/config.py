"""
Configuration management for Smart Farmer Backend
Centralizes all environment variables and settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
DATASET_DIR = BASE_DIR / "dataset"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
MODEL_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# ML Model Configuration
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0")
MODEL_PATH = os.getenv("MODEL_PATH", str(MODEL_DIR / f"smart_farmer_vision_{MODEL_VERSION}.h5"))
MIN_PREDICTION_CONFIDENCE = float(os.getenv("MIN_PREDICTION_CONFIDENCE", "0.7"))
DISABLE_TENSORFLOW = os.getenv("DISABLE_TENSORFLOW", "false").lower() == "true"

# Monitoring & Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENABLE_PREDICTION_LOGGING = os.getenv("ENABLE_PREDICTION_LOGGING", "true").lower() == "true"
ENABLE_PERFORMANCE_MONITORING = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"

# DigitalOcean Spaces
SPACES_KEY = os.getenv("SPACES_KEY")
SPACES_SECRET = os.getenv("SPACES_SECRET")
SPACES_REGION = os.getenv("SPACES_REGION", "nyc3")
SPACES_BUCKET = os.getenv("SPACES_BUCKET")

# Training Configuration
TRAINING_CONFIG = {
    "img_size": (224, 224),
    "batch_size": int(os.getenv("BATCH_SIZE", "16")),  # Reduced for better learning
    "epochs": int(os.getenv("EPOCHS", "100")),  # Increased from 50
    "learning_rate": float(os.getenv("LEARNING_RATE", "0.0001")),  # Lower for fine-tuning
    "validation_split": 0.2,
    "test_split": 0.1,
    "early_stopping_patience": 15,  # Increased patience
    "reduce_lr_patience": 5,
    "min_lr": 1e-7,
    "class_weight_auto": True,
    
    # Data Augmentation (Enhanced)
    "augmentation": {
        "rotation_range": 30,  # Increased from 20
        "width_shift_range": 0.25,  # Increased from 0.2
        "height_shift_range": 0.25,
        "shear_range": 0.25,
        "zoom_range": 0.25,
        "horizontal_flip": True,
        "vertical_flip": True,  # Added vertical flip
        "brightness_range": [0.8, 1.2],  # Added brightness variation
        "fill_mode": "nearest"
    },
    
    # Transfer Learning
    "base_model": "MobileNetV2",  # Can change to ResNet50 for better accuracy
    "unfreeze_layers": 50,  # Increased from 30 - more layers trainable
    "dropout_rate": 0.3,  # Reduced from 0.5 for better learning
}

# Lifecycle Prediction Configuration
LIFECYCLE_CONFIG = {
    "min_remaining_hours_critical": int(os.getenv("MIN_REMAINING_CRITICAL", "100")),
    "min_remaining_hours_warning": int(os.getenv("MIN_REMAINING_WARNING", "300")),
    "condition_bonus_threshold": float(os.getenv("CONDITION_BONUS_THRESHOLD", "0.20")),
    "max_condition_bonus": float(os.getenv("MAX_CONDITION_BONUS", "0.50")),
}

def validate_config():
    """Validate critical configuration settings"""
    errors = []
    warnings = []
    
    # Check critical API keys for production
    if not SECRET_KEY or SECRET_KEY == "dev-secret-key-change-in-production":
        warnings.append("SECRET_KEY is using default value - change for production!")
    
    if not GEMINI_API_KEY:
        warnings.append("GEMINI_API_KEY not set - AI knowledge will use cache/simulation only")
    
    if not WEATHER_API_KEY:
        warnings.append("WEATHER_API_KEY not set - weather forecasting disabled")
    
    # Check model file exists
    if not DISABLE_TENSORFLOW and not Path(MODEL_PATH).exists():
        warnings.append(f"Model file not found: {MODEL_PATH}")
    
    return errors, warnings

if __name__ == "__main__":
    errors, warnings = validate_config()
    
    print("=== Configuration Validation ===")
    if errors:
        print("\n❌ ERRORS:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("✅ All configuration valid!")
    
    print(f"\nModel Path: {MODEL_PATH}")
    print(f"Database: {DATABASE_URL}")
    print(f"TensorFlow Disabled: {DISABLE_TENSORFLOW}")
