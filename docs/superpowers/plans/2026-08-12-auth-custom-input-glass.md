# Auth + Custom Input + Glassmorphism UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add login/signup auth, a "New Analysis" form for custom customer input, and enhanced glassmorphism UI to the banking engine prototype.

**Architecture:** Token-based auth stored in `users.json` (backend) + `localStorage` (frontend); sessions held in-memory (SESSIONS dict). Custom analysis reuses the existing `/api/simulate` endpoint. A separate view section (`view-new-customer`) with its own Chart.js instances renders results inline without touching existing panels.

**Tech Stack:** FastAPI + Python stdlib (`hashlib`, `secrets`) for auth; vanilla JS + Chart.js for frontend; CSS custom properties + backdrop-filter for glassmorphism.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `backend/main.py` | Modify | Add auth imports, SESSIONS dict, helpers, AuthRequest model, 3 auth endpoints, demo user seeding |
| `frontend/index.html` | Modify | Add auth overlay, "New Analysis" nav item, sidebar-footer logout area, new view section |
| `frontend/styles.css` | Modify | Append auth overlay CSS, form grid CSS, enhanced glassmorphism |
| `frontend/app.js` | Modify | Add auth check + handlers at DOMContentLoaded start; add custom form variables + handlers at end |

---

### Task 1: Backend — Auth imports, helpers, model

**Files:**
- Modify: `backend/main.py` (top imports + after NOTES_FILE line)

- [ ] **Step 1: Add `hashlib` and `secrets` to imports**

In `backend/main.py`, change:
```python
import os
import random
import json
```
to:
```python
import os
import random
import json
import hashlib
import secrets
```

- [ ] **Step 2: Add SESSIONS dict, USERS_FILE, helpers, and AuthRequest model**

After the line `NOTES_FILE = "notes.json"`, add:
```python
SESSIONS: dict = {}  # token -> username (in-memory, cleared on restart)
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users: dict) -> None:
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class AuthRequest(BaseModel):
    username: str
    password: str
```

- [ ] **Step 3: Verify file is syntactically valid**

```bash
cd /c/Users/sait9/OneDrive/Desktop/banking_engine/backend
venv/Scripts/python.exe -c "import ast, open; ast.parse(open('main.py').read()); print('OK')"
```
Expected: `OK`

---

### Task 2: Backend — Seed demo user on startup

**Files:**
- Modify: `backend/main.py` (startup_event function)

- [ ] **Step 1: Update startup_event to seed the demo user**

Change:
```python
@app.on_event("startup")
async def startup_event():
    train_models()
```
to:
```python
@app.on_event("startup")
async def startup_event():
    train_models()
    users = load_users()
    if "demo" not in users:
        users["demo"] = hash_password("demo123")
        save_users(users)
        print("Demo user created: demo / demo123")
```

- [ ] **Step 2: Verify syntax**

```bash
cd /c/Users/sait9/OneDrive/Desktop/banking_engine/backend
venv/Scripts/python.exe -c "import py_compile; py_compile.compile('main.py', doraise=True); print('OK')"
```
Expected: `OK`

---

### Task 3: Backend — Auth endpoints (signup / login / verify)

**Files:**
- Modify: `backend/main.py` (add 3 endpoints before the static file mount)

- [ ] **Step 1: Add the three auth endpoints**

Just before the line `# Serve frontend static files`, add:
```python
@app.post("/api/auth/signup")
async def signup(req: AuthRequest):
    if len(req.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    users = load_users()
    if req.username in users:
        raise HTTPException(status_code=400, detail="Username already exists")
    users[req.username] = hash_password(req.password)
    save_users(users)
    token = secrets.token_hex(32)
    SESSIONS[token] = req.username
    return {"token": token, "username": req.username}

@app.post("/api/auth/login")
async def login(req: AuthRequest):
    users = load_users()
    stored = users.get(req.username)
    if not stored or stored != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = secrets.token_hex(32)
    SESSIONS[token] = req.username
    return {"token": token, "username": req.username}

@app.get("/api/auth/verify")
async def verify_token(token: str):
    username = SESSIONS.get(token)
    if username:
        return {"valid": True, "username": username}
    raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
```

- [ ] **Step 2: Verify the app loads and all routes are registered**

