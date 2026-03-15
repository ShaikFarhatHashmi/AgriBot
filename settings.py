"""

settings.py - All app configuration in one place

Place this file in your project ROOT (same folder as run.py)

"""

import os

from dotenv import load_dotenv



load_dotenv()



class AppConfig:



    # Flask

    SECRET_KEY       = os.getenv("SECRET_KEY", "agribot-secret-key")

    DEBUG            = False



    # Groq LLM

    GROQ_API_KEY     = os.getenv("GROQ_API_KEY")

    GROQ_MODEL       = "llama-3.3-70b-versatile"

    LLM_TEMPERATURE  = 0.1

    LLM_MAX_TOKENS   = 2048



    # Embeddings

    EMBEDDING_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"



    # ChromaDB

    CHROMA_DIR       = "./chroma_db"

    FINGERPRINT_FILE = "./chroma_db/.fingerprint.json"



    # Documents

    DATA_DIR         = "./Data"

    URLS = [

        "https://vikaspedia.in/agriculture/crop-production",

        "https://www.fao.org/agriculture/crops/en/",

        "https://vikaspedia.in/agriculture/crop-production/integrated-pest-management",

        "https://vikaspedia.in/agriculture/soil-health",

        "https://agritech.tnau.ac.in/pdf/AGRICULTURE.pdf",

        "https://tnau.ac.in/site/research/wp-content/uploads/sites/60/2020/02/Horticulture-CPG-2020.pdf",

        "https://bmpbooks.com/media/Infosheet-15-Soil-Management.pdf",

        "https://nesfp.org/sites/default/files/resources/organic_production_and_soil_management_basics_rapp_curriculum_share.pdf",

    ]



    # Text splitting

    CHUNK_SIZE       = 4000

    CHUNK_OVERLAP    = 200

    RETRIEVER_K      = 4



    # Validation

    MAX_QUERY_LENGTH = 500



    # ── CNN Plant Disease Detection ───────────────────────────────

    BASE_DIR                 = os.path.dirname(os.path.abspath(__file__))

    CNN_MODEL_PATH           = os.path.join(BASE_DIR, "ml_models", "plant_disease_model.keras")

    CLASS_MAPPING_PATH       = os.path.join(BASE_DIR, "ml_models", "class_mapping.json")

    CNN_IMG_SIZE             = (224, 224)

    CNN_CONFIDENCE_MIN       = 40.0

    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    MAX_IMAGE_SIZE_MB        = 5



    # ── Chat History (SQLite) ─────────────────────────────────────

    CHAT_DB_PATH = os.path.join(BASE_DIR, "chat_history.db")