from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os

from src.retrieval import Retriever
from src.generation import Generator
from src.logging import get_gap_logs
from src.ingestion import ingest_directory
from src.chunking import chunk_documents
from src.embedding import EmbeddingStore

app = FastAPI(title="College Circulars RAG")

# Lazy load components
retriever = None
generator = None

@app.on_event("startup")
def startup_event():
    # We no longer eagerly load the models or ingest here to save memory.
    # Everything is deferred to the first user request (lazy-loading).
    pass

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: list

@app.post("/api/query", response_model=QueryResponse)
def query_api(request: QueryRequest):
    global retriever, generator
    
    # Lazy Initialization on first request
    if retriever is None or generator is None:
        print("Lazy-loading models and database on first request...")
        # Ingest documents just-in-time
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(data_dir, exist_ok=True)
        docs = ingest_directory(data_dir)
        
        if docs:
            chunks = chunk_documents(docs)
            store = EmbeddingStore()
            store.add_chunks(chunks)
            print("Just-in-time ingestion complete!")
            
        retriever = Retriever()
        generator = Generator()

    chunks = retriever.retrieve(request.query)
    answer, _ = generator.generate_answer(request.query, chunks)
    
    sources = [{"source": c["metadata"].get("source"), "page": c["metadata"].get("page_number")} for c in chunks]
    return QueryResponse(answer=answer, sources=sources)

@app.get("/api/logs")
def logs_api():
    return {"gap_logs": get_gap_logs()}