```bash
cd /c/Users/sait9/OneDrive/Desktop/banking_engine/backend
venv/Scripts/python.exe -c "
import os; os.chdir(r'C:/Users/sait9/OneDrive/Desktop/banking_engine/backend')
from main import app
paths = [r.path for r in app.routes]
assert '/api/auth/signup' in paths, 'signup missing'
assert '/api/auth/login' in paths, 'login missing'
assert '/api/auth/verify' in paths, 'verify missing'
print('All auth routes registered:', [p for p in paths if 'auth' in p])
"
```
Expected output contains: `['/api/auth/signup', '/api/auth/login', '/api/auth/verify']`

---

### Task 4: Frontend HTML — Auth overlay

**Files:**
- Modify: `frontend/index.html`

- [ ] **Step 1: Add the auth overlay as the first element inside `<body>`**

After `<body>` opening tag (before `<div class="ambient-glow glow-1">`), add:
```html
<!-- ===== AUTH OVERLAY ===== -->
<div id="auth-overlay" class="auth-overlay">
    <div class="auth-container glass-card">
        <div class="auth-logo">
            <div class="logo-orb" style="width:44px;height:44px;"></div>
            <h1 style="font-size:2rem; letter-spacing:-1px;">Aether AI</h1>
        </div>
        <p style="color:var(--text-muted); margin-bottom:1.5rem; text-align:center; font-size:0.95rem;">Banking Intelligence Platform</p>

        <div class="auth-tabs">
            <button class="auth-tab active" id="tab-login">Login</button>
            <button class="auth-tab" id="tab-signup">Sign Up</button>
        </div>

        <!-- Login Form -->
        <div id="login-form">
            <div class="auth-input-wrap">
                <label>Username</label>
                <input type="text" id="login-username" class="glass-input" placeholder="e.g. demo" style="width:100%;" autocomplete="username">
            </div>
            <div class="auth-input-wrap">
                <label>Password</label>
                <input type="password" id="login-password" class="glass-input" placeholder="Enter password" style="width:100%;" autocomplete="current-password">
            </div>
            <div id="login-error" class="auth-error"></div>
            <button id="login-btn" class="neon-btn" style="width:100%; margin-top:1.2rem; font-size:1rem; padding:0.9rem;">Login</button>
            <div class="sample-badge">
                <strong>Sample credentials:</strong><br>
                Username: <code>demo</code> &nbsp;&nbsp; Password: <code>demo123</code>
            </div>
        </div>

        <!-- Signup Form -->
        <div id="signup-form" style="display:none;">
            <div class="auth-input-wrap">
                <label>Username</label>
                <input type="text" id="signup-username" class="glass-input" placeholder="Choose a username (min 3 chars)" style="width:100%;" autocomplete="username">
            </div>
            <div class="auth-input-wrap">
                <label>Password</label>
                <input type="password" id="signup-password" class="glass-input" placeholder="Choose a password (min 4 chars)" style="width:100%;" autocomplete="new-password">
            </div>
            <div id="signup-error" class="auth-error"></div>
            <button id="signup-btn" class="neon-btn" style="width:100%; margin-top:1.2rem; font-size:1rem; padding:0.9rem;">Create Account</button>
        </div>
    </div>
</div>
```

---

### Task 5: Frontend HTML — New nav item + sidebar footer + new view

**Files:**
- Modify: `frontend/index.html`

- [ ] **Step 1: Add "New Analysis" nav item and sidebar footer**

Change the sidebar `<nav>` + close `</aside>` block from:
```html
            <nav class="nav-menu">
                <li class="nav-item active" data-target="view-customer"><span class="icon">🔍</span> AI Assessment</li>
                <li class="nav-item" data-target="view-analytics"><span class="icon">📈</span> Portfolio Analytics</li>
                <li class="nav-item" data-target="view-settings"><span class="icon">⚙️</span> Config</li>
            </nav>
        </aside>
```
to:
```html
            <nav class="nav-menu">
                <li class="nav-item active" data-target="view-customer"><span class="icon">🔍</span> AI Assessment</li>
                <li class="nav-item" data-target="view-analytics"><span class="icon">📈</span> Portfolio Analytics</li>
                <li class="nav-item" data-target="view-new-customer"><span class="icon">➕</span> New Analysis</li>
                <li class="nav-item" data-target="view-settings"><span class="icon">⚙️</span> Config</li>
            </nav>
            <div class="sidebar-footer">
                <div class="sidebar-user" id="logged-in-user"></div>
                <button id="logout-btn" class="logout-btn">Logout</button>
            </div>
        </aside>
```

