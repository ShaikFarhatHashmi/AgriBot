# chat2.py - GROQ VERSION (with Smart ChromaDB Persistence)
#
# How ChromaDB persistence works here:
#   1. A "fingerprint" is computed from your URL list + PDF files in ./Data/
#   2. On startup, the saved fingerprint is compared to the current one
#   3. If they MATCH  → load existing ChromaDB from disk (fast startup)
#   4. If they DIFFER → rebuild ChromaDB from scratch (sources changed)
#   5. The new fingerprint is saved after every successful rebuild

from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import os
import json
import hashlib
import shutil
import stat
import time
import logging
from dotenv import load_dotenv

# ── Environment setup ──────────────────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file!")

# ── Constants ──────────────────────────────────────────────────────────────────
CHROMA_DIR       = "./chroma_db"
FINGERPRINT_FILE = "./chroma_db/.fingerprint.json"
DATA_DIR         = "./Data"

# ── URL list (your data sources) ──────────────────────────────────────────────
# IMPORTANT: Any change here (add/remove/edit a URL) will trigger a DB rebuild
URLS = [
    # Crop profitability & farming guides
    "https://vikaspedia.in/agriculture/crop-production",
    "https://www.fao.org/agriculture/crops/en/",

    # Indian agriculture specific
    "https://vikaspedia.in/agriculture/crop-production/integrated-pest-management",
    "https://vikaspedia.in/agriculture/soil-health",

    # Crop production
    "https://agritech.tnau.ac.in/pdf/AGRICULTURE.pdf",

    # Horticulture
    "https://tnau.ac.in/site/research/wp-content/uploads/sites/60/2020/02/Horticulture-CPG-2020.pdf",

    # Soil management
    "https://bmpbooks.com/media/Infosheet-15-Soil-Management.pdf",
    "https://nesfp.org/sites/default/files/resources/organic_production_and_soil_management_basics_rapp_curriculum_share.pdf",
]

# ── Lazy initialization ────────────────────────────────────────────────────────
qa_chain = None

def get_chain():
    """Return the QA chain, building it on first call (lazy loading)."""
    global qa_chain
    if qa_chain is None:
        logger.info("QA chain not yet initialized — building now...")
        qa_chain = setup_chain()
    return qa_chain


# ══════════════════════════════════════════════════════════════════════════════
#  FINGERPRINTING SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

def compute_fingerprint():
    """
    Create a unique fingerprint of all current data sources.

    Built from:
      - Sorted list of URLs
      - Each PDF file's name + size + last-modified time

    Any change in URLs or PDF files produces a different fingerprint.
    """
    hasher = hashlib.md5()

    # 1. Hash the URLs
    for url in sorted(URLS):
        hasher.update(url.encode("utf-8"))

    # 2. Hash PDF file metadata
    if os.path.exists(DATA_DIR):
        pdf_files = []
        for root, _, files in os.walk(DATA_DIR):
            for filename in files:
                if filename.lower().endswith(".pdf"):
                    pdf_files.append(os.path.join(root, filename))

        for filepath in sorted(pdf_files):
            file_stat = os.stat(filepath)
            file_info = f"{filepath}:{file_stat.st_size}:{file_stat.st_mtime}"
            hasher.update(file_info.encode("utf-8"))

    fingerprint = hasher.hexdigest()
    logger.info(f"Computed fingerprint: {fingerprint}")
    return fingerprint


def load_saved_fingerprint():
    """Load the fingerprint saved from the last ChromaDB build. Returns None if not found."""
    if not os.path.exists(FINGERPRINT_FILE):
        return None
    try:
        with open(FINGERPRINT_FILE, "r") as f:
            return json.load(f).get("fingerprint")
    except Exception as e:
        logger.warning(f"Could not read fingerprint file: {e}")
        return None


def save_fingerprint(fingerprint):
    """Save fingerprint to disk after a successful ChromaDB build."""
    os.makedirs(CHROMA_DIR, exist_ok=True)
    with open(FINGERPRINT_FILE, "w") as f:
        json.dump({"fingerprint": fingerprint}, f)
    logger.info(f"✓ Fingerprint saved: {fingerprint}")


def should_rebuild_db():
    """
    Decide if ChromaDB needs to be rebuilt.

    Returns:
        (bool, str) → (rebuild_needed, reason_message)
    """
    # Case 1: ChromaDB folder missing entirely
    if not os.path.exists(CHROMA_DIR) or not os.listdir(CHROMA_DIR):
        return True, "ChromaDB not found — building for the first time"

    # Case 2: DB exists but no fingerprint (built before this system was added)
    saved = load_saved_fingerprint()
    if saved is None:
        return True, "No fingerprint found — rebuilding to establish baseline"

    # Case 3: Compare current vs saved fingerprint
    current = compute_fingerprint()
    if current != saved:
        return True, "Sources changed (fingerprint mismatch) — rebuilding ChromaDB"

    return False, "Sources unchanged — loading existing ChromaDB (fast startup)"


# ══════════════════════════════════════════════════════════════════════════════
#  DOCUMENT LOADING
# ══════════════════════════════════════════════════════════════════════════════

