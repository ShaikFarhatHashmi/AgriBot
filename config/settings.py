"""
config/settings.py — Application Configuration
================================================
All environment variables and app-wide constants live here.
Never hardcode secrets — always read from .env via python-dotenv.

Usage in other files:
    from config.settings import AppConfig
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env from project root


class AppConfig:
    """Base configuration shared across all environments."""

    # ── Flask ──────────────────────────────────────────────────────────────────
    SECRET_KEY        = os.getenv("SECRET_KEY", "change-me-in-production")
    DEBUG             = False
    TESTING           = False

    # ── Groq LLM ──────────────────────────────────────────────────────────────
    GROQ_API_KEY      = os.getenv("GROQ_API_KEY")
    GROQ_MODEL        = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE   = 0.1
    LLM_MAX_TOKENS    = 512

    # ── Embedding Model ────────────────────────────────────────────────────────
    EMBEDDING_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"

    # ── Vector Store (ChromaDB) ────────────────────────────────────────────────
    CHROMA_DIR        = "./chroma_db"
    FINGERPRINT_FILE  = "./chroma_db/.fingerprint.json"

    # ── Document Sources ───────────────────────────────────────────────────────
    DATA_DIR          = "./Data"           # local PDF folder

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

    # ── Text Splitting ─────────────────────────────────────────────────────────
    CHUNK_SIZE        = 1000
    CHUNK_OVERLAP     = 200
    RETRIEVER_K       = 4                  # top-k chunks to retrieve

    # ── Query Validation ───────────────────────────────────────────────────────
    MAX_QUERY_LENGTH  = 500


class DevelopmentConfig(AppConfig):
    DEBUG = True


class ProductionConfig(AppConfig):
    DEBUG = False


def get_config():
    """Return the correct config class based on FLASK_ENV environment variable."""
    env = os.getenv("FLASK_ENV", "development").lower()
    configs = {
        "development": DevelopmentConfig,
        "production":  ProductionConfig,
    }
    return configs.get(env, DevelopmentConfig)