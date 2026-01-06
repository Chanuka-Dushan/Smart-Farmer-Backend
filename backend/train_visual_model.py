# file: backend/train_visual_model.py
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
import os

# --- CONFIGURATION ---
# We point to the folder where you pasted your images
DATASET_DIR = "dataset" 
IMG_SIZE = (224, 224)
BATCH_SIZE = 8  # Small batch size is better for laptops
EPOCHS = 10     # How many times to study the images (10 is usually enough)

def train_model():
    # 1. Check if data exists
    if not os.path.exists(DATASET_DIR):
        print(f"❌ ERROR: Folder '{DATASET_DIR}' not found!")
        print("Please ensure you created 'backend/dataset' with 'good_parts' and 'damaged_parts' inside.")
        return

    print("🔍 Scanning your dataset...")
    
    # 2. Setup Data Generators (This loads images + adds variety/augmentation)
    # We add rotation and zooming so 1 image looks like 5 different ones to the AI
    train_datagen = ImageDataGenerator(
        rescale=1./255,         # Normalize pixel colors
        rotation_range=20,      # Rotate slightly
        zoom_range=0.15,        # Zoom in/out
        width_shift_range=0.2,  # Move side to side
        height_shift_range=0.2, # Move up and down
        horizontal_flip=True,   # Mirror image
        validation_split=0.2    # Save 20% of images for testing exams
    )

    # 3. Load Images from Folders
    # This automatically finds 'good_parts' and 'damaged_parts'
    print("\n--- TRAINING SET (80%) ---")
    train_generator = train_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='binary',   # 'good' vs 'damaged' (0 or 1)
        subset='training'
    )

    print("\n--- VALIDATION SET (20%) ---")
    validation_generator = train_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='binary',
        subset='validation'
    )

    # 4. Build the Brain (Transfer Learning)
    print("\n🏗️ Building MobileNetV2 Model...")
    # Load MobileNetV2 (pre-trained on ImageNet) but cut off the "head"
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=IMG_SIZE + (3,))
    
    # Freeze the base so we don't destroy its existing knowledge
    base_model.trainable = False

    # Add our own "Smart Farmer" layers on top
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x) # Thinking layer
    x = Dropout(0.3)(x)                  # Forget 30% to prevent memorization
    predictions = Dense(1, activation='sigmoid')(x) # Final Answer: 0.0 to 1.0

    model = Model(inputs=base_model.input, outputs=predictions)

    # 5. Compile
    model.compile(optimizer=Adam(learning_rate=0.0001),
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    # 6. Train
    print("\n🚀 Starting Training on your Laptop...")
    history = model.fit(
        train_generator,
        steps_per_epoch=train_generator.samples // BATCH_SIZE,
        validation_data=validation_generator,
        validation_steps=validation_generator.samples // BATCH_SIZE,
        epochs=EPOCHS
    )

    # 7. Save
    print("\n💾 Saving Model...")
    model.save("smart_farmer_vision_v1.h5")
    print("✅ SUCCESS! Model saved as 'smart_farmer_vision_v1.h5'")
    print("You can now restart your backend server to use it.")

if __name__ == "__main__":
    train_model()