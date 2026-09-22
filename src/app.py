from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
from typing import List

app = FastAPI(title="Campusquer RAG")

# CORS Setup
origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy load components
retriever = None
generator = None

@app.on_event("startup")
def startup_event():
    global retriever, generator
    from src.retrieval import Retriever
    from src.generation import Generator
    
    print("Loading pre-baked database and models...")
    retriever = Retriever()
    generator = Generator()
    print("System ready!")

class QueryRequest(BaseModel):
    query: str

class Source(BaseModel):
    filename: str
    snippet: str

class QueryResponse(BaseModel):
    answer: str
    answered: bool
    sources: List[Source]

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/gaps")
def gaps_api():
    from src.logging import get_gap_logs
    logs = get_gap_logs()
    # Sort newest first
    return sorted(logs, key=lambda x: x['timestamp'], reverse=True)

@app.get("/documents")
def documents_api():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    if not os.path.isdir(data_dir):
        return []
    docs = []
    for name in sorted(os.listdir(data_dir)):
        path = os.path.join(data_dir, name)
        if os.path.isfile(path) and not name.startswith("."):
            docs.append({"filename": name, "size": os.path.getsize(path)})
    return docs

@app.post("/api/query", response_model=QueryResponse)
def query_api(request: QueryRequest):
    global retriever, generator
    
    try:
        chunks = retriever.retrieve(request.query)
        answer, answered = generator.generate_answer(request.query, chunks)
        
        sources = [
            Source(
                filename=c["metadata"].get("source", "Unknown"), 
                snippet=c["text"]
            ) 
            for c in chunks
        ]
        
        return QueryResponse(answer=answer, answered=answered, sources=sources)
    except Exception as e:
        print(f"Error during query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")
