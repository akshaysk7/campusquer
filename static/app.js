// Configure API Base URL
const API_BASE_URL = window.location.origin;

// DOM Elements
const inputElement = document.getElementById('query-input');
const askBtn = document.getElementById('ask-btn');
const examples = document.querySelectorAll('.example-btn');
const resultContainer = document.getElementById('result-container');

const states = {
    loading: document.getElementById('loading-state'),
    answered: document.getElementById('answered-state'),
    refused: document.getElementById('refused-state'),
    error: document.getElementById('error-state')
};

// --- Initialization & Health Check ---
document.addEventListener('DOMContentLoaded', async () => {
    // Check server health to handle cold starts
    const startupAlert = document.getElementById('startup-alert');
    let isHealthy = false;
    
    // Show alert if it takes more than 1.5s to respond
    const slowStartTimer = setTimeout(() => {
        if (!isHealthy) startupAlert.classList.remove('hidden');
    }, 1500);

    try {
        await fetch(`${API_BASE_URL}/api/health`);
        isHealthy = true;
    } catch (e) {
        console.warn("Health check failed, server might be waking up");
    } finally {
        clearTimeout(slowStartTimer);
        startupAlert.classList.add('hidden');
    }
});

// --- Search Functionality ---
inputElement.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') executeSearch();
});

askBtn.addEventListener('click', executeSearch);
document.getElementById('retry-btn').addEventListener('click', executeSearch);

examples.forEach(btn => {
    btn.addEventListener('click', () => {
        inputElement.value = btn.textContent;
        executeSearch();
    });
});

function showState(stateName) {
    resultContainer.classList.remove('hidden');
    Object.keys(states).forEach(key => {
        if (key === stateName) {
            states[key].classList.remove('hidden');
        } else {
            states[key].classList.add('hidden');
        }
    });
}

async function executeSearch() {
    const query = inputElement.value.trim();
    if (!query) return;

    showState('loading');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || "The server encountered an error while processing the request.");
        }
        
        if (data.answered) {
            // Render Answer
            document.getElementById('answer-text').textContent = data.answer;
            
            // Render Sources
            const sourcesList = document.getElementById('sources-list');
            sourcesList.innerHTML = ''; // safe to clear
            
            // Deduplicate exact snippet matches if necessary, but backend chunks are usually unique
            data.sources.forEach((src, idx) => {
                const card = document.createElement('div');
                card.className = "bg-white border border-slate-200 rounded-lg p-4 shadow-sm";
                
                const header = document.createElement('div');
                header.className = "flex items-center gap-2 mb-2 text-campus-700 font-medium text-sm";
                header.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>`;
                
                const titleNode = document.createElement('span');
                titleNode.textContent = src.filename;
                header.appendChild(titleNode);
                
                const body = document.createElement('p');
                body.className = "text-sm text-slate-600 line-clamp-3 leading-relaxed";
                body.textContent = src.snippet;
                
                card.appendChild(header);
                card.appendChild(body);
                sourcesList.appendChild(card);
            });
            
            showState('answered');
        } else {
            // Document refused to answer
            showState('refused');
        }
        
    } catch (error) {
        document.getElementById('error-text').textContent = error.message;
        showState('error');
    }
}

// --- View Switching & Gap Logs ---
const tabQa = document.getElementById('tab-qa');
const tabLogs = document.getElementById('tab-logs');
const viewQa = document.getElementById('view-qa');
const viewLogs = document.getElementById('view-logs');

tabQa.addEventListener('click', () => {
    tabQa.className = "hover:text-campus-100 transition-colors font-medium tab-active";
    tabLogs.className = "text-campus-100/70 hover:text-campus-100 transition-colors tab-inactive";
    viewQa.classList.remove('hidden');
    viewLogs.classList.add('hidden');
});

tabLogs.addEventListener('click', () => {
    tabLogs.className = "hover:text-campus-100 transition-colors font-medium tab-active";
    tabQa.className = "text-campus-100/70 hover:text-campus-100 transition-colors tab-inactive";
    viewLogs.classList.remove('hidden');
    viewQa.classList.add('hidden');
    
    // Fetch logs when tab is opened
    fetchGapLogs();
});

async function fetchGapLogs() {
    const tbody = document.getElementById('logs-table-body');
    const loading = document.getElementById('logs-loading');
    const empty = document.getElementById('logs-empty');
    
    tbody.innerHTML = '';
    loading.classList.remove('hidden');
    empty.classList.add('hidden');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/gaps`);
        const logs = await response.json();
        
        loading.classList.add('hidden');
        
        if (!logs || logs.length === 0) {
            empty.classList.remove('hidden');
            return;
        }
        
        logs.forEach(log => {
            const tr = document.createElement('tr');
            tr.className = "hover:bg-slate-50 transition-colors";
            
            const tdDate = document.createElement('td');
            tdDate.className = "px-6 py-4 text-slate-500 whitespace-nowrap";
            tdDate.textContent = new Date(log.timestamp).toLocaleString();
            
            const tdQuery = document.createElement('td');
            tdQuery.className = "px-6 py-4 text-slate-800 font-medium";
            tdQuery.textContent = log.query;
            
            tr.appendChild(tdDate);
            tr.appendChild(tdQuery);
            tbody.appendChild(tr);
        });
        
    } catch (error) {
        loading.classList.add('hidden');
        empty.classList.remove('hidden');
        empty.textContent = "Failed to load gap logs. Please check connection.";
    }
}

// Initial tab state
tabQa.className = "hover:text-campus-100 transition-colors font-medium tab-active";
tabLogs.className = "text-campus-100/70 hover:text-campus-100 transition-colors tab-inactive";
