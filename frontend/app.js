const API_BASE = '/api';
let riskChartInstance = null;
let shapChartInstance = null;
let scatterChartInstance = null;
let debounceTimer;

let portfolioAverages = {
    credit_score: 650,
    income: 60000,
    loan_amount: 15000,
    age: 40
};

document.addEventListener('DOMContentLoaded', () => {

    // Theme Toggle
    document.getElementById('theme-btn').addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
        // Update charts color based on mode
        const isLight = document.body.classList.contains('light-mode');
        Chart.defaults.color = isLight ? '#475569' : '#94a3b8';
        if(shapChartInstance) shapChartInstance.update();
    });

    // Export Print
    document.getElementById('export-btn').addEventListener('click', () => {
        window.print();
    });
    
    // Export CSV
    document.getElementById('csv-export-btn').addEventListener('click', () => {
        const custId = document.getElementById('sim-cust-id').value;
        if (!custId) {
            alert("Please load a customer first.");
            return;
        }
        
        const age = document.getElementById('sim-age').value;
        const emp = document.getElementById('sim-emp').value;
        const credit = document.getElementById('sim-credit').value;
        const loan = document.getElementById('sim-loan').value;
        const income = document.getElementById('sim-income').value;
        const risk = document.getElementById('risk-score-value').textContent;
        const clv = document.getElementById('clv-value').textContent;
        const fraud = document.getElementById('fraud-value').textContent;
        
        const csvContent = "data:text/csv;charset=utf-8," 
            + "Customer ID,Age,Employment Length,Credit Score,Loan Amount,Income,Default Risk,Est CLV,Fraud Probability\n"
            + `${custId},${age},${emp},${credit},${loan},${income},${risk},${clv.replace('$','')},${fraud}`;
            
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `customer_${custId}_report.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // Tab switching
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.querySelectorAll('.view-section').forEach(v => {
                v.classList.add('hidden');
                v.classList.remove('active');
            });
            item.classList.add('active');
            const targetId = item.getAttribute('data-target');
            const target = document.getElementById(targetId);
            if (target) {
                target.classList.add('active');
                target.classList.remove('hidden');
            }
        });
    });

    // Settings theme button mirrors main theme toggle
    const settingsThemeBtn = document.getElementById('settings-theme-btn');
    if (settingsThemeBtn) {
        settingsThemeBtn.addEventListener('click', () => {
            document.getElementById('theme-btn').click();
        });
    }

    fetchPortfolio();
    fetchCustomers();
    initRiskChart();
    initShapChart();
    initScatterChart();
    initHeatmap();

    document.getElementById('search-btn').addEventListener('click', () => {
        const customerId = document.getElementById('customer-select').value;
        if (customerId) analyzeCustomer(customerId);
    });

    // CRM Notes
    document.getElementById('save-notes-btn').addEventListener('click', async () => {
        const custId = document.getElementById('sim-cust-id').value;
        const note = document.getElementById('crm-notes-input').value;
        if(!custId) return;
        document.getElementById('save-notes-btn').textContent = 'Saving...';
        try {
            await fetch(`${API_BASE}/customers/${custId}/notes`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({note: note})
            });
            document.getElementById('save-notes-btn').textContent = 'Saved!';
            setTimeout(() => document.getElementById('save-notes-btn').textContent = 'Save Note', 2000);
        } catch(e) { console.error(e); document.getElementById('save-notes-btn').textContent = 'Error'; }
    });

    // Decision Engine
    document.getElementById('decision-engine-btn').addEventListener('click', () => {
        const risk = parseFloat(document.getElementById('risk-score-value').textContent);
        const out = document.getElementById('decision-output');
        if(risk < 15) { out.textContent = "✅ APPROVED"; out.style.color = "#10b981"; }
        else if(risk > 50) { out.textContent = "❌ DECLINED"; out.style.color = "#ef4444"; }
        else { out.textContent = "⚠️ MANUAL REVIEW"; out.style.color = "#f59e0b"; }
    });

    // Setup Slider Listeners
    const simLoan = document.getElementById('sim-loan');
    const simIncome = document.getElementById('sim-income');
    const simEnv = document.getElementById('sim-environment');

    simLoan.addEventListener('input', (e) => {
        document.getElementById('loan-val-display').textContent = '$' + parseInt(e.target.value).toLocaleString();
        triggerSimulation();
    });

    simIncome.addEventListener('input', (e) => {
        document.getElementById('income-val-display').textContent = '$' + parseInt(e.target.value).toLocaleString();
        triggerSimulation();
    });

    simEnv.addEventListener('change', () => {
        triggerSimulation();
    });
});

async function fetchPortfolio() {
    try {
        const res = await fetch(`${API_BASE}/portfolio`);
        const data = await res.json();
        portfolioAverages.credit_score = data.average_credit_score;
        portfolioAverages.income = 65000;
        portfolioAverages.loan_amount = 18000;
        portfolioAverages.age = 45;
    } catch (e) { console.error(e); }
}

async function fetchCustomers() {
    try {
        const res = await fetch(`${API_BASE}/customers`);
        const customers = await res.json();
        const select = document.getElementById('customer-select');
        customers.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.customer_id;
            opt.textContent = `Customer #${c.customer_id}`;
            select.appendChild(opt);
        });
    } catch(e) { console.error(e); }
}