- [ ] **Step 2: Add the "New Analysis" view section**

Just before `<!-- AI Chatbot Floating UI -->`, add:
```html
            <!-- VIEW: NEW CUSTOMER ANALYSIS -->
            <div id="view-new-customer" class="view-section hidden">
                <header class="topbar glass-panel">
                    <div>
                        <h2>New Customer Analysis</h2>
                        <p style="color:var(--text-muted); font-size:0.85rem; margin-top:0.25rem;">Enter any customer data to get instant AI risk analysis.</p>
                    </div>
                </header>

                <div class="new-customer-layout">
                    <!-- Input Form -->
                    <section class="card glass-card highlight-border">
                        <h2>Customer Input Form</h2>
                        <p style="color:var(--text-muted); font-size:0.85rem; margin:0.5rem 0 1.5rem;">Sample data is pre-filled. Edit any field and click Run Analysis.</p>
                        <div class="input-form-grid">
                            <div class="form-group">
                                <label class="form-label">Age</label>
                                <input type="number" id="input-age" value="35" min="18" max="90" class="glass-input form-input">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Annual Income ($)</label>
                                <input type="number" id="input-income" value="75000" min="10000" max="500000" class="glass-input form-input">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Employment Length (yrs)</label>
                                <input type="number" id="input-emp" value="7" min="0" max="40" class="glass-input form-input">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Credit Score (300–850)</label>
                                <input type="number" id="input-credit" value="680" min="300" max="850" class="glass-input form-input">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Loan Amount ($)</label>
                                <input type="number" id="input-loan" value="25000" min="1000" max="500000" class="glass-input form-input">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Economic Environment</label>
                                <select id="input-env" class="glass-input form-input">
                                    <option value="Neutral">Neutral (Baseline)</option>
                                    <option value="Recession">Severe Recession</option>
                                    <option value="High Interest">High Interest Rates</option>
                                    <option value="Booming">Booming Economy</option>
                                </select>
                            </div>
                        </div>
                        <div style="display:flex; gap:1rem; margin-top:1.5rem;">
                            <button id="analyze-custom-btn" class="neon-btn" style="flex:1; font-size:1rem;">Run AI Analysis</button>
                            <button id="reset-sample-btn" class="neon-btn" style="background:rgba(255,255,255,0.07); color:var(--text-main); box-shadow:none; border:1px solid var(--border-card);">Load Sample</button>
                        </div>
                    </section>

                    <!-- Results Panel (hidden until first run) -->
                    <div id="custom-results-panel" style="display:none; flex-direction:column; gap:1.5rem;">
                        <div class="custom-results-metrics">
                            <section class="card glass-card metrics-card flex-1">
                                <h2 style="margin-bottom:0;">Default Risk</h2>
                                <div class="chart-container-small">
                                    <canvas id="customRiskChart"></canvas>
                                    <div class="gauge-value" id="custom-risk-value">0%</div>
                                </div>
                            </section>
                            <section class="card glass-card metrics-card flex-1 flex-col justify-center">
                                <div class="advanced-metric">
                                    <label>Est. Lifetime Value (CLV)</label>
                                    <div class="metric-big glow-text text-green" id="custom-clv-value">$0</div>
                                </div>
                                <div class="advanced-metric mt-4">
                                    <label>Fraud Probability</label>
                                    <div class="metric-big" id="custom-fraud-value">0%</div>
                                    <div class="progress-bar-bg"><div class="progress-bar-fill" id="custom-fraud-bar"></div></div>
                                </div>
                            </section>
                        </div>

                        <section class="card glass-card">
                            <h2>AI Explainability (SHAP)</h2>
                            <div class="chart-container-wide">
                                <canvas id="customShapChart"></canvas>
                            </div>
                        </section>

                        <section class="card glass-card">
                            <h2>Risk Summary</h2>
                            <div id="custom-risk-summary"></div>
                            <button id="custom-decision-btn" class="neon-btn" style="width:100%; margin-top:1rem;">Run Decision Engine</button>
                            <div id="custom-decision-output" style="text-align:center; margin-top:1rem; font-size:1.3rem; font-weight:bold;"></div>
                        </section>
                    </div>
                </div>
            </div>

```

