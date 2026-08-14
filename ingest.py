import logging
from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ==========================================================
# Configuration
# ==========================================================

PDF_PATH = "data/data.pdf"
DB_FAISS_PATH = "vectorstore/db_faiss"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ==========================================================
# Logging
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# ==========================================================
# Main
# ==========================================================

def create_vector_db():

    logger.info("=" * 70)
    logger.info("Medical Knowledge Base Creation Started")
    logger.info("=" * 70)

    # ------------------------------------------------------
    # Load PDF
    # ------------------------------------------------------

    logger.info(f"Loading PDF: {PDF_PATH}")

    loader = PyMuPDFLoader(PDF_PATH)

    documents = loader.load()

    logger.info(f"Successfully loaded {len(documents)} pages.")

    # ------------------------------------------------------
    # Split into chunks
    # ------------------------------------------------------

    logger.info("Splitting pages into chunks...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            ". ",
            "? ",
            "! ",
            "; ",
            ", ",
            " ",
            ""
        ]
    )

    texts = splitter.split_documents(documents)

    logger.info(f"Created {len(texts)} chunks.")

    # ------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------

    logger.info("Loading embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu"
        },
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 16
        }
    )

    # ------------------------------------------------------
    # Build FAISS
    # ------------------------------------------------------

    logger.info("Generating embeddings...")

    db = FAISS.from_documents(
        texts,
        embeddings
    )

    Path(DB_FAISS_PATH).mkdir(
        parents=True,
        exist_ok=True
    )

    db.save_local(DB_FAISS_PATH)

    logger.info("=" * 70)
    logger.info("Medical Knowledge Base Created Successfully")
    logger.info("=" * 70)
    logger.info(f"PDF File         : {PDF_PATH}")
    logger.info(f"Pages Loaded     : {len(documents)}")
    logger.info(f"Chunks Created   : {len(texts)}")
    logger.info(f"Embedding Model  : {EMBEDDING_MODEL}")
    logger.info(f"Vector DB Saved  : {DB_FAISS_PATH}")
    logger.info("=" * 70)


if __name__ == "__main__":
    create_vector_db()