"""
app/services/disease_predictor.py
CNN-based plant disease prediction service.
Updated settings — MobileNetV2 fine-tuned model:
  - IMG_SIZE    : (224, 224)
  - Normalize   : mobilenet_v2.preprocess_input  → [-1, 1]
  - Color mode  : RGB
  - Classes     : 65
"""
import numpy as np
import json
from PIL import Image
from tensorflow import keras
from settings import AppConfig

# ── Load ONCE at Flask startup ────────────────────────────────
print("[AgriBot] Loading CNN model...")
model = keras.models.load_model(AppConfig.CNN_MODEL_PATH)
print("[AgriBot] CNN model loaded successfully.")

with open(AppConfig.CLASS_MAPPING_PATH, "r") as f:
    class_mapping = json.load(f)

IMG_SIZE = AppConfig.CNN_IMG_SIZE  # (224, 224)


# ── Preprocessing ─────────────────────────────────────────────
def preprocess_image(image_file):
    """
    Matches the MobileNetV2 training pipeline in Kaggle notebook:
      tf.image.decode_jpeg(img, channels=3)               → RGB
      tf.image.resize(img, IMG_SIZE)                       → 224x224
      tf.cast(img, tf.float32)                             → float
      mobilenet_v2.preprocess_input(img)                   → [-1, 1]

    ⚠️  Old pipeline used / 255.0  → [0, 1]
        MobileNetV2 expects       → [-1, 1]
        Using wrong range = bad predictions regardless of training quality
    """
    img = Image.open(image_file).convert("RGB")        # matches channels=3
    img = img.resize(IMG_SIZE)                         # matches resize(224,224)

    img_array = np.array(img, dtype=np.float32)        # float32, still [0, 255]

    # MobileNetV2 preprocessing: scales [0,255] → [-1, 1]
    # Formula internally: (img / 127.5) - 1.0
    img_array = keras.applications.mobilenet_v2.preprocess_input(img_array)

    img_array = np.expand_dims(img_array, axis=0)      # shape → (1, 224, 224, 3)
    return img_array


# # ── Prediction ────────────────────────────────────────────────
# def predict_disease(image_file):
#     img_array    = preprocess_image(image_file)
#     predictions  = model.predict(img_array)            # shape: (1, 65)
#     class_index  = str(np.argmax(predictions))         # e.g. "55"
#     confidence   = float(np.max(predictions)) * 100    # e.g. 94.26

#     disease_name = class_mapping[class_index]
#     # e.g. "Tomato___Late_blight"

#     display_name = disease_name.replace("___", " — ").replace("_", " ")
#     # e.g. "Tomato — Late blight"

#     return {
#         "disease":      disease_name,          # → used for RAG query
#         "display_name": display_name,          # → shown in UI
#         "confidence":   round(confidence, 2),  # → e.g. 94.26
#         "class_index":  class_index,           # → e.g. "55"
#         "reliable":     confidence >= AppConfig.CNN_CONFIDENCE_MIN
#     }

def predict_disease(image_file):
    img_array   = preprocess_image(image_file)
    predictions = model.predict(img_array)[0]  # shape: (65,)

    # ── DIAGNOSTIC — paste console output here, then remove ───
    print("\n" + "="*60)
    print("DIAGNOSTIC REPORT")
    print("="*60)
    print(f"Model arch          : {type(model.layers[1]).__name__}")
    print(f"Total layers        : {len(model.layers)}")
    print(f"Pixel range         : [{img_array.min():.3f}, {img_array.max():.3f}]")
    print(f"Preprocessing OK    : {img_array.min() < -0.5}")
    print(f"Predictions sum     : {predictions.sum():.6f}")
    print(f"Max confidence      : {predictions.max()*100:.2f}%")
    print(f"Top 5 predictions:")
    top5 = predictions.argsort()[::-1][:5]
    for i, idx in enumerate(top5):
        print(f"  {i+1}. [{idx:>2}] {class_mapping[str(idx)]:<45} {predictions[idx]*100:.2f}%")
    print("="*60 + "\n")
    # ── END DIAGNOSTIC ─────────────────────────────────────────

    class_index  = str(np.argmax(predictions))
    confidence   = float(np.max(predictions)) * 100
    disease_name = class_mapping[class_index]
    display_name = disease_name.replace("___", " — ").replace("_", " ")

    return {
        "disease":      disease_name,
        "display_name": display_name,
        "confidence":   round(confidence, 2),
        "class_index":  class_index,
        "reliable":     confidence >= AppConfig.CNN_CONFIDENCE_MIN
    }


# ── RAG Query Builder ─────────────────────────────────────────
def build_rag_query(prediction_result):
    """Converts CNN output into a ChromaDB search query."""
    disease = prediction_result["display_name"]
    return f"What are the symptoms, causes and treatment for {disease}?"