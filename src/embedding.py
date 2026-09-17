import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

class EmbeddingStore:
    def __init__(self, db_dir: str = "../db", collection_name: str = "circulars"):
        # We ensure ChromaDB persists to disk
        os.makedirs(db_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_dir)
        
        # We use ChromaDB's default ONNX embedding function (all-MiniLM-L6-v2)
        # This completely removes the PyTorch memory overhead!
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=collection_name, 
            embedding_function=self.ef
        )

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Embed and store chunks in ChromaDB."""
        if not chunks:
            return
            
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Generate unique IDs for each chunk based on source and a counter
        ids = [f"{m['source']}_p{m.get('page_number', 0)}_{i}" for i, m in enumerate(metadatas)]
        
        # Store in ChromaDB. The default embedding function handles the embedding automatically.
        self.collection.add(
            ids=ids,
            metadatas=metadatas,
            documents=texts
        )