---

### Task 6: Frontend CSS — Auth styles + form grid + enhanced glassmorphism

**Files:**
- Modify: `frontend/styles.css` (append to end)

- [ ] **Step 1: Append all new CSS to end of styles.css**

```css

/* ===== AUTH OVERLAY ===== */
.auth-overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: linear-gradient(135deg, #08080f 0%, #0d0d1e 100%);
    display: flex; align-items: center; justify-content: center;
    z-index: 9999;
}
.auth-overlay.hidden { display: none; }

.auth-container {
    width: 440px; padding: 2.5rem;
    border: 1px solid rgba(99,102,241,0.45) !important;
    box-shadow: 0 0 80px rgba(99,102,241,0.12), 0 25px 60px rgba(0,0,0,0.6) !important;
    animation: fadeInUp 0.4s ease both;
}
.auth-logo {
    display: flex; align-items: center; gap: 14px;
    justify-content: center; margin-bottom: 0.4rem;
}
.auth-tabs {
    display: flex; margin-bottom: 1.5rem;
    border: 1px solid var(--border-card); border-radius: 10px; overflow: hidden;
}
.auth-tab {
    flex: 1; padding: 0.65rem; background: none; border: none;
    color: var(--text-muted); cursor: pointer; font-family: inherit;
    font-size: 0.9rem; font-weight: 500; transition: all 0.2s;
}
.auth-tab.active {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    color: white; font-weight: 700;
}
.auth-input-wrap { margin-bottom: 1rem; }
.auth-input-wrap label {
    display: block; font-size: 0.78rem; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 0.4rem; font-weight: 600;
}
.auth-error {
    display: none; color: var(--accent-danger); font-size: 0.85rem;
    margin-top: 0.5rem; padding: 0.5rem 0.75rem;
    background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.25); border-radius: 8px;
}
.sample-badge {
    margin-top: 1rem; padding: 0.75rem 1rem; font-size: 0.83rem; line-height: 1.7;
    background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2);
    border-radius: 10px; color: var(--text-muted);
}
.sample-badge code {
    background: rgba(99,102,241,0.2); padding: 0.1rem 0.4rem;
    border-radius: 4px; color: var(--text-main); font-size: 0.85rem; font-family: monospace;
}

/* ===== SIDEBAR FOOTER ===== */
.sidebar-footer {
    margin-top: auto; padding-top: 1.25rem;
    border-top: 1px solid var(--border-card);
    display: flex; flex-direction: column; gap: 0.5rem;
}
.sidebar-user { font-size: 0.78rem; color: var(--text-muted); padding: 0 0.25rem; }
.logout-btn {
    background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2);
    color: #f87171; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer;
    font-family: inherit; font-size: 0.82rem; font-weight: 600; text-align: center;
    transition: all 0.2s;
}
.logout-btn:hover { background: rgba(239,68,68,0.18); color: #ef4444; }

/* ===== CUSTOM ANALYSIS FORM ===== */
.input-form-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem;
}
.form-group { display: flex; flex-direction: column; gap: 0.4rem; }
.form-label {
    font-size: 0.78rem; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600;
}
.form-input { width: 100% !important; }

.new-customer-layout { display: flex; flex-direction: column; gap: 1.5rem; }
.custom-results-metrics { display: flex; gap: 1.5rem; }

/* ===== ENHANCED GLASSMORPHISM ===== */
.glass-card {
    background: linear-gradient(145deg, rgba(22,22,38,0.72) 0%, rgba(12,12,24,0.65) 100%);
    backdrop-filter: blur(22px) saturate(160%);
    -webkit-backdrop-filter: blur(22px) saturate(160%);
}
body.light-mode .glass-card {
    background: linear-gradient(145deg, rgba(255,255,255,0.88) 0%, rgba(248,250,252,0.78) 100%);
}
.glass-panel {
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
}
.highlight-border {
    border: 1px solid rgba(99,102,241,0.5) !important;
    box-shadow:
        0 0 0 1px rgba(99,102,241,0.08),
        0 0 40px rgba(99,102,241,0.07),
        inset 0 0 30px rgba(99,102,241,0.03) !important;
}
.neon-btn {
    box-shadow: 0 0 18px rgba(99,102,241,0.25), 0 4px 15px rgba(236,72,153,0.25);
}
.neon-btn:hover {
    box-shadow: 0 0 30px rgba(99,102,241,0.45), 0 6px 20px rgba(236,72,153,0.45);
    transform: scale(1.025);
}
.glass-input:focus {
    border-color: rgba(99,102,241,0.6);
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12);
    outline: none;
}
```