def load_documents():
    """Load all documents from URLs and local PDFs."""

    logger.info("Loading web documents...")
    web_docs = []
    for url in URLS:
        try:
            loader = WebBaseLoader(url)
            loader.requests_kwargs = {"timeout": 10}
            web_docs.extend(loader.load())
            logger.info(f"  ✓ Loaded: {url}")
        except Exception as e:
            logger.warning(f"  ✗ Failed to load {url}: {e}")

    logger.info("Loading local PDF documents...")
    pdf_docs = []
    try:
        if os.path.exists(DATA_DIR) and os.listdir(DATA_DIR):
            pdf_loader = DirectoryLoader(DATA_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader)
            pdf_docs = pdf_loader.load()
            logger.info(f"  ✓ Loaded {len(pdf_docs)} PDF documents")
        else:
            logger.warning("  ./Data/ folder not found or empty — skipping local PDFs")
    except Exception as e:
        logger.error(f"  ✗ Failed to load PDFs: {e}")

    all_docs = web_docs + pdf_docs
    logger.info(f"Total documents loaded: {len(all_docs)}")

    if not all_docs:
        raise RuntimeError(
            "No documents loaded from any source. "
            "Check your internet connection and ./Data/ folder."
        )
    return all_docs


# ══════════════════════════════════════════════════════════════════════════════
#  VECTOR STORE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def force_delete_directory(path):
    """
    Windows-safe directory deletion.

    On Windows, ChromaDB holds file locks even after the client is closed.
    shutil.rmtree() fails with [WinError 5] Access Denied in that case.

    This function handles it by:
      1. Retrying up to 5 times with a short wait between attempts
      2. On each retry, forcing read-only files to be writable first
         (Windows often marks DB files as read-only)
      3. If all retries fail, it raises a clear error message
    """
    def handle_remove_error(func, path, exc_info):
        """Called by shutil.rmtree when a file can't be deleted."""
        try:
            # Remove read-only flag and retry deletion
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception as e:
            logger.warning(f"Could not remove {path}: {e}")

    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            shutil.rmtree(path, onerror=handle_remove_error)
            if not os.path.exists(path):
                logger.info(f"✓ Successfully deleted {path}")
                return
        except Exception as e:
            logger.warning(f"Delete attempt {attempt}/{max_retries} failed: {e}")

        if attempt < max_retries:
            wait = attempt * 2  # 2s, 4s, 6s, 8s between retries
            logger.info(f"Waiting {wait}s before retry...")
            time.sleep(wait)

    raise RuntimeError(
        f"Could not delete '{path}' after {max_retries} attempts.\n"
        "Please manually delete the 'chroma_db' folder and restart the app."
    )


def build_vectorstore(embeddings):
    """Delete old ChromaDB, load fresh documents, and build a new vector store."""
    if os.path.exists(CHROMA_DIR):
        logger.info("Deleting old ChromaDB...")
        force_delete_directory(CHROMA_DIR)

    all_docs = load_documents()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(all_docs)
    logger.info(f"Created {len(splits)} text chunks")

    logger.info("Building ChromaDB vector store...")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    logger.info("✓ ChromaDB built and saved to disk")
    return vectorstore


def load_vectorstore(embeddings):
    """Load an existing ChromaDB from disk."""
    logger.info("Loading existing ChromaDB from disk...")
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )
    logger.info("✓ ChromaDB loaded from disk")
    return vectorstore


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN SETUP
# ══════════════════════════════════════════════════════════════════════════════

def setup_chain():
    """Initialize and return the full QA chain with smart ChromaDB persistence."""

    # Step 1: Should we rebuild ChromaDB?
    rebuild, reason = should_rebuild_db()
    logger.info(f"ChromaDB decision: {reason}")

    # Step 2: Load embeddings (needed whether rebuilding or loading)
    logger.info("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Step 3: Build or load ChromaDB
    if rebuild:
        current_fingerprint = compute_fingerprint()
        vectorstore = build_vectorstore(embeddings)
        save_fingerprint(current_fingerprint)   # Save AFTER successful build
    else:
        vectorstore = load_vectorstore(embeddings)

    # Step 4: Initialize Groq LLM
    logger.info("Initializing Groq LLM...")
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        max_tokens=512,
        groq_api_key=GROQ_API_KEY
    )

    # Step 5: Prompt template
    prompt_template = """You are AgriBot, an expert agricultural assistant
specializing in Indian farming and agriculture.

Instructions:
- If the context contains relevant information, use it as your PRIMARY source
- If the context is insufficient, supplement with your own agricultural knowledge
- If you genuinely don't know something, say so honestly rather than guessing
- Focus on Indian agriculture, crops, and farming practices
- Be specific, practical, and easy to understand for farmers

Context: {context}

Farmer's Question: {question}

Provide a complete and helpful answer:"""

    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    # Step 6: Retriever
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )

    # Step 7: Build QA chain
    logger.info("Creating QA chain...")
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=False,
        chain_type_kwargs={"prompt": PROMPT}
    )

    logger.info("✓ AgriBot QA chain is ready!")
    return chain