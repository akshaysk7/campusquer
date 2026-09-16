import os
from datetime import datetime
import json

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "gap_log.jsonl")

def log_gap(query: str):
    """Log queries that the system could not answer based on the provided documents."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query
    }
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

def get_gap_logs():
    """Retrieve all logged gap queries."""
    if not os.path.exists(LOG_FILE):
        return []
        
    logs = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))
    return logs