---

### Task 7: Frontend JS — Auth logic

**Files:**
- Modify: `frontend/app.js`

- [ ] **Step 1: Add auth state variables and check at top of DOMContentLoaded**

At the very start of the `document.addEventListener('DOMContentLoaded', () => {` callback (before the `// Theme Toggle` comment), add:
```javascript
    // ===== AUTH =====
    const authOverlay = document.getElementById('auth-overlay');

    // Optimistic hide if token exists — verify in background
    const storedToken = localStorage.getItem('aether_token');
    if (storedToken) {
        authOverlay.classList.add('hidden');
        fetch(`${API_BASE}/auth/verify?token=${storedToken}`)
            .then(r => r.ok ? r.json() : Promise.reject())
            .then(d => { document.getElementById('logged-in-user').textContent = '👤 ' + d.username; })
            .catch(() => {
                localStorage.removeItem('aether_token');
                localStorage.removeItem('aether_username');
                authOverlay.classList.remove('hidden');
            });
    }

    // Tab switching
    document.getElementById('tab-login').addEventListener('click', () => {
        document.getElementById('tab-login').classList.add('active');
        document.getElementById('tab-signup').classList.remove('active');
        document.getElementById('login-form').style.display = 'block';
        document.getElementById('signup-form').style.display = 'none';
    });
    document.getElementById('tab-signup').addEventListener('click', () => {
        document.getElementById('tab-signup').classList.add('active');
        document.getElementById('tab-login').classList.remove('active');
        document.getElementById('signup-form').style.display = 'block';
        document.getElementById('login-form').style.display = 'none';
    });

    // Login
    const doLogin = async () => {
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        const errEl = document.getElementById('login-error');
        errEl.style.display = 'none';
        if (!username || !password) { errEl.textContent = 'Please fill all fields.'; errEl.style.display = 'block'; return; }
        const btn = document.getElementById('login-btn');
        btn.textContent = 'Logging in...'; btn.disabled = true;
        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Login failed'); }
            const data = await res.json();
            localStorage.setItem('aether_token', data.token);
            localStorage.setItem('aether_username', data.username);
            document.getElementById('logged-in-user').textContent = '👤 ' + data.username;
            authOverlay.classList.add('hidden');
        } catch(e) { errEl.textContent = e.message; errEl.style.display = 'block'; }
        finally { btn.textContent = 'Login'; btn.disabled = false; }
    };
    document.getElementById('login-btn').addEventListener('click', doLogin);
    document.getElementById('login-password').addEventListener('keypress', e => { if(e.key === 'Enter') doLogin(); });

    // Signup
    const doSignup = async () => {
        const username = document.getElementById('signup-username').value.trim();
        const password = document.getElementById('signup-password').value;
        const errEl = document.getElementById('signup-error');
        errEl.style.display = 'none';
        if (!username || !password) { errEl.textContent = 'Please fill all fields.'; errEl.style.display = 'block'; return; }
        const btn = document.getElementById('signup-btn');
        btn.textContent = 'Creating...'; btn.disabled = true;
        try {
            const res = await fetch(`${API_BASE}/auth/signup`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Signup failed'); }
            const data = await res.json();
            localStorage.setItem('aether_token', data.token);
            localStorage.setItem('aether_username', data.username);
            document.getElementById('logged-in-user').textContent = '👤 ' + data.username;
            authOverlay.classList.add('hidden');
        } catch(e) { errEl.textContent = e.message; errEl.style.display = 'block'; }
        finally { btn.textContent = 'Create Account'; btn.disabled = false; }
    };
    document.getElementById('signup-btn').addEventListener('click', doSignup);
    document.getElementById('signup-password').addEventListener('keypress', e => { if(e.key === 'Enter') doSignup(); });

    // Logout
    document.getElementById('logout-btn').addEventListener('click', () => {
        localStorage.removeItem('aether_token');
        localStorage.removeItem('aether_username');
        document.getElementById('logged-in-user').textContent = '';
        document.getElementById('login-username').value = '';
        document.getElementById('login-password').value = '';
        authOverlay.classList.remove('hidden');
    });
    // ===== END AUTH =====

```