@app.get("/", response_class=HTMLResponse)
def index():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>University Knowledge Base</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            campus: {
                                900: '#1a365d',
                                800: '#2a4365',
                                700: '#2b6cb0',
                            }
                        }
                    }
                }
            }
        </script>
        <style>
            body { font-family: 'Inter', system-ui, -apple-system, sans-serif; }
            .loader { border: 3px solid #f3f3f3; border-top: 3px solid #2b6cb0; border-radius: 50%; width: 24px; height: 24px; animation: spin 1s linear infinite; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body class="bg-slate-50 min-h-screen text-slate-800">
        <!-- Navigation -->
        <nav class="bg-campus-900 text-white shadow-lg">
            <div class="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
                <div class="text-xl font-bold flex items-center gap-2">
                    <i class="fa-solid fa-building-columns"></i>
                    University Knowledge Base
                </div>
                <button onclick="toggleLogs()" class="text-sm bg-campus-800 hover:bg-campus-700 px-4 py-2 rounded transition">
                    <i class="fa-solid fa-clipboard-list mr-1"></i> Admin Logs
                </button>
            </div>
        </nav>

        <main class="max-w-3xl mx-auto px-4 py-12">
            <!-- Search Header -->
            <div class="text-center mb-10">
                <h1 class="text-4xl font-extrabold text-campus-900 mb-4">Official Circulars Directory</h1>
                <p class="text-slate-500">Ask any question about university policies, exam schedules, or official notices. Answers are generated exclusively from verified circulars.</p>
            </div>

            <!-- Search Box -->
            <div class="bg-white rounded-xl shadow-md p-2 flex items-center border border-slate-200 focus-within:ring-2 focus-within:ring-campus-700 focus-within:border-transparent transition-all">
                <i class="fa-solid fa-magnifying-glass text-slate-400 ml-3 mr-2"></i>
                <input type="text" id="query" class="w-full py-3 px-2 outline-none text-lg bg-transparent" placeholder="e.g., When do the final exams start?" onkeypress="handleKeyPress(event)">
                <button onclick="ask()" id="askBtn" class="bg-campus-700 hover:bg-campus-800 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center gap-2">
                    Search
                </button>
            </div>

            <!-- Results Section -->
            <div id="result-container" class="mt-8 hidden">
                <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                    <div class="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-2">
                        <i class="fa-solid fa-robot text-campus-700"></i>
                        <span class="font-semibold text-campus-900">Official Response</span>
                    </div>
                    <div class="p-6">
                        <div id="loading" class="hidden flex items-center gap-3 text-slate-500">
                            <div class="loader"></div>
                            Searching official documents...
                        </div>
                        <div id="answer-text" class="text-lg leading-relaxed text-slate-700 mb-6 hidden whitespace-pre-wrap"></div>
                        
                        <!-- Sources -->
                        <div id="sources-container" class="hidden">
                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Cited Sources</h4>
                            <ul id="sources-list" class="flex flex-wrap gap-2"></ul>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Admin Logs Section (Hidden by default) -->
            <div id="logs-section" class="mt-16 hidden">
                <h3 class="text-xl font-bold text-campus-900 mb-4 flex items-center gap-2">
                    <i class="fa-solid fa-file-circle-exclamation text-amber-500"></i> Unanswered Queries Log
                </h3>
                <p class="text-sm text-slate-500 mb-4">Questions asked by students that were not found in the current document database.</p>
                <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-sm">
                            <thead class="bg-slate-50 border-b border-slate-200">
                                <tr>
                                    <th class="px-6 py-3 font-semibold text-slate-700">Timestamp</th>
                                    <th class="px-6 py-3 font-semibold text-slate-700">Student Question</th>
                                </tr>
                            </thead>
                            <tbody id="logs-table-body" class="divide-y divide-slate-100">
                                <!-- Logs injected here -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </main>

        <script>
            function handleKeyPress(e) {
                if (e.key === 'Enter') ask();
            }

            async function ask() {
                const q = document.getElementById('query').value.trim();
                if (!q) return;

                // UI State
                const resultContainer = document.getElementById('result-container');
                const loading = document.getElementById('loading');
                const answerText = document.getElementById('answer-text');
                const sourcesContainer = document.getElementById('sources-container');
                
                resultContainer.classList.remove('hidden');
                loading.classList.remove('hidden');
                answerText.classList.add('hidden');
                sourcesContainer.classList.add('hidden');

                try {
                    const response = await fetch('/api/query', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({query: q})
                    });
                    const data = await response.json();
                    
                    // Display answer
                    loading.classList.add('hidden');
                    answerText.innerHTML = data.answer;
                    answerText.classList.remove('hidden');

                    // Display sources if applicable
                    if (data.sources && data.sources.length > 0) {
                        const uniqueSources = [...new Set(data.sources.map(s => JSON.stringify(s)))].map(s => JSON.parse(s));
                        const sourcesList = document.getElementById('sources-list');
                        sourcesList.innerHTML = '';
                        uniqueSources.forEach(src => {
                            const li = document.createElement('li');
                            li.className = "bg-slate-100 border border-slate-200 text-slate-600 text-xs px-3 py-1.5 rounded-full flex items-center gap-1.5";
                            li.innerHTML = `<i class="fa-regular fa-file-pdf"></i> ${src.source} (Page ${src.page})`;
                            sourcesList.appendChild(li);
                        });
                        sourcesContainer.classList.remove('hidden');
                    }
                    
                    // Refresh logs in background
                    fetchLogs();
                } catch (error) {
                    loading.classList.add('hidden');
                    answerText.innerHTML = "An error occurred connecting to the server.";
                    answerText.classList.remove('hidden');
                }
            }
            
            let logsVisible = false;
            function toggleLogs() {
                logsVisible = !logsVisible;
                const logsSection = document.getElementById('logs-section');
                if (logsVisible) {
                    logsSection.classList.remove('hidden');
                    fetchLogs();
                } else {
                    logsSection.classList.add('hidden');
                }
            }

            async function fetchLogs() {
                if (!logsVisible) return;
                try {
                    const response = await fetch('/api/logs');
                    const data = await response.json();
                    const tbody = document.getElementById('logs-table-body');
                    tbody.innerHTML = '';
                    
                    if (data.gap_logs.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="2" class="px-6 py-4 text-center text-slate-400">No unanswered queries logged yet.</td></tr>';
                        return;
                    }

                    // Sort newest first
                    data.gap_logs.reverse().forEach(log => {
                        const date = new Date(log.timestamp).toLocaleString();
                        const tr = document.createElement('tr');
                        tr.className = "hover:bg-slate-50 transition-colors";
                        tr.innerHTML = `
                            <td class="px-6 py-4 text-slate-500 whitespace-nowrap">${date}</td>
                            <td class="px-6 py-4 text-slate-800 font-medium">${log.query}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                } catch (error) {
                    console.error("Failed to fetch logs", error);
                }
            }
        </script>
    </body>
    </html>
    """
    return html
