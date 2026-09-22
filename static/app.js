// Campusquer frontend: plain JS, no dependencies.
// Rule: every piece of model output or document text is written with textContent.
(() => {
    'use strict';

    const API_BASE_URL = window.location.origin;
    const $ = (id) => document.getElementById(id);
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

    // ---------- Elements ----------
    const sidebar = $('sidebar');
    const menuBtn = $('menu-btn');
    const navLinks = [...document.querySelectorAll('.nav-link')];
    const views = [...document.querySelectorAll('.view')];

    const form = $('ask-form');
    const input = $('query-input');
    const askBtn = $('ask-btn');
    const chips = [...document.querySelectorAll('.chip')];

    const pipelineWrap = $('pipeline-wrap');
    const pipelineNote = $('pipeline-note');
    const stages = [...document.querySelectorAll('#pipeline .stage')];
    const srStatus = $('sr-status');

    const answeredEl = $('answered-state');
    const answerText = $('answer-text');
    const answerQuestion = $('answer-question');
    const answerMeta = $('answer-meta');
    const copyBtn = $('copy-btn');
    const sourcesBlock = $('sources-block');
    const sourcesList = $('sources-list');
    const sourcesCount = $('sources-count');
    const refusedEl = $('refused-state');
    const refusedQuestion = $('refused-question');
    const errorEl = $('error-state');
    const errorText = $('error-text');
    const retryBtn = $('retry-btn');

    const statusEl = $('server-status');
    const statusText = $('status-text');
    const startupAlert = $('startup-alert');
    const gapCount = $('gap-count');
    const docCount = $('doc-count');

    const gapList = $('gap-list');
    const gapsStatus = $('gaps-status');
    const docGrid = $('doc-grid');
    const docsStatus = $('docs-status');

    const tplSource = $('tpl-source');
    const tplGap = $('tpl-gap');
    const tplDoc = $('tpl-doc');

    const announce = (msg) => { srStatus.textContent = msg; };

    // ---------- Navigation ----------
    const VIEW_TITLES = { ask: 'Ask', gaps: 'Gap Log', sources: 'Sources', how: 'How It Works' };

    function viewFromHash() {
        const name = window.location.hash.slice(1);
        return Object.prototype.hasOwnProperty.call(VIEW_TITLES, name) ? name : null;
    }

    function showView(name, { focus = false } = {}) {
        views.forEach((v) => { v.hidden = v.dataset.view !== name; });
        navLinks.forEach((a) => {
            if (a.dataset.view === name) a.setAttribute('aria-current', 'page');
            else a.removeAttribute('aria-current');
        });
        document.title = `${VIEW_TITLES[name]} · Campusquer`;
        closeMenu();

        if (name === 'gaps') loadGaps();
        if (name === 'sources') loadDocs();

        if (focus) {
            window.scrollTo(0, 0);
            const heading = document.querySelector(`#view-${name} h1`);
            if (heading) heading.focus({ preventScroll: true });
        }
    }

    window.addEventListener('hashchange', () => {
        const name = viewFromHash();
        // Ignore non-section hashes such as the skip link's #main
        if (name) showView(name, { focus: true });
    });

    function openMenu() {
        sidebar.classList.add('menu-open');
        menuBtn.setAttribute('aria-expanded', 'true');
        menuBtn.setAttribute('aria-label', 'Close menu');
    }
    function closeMenu() {
        sidebar.classList.remove('menu-open');
        menuBtn.setAttribute('aria-expanded', 'false');
        menuBtn.setAttribute('aria-label', 'Open menu');
    }
    menuBtn.addEventListener('click', () => {
        if (sidebar.classList.contains('menu-open')) closeMenu();
        else openMenu();
    });

    // ---------- Keyboard ----------
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && sidebar.classList.contains('menu-open')) {
            closeMenu();
            menuBtn.focus();
            return;
        }
        if (e.key !== '/' || e.ctrlKey || e.metaKey || e.altKey) return;
        const t = e.target;
        if (t instanceof Element && t.closest('input, textarea, select, [contenteditable="true"]')) return;
        e.preventDefault();
        if ($('view-ask').hidden) {
            history.pushState(null, '', '#ask');
            showView('ask');
        }
        input.focus();
        input.select();
    });

    // ---------- Server health / cold start ----------
    let serverOnline = false;

    function setServerStatus(state, label) {
        statusEl.dataset.state = state;
        statusText.textContent = label;
    }

    function markOnline() {
        if (serverOnline) return;
        serverOnline = true;
        startupAlert.hidden = true;
        setServerStatus('online', 'Online');
    }

    async function checkHealth() {
        setServerStatus('checking', 'Checking');
        const slowTimer = setTimeout(() => {
            if (!serverOnline) {
                setServerStatus('waking', 'Waking up');
                startupAlert.hidden = false;
            }
        }, 1500);

        // A sleeping Render instance holds the request until it wakes; a
        // refused connection fails fast, so retry for roughly a minute.
        for (let attempt = 0; attempt < 20 && !serverOnline; attempt++) {
            try {
                const res = await fetch(`${API_BASE_URL}/api/health`, { cache: 'no-store' });
                if (res.ok) { markOnline(); break; }
            } catch (e) {
                // still waking up
            }
            await sleep(3000);
        }

        clearTimeout(slowTimer);
        if (serverOnline) {
            refreshCounts();
        } else {
            startupAlert.hidden = true;
            setServerStatus('offline', 'Offline');
        }
    }

    // ---------- Pipeline status ----------
    let pipelineTimers = [];

    function setStage(i, state) { stages[i].dataset.state = state; }
    function clearPipelineTimers() { pipelineTimers.forEach(clearTimeout); pipelineTimers = []; }

    function startPipeline() {
        clearPipelineTimers();
        pipelineWrap.hidden = false;
        pipelineNote.hidden = true;
        stages.forEach((_, i) => setStage(i, 'idle'));
        setStage(0, 'active');
        announce('Searching circulars');
        pipelineTimers.push(setTimeout(() => { setStage(0, 'done'); setStage(1, 'active'); announce('Reading sources'); }, 900));
        pipelineTimers.push(setTimeout(() => { setStage(1, 'done'); setStage(2, 'active'); announce('Writing answer'); }, 2000));
        pipelineTimers.push(setTimeout(() => { pipelineNote.hidden = false; }, 9000));
    }

    async function finishPipeline() {
        clearPipelineTimers();
        pipelineNote.hidden = true;
        for (let i = 0; i < stages.length; i++) {
            if (stages[i].dataset.state === 'done') continue;
            if (!reduceMotion.matches) {
                setStage(i, 'active');
                await sleep(110);
            }
            setStage(i, 'done');
        }
    }

    function failPipeline() {
        clearPipelineTimers();
        pipelineNote.hidden = true;
        const i = stages.findIndex((s) => s.dataset.state === 'active');
        if (i >= 0) setStage(i, 'failed');
    }

    // ---------- Asking ----------
    let busy = false;
    let lastQuery = '';
    let runId = 0;
    let currentAnswer = '';

    function setBusy(on) {
        busy = on;
        askBtn.disabled = on;
        askBtn.firstElementChild.textContent = on ? 'Asking' : 'Ask';
        chips.forEach((c) => { c.disabled = on; });
        form.setAttribute('aria-busy', String(on));
    }

    function hideResults() {
        answeredEl.hidden = true;
        sourcesBlock.hidden = true;
        refusedEl.hidden = true;
        errorEl.hidden = true;
    }

    async function ask(raw) {
        const query = (raw || '').trim();
        if (busy) return;
        if (!query) { input.focus(); return; }

        const id = ++runId;
        lastQuery = query;
        setBusy(true);
        hideResults();
        startPipeline();

        let data = null;
        let errorMessage = '';
        try {
            const res = await fetch(`${API_BASE_URL}/api/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query }),
            });
            let body = null;
            try { body = await res.json(); } catch (e) { /* non-JSON body */ }
            if (!res.ok) {
                const detail = body && typeof body.detail === 'string' ? body.detail : '';
                throw new Error(detail || `The server responded with status ${res.status}.`);
            }
            if (!body || typeof body.answer !== 'string') {
                throw new Error('The server sent an unexpected response.');
            }
            markOnline();
            data = body;
        } catch (err) {
            errorMessage = err instanceof TypeError
                ? "Couldn't reach the server. Check your connection, then retry."
                : err.message;
        }

        if (errorMessage) {
            failPipeline();
            showError(errorMessage);
        } else {
            await finishPipeline();
            if (data.answered) showAnswer(query, data, id);
            else showRefused(query);
        }
        setBusy(false);
    }

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        ask(input.value);
    });

    chips.forEach((chip) => {
        chip.addEventListener('click', () => {
            input.value = chip.textContent.trim();
            ask(input.value);
        });
    });

    retryBtn.addEventListener('click', () => {
        if (!lastQuery) return;
        input.value = lastQuery;
        ask(lastQuery);
    });

    // ---------- Answered ----------
    function showAnswer(query, data, id) {
        const sources = Array.isArray(data.sources) ? data.sources : [];
        currentAnswer = data.answer;

        answerQuestion.textContent = query;
        answerMeta.textContent = sources.length
            ? `${sources.length} source${sources.length === 1 ? '' : 's'} retrieved`
            : '';
        copyBtn.textContent = 'Copy';
        answeredEl.hidden = false;
        announce('Answer ready');

        typeOut(answerText, data.answer, id).then((completed) => {
            if (completed) renderWithCitations(answerText, data.answer);
        });

        renderSources(sources, data.answer);
    }

    // Types the answer out, always finishing in about a second or less.
    function typeOut(el, text, id) {
        return new Promise((resolve) => {
            if (reduceMotion.matches || text.length < 2) {
                el.textContent = text;
                resolve(true);
                return;
            }
            const duration = Math.min(1000, 250 + text.length * 3);
            const start = performance.now();
            el.classList.add('typing');
            el.textContent = '';

            function frame(now) {
                if (id !== runId) { el.classList.remove('typing'); resolve(false); return; }
                const p = Math.min(1, (now - start) / duration);
                const eased = 1 - (1 - p) * (1 - p);
                el.textContent = text.slice(0, Math.round(text.length * eased));
                if (p < 1) {
                    requestAnimationFrame(frame);
                } else {
                    el.classList.remove('typing');
                    resolve(true);
                }
            }
            requestAnimationFrame(frame);
        });
    }

    // Wraps [bracketed citations] in spans, using text nodes only.
    function renderWithCitations(el, text) {
        const frag = document.createDocumentFragment();
        const re = /\[[^[\]\n]{2,200}\]/g;
        let last = 0;
        let m;
        while ((m = re.exec(text)) !== null) {
            if (m.index > last) frag.append(document.createTextNode(text.slice(last, m.index)));
            const span = document.createElement('span');
            span.className = 'cite';
            span.textContent = m[0];
            frag.append(span);
            last = re.lastIndex;
        }
        frag.append(document.createTextNode(text.slice(last)));
        el.replaceChildren(frag);
    }

    function renderSources(sources, answer) {
        sourcesList.replaceChildren();
        if (!sources.length) return;

        const totals = {};
        sources.forEach((s) => { const f = String(s.filename || 'Unknown'); totals[f] = (totals[f] || 0) + 1; });
        const seen = {};
        const answerLower = String(answer || '').toLowerCase();

        sources.forEach((src, i) => {
            const filename = String(src.filename || 'Unknown');
            seen[filename] = (seen[filename] || 0) + 1;

            const node = tplSource.content.firstElementChild.cloneNode(true);
            const head = node.querySelector('.source-head');
            const body = node.querySelector('.source-body');
            const bodyId = `source-body-${i}`;

            node.querySelector('.source-idx').textContent = String(i + 1).padStart(2, '0');
            node.querySelector('.source-name').textContent = totals[filename] > 1
                ? `${filename} · passage ${seen[filename]}`
                : filename;
            node.querySelector('.source-name').title = filename;
            node.querySelector('.source-snippet').textContent = String(src.snippet || '');
            if (answerLower.includes(filename.toLowerCase())) {
                node.querySelector('.source-cited').hidden = false;
            }

            body.id = bodyId;
            head.setAttribute('aria-controls', bodyId);
            head.addEventListener('click', () => {
                const open = head.getAttribute('aria-expanded') !== 'true';
                head.setAttribute('aria-expanded', String(open));
                body.hidden = !open;
                node.classList.toggle('open', open);
            });

            sourcesList.append(node);
        });

        sourcesCount.textContent = `· ${sources.length}`;
        sourcesBlock.hidden = false;
    }

    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(currentAnswer);
            copyBtn.textContent = 'Copied';
        } catch (e) {
            copyBtn.textContent = 'Copy failed';
        }
        setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1600);
    });

    // ---------- Refused & error ----------
    function showRefused(query) {
        refusedQuestion.textContent = query;
        refusedEl.hidden = false;
        announce('Not found in the circulars. Your question has been logged for the administration.');
        refreshCounts();
    }

    function showError(message) {
        errorText.textContent = message;
        errorEl.hidden = false;
    }

    // ---------- Gap log ----------
    let gapsToken = 0;

    async function fetchJSON(path) {
        const res = await fetch(`${API_BASE_URL}${path}`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`Status ${res.status}`);
        return res.json();
    }

    function setCount(el, n) { el.textContent = n > 0 ? String(n) : ''; }

    const dateFmt = new Intl.DateTimeFormat(undefined, {
        day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });
    const relFmt = typeof Intl.RelativeTimeFormat === 'function'
        ? new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' })
        : null;

    function relativeTime(date) {
        if (!relFmt) return '';
        const secs = Math.round((date.getTime() - Date.now()) / 1000);
        const units = [['year', 31536000], ['month', 2592000], ['week', 604800], ['day', 86400], ['hour', 3600], ['minute', 60]];
        for (const [unit, size] of units) {
            if (Math.abs(secs) >= size) return relFmt.format(Math.round(secs / size), unit);
        }
        return 'just now';
    }

    async function loadGaps() {
        const token = ++gapsToken;
        gapsStatus.hidden = false;
        gapsStatus.classList.remove('is-error');
        gapsStatus.textContent = 'Loading gap log…';

        try {
            const logs = await fetchJSON('/api/gaps');
            if (token !== gapsToken) return;
            const list = Array.isArray(logs) ? logs : [];
            setCount(gapCount, list.length);
            gapList.replaceChildren();

            if (!list.length) {
                gapsStatus.textContent = 'No unanswered questions yet. Every question so far was covered by the circulars.';
                return;
            }
            gapsStatus.hidden = true;

            list.forEach((log) => {
                const row = tplGap.content.firstElementChild.cloneNode(true);
                const time = row.querySelector('.gap-time');
                const stamp = String(log.timestamp || '');
                const date = new Date(stamp);
                time.setAttribute('datetime', stamp);
                if (Number.isNaN(date.getTime())) {
                    row.querySelector('.gap-date').textContent = stamp;
                } else {
                    row.querySelector('.gap-date').textContent = dateFmt.format(date);
                    row.querySelector('.gap-rel').textContent = relativeTime(date);
                }
                row.querySelector('.gap-query').textContent = String(log.query || '');
                gapList.append(row);
            });
        } catch (e) {
            if (token !== gapsToken) return;
            gapList.replaceChildren();
            gapsStatus.textContent = "Couldn't load the gap log. Check the connection and press Refresh.";
            gapsStatus.classList.add('is-error');
        }
    }

    $('gaps-refresh').addEventListener('click', loadGaps);

    // ---------- Sources (documents) ----------
    let docsToken = 0;

    function formatSize(bytes) {
        if (typeof bytes !== 'number' || !Number.isFinite(bytes)) return '';
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    async function loadDocs() {
        const token = ++docsToken;
        docsStatus.hidden = false;
        docsStatus.classList.remove('is-error');
        docsStatus.textContent = 'Loading documents…';

        try {
            const docs = await fetchJSON('/documents');
            if (token !== docsToken) return;
            const list = Array.isArray(docs) ? docs : [];
            setCount(docCount, list.length);
            docGrid.replaceChildren();

            if (!list.length) {
                docsStatus.textContent = 'No documents in the knowledge base yet.';
                return;
            }
            docsStatus.hidden = true;

            list.forEach((doc) => {
                const name = String(doc.filename || '');
                const dot = name.lastIndexOf('.');
                const tile = tplDoc.content.firstElementChild.cloneNode(true);
                tile.querySelector('.doc-type').textContent = dot > 0 ? name.slice(dot + 1).toUpperCase() : 'FILE';
                tile.querySelector('.doc-name').textContent = name;
                tile.querySelector('.doc-size').textContent = formatSize(doc.size);
                docGrid.append(tile);
            });
        } catch (e) {
            if (token !== docsToken) return;
            docGrid.replaceChildren();
            docsStatus.textContent = "Couldn't load the document list. Check the connection and try again.";
            docsStatus.classList.add('is-error');
        }
    }

    // Quietly fill the sidebar counts without touching the views.
    async function refreshCounts() {
        try {
            const logs = await fetchJSON('/api/gaps');
            if (Array.isArray(logs)) setCount(gapCount, logs.length);
        } catch (e) { /* counts are optional */ }
        try {
            const docs = await fetchJSON('/documents');
            if (Array.isArray(docs)) setCount(docCount, docs.length);
        } catch (e) { /* counts are optional */ }
    }

    // ---------- Init ----------
    showView(viewFromHash() || 'ask');
    checkHealth();
})();