---

### Task 8: Frontend JS — Custom analysis form logic

**Files:**
- Modify: `frontend/app.js` (append at end of file)

- [ ] **Step 1: Append custom analysis chart variables and functions at end of app.js**

```javascript

// ===== CUSTOM ANALYSIS =====
let customRiskChartInstance = null;
let customShapChartInstance = null;

function initCustomCharts() {
    const rctx = document.getElementById('customRiskChart').getContext('2d');
    customRiskChartInstance = new Chart(rctx, {
        type: 'doughnut',
        data: { datasets: [{ data: [0, 100], backgroundColor: ['#6366f1', 'rgba(150,150,150,0.1)'], borderWidth: 0, cutout: '80%', circumference: 180, rotation: 270 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { tooltip: { enabled: false } }, animation: { duration: 500 } }
    });

    const sctx = document.getElementById('customShapChart').getContext('2d');
    customShapChartInstance = new Chart(sctx, {
        type: 'bar',
        data: { labels: [], datasets: [{ label: 'Impact %', data: [], backgroundColor: [] }] },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            scales: { x: { grid: { color: 'rgba(150,150,150,0.1)' } }, y: { grid: { display: false } } },
            plugins: { legend: { display: false } }, animation: { duration: 300 }
        }
    });
}

function updateCustomResults(data) {
    const panel = document.getElementById('custom-results-panel');
    panel.style.display = 'flex';

    if (!customRiskChartInstance) initCustomCharts();

    // Risk gauge
    const prob = data.risk_assessment.default_probability;
    const color = prob > 50 ? '#ef4444' : prob > 20 ? '#f59e0b' : '#10b981';
    const riskEl = document.getElementById('custom-risk-value');
    riskEl.textContent = prob + '%';
    riskEl.style.color = color;
    customRiskChartInstance.data.datasets[0].data = [prob, 100 - prob];
    customRiskChartInstance.data.datasets[0].backgroundColor[0] = color;
    customRiskChartInstance.update();

    // Advanced metrics
    document.getElementById('custom-clv-value').textContent = '$' + data.advanced_metrics.clv.toLocaleString(undefined, {maximumFractionDigits: 0});
    const fraud = data.advanced_metrics.fraud_probability;
    document.getElementById('custom-fraud-value').textContent = fraud.toFixed(1) + '%';
    const fraudBar = document.getElementById('custom-fraud-bar');
    fraudBar.style.width = Math.min(fraud, 100) + '%';
    fraudBar.style.background = fraud > 20 ? 'linear-gradient(90deg, #ef4444, #991b1b)' : 'linear-gradient(90deg, #f59e0b, #ef4444)';

    // SHAP
    customShapChartInstance.data.labels = data.xai.shap_values.map(s => `${s.feature} (${s.value})`);
    customShapChartInstance.data.datasets[0].data = data.xai.shap_values.map(s => s.impact);
    customShapChartInstance.data.datasets[0].backgroundColor = data.xai.shap_values.map(s => s.impact > 0 ? '#ef4444' : '#10b981');
    customShapChartInstance.update();

    // Summary table
    const level = data.risk_assessment.risk_level;
    const lvlColor = level === 'Low' ? '#10b981' : level === 'High' ? '#ef4444' : '#f59e0b';
    document.getElementById('custom-risk-summary').innerHTML = `
        <div class="info-row"><span class="info-label">Risk Level</span><span class="info-value" style="color:${lvlColor}; font-size:1.2rem; font-weight:700;">${level}</span></div>
        <div class="info-row"><span class="info-label">Default Probability</span><span class="info-value">${prob}%</span></div>
        <div class="info-row"><span class="info-label">Est. Lifetime Value</span><span class="info-value">$${data.advanced_metrics.clv.toLocaleString(undefined, {maximumFractionDigits:0})}</span></div>
        <div class="info-row"><span class="info-label">Fraud Score</span><span class="info-value">${fraud.toFixed(1)}%</span></div>
    `;

    // Reset decision
    document.getElementById('custom-decision-output').textContent = '';
    document.getElementById('custom-decision-btn').onclick = () => {
        const out = document.getElementById('custom-decision-output');
        if (prob < 15) { out.textContent = '✅ APPROVED'; out.style.color = '#10b981'; }
        else if (prob > 50) { out.textContent = '❌ DECLINED'; out.style.color = '#ef4444'; }
        else { out.textContent = '⚠️ MANUAL REVIEW'; out.style.color = '#f59e0b'; }
    };

    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('analyze-custom-btn').addEventListener('click', async () => {
        const age = parseInt(document.getElementById('input-age').value);
        const income = parseFloat(document.getElementById('input-income').value);
        const emp = parseInt(document.getElementById('input-emp').value);
        const credit = parseInt(document.getElementById('input-credit').value);
        const loan = parseFloat(document.getElementById('input-loan').value);
        const env = document.getElementById('input-env').value;

        if (!age || !income || isNaN(emp) || !credit || !loan) {
            alert('Please fill in all fields before running analysis.');
            return;
        }

        const btn = document.getElementById('analyze-custom-btn');
        btn.textContent = 'Analyzing...'; btn.disabled = true;
        try {
            const res = await fetch(`${API_BASE}/simulate`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ customer_id: 0, age, income, employment_length: emp, credit_score: credit, loan_amount: loan, environment: env })
            });
            if (!res.ok) throw new Error('API error ' + res.status);
            const data = await res.json();
            updateCustomResults(data);
        } catch(e) {
            console.error(e);
            alert('Analysis failed. Make sure the backend server is running.');
        } finally {
            btn.textContent = 'Run AI Analysis'; btn.disabled = false;
        }
    });

    document.getElementById('reset-sample-btn').addEventListener('click', () => {
        document.getElementById('input-age').value = 35;
        document.getElementById('input-income').value = 75000;
        document.getElementById('input-emp').value = 7;
        document.getElementById('input-credit').value = 680;
        document.getElementById('input-loan').value = 25000;
        document.getElementById('input-env').value = 'Neutral';
    });
});
// ===== END CUSTOM ANALYSIS =====
```

