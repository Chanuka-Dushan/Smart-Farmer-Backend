"""
Production-Ready Visual Damage Detection Model Training Script
Trains a CNN model to detect visual damage in tractor parts
"""

import os
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import warnings
warnings.filterwarnings('ignore')

import json
import logging
from pathlib import Path
from datetime import datetime
import numpy as np

# Check for required libraries
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
    from tensorflow.keras.models import Model
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import (
        EarlyStopping, ModelCheckpoint, ReduceLROnPlateau,
        TensorBoard, CSVLogger
    )
    from sklearn.metrics import (
        classification_report, confusion_matrix, 
        roc_auc_score, roc_curve
    )
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    TENSORFLOW_AVAILABLE = True
except ImportError as e:
    print(f"❌ ERROR: Required libraries not installed: {e}")
    print("Install with: pip install tensorflow scikit-learn matplotlib seaborn")
    sys.exit(1)

# Import our ML utilities
from ml_utils import ModelEvaluator, save_model_metadata
from config import TRAINING_CONFIG, DATASET_DIR, MODEL_DIR, LOGS_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Training Configuration
IMG_SIZE = TRAINING_CONFIG["img_size"]
BATCH_SIZE = TRAINING_CONFIG["batch_size"]
EPOCHS = TRAINING_CONFIG["epochs"]
LEARNING_RATE = TRAINING_CONFIG["learning_rate"]
VALIDATION_SPLIT = TRAINING_CONFIG["validation_split"]
TEST_SPLIT = TRAINING_CONFIG["test_split"]

