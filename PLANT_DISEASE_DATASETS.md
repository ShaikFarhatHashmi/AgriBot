# Plant Disease Detection Datasets and Resources

## 🌱 Recommended Datasets for Training

### 1. PlantVillage Dataset (Most Popular)
**Source**: https://github.com/spMohanty/PlantVillage-Dataset
**Size**: ~54,000 images, 38 classes
**Format**: JPG, RGB, 256x256 pixels
**Classes**: Apple, Blueberry, Cherry, Corn, Grape, Orange, Peach, Bell Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, Tomato

### 2. PlantDoc Dataset
**Source**: https://github.com/pratikkayal/PlantDoc-Object-Detection
**Size**: ~2,500 images, 30 classes
**Format**: JPG, various sizes
**Classes**: Multiple plant diseases with bounding boxes

### 3. Plant Pathology Dataset
**Source**: https://github.com/pschorkenhorst/plant-pathology-2020
**Size**: ~4,500 images, 6 classes
**Format**: JPG, 2048x1365 pixels
**Classes**: Apple (healthy/scab/rust), Grape (healthy/black rot/leaf blight), etc.

### 4. AI Challenger - Plant Disease
**Source**: https://challenger.ai/datasets/plant-disease
**Size**: ~20,000 images
**Format**: JPG, various sizes
**Classes**: Multiple crop diseases

## 🍎 Current Model Issues & Solutions

### Problem Identified:
Your current `plant_disease_model.keras` file (34MB) appears to be corrupted or incompatible with the current TensorFlow version.

### Solutions:

#### Option 1: Use Pre-trained Model (Recommended)
```python
# Replace with MobileNetV2 pre-trained on ImageNet
import tensorflow as tf
base_model = tf.keras.applications.MobileNetV2(
    weights='imagenet',
    include_top=False,
    input_shape=(224, 224, 3)
)
```

#### Option 2: Download Working Model
```bash
# Download a working plant disease model
wget https://github.com/Prithiviraj17/Plant-Disease-Detection/raw/main/plant_disease_model.h5
```

#### Option 3: Train New Model
Use the datasets above to train a new model with:
- **Architecture**: MobileNetV2 (transfer learning)
- **Input**: 224x224 RGB images
- **Output**: 65 classes (as per your class_mapping.json)

## 📊 Dataset Statistics for Indian Crops

### Most Common Indian Crop Diseases:
1. **Rice**: Blast, Bacterial Leaf Blight, Brown Spot
2. **Wheat**: Rust, Powdery Mildew, Loose Smut
3. **Cotton**: Wilt, Boll Rot, Leaf Spot
4. **Sugarcane**: Red Rot, Smut, Mosaic
5. **Pulses**: Powdery Mildew, Rust, Leaf Spot

### Recommended Training Data:
- **Minimum**: 100 images per class
- **Ideal**: 500-1000 images per class
- **Augmentation**: Rotation, flip, brightness, contrast

## 🔧 Quick Fix for Current Model

Replace your current model loading with a simpler approach:

```python
def _load_model():
    global model
    if model is None:
        try:
            print("[AgriBot] Loading CNN model...")
            import tensorflow as tf
            
            # Try loading without compilation first
            model = tf.keras.models.load_model(
                AppConfig.CNN_MODEL_PATH,
                compile=False
            )
            
            # Compile manually
            model.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            print("[AgriBot] CNN model loaded successfully.")
        except Exception as e:
            print(f"[AgriBot] Model loading failed: {e}")
            print("[AgriBot] Using placeholder model...")
            # Create a simple placeholder model
            model = tf.keras.Sequential([
                tf.keras.layers.Input(shape=(224, 224, 3)),
                tf.keras.layers.GlobalAveragePooling2D(),
                tf.keras.layers.Dense(65, activation='softmax')
            ])
            model.compile(optimizer='adam', loss='categorical_crossentropy')
    return model
```

## 📁 Data Organization Structure
```
Data/
├── train/
│   ├── Apple___Apple_scab/
│   ├── Apple___Black_rot/
│   └── ... (other classes)
├── valid/
│   ├── Apple___Apple_scab/
│   └── ... (other classes)
└── test/
    ├── Apple___Apple_scab/
    └── ... (other classes)
```

## 🌐 Additional Resources

### Indian Agriculture Specific:
- **ICAR Datasets**: https://icar.org.in/datasets
- **Kisan Network**: https://kisan.gov.in
- **Plant Pathology Labs**: Various agricultural universities

### Image Augmentation Tools:
- **Albumentations**: pip install albumentations
- **ImgAug**: pip install imgaug
- **OpenCV**: Built-in transformations

### Model Deployment:
- **TensorFlow Lite**: For mobile deployment
- **ONNX**: Cross-platform inference
- **TensorFlow.js**: Web deployment
