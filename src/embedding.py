import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

class EmbeddingStore:
    def __init__(self, db_dir: str = "../db", collection_name: str = "circulars"):
        # We ensure ChromaDB persists to disk
        os.makedirs(db_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_dir)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
        # Load embedding model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Embed and store chunks in ChromaDB."""
        if not chunks:
            return
            
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Generate unique IDs for each chunk based on source and a counter
        ids = [f"{m['source']}_p{m.get('page_number', 0)}_{i}" for i, m in enumerate(metadatas)]
        
        # Embed texts
        embeddings = self.model.encode(texts).tolist()
        
        # Store in ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts
        )