class SmartFarmerModelTrainer:
    """Handles the complete training pipeline"""
    
    def __init__(self, dataset_dir: Path, output_dir: Path):
        self.dataset_dir = Path(dataset_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.model = None
        self.history = None
        self.train_generator = None
        self.validation_generator = None
        self.test_generator = None
        
        # Create version-specific output directory
        self.version = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.version_dir = self.output_dir / f"training_{self.version}"
        self.version_dir.mkdir(exist_ok=True)
        
        logger.info(f"Training version: {self.version}")
        logger.info(f"Output directory: {self.version_dir}")
    
    def validate_dataset(self) -> bool:
        """Validate dataset structure and quality"""
        logger.info("Validating dataset...")
        
        if not self.dataset_dir.exists():
            logger.error(f"Dataset directory not found: {self.dataset_dir}")
            return False
        
        # Check for required subdirectories
        good_parts_dir = self.dataset_dir / "good_parts"
        damaged_parts_dir = self.dataset_dir / "damaged_parts"
        
        if not good_parts_dir.exists():
            logger.error(f"'good_parts' directory not found in {self.dataset_dir}")
            return False
        
        if not damaged_parts_dir.exists():
            logger.error(f"'damaged_parts' directory not found in {self.dataset_dir}")
            return False
        
        # Count images
        good_images = list(good_parts_dir.glob("*.png")) + list(good_parts_dir.glob("*.jpg")) + list(good_parts_dir.glob("*.bmp"))
        damaged_images = list(damaged_parts_dir.glob("*.png")) + list(damaged_parts_dir.glob("*.jpg")) + list(damaged_parts_dir.glob("*.bmp"))
        
        logger.info(f"Good parts: {len(good_images)} images")
        logger.info(f"Damaged parts: {len(damaged_images)} images")
        
        if len(good_images) < 50:
            logger.warning(f"⚠️  Low number of good part images: {len(good_images)}")
        
        if len(damaged_images) < 50:
            logger.warning(f"⚠️  Low number of damaged part images: {len(damaged_images)}")
        
        # Check class imbalance
        imbalance_ratio = max(len(good_images), len(damaged_images)) / max(min(len(good_images), len(damaged_images)), 1)
        if imbalance_ratio > 3:
            logger.warning(f"⚠️  Class imbalance detected: {imbalance_ratio:.2f}:1 ratio")
            logger.warning("   Consider using class weights or data augmentation")
        
        # Check for suspicious files (all same size)
        damaged_sizes = [img.stat().st_size for img in damaged_images[:100]]
        if len(set(damaged_sizes)) == 1 and len(damaged_sizes) > 10:
            logger.warning("⚠️  Suspicious: Many damaged images have identical file sizes")
            logger.warning("   This may indicate synthetic or corrupted data")
        
        total_images = len(good_images) + len(damaged_images)
        logger.info(f"✅ Total dataset: {total_images} images")
        
        return total_images >= 100  # Minimum viable dataset
    
    def prepare_data_generators(self):
        """Prepare train, validation, and test data generators"""
        logger.info("Preparing data generators...")
        
        # Calculate actual validation split (we'll use part of it for testing)
        # If we want 20% val and 10% test from total, we need to split differently
        # Total = Train + Val + Test
        # 1.0 = (1 - val_split) + val_split
        # We want: 70% train, 20% val, 10% test
        # So from the validation set, we'll use half for actual validation and half for testing
        
        # Training data generator with augmentation
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=20,
            zoom_range=0.15,
            width_shift_range=0.2,
            height_shift_range=0.2,
            horizontal_flip=True,
            vertical_flip=False,
            fill_mode='nearest',
            validation_split=VALIDATION_SPLIT + TEST_SPLIT  # Reserve for val + test
        )
        
        # Validation/Test data generator (no augmentation)
        val_test_datagen = ImageDataGenerator(
            rescale=1./255,
            validation_split=VALIDATION_SPLIT + TEST_SPLIT
        )
        
        # Training set
        logger.info("Loading training set...")
        self.train_generator = train_datagen.flow_from_directory(
            self.dataset_dir,
            target_size=IMG_SIZE,
            batch_size=BATCH_SIZE,
            class_mode='binary',
            subset='training',
            shuffle=True,
            seed=42
        )
        
        # Validation set (we'll use this for both validation and testing)
        logger.info("Loading validation set...")
        self.validation_generator = val_test_datagen.flow_from_directory(
            self.dataset_dir,
            target_size=IMG_SIZE,
            batch_size=BATCH_SIZE,
            class_mode='binary',
            subset='validation',
            shuffle=False,
            seed=42
        )
        
        # For testing, we'll use a separate generator with the same data
        # but we'll only use the first half for validation and second half for testing
        logger.info("Loading test set...")
        self.test_generator = val_test_datagen.flow_from_directory(
            self.dataset_dir,
            target_size=IMG_SIZE,
            batch_size=BATCH_SIZE,
            class_mode='binary',
            subset='validation',
            shuffle=False,
            seed=42
        )
        
        logger.info(f"Training samples: {self.train_generator.samples}")
        logger.info(f"Validation samples: {self.validation_generator.samples}")
        logger.info(f"Class indices: {self.train_generator.class_indices}")
        
        # Calculate class weights for imbalanced dataset
        total_samples = self.train_generator.samples
        class_counts = np.bincount(self.train_generator.classes)
        self.class_weights = {
            i: total_samples / (len(class_counts) * count) 
            for i, count in enumerate(class_counts)
        }
        logger.info(f"Class weights: {self.class_weights}")
    
    def build_model(self):
        """Build the MobileNetV2-based model"""
        logger.info("Building model architecture...")
        
        # Load pre-trained MobileNetV2
        base_model = MobileNetV2(
            weights='imagenet', 
            include_top=False, 
            input_shape=IMG_SIZE + (3,)
        )
        
        # Freeze base model initially
        base_model.trainable = False
        logger.info(f"Base model loaded with {len(base_model.layers)} layers (frozen)")
        
        # Add custom classification head
        x = base_model.output
        x = GlobalAveragePooling2D(name='global_avg_pool')(x)
        x = Dense(256, activation='relu', name='dense_1')(x)
        x = Dropout(0.5, name='dropout_1')(x)
        x = Dense(128, activation='relu', name='dense_2')(x)
        x = Dropout(0.3, name='dropout_2')(x)
        predictions = Dense(1, activation='sigmoid', name='output')(x)
        
        self.model = Model(inputs=base_model.input, outputs=predictions)
        
        # Compile model
        self.model.compile(
            optimizer=Adam(learning_rate=LEARNING_RATE),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
        )
        
        logger.info("Model compiled successfully")
        logger.info(f"Total parameters: {self.model.count_params():,}")
        
        # Save model summary
        with open(self.version_dir / 'model_summary.txt', 'w', encoding='utf-8') as f:
            self.model.summary(print_fn=lambda x: f.write(x + '\n'))
    
    def setup_callbacks(self):
        """Setup training callbacks"""
        callbacks = [
            # Early stopping
            EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            
            # Model checkpoint
            ModelCheckpoint(
                filepath=str(self.version_dir / 'best_model.h5'),
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            ),
            
            # Learning rate reduction
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            ),
            
            # TensorBoard
            TensorBoard(
                log_dir=str(self.version_dir / 'tensorboard_logs'),
                histogram_freq=1,
                write_graph=True
            ),
            
            # CSV Logger
            CSVLogger(
                filename=str(self.version_dir / 'training_history.csv'),
                append=False
            )
        ]
        
        return callbacks
    
    def train(self):
        """Execute the training process"""
        logger.info("=" * 60)
        logger.info("STARTING TRAINING")
        logger.info("=" * 60)
        
        callbacks = self.setup_callbacks()
        
        # Calculate steps
        steps_per_epoch = self.train_generator.samples // BATCH_SIZE
        validation_steps = self.validation_generator.samples // BATCH_SIZE
        
        logger.info(f"Steps per epoch: {steps_per_epoch}")
        logger.info(f"Validation steps: {validation_steps}")
        logger.info(f"Total epochs: {EPOCHS}")
        
        # Train the model
        self.history = self.model.fit(
            self.train_generator,
            steps_per_epoch=steps_per_epoch,
            epochs=EPOCHS,
            validation_data=self.validation_generator,
            validation_steps=validation_steps,
            class_weight=self.class_weights,
            callbacks=callbacks,
            verbose=1
        )
        
        logger.info("✅ Training completed!")
    
    def evaluate_model(self):
        """Evaluate the trained model"""
        logger.info("=" * 60)
        logger.info("EVALUATING MODEL")
        logger.info("=" * 60)
        
        # Evaluate on test set
        logger.info("Evaluating on test set...")
        test_loss, test_accuracy, test_precision, test_recall = self.model.evaluate(
            self.test_generator,
            steps=self.test_generator.samples // BATCH_SIZE,
            verbose=1
        )
        
        logger.info(f"Test Loss: {test_loss:.4f}")
        logger.info(f"Test Accuracy: {test_accuracy:.4f}")
        logger.info(f"Test Precision: {test_precision:.4f}")
        logger.info(f"Test Recall: {test_recall:.4f}")
        
        # Use ModelEvaluator for detailed metrics
        evaluator = ModelEvaluator(str(self.version_dir / 'best_model.h5'))
        evaluator.load_model()
        results = evaluator.evaluate_on_generator(self.test_generator)
        
        # Save evaluation report
        report_path = evaluator.save_evaluation_report(str(self.version_dir))
        logger.info(f"Detailed evaluation report saved to {report_path}")
        
        return results
    
    def save_final_model(self, evaluation_results: dict):
        """Save the final model with metadata"""
        logger.info("Saving final model...")
        
        # Determine model version based on accuracy
        accuracy = evaluation_results.get('accuracy', 0)
        version_str = f"v1.0_acc_{accuracy:.2f}".replace('.', '_')
        
        final_model_path = MODEL_DIR / f"smart_farmer_vision_{version_str}.h5"
        
        # Copy best model to final location
        import shutil
        shutil.copy(
            self.version_dir / 'best_model.h5',
            final_model_path
        )
        
        # Save metadata
        metadata = {
            "version": version_str,
            "training_date": datetime.now().isoformat(),
            "accuracy": float(accuracy),
            "precision": float(evaluation_results.get('precision', 0)),
            "recall": float(evaluation_results.get('recall', 0)),
            "f1_score": float(evaluation_results.get('f1_score', 0)),
            "roc_auc": float(evaluation_results.get('roc_auc', 0)) if evaluation_results.get('roc_auc') else None,
            "total_samples": int(evaluation_results.get('total_samples', 0)),
            "training_config": {
                "epochs": EPOCHS,
                "batch_size": BATCH_SIZE,
                "learning_rate": LEARNING_RATE,
                "img_size": IMG_SIZE,
            },
            "class_distribution": {
                "good_parts": int(self.train_generator.classes.tolist().count(0)),
                "damaged_parts": int(self.train_generator.classes.tolist().count(1)),
            }
        }
        
        save_model_metadata(str(final_model_path), metadata)
        
        logger.info(f"✅ Final model saved to: {final_model_path}")
        logger.info(f"   Accuracy: {accuracy:.2%}")
        logger.info(f"   F1 Score: {evaluation_results.get('f1_score', 0):.2%}")
        
        return final_model_path
    
    def run_complete_pipeline(self):
        """Run the complete training pipeline"""
        try:
            # Step 1: Validate dataset
            if not self.validate_dataset():
                logger.error("Dataset validation failed!")
                return False
            
            # Step 2: Prepare data
            self.prepare_data_generators()
            
            # Step 3: Build model
            self.build_model()
            
            # Step 4: Train
            self.train()
            
            # Step 5: Evaluate
            results = self.evaluate_model()
            
            # Step 6: Save final model
            final_model_path = self.save_final_model(results)
            
            logger.info("=" * 60)
            logger.info("✅ TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            logger.info(f"Model saved to: {final_model_path}")
            logger.info(f"Training artifacts in: {self.version_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Training pipeline failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point"""
    print("=" * 60)
    print("SMART FARMER VISION MODEL TRAINING")
    print("=" * 60)
    print()
    
    # Initialize trainer
    trainer = SmartFarmerModelTrainer(
        dataset_dir=DATASET_DIR,
        output_dir=MODEL_DIR
    )
    
    # Run training pipeline
    success = trainer.run_complete_pipeline()
    
    if success:
        print("\n✅ Training completed successfully!")
        print(f"Check {trainer.version_dir} for detailed results")
        sys.exit(0)
    else:
        print("\n❌ Training failed! Check logs for details")
        sys.exit(1)


if __name__ == "__main__":
    main()