from typing import List, Dict, Any
from src.embedding import EmbeddingStore

class Retriever:
    def __init__(self, db_dir: str = "../db", collection_name: str = "circulars"):
        self.store = EmbeddingStore(db_dir=db_dir, collection_name=collection_name)
        
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve the top_k most similar chunks for a given query."""
        
        # Embed the query using the same model
        query_embedding = self.store.model.encode([query]).tolist()
        
        # Query ChromaDB collection
        results = self.store.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        
        # Format results
        retrieved_chunks = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                retrieved_chunks.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else None
                })
                
        return retrieved_chunks
