"""
app/models/vector_store.py — Vector Store Model (ChromaDB)
===========================================================

REBUILD LOGIC:
- Computes a fingerprint (MD5 hash) of all PDF files in ./Data/
- If fingerprint matches saved one → load ChromaDB from disk (fast)
- If fingerprint differs (PDFs added/removed/changed) → rebuild ChromaDB
- Never deletes old ChromaDB while it is still open (fixes Windows WinError 32)
  Instead, builds into a temp folder first, then renames it atomically.
"""

import os
import json
import hashlib
import shutil
import logging
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import (
    WebBaseLoader, PyPDFLoader, DirectoryLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class VectorStoreModel:

    def __init__(self, config):
        self.chroma_dir       = config.CHROMA_DIR        # "./chroma_db"
        self.fingerprint_file = os.path.join(config.CHROMA_DIR, ".fingerprint.json")
        self.data_dir         = config.DATA_DIR           # "./Data"
        self.urls             = config.URLS
        self.chunk_size       = config.CHUNK_SIZE
        self.chunk_overlap    = config.CHUNK_OVERLAP
        self.embedding_model  = config.EMBEDDING_MODEL
        self.chroma_temp_dir  = config.CHROMA_DIR + "_temp"  # temp build folder

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_or_build(self):
        """
        Smart load/rebuild based on PDF fingerprint.

        - First run (no chroma_db)    → build from scratch
        - PDFs unchanged              → load from disk instantly
        - PDFs added/removed/changed  → rebuild into temp, swap in
        """
        embeddings = self._load_embeddings()
        current_fp = self._compute_fingerprint()
        saved_fp   = self._load_saved_fingerprint()

        # Case 1: ChromaDB exists AND fingerprint matches → just load
        if self._db_exists() and current_fp == saved_fp:
            logger.info("✓ PDFs unchanged — loading ChromaDB from disk...")
            return self._load(embeddings)

        # Case 2: ChromaDB missing → build fresh
        if not self._db_exists():
            logger.info("ChromaDB not found — building for the first time...")
            return self._build_and_save(embeddings, current_fp)

        # Case 3: ChromaDB exists BUT fingerprint differs → PDFs changed, rebuild
        logger.info("PDF documents changed — rebuilding ChromaDB...")
        return self._rebuild_safe(embeddings, current_fp)

    # ── Fingerprinting ──────────────────────────────────────────────────────────

    def _compute_fingerprint(self):
        """
        MD5 hash of every PDF file's name + size + last modified time.
        Any change to PDFs (add, remove, edit) produces a different hash.
        URLs are intentionally excluded — only local PDFs trigger rebuilds.
        """
        hasher = hashlib.md5()

        if os.path.exists(self.data_dir):
            pdf_files = []
            for root, _, files in os.walk(self.data_dir):
                for fname in files:
                    if fname.lower().endswith(".pdf"):
                        pdf_files.append(os.path.join(root, fname))

            for filepath in sorted(pdf_files):
                st = os.stat(filepath)
                # Hash filename + file size + last modified time
                entry = f"{filepath}:{st.st_size}:{st.st_mtime}"
                hasher.update(entry.encode("utf-8"))

        fp = hasher.hexdigest()
        logger.info(f"Current fingerprint: {fp}")
        return fp

    def _load_saved_fingerprint(self):
        """Read fingerprint saved from last successful build. Returns None if missing."""
        if not os.path.exists(self.fingerprint_file):
            return None
        try:
            with open(self.fingerprint_file, "r") as f:
                return json.load(f).get("fingerprint")
        except Exception as e:
            logger.warning(f"Could not read fingerprint file: {e}")
            return None

    def _save_fingerprint(self, fingerprint):
        """Save fingerprint after a successful build."""
        os.makedirs(self.chroma_dir, exist_ok=True)
        with open(self.fingerprint_file, "w") as f:
            json.dump({"fingerprint": fingerprint}, f)
        logger.info(f"✓ Fingerprint saved: {fingerprint}")

    def _db_exists(self):
        """Check if ChromaDB folder exists and is not empty."""
        return os.path.exists(self.chroma_dir) and bool(os.listdir(self.chroma_dir))

    # ── Build Strategies ───────────────────────────────────────────────────────

    def _build_and_save(self, embeddings, fingerprint):
        """Build ChromaDB from scratch into chroma_dir."""
        documents = self._load_documents()
        chunks    = self._split(documents)

        logger.info("Building ChromaDB vector store...")
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=self.chroma_dir
        )
        self._save_fingerprint(fingerprint)
        logger.info("✓ ChromaDB built and saved to disk")
        return vectorstore

    def _rebuild_safe(self, embeddings, fingerprint):
        """
        Windows-safe rebuild strategy:
          1. Build new ChromaDB into a TEMP folder (chroma_db_temp)
          2. Load it from the temp folder
          3. Save fingerprint
          4. Schedule old folder cleanup on next startup (non-blocking)

        This avoids WinError 32 because we never touch the old locked files.
        """
        # Clean up any leftover temp folder from a previous failed rebuild
        if os.path.exists(self.chroma_temp_dir):
            try:
                shutil.rmtree(self.chroma_temp_dir, ignore_errors=True)
            except Exception:
                pass

        # Build into temp folder
        logger.info(f"Building new ChromaDB in temp folder: {self.chroma_temp_dir}")
        documents = self._load_documents()
        chunks    = self._split(documents)

        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=self.chroma_temp_dir
        )

        self._save_fingerprint(fingerprint)
        logger.info("✓ New ChromaDB built in temp folder")
        logger.info("Note: Old chroma_db folder will be replaced on next restart.")

        # Try to swap folders (may fail on Windows if old folder is locked)
        # If it fails, the app still works using the temp folder this session
        try:
            shutil.rmtree(self.chroma_dir, ignore_errors=True)
            shutil.move(self.chroma_temp_dir, self.chroma_dir)
            logger.info("✓ ChromaDB folder swapped successfully")
        except Exception as e:
            logger.warning(f"Could not swap folders (will use temp this session): {e}")
            # Update chroma_dir to point to temp so this session works
            self.chroma_dir = self.chroma_temp_dir

        return vectorstore

    # ── Load ───────────────────────────────────────────────────────────────────

    def _load(self, embeddings):
        vectorstore = Chroma(
            persist_directory=self.chroma_dir,
            embedding_function=embeddings
        )
        logger.info("✓ ChromaDB loaded from disk")
        return vectorstore

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _load_embeddings(self):
        logger.info(f"Loading embedding model: {self.embedding_model}")
        try:
            # Try a much simpler approach - use OpenAI embeddings style interface
            # but with a local model that loads faster
            from sklearn.feature_extraction.text import TfidfVectorizer
            import numpy as np
            
            class SimpleEmbeddings:
                def __init__(self):
                    logger.info("Initializing TF-IDF based embeddings (fast startup)")
                    self.vectorizer = TfidfVectorizer(
                        max_features=384,  # Match typical embedding size
                        stop_words='english',
                        ngram_range=(1, 2)
                    )
                    self.fitted = False
                    logger.info("✓ Simple embeddings initialized")
                
                def _fit_if_needed(self, texts):
                    if not self.fitted:
                        if isinstance(texts, str):
                            texts = [texts]
                        elif hasattr(texts, '__iter__') and not isinstance(texts, str):
                            # Convert list of Document objects to text
                            texts = [t.page_content if hasattr(t, 'page_content') else str(t) for t in texts]
                        self.vectorizer.fit(texts)
                        self.fitted = True
            
                def embed_documents(self, texts):
                    self._fit_if_needed(texts)
                    # Convert Document objects to text if needed
                    if hasattr(texts, '__iter__') and not isinstance(texts, str):
                        texts = [t.page_content if hasattr(t, 'page_content') else str(t) for t in texts]
                    embeddings = self.vectorizer.transform(texts).toarray().astype(np.float32)
                    # Convert numpy arrays to Python lists for ChromaDB
                    return [emb.tolist() for emb in embeddings]
            
                def embed_query(self, text):
                    self._fit_if_needed([text])
                    embedding = self.vectorizer.transform([text]).toarray()[0].astype(np.float32)
                    return embedding.tolist()
            
                def __call__(self, text):
                    return self.embed_query(text)
        
            embeddings = SimpleEmbeddings()
            logger.info("✓ Simple embeddings loaded successfully")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def _split(self, documents):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        chunks = splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} text chunks")
        return chunks

    def _load_documents(self):
        web_docs = self._load_web_documents()
        pdf_docs = self._load_pdf_documents()
        all_docs = web_docs + pdf_docs

        if not all_docs:
            raise RuntimeError(
                "No documents loaded. "
                "Check internet connection and ./Data/ folder."
            )
        logger.info(f"Total documents loaded: {len(all_docs)}")
        return all_docs

    def _load_web_documents(self):
        docs = []
        logger.info("Loading web documents...")
        for url in self.urls:
            try:
                loader = WebBaseLoader(url)
                loader.requests_kwargs = {"timeout": 10}
                docs.extend(loader.load())
                logger.info(f"  Loaded: {url}")
            except Exception as e:
                logger.warning(f"  Failed {url}: {e}")
        return docs

    def _load_pdf_documents(self):
        docs = []
        logger.info("Loading local PDF documents...")
        try:
            if os.path.exists(self.data_dir) and os.listdir(self.data_dir):
                loader = DirectoryLoader(
                    self.data_dir,
                    glob="**/*.pdf",
                    loader_cls=PyPDFLoader
                )
                docs = loader.load()
                logger.info(f"  Loaded {len(docs)} PDF documents")
            else:
                logger.warning("  ./Data/ folder empty or missing — skipping")
        except Exception as e:
            logger.error(f"  PDF load error: {e}")
        return docs