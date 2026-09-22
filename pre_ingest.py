import os
import sys

# Ensure the src module can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ingestion import ingest_directory
from src.chunking import chunk_documents
from src.embedding import EmbeddingStore

def run_pre_ingestion():
    print("Starting build-time data ingestion...")
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    docs = ingest_directory(data_dir)
    if not docs:
        print("No documents found in data/. Skipping embedding.")
        return
        
    print(f"Found {len(docs)} document pages. Chunking...")
    chunks = chunk_documents(docs)
    
    print("Initializing ChromaDB and downloading ONNX embedding model...")
    # This will download the ONNX weights during the Docker build so they are cached in the image
    store = EmbeddingStore(db_dir="db")
    
    print("Embedding chunks and saving to database...")
    store.add_chunks(chunks)
    
    print("Pre-ingestion complete! Database is baked into the image.")

if __name__ == "__main__":
    run_pre_ingestion()
