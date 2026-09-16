import os
import time
from src.ingestion import ingest_directory
from src.chunking import chunk_documents
from src.embedding import EmbeddingStore
from src.retrieval import Retriever
from src.generation import Generator
from src.logging import get_gap_logs

def run_demo():
    print("=== College Circulars RAG Demo ===")
    
    # 1. Setup Data Directory
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Create a dummy circular for testing
    dummy_file = os.path.join(data_dir, "exam_schedule_2025.txt")
    if not os.path.exists(dummy_file):
        with open(dummy_file, "w") as f:
            f.write("OFFICIAL CIRCULAR\nDate: 12/03/2025\n\nThe final examinations for the Spring semester will commence on May 15, 2025. Students must carry their ID cards. Any student found with a mobile phone in the exam hall will be immediately suspended.")
        print(f"Created test document: {dummy_file}")
        
    # 2. Ingest & Chunk
    print("\n--- Ingesting and Chunking ---")
    docs = ingest_directory(data_dir)
    chunks = chunk_documents(docs)
    print(f"Extracted {len(docs)} documents into {len(chunks)} chunks.")
    
    # 3. Embed & Store
    print("\n--- Embedding and Storing ---")
    store = EmbeddingStore()
    store.add_chunks(chunks)
    print("Chunks stored in ChromaDB.")
    
    # 4. Initialize components
    retriever = Retriever()
    generator = Generator()
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("\nWARNING: OPENAI_API_KEY is not set. Generation step will likely fail.")
        print("Please set it with: $env:OPENAI_API_KEY='your-key'")
        return

    # Scenario 1: Answered with citation
    query1 = "When do the final exams start?"
    print(f"\n--- Scenario 1: Answerable Query ---")
    print(f"Q: {query1}")
    retrieved1 = retriever.retrieve(query1)
    ans1, _ = generator.generate_answer(query1, retrieved1)
    print(f"A: {ans1}")
    
    # Scenario 2: Refused and logged
    query2 = "What is the penalty for being late to class?"
    print(f"\n--- Scenario 2: Unanswerable Query (Should Refuse) ---")
    print(f"Q: {query2}")
    retrieved2 = retriever.retrieve(query2)
    ans2, _ = generator.generate_answer(query2, retrieved2)
    print(f"A: {ans2}")
    
    # Scenario 3: Viewing Gap Log
    print(f"\n--- Scenario 3: Viewing Gap Log ---")
    logs = get_gap_logs()
    print(f"Found {len(logs)} gap logs:")
    for log in logs:
        print(f" - [{log['timestamp']}] {log['query']}")
        
    print("\n=== Demo Complete ===")
    
if __name__ == "__main__":
    run_demo()