async function analyzeCustomer(customerId) {
    const btn = document.getElementById('search-btn');
    btn.textContent = 'Analyzing...';
    try {
        const res = await fetch(`${API_BASE}/customers/${customerId}`);
        const data = await res.json();
        
        const cust = data.customer;
        
        // Populate Hidden State
        document.getElementById('sim-cust-id').value = cust.customer_id;
        document.getElementById('sim-age').value = cust.age;
        document.getElementById('sim-emp').value = cust.employment_length;
        document.getElementById('sim-credit').value = cust.credit_score;

        // Populate and enable sliders
        const simLoan = document.getElementById('sim-loan');
        const simIncome = document.getElementById('sim-income');
        const simEnv = document.getElementById('sim-environment');
        
        simLoan.value = cust.loan_amount;
        simIncome.value = cust.income;
        simEnv.value = "Neutral";
        simLoan.disabled = false;
        simIncome.disabled = false;
        simEnv.disabled = false;
        
        document.getElementById('loan-val-display').textContent = '$' + parseInt(cust.loan_amount).toLocaleString();
        document.getElementById('income-val-display').textContent = '$' + parseInt(cust.income).toLocaleString();

        // Update UI
        updateProfile(cust);
        updateRisk(data.risk_assessment);
        updateAdvancedMetrics(data.advanced_metrics);
        updateShap(data.xai);
        updateCrossSell(data.recommendations);
        updateScatter(cust, data.risk_assessment.default_probability);
        
        // Fetch CRM notes
        document.getElementById('crm-notes-input').disabled = false;
        document.getElementById('save-notes-btn').disabled = false;
        document.getElementById('decision-engine-btn').disabled = false;
        document.getElementById('decision-output').textContent = "";
        
        try {
            const notesRes = await fetch(`${API_BASE}/customers/${customerId}/notes`);
            const notesData = await notesRes.json();
            document.getElementById('crm-notes-input').value = notesData.notes || "";
        } catch(e) { console.error("Notes fetch failed", e); }


    } catch (e) {
        console.error(e);
        document.getElementById('profile-details').innerHTML = `<div style="color:red; font-weight:bold; padding:10px; border:1px solid red; background:rgba(255,0,0,0.1); border-radius:8px;">
            <h3>ERROR OCCURRED:</h3>
            <p>${e.name}: ${e.message}</p>
            <p style="font-size:0.8em; margin-top:10px;">Please type this exact message to the AI.</p>
        </div>`;
    } finally {
        btn.textContent = 'Load AI Profile';
    }
}

