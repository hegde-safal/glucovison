document.addEventListener('DOMContentLoaded', () => {

    const analyzeBtn = document.getElementById('analyze-btn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', handleAnalysis);
    }

    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', handleSettingsUpdate);
    }

    if (document.getElementById('chart-sugar')) {
        updateDashboard();
    }

    checkOnboarding();

    const onboardingForm = document.getElementById('onboarding-form');
    if (onboardingForm) {
        onboardingForm.addEventListener('submit', handleOnboarding);
    }
});

function checkOnboarding() {
    // Reverting to localStorage check as requested (Client-side persistence)
    if (localStorage.getItem('glucovision_user_name')) {
        return;
    }

    fetch('/api/settings/status')
        .then(r => r.json())
        .then(data => {
            if (!data.setup_complete) {
                // Only show if backend says we are NOT set up
                document.getElementById('onboarding-modal').classList.remove('hidden');
            }
        })
        .catch(console.error);
}

async function handleOnboarding(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const name = fd.get('name');

    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, sugar_limit: 25.0 })
        });
        document.getElementById('onboarding-modal').classList.add('hidden');
        localStorage.setItem('glucovision_user_name', name);
        alert("Welcome, " + name + "!");
        window.location.reload();
    } catch (error) {
        alert("Setup failed.");
    }
}

async function handleAnalysis() {
    const btn = document.getElementById('analyze-btn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="loader">⚙️</span> Analyzing...`;

    const meals = {
        breakfast: document.getElementById('breakfast').value,
        lunch: document.getElementById('lunch').value,
        snacks: document.getElementById('snacks').value,
        dinner: document.getElementById('dinner').value,
    };

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(meals)
        });

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        displayResults(data);

        // Real-time update of graphs
        await updateDashboard();

    } catch (error) {
        alert("Analysis failed: " + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

function displayResults(data) {
    // Show Results Section
    document.getElementById('results-section').classList.remove('hidden');

    // Update Macros
    const totals = data.totals;
    document.getElementById('cal-val').textContent = totals.total_calories;
    document.getElementById('carb-val').textContent = totals.total_carbs;
    document.getElementById('sugar-val').textContent = totals.total_sugar;
    document.getElementById('prot-val').textContent = totals.total_protein;
    document.getElementById('fat-val').textContent = totals.total_fat;
    document.getElementById('fib-val').textContent = totals.total_fiber;

    // Update Risk
    const riskEl = document.getElementById('risk-card');
    const riskTitle = document.getElementById('risk-title');
    const riskDesc = document.getElementById('risk-desc');

    // Reset classes
    riskEl.className = 'risk-banner';

    if (data.risk_level === 'Safe') {
        riskEl.classList.add('risk-safe');
        riskTitle.innerHTML = '✅ Glycaemic Risk: Low/Safe';
    } else if (data.risk_level === 'Moderate') {
        riskEl.classList.add('risk-moderate');
        riskTitle.innerHTML = '⚠️ Glycaemic Risk: Moderate';
    } else {
        riskEl.classList.add('risk-high');
        riskTitle.innerHTML = '🚨 Glycaemic Risk: High';
    }

    riskDesc.textContent = data.risk_reason || data.risk_level;

    // Suggestions & Analysis
    const sugList = document.getElementById('sug-list');
    sugList.innerHTML = '';

    // Check if new format (object with suggestions/analysis) or old (array)
    let suggestions = [];
    let analysis = [];

    if (Array.isArray(data.suggestions)) {
        suggestions = data.suggestions;
    } else if (typeof data.suggestions === 'object') {
        suggestions = data.suggestions.suggestions || [];
        analysis = data.suggestions.analysis || [];
    }

    // Render Suggestions
    if (suggestions.length > 0) {
        suggestions.forEach(s => {
            const li = document.createElement('li');
            li.textContent = s;
            sugList.appendChild(li);
        });
    } else {
        sugList.innerHTML = '<li>No specific suggestions for this entry.</li>';
    }

    // Render Analysis (Dynamic Section)
    let analysisContainer = document.getElementById('ai-analysis-container');

    // Create container if missing
    if (!analysisContainer) {
        const parent = sugList.parentElement; // .card or similar wrapper
        analysisContainer = document.createElement('div');
        analysisContainer.id = 'ai-analysis-container';
        analysisContainer.style.marginTop = '1.5rem';
        analysisContainer.style.paddingTop = '1rem';
        analysisContainer.style.borderTop = '1px dashed var(--border)';

        const title = document.createElement('h4');
        title.textContent = '📊 AI Risk Analysis';
        title.style.marginBottom = '0.5rem';
        title.style.color = 'var(--primary)';
        title.style.fontSize = '1rem';

        const ul = document.createElement('ul');
        ul.id = 'ai-analysis-list';
        ul.className = 'suggestions-list';

        analysisContainer.appendChild(title);
        analysisContainer.appendChild(ul);
        parent.appendChild(analysisContainer);
    }

    const analysisList = document.getElementById('ai-analysis-list');
    analysisList.innerHTML = '';

    if (analysis.length > 0) {
        analysis.forEach(a => {
            const li = document.createElement('li');
            li.textContent = a;
            li.style.borderLeft = '3px solid var(--accent)';
            li.style.background = 'var(--surface-hover)';
            analysisList.appendChild(li);
        });
        analysisContainer.style.display = 'block';
    } else {
        analysisContainer.style.display = 'none';
    }

    // Unmatched
    if (data.unmatched.length > 0) {
        alert('Could not match: ' + data.unmatched.join(', '));
    }

    // Scroll to results
    riskEl.scrollIntoView({ behavior: 'smooth' });
}

async function handleSettingsUpdate(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const data = Object.fromEntries(fd.entries());

    // Convert checkboxes
    data.weekly = fd.get('weekly') === 'on';
    data.monthly = fd.get('monthly') === 'on';

    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        alert('Settings saved!');
        // Reload to reflect name change in header
        window.location.reload();
    } catch (err) {
        alert('Failed to save settings');
    }
}

// Chart Global Variables to destroy before re-render
let chartSugar = null;
let chartCarbs = null;
let chartFiber = null;
let chartRisk = null;

async function updateDashboard() {
    try {
        const res = await fetch('/api/stats/weekly');
        const data = await res.json();

        // Update Context
        const contextEl = document.getElementById('weekly-context');
        if (contextEl && data.context) {
            contextEl.textContent = data.context;
        }

        renderCharts(data);
    } catch (e) {
        console.error("Failed to update dashboard", e);
    }
}

function renderCharts(data) {
    const commonOptions = {
        responsive: true,
        plugins: {
            legend: { position: 'bottom' }
        },
        scales: {
            y: { beginAtZero: true }
        }
    };

    // 1. Sugar Chart
    const ctxSugar = document.getElementById('chart-sugar').getContext('2d');
    if (chartSugar) chartSugar.destroy();

    chartSugar = new Chart(ctxSugar, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Sugar (g)',
                data: data.sugar,
                borderColor: '#ec4899', // Pink
                backgroundColor: '#fbcfe8',
                tension: 0.3,
                fill: true
            }, {
                label: 'Recommended Limit (25g)',
                data: Array(data.dates.length).fill(25),
                borderColor: '#10b981', // Green
                borderDash: [5, 5],
                pointRadius: 0
            }]
        },
        options: commonOptions
    });

    // 2. Carbs Chart
    const ctxCarbs = document.getElementById('chart-carbs').getContext('2d');
    if (chartCarbs) chartCarbs.destroy();

    chartCarbs = new Chart(ctxCarbs, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Carbs (g)',
                data: data.carbs,
                borderColor: '#3b82f6', // Blue
                backgroundColor: '#dbeafe',
                tension: 0.3,
                fill: true
            }]
        },
        options: commonOptions
    });

    // 3. Fiber vs Carb
    const ctxFiber = document.getElementById('chart-fiber-carb').getContext('2d');
    if (chartFiber) chartFiber.destroy();

    chartFiber = new Chart(ctxFiber, {
        type: 'bar',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Fiber (g)',
                data: data.fiber,
                backgroundColor: '#10b981'
            }, {
                label: 'Carbs (g)',
                data: data.carbs,
                backgroundColor: '#93c5fd'
            }]
        },
        options: commonOptions
    });

    // 4. Risk Summary (Doughnut)
    const ctxRisk = document.getElementById('chart-risk').getContext('2d');
    if (chartRisk) chartRisk.destroy();

    chartRisk = new Chart(ctxRisk, {
        type: 'doughnut',
        data: {
            labels: ['Safe', 'Moderate', 'High'],
            datasets: [{
                data: [
                    data.risk_counts.Safe,
                    data.risk_counts.Moderate,
                    data.risk_counts.High
                ],
                backgroundColor: [
                    '#10b981', // Safe Green
                    '#f59e0b', // Mod Amber
                    '#ef4444'  // High Red
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}