---

### Task 9: Smoke test — Run the full app

- [ ] **Step 1: Start backend**

```bash
cd /c/Users/sait9/OneDrive/Desktop/banking_engine/backend
venv/Scripts/python.exe main.py
```
Expected in console: `Demo user created: demo / demo123` (first run only), then `Uvicorn running on http://0.0.0.0:8001`

- [ ] **Step 2: Open browser and verify auth screen appears**

Open `http://localhost:8001` — should see the Aether AI auth overlay, NOT the main dashboard.

- [ ] **Step 3: Log in with sample credentials**

Enter `demo` / `demo123` → click Login → main dashboard should appear.

- [ ] **Step 4: Test "New Analysis" nav item**

Click "➕ New Analysis" in sidebar → form with pre-filled sample data appears.

- [ ] **Step 5: Run a custom analysis**

Click "Run AI Analysis" → results panel appears below form showing risk gauge, CLV, fraud score, SHAP chart, summary.

- [ ] **Step 6: Test "Run Decision Engine"**

Click the button → shows APPROVED / MANUAL REVIEW / DECLINED.

- [ ] **Step 7: Test logout**

Click "Logout" → auth overlay reappears.

- [ ] **Step 8: Test signup**

Click "Sign Up" tab → create a new account → dashboard appears.

- [ ] **Step 9: Test token persistence**

Log in, then refresh the page → dashboard appears immediately (no login screen), username shown in sidebar.

- [ ] **Step 10: Test existing features still work**

Load any customer from "AI Assessment" tab, verify risk chart, SHAP, recommendations, what-if simulator, CRM notes all still function.