function triggerSimulation() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
        const payload = {
            customer_id: parseInt(document.getElementById('sim-cust-id').value),
            age: parseInt(document.getElementById('sim-age').value),
            employment_length: parseInt(document.getElementById('sim-emp').value),
            credit_score: parseInt(document.getElementById('sim-credit').value),
            loan_amount: parseFloat(document.getElementById('sim-loan').value),
            income: parseFloat(document.getElementById('sim-income').value),
            environment: document.getElementById('sim-environment').value
        };

        if(isNaN(payload.customer_id)) return;

        try {
            const res = await fetch(`${API_BASE}/simulate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            updateRisk(data.risk_assessment);
            updateAdvancedMetrics(data.advanced_metrics);
            updateShap(data.xai);
            updateScatter(payload, data.risk_assessment.default_probability);

            // Calculate Amortization (5 Yrs @ 7%)
            const principal = payload.loan_amount;
            const r = 0.07 / 12;
            const n = 5 * 12;
            const monthlyPayment = principal * (r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
            document.getElementById('monthly-payment-display').textContent = '$' + monthlyPayment.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});

        } catch (e) { console.error("Simulation failed", e); }
    }, 150); 
}

function updateProfile(cust) {
    document.getElementById('profile-details').innerHTML = `
        <div class="info-row"><span class="info-label">Customer ID</span><span class="info-value">#${cust.customer_id}</span></div>
        <div class="info-row"><span class="info-label">Age</span><span class="info-value">${cust.age}</span></div>
        <div class="info-row"><span class="info-label">Credit Score</span><span class="info-value glow-text">${cust.credit_score}</span></div>
        <div class="info-row"><span class="info-label">Employment</span><span class="info-value">${cust.employment_length} yrs</span></div>
        <div class="info-row"><span class="info-label">Income</span><span class="info-value">$${parseInt(cust.income).toLocaleString()}</span></div>
        <div class="info-row"><span class="info-label">Loan Amount</span><span class="info-value">$${parseInt(cust.loan_amount).toLocaleString()}</span></div>
    `;
    const productsSection = document.getElementById('products-section');
    const tagsDiv = document.getElementById('owned-products');
    if (cust.owned_products && cust.owned_products.length) {
        tagsDiv.innerHTML = cust.owned_products.map(p => `<span class="tag">${p}</span>`).join('');
        productsSection.style.display = 'block';
    } else {
        productsSection.style.display = 'none';
    }
}

function initRiskChart() {
    const ctx = document.getElementById('riskChart').getContext('2d');
    riskChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: { datasets: [{ data: [0, 100], backgroundColor: ['#6366f1', 'rgba(150,150,150,0.1)'], borderWidth: 0 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '80%', circumference: 180, rotation: 270, plugins: {tooltip: {enabled: false}}, animation: {duration: 500} }
    });
}

function updateRisk(riskInfo) {
    const prob = riskInfo.default_probability;
    const valEl = document.getElementById('risk-score-value');
    valEl.textContent = prob + '%';
    
    let color = '#10b981'; // green
    if(prob > 50) color = '#ef4444';
    else if(prob > 20) color = '#f59e0b';
    
    valEl.style.color = color;
    
    const arcProb = Math.max(prob, 2); // minimum arc so gauge is always visible
    riskChartInstance.data.datasets[0].data = [arcProb, 100 - arcProb];
    riskChartInstance.data.datasets[0].backgroundColor[0] = color;
    riskChartInstance.update();
}

function updateAdvancedMetrics(metrics) {
    document.getElementById('clv-value').textContent = '$' + metrics.clv.toLocaleString();
    const fraud = metrics.fraud_probability;
    document.getElementById('fraud-value').textContent = fraud.toFixed(1) + '%';
    const bar = document.getElementById('fraud-bar');
    bar.style.width = fraud + '%';
    if(fraud > 20) bar.style.background = 'linear-gradient(90deg, #ef4444, #991b1b)';
    else bar.style.background = 'linear-gradient(90deg, #f59e0b, #ef4444)';
}

function initShapChart() {
    Chart.defaults.color = '#94a3b8';
    const ctx = document.getElementById('shapChart').getContext('2d');
    shapChartInstance = new Chart(ctx, {
        type: 'bar',
        data: { labels: [], datasets: [{ label: 'Impact %', data: [], backgroundColor: [] }] },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            scales: { x: { grid: {color: 'rgba(150,150,150,0.1)'} }, y: { grid: {display: false} } },
            plugins: { legend: {display: false} },
            animation: {duration: 300}
        }
    });
}

function updateShap(xai) {
    shapChartInstance.data.labels = xai.shap_values.map(s => s.feature);
    shapChartInstance.data.datasets[0].data = xai.shap_values.map(s => s.impact);
    shapChartInstance.data.datasets[0].backgroundColor = xai.shap_values.map(s => s.impact > 0 ? '#ef4444' : '#10b981');
    shapChartInstance.update();
}


function updateCrossSell(recs) {
    const div = document.getElementById('recommendations-list');
    if(!recs.length) { div.innerHTML = '<p class="placeholder-text">No offers available.</p>'; return; }
    
    div.innerHTML = recs.map(r => `
        <div class="recommendation-item">
            <div class="rec-info">
                <h3>${r.product}</h3>
                <p>${r.reasons.join(', ')}</p>
            </div>
            <div class="rec-confidence">
                <div class="conf-value">${r.confidence}%</div>
                <div class="conf-label">Confidence</div>
            </div>
        </div>
    `).join('');
}

async function initScatterChart() {
    let backgroundData = [];
    try {
        const res = await fetch(`${API_BASE}/portfolio/scatter`);
        const json = await res.json();
        backgroundData = json.scatter.map(d => ({ x: d.income, y: d.prob }));
    } catch(e) { console.error(e); }

    const ctx = document.getElementById('scatterChart').getContext('2d');
    scatterChartInstance = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Portfolio Sample',
                    data: backgroundData,
                    backgroundColor: 'rgba(150, 150, 150, 0.4)',
                    pointRadius: 4
                },
                {
                    label: 'Current Customer',
                    data: [],
                    backgroundColor: '#ef4444',
                    pointRadius: 8,
                    pointHoverRadius: 10,
                    borderColor: '#fff',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'Income ($)' }, grid: { color: 'rgba(150,150,150,0.1)' } },
                y: { title: { display: true, text: 'Default Risk (%)' }, grid: { color: 'rgba(150,150,150,0.1)' }, min: 0, max: 100 }
            },
            plugins: { tooltip: { callbacks: { label: (ctx) => `Income: $${ctx.raw.x}, Risk: ${ctx.raw.y.toFixed(1)}%` } } }
        }
    });
}

function updateScatter(cust, riskProb) {
    if(!scatterChartInstance) return;
    scatterChartInstance.data.datasets[1].data = [{ x: cust.income, y: riskProb }];
    scatterChartInstance.update();
}


let heatmapChartInstance;
function initHeatmap() {
    const ctx = document.getElementById('heatmapChart').getContext('2d');
    const data = [
        { x: 1, y: 3, r: 25, val: 0.8 }, 
        { x: 2, y: 3, r: 15, val: -0.4 }, 
        { x: 3, y: 1, r: 30, val: 0.9 }, 
        { x: 3, y: 2, r: 20, val: 0.5 }, 
        { x: 1, y: 1, r: 35, val: 1.0 }, 
        { x: 2, y: 2, r: 35, val: 1.0 }, 
        { x: 3, y: 3, r: 35, val: 1.0 }, 
    ];

    heatmapChartInstance = new Chart(ctx, {
        type: 'bubble',
        data: {
            datasets: [{
                label: 'Correlation Strength',
                data: data.map(d => ({ x: d.x, y: d.y, r: d.r })),
                backgroundColor: data.map(d => d.val > 0.7 ? 'rgba(239,68,68,0.7)' : (d.val < 0 ? 'rgba(16,185,129,0.7)' : 'rgba(245,158,11,0.7)'))
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    ticks: { callback: val => ['','Income','Credit','Loan','Default'][val] || '' },
                    min: 0, max: 4, grid: { display: false }
                },
                y: {
                    ticks: { callback: val => ['','Income','Credit','Loan','Default'][val] || '' },
                    min: 0, max: 4, grid: { display: false }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: (ctx) => 'Correlation Intensity: ' + ctx.raw.r } }
            }
        }
    });
}

// ===== CUSTOM ANALYSIS =====
let customRiskChartInstance = null;
let customShapChartInstance = null;

function initCustomCharts() {
    const rctx = document.getElementById('customRiskChart').getContext('2d');
    customRiskChartInstance = new Chart(rctx, {
        type: 'doughnut',
        data: { datasets: [{ data: [0, 100], backgroundColor: ['#6366f1', 'rgba(150,150,150,0.1)'], borderWidth: 0 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '80%', circumference: 180, rotation: 270, plugins: { tooltip: { enabled: false } }, animation: { duration: 500 } }
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

    const prob = data.risk_assessment.default_probability;
    const color = prob > 50 ? '#ef4444' : prob > 20 ? '#f59e0b' : '#10b981';
    const riskEl = document.getElementById('custom-risk-value');
    riskEl.textContent = prob + '%';
    riskEl.style.color = color;
    const arcProb2 = Math.max(prob, 2);
    customRiskChartInstance.data.datasets[0].data = [arcProb2, 100 - arcProb2];
    customRiskChartInstance.data.datasets[0].backgroundColor[0] = color;
    customRiskChartInstance.update();

    document.getElementById('custom-clv-value').textContent = '$' + data.advanced_metrics.clv.toLocaleString(undefined, {maximumFractionDigits: 0});
    const fraud = data.advanced_metrics.fraud_probability;
    document.getElementById('custom-fraud-value').textContent = fraud.toFixed(1) + '%';
    const fraudBar = document.getElementById('custom-fraud-bar');
    fraudBar.style.width = Math.min(fraud, 100) + '%';
    fraudBar.style.background = fraud > 20 ? 'linear-gradient(90deg, #ef4444, #991b1b)' : 'linear-gradient(90deg, #f59e0b, #ef4444)';

    customShapChartInstance.data.labels = data.xai.shap_values.map(s => `${s.feature} (${s.value})`);
    customShapChartInstance.data.datasets[0].data = data.xai.shap_values.map(s => s.impact);
    customShapChartInstance.data.datasets[0].backgroundColor = data.xai.shap_values.map(s => s.impact > 0 ? '#ef4444' : '#10b981');
    customShapChartInstance.update();

    const level = data.risk_assessment.risk_level;
    const lvlColor = level === 'Low' ? '#10b981' : level === 'High' ? '#ef4444' : '#f59e0b';
    document.getElementById('custom-risk-summary').innerHTML = `
        <div class="info-row"><span class="info-label">Risk Level</span><span class="info-value" style="color:${lvlColor}; font-size:1.2rem; font-weight:700;">${level}</span></div>
        <div class="info-row"><span class="info-label">Default Probability</span><span class="info-value">${prob}%</span></div>
        <div class="info-row"><span class="info-label">Est. Lifetime Value</span><span class="info-value">$${data.advanced_metrics.clv.toLocaleString(undefined, {maximumFractionDigits:0})}</span></div>
        <div class="info-row"><span class="info-label">Fraud Score</span><span class="info-value">${fraud.toFixed(1)}%</span></div>
    `;

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
