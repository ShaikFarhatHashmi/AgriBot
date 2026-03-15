#!/usr/bin/env python3
"""
Download Plant Disease Datasets
Automatically downloads and prepares plant disease datasets for training
"""
import os
import urllib.request
import zipfile
from pathlib import Path

def download_file(url, destination):
    """Download file with progress indicator"""
    try:
        print(f"Downloading: {url}")
        urllib.request.urlretrieve(url, destination)
        print(f"✓ Downloaded to: {destination}")
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def extract_zip(zip_path, extract_to):
    """Extract zip file"""
    try:
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"✓ Extracted to: {extract_to}")
        os.remove(zip_path)  # Clean up zip file
        return True
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

def create_directory_structure(base_path):
    """Create standard ML directory structure"""
    dirs = [
        "Data/train",
        "Data/valid", 
        "Data/test",
        "models",
        "notebooks"
    ]
    
    for dir_path in dirs:
        full_path = os.path.join(base_path, dir_path)
        os.makedirs(full_path, exist_ok=True)
        print(f"✓ Created directory: {full_path}")

def download_plant_village():
    """Download PlantVillage dataset (subset)"""
    base_url = "https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color/"
    
    # Sample classes to download (reduce download size)
    classes = [
        "Apple___Apple_scab",
        "Apple___Black_rot", 
        "Apple___Cedar_apple_rust",
        "Apple___healthy",
        "Tomato___Bacterial_spot",
        "Tomato___Early_blight",
        "Tomato___Late_blight",
        "Tomato___Leaf_Mold",
        "Tomato___Septoria_leaf_spot",
        "Tomato___Spider_mites Two-spotted_spider_mite",
        "Tomato___Target_Spot",
        "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
        "Tomato___Tomato_mosaic_virus",
        "Tomato___healthy"
    ]
    
    print("🍎 Downloading PlantVillage subset...")
    
    for class_name in classes:
        # Create class directory
        class_dir = f"Data/train/{class_name}"
        os.makedirs(class_dir, exist_ok=True)
        
        # Download a few sample images per class (to reduce size)
        for i in range(5):  # Download 5 images per class
            img_url = f"{base_url}{class_name}/{class_name}_{i:03d}.jpg"
            img_path = f"{class_dir}/{class_name}_{i:03d}.jpg"
            
            # Try to download (some images may not exist)
            download_file(img_url, img_path)

def download_sample_images():
    """Download sample plant disease images from various sources"""
    sample_urls = [
        # Apple diseases
        "https://raw.githubusercontent.com/pratikkayal/PlantDoc-Object-Detection/main/test/images/apple_scab.jpg",
        "https://raw.githubusercontent.com/pratikkayal/PlantDoc-Object-Detection/main/test/images/apple_healthy.jpg",
        
        # Tomato diseases  
        "https://raw.githubusercontent.com/pratikkayal/PlantDoc-Object-Detection/main/test/images/tomato_bacterial_spot.jpg",
        "https://raw.githubusercontent.com/pratikkayal/PlantDoc-Object-Detection/main/test/images/tomato_early_blight.jpg",
        "https://raw.githubusercontent.com/pratikkayal/PlantDoc-Object-Detection/main/test/images/tomato_healthy.jpg",
        
        # Other crops
        "https://raw.githubusercontent.com/pratikkayal/PlantDoc-Object-Detection/main/test/images/grape_leaf_blight.jpg",
        "https://raw.githubusercontent.com/pratikkayal/PlantDoc-Object-Detection/main/test/images/corn_common_rust.jpg"
    ]
    
    print("🌱 Downloading sample disease images...")
    
    for i, url in enumerate(sample_urls):
        filename = f"Data/sample_{i:02d}.jpg"
        download_file(url, filename)

def create_training_script():
    """Create a basic training script"""
    script_content = '''#!/usr/bin/env python3
"""
Basic Plant Disease Training Script
Uses transfer learning with MobileNetV2
"""
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam

# Configuration
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 10
NUM_CLASSES = 65  # Adjust based on your dataset

def create_data_generators():
    """Create training and validation data generators"""
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest',
        validation_split=0.2
    )
    
    train_generator = train_datagen.flow_from_directory(
        'Data/train',
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='training'
    )
    
    validation_generator = train_datagen.flow_from_directory(
        'Data/train',
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='validation'
    )
    
    return train_generator, validation_generator

def create_model():
    """Create MobileNetV2 model with transfer learning"""
    base_model = MobileNetV2(
        weights='imagenet',
        include_top=False,
        input_shape=IMG_SIZE + (3,)
    )
    
    # Freeze base model layers
    base_model.trainable = False
    
    # Add custom layers
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.5)(x)
    predictions = Dense(NUM_CLASSES, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=predictions)
    
    # Compile model
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

def train_model():
    """Train the model"""
    print("🌱 Starting Plant Disease Model Training...")
    
    # Create data generators
    train_gen, val_gen = create_data_generators()
    
    # Create model
    model = create_model()
    
    # Train
    history = model.fit(
        train_gen,
        epochs=EPOCHS,
        validation_data=val_gen,
        verbose=1
    )
    
    # Save model
    model.save('models/plant_disease_model_new.keras')
    print("✓ Model saved to models/plant_disease_model_new.keras")
    
    return model, history

if __name__ == "__main__":
    # Check if data exists
    if not os.path.exists('Data/train'):
        print("❌ Training data not found. Run download script first.")
        exit(1)
    
    train_model()
'''
    
    with open("train_plant_model.py", "w") as f:
        f.write(script_content)
    
    print("✓ Created training script: train_plant_model.py")

def main():
    """Main function to download and setup datasets"""
    print("🌾 Plant Disease Dataset Downloader")
    print("=" * 40)
    
    # Create directory structure
    create_directory_structure(".")
    
    # Download sample images
    download_sample_images()
    
    # Download PlantVillage subset
    download_plant_village()
    
    # Create training script
    create_training_script()
    
    print("\n✅ Setup complete!")
    print("\n📁 Directory Structure:")
    print("AgriBot/")
    print("├── Data/")
    print("│   ├── train/          # Training images")
    print("│   ├── valid/          # Validation images") 
    print("│   └── test/           # Test images")
    print("├── models/              # Saved models")
    print("├── train_plant_model.py # Training script")
    print("└── ml_models/          # Current models")
    
    print("\n🚀 Next Steps:")
    print("1. Add more images to Data/train/")
    print("2. Run: python train_plant_model.py")
    print("3. Replace ml_models/plant_disease_model.keras")
    print("4. Test with: python simple_disease_detector.py")

if __name__ == "__main__":
    main()
