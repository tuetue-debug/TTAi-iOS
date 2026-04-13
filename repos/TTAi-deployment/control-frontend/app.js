// TTAi Control Dashboard - Main JavaScript

// Configuration
const API_BASE = window.location.origin; // Same origin as FastAPI

// State
let currentPage = 'overview';
let overviewData = null;
let quotaData = null;
let billingData = null;
let errorsData = null;
let modelsData = null;
let systemData = null;
let usageData = null;
let topologyData = null;
let proxyStateData = null;
let proxyBackendsData = null;
let proxyBenchmarkData = null;

// DOM Elements
const navItems = document.querySelectorAll('.nav-item');
const pages = document.querySelectorAll('.page');
const pageTitle = document.querySelector('.page-title');
const refreshBtn = document.getElementById('refresh-btn');
const logoutBtn = document.getElementById('logout-btn');
const currentTimeEl = document.getElementById('current-time');
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    initNavigation();
    initTimeDisplay();

    try {
        await fetchAPI('/control-auth/session');
    } catch (error) {
        return;
    }

    const initialHashPage = (window.location.hash || '#overview').replace('#', '');
    const allowedPages = ['overview', 'quota', 'billing', 'errors', 'models', 'system', 'usage', 'proxy', 'about'];
    if (allowedPages.includes(initialHashPage)) {
        switchPage(initialHashPage, false);
    } else {
        setActivePage(currentPage);
        loadPage(currentPage);
    }

    window.addEventListener('hashchange', () => {
        const hashPage = (window.location.hash || '#overview').replace('#', '');
        if (allowedPages.includes(hashPage) && hashPage !== currentPage) {
            switchPage(hashPage, false);
        }
    });
    
    refreshBtn.addEventListener('click', () => {
        refreshCurrentPage();
    });

    logoutBtn?.addEventListener('click', async () => {
        try {
            await fetchAPI('/control-auth/logout', { method: 'POST' });
        } catch (error) {
            console.warn('Logout request failed', error);
        }
        window.location.href = '/control-login';
    });

    sidebarToggle?.addEventListener('click', () => {
        sidebar?.classList.toggle('collapsed');
        document.body.classList.toggle('sidebar-collapsed');
    });
});

// Navigation
function initNavigation() {
    navItems.forEach(item => {
        if (item.classList.contains('disabled')) return;
        
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.getAttribute('data-page');
            if (page && page !== currentPage) {
                switchPage(page);
            }
        });
    });
}

function setActivePage(page) {
    // Update active nav item
    navItems.forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-page') === page) {
            item.classList.add('active');
        }
    });

    // Update page title
    const pageTitles = {
        overview: 'Overview',
        quota: 'Quota',
        billing: 'Billing',
        errors: 'Errors',
        models: 'Models',
        system: 'System',
        usage: 'Usage',
        about: 'About'
    };
    pageTitle.textContent = pageTitles[page] || 'Dashboard';

    // Show/hide pages
    pages.forEach(p => {
        p.classList.remove('active');
        if (p.id === `page-${page}`) {
            p.classList.add('active');
        }
    });

    currentPage = page;
}

function switchPage(page, updateHash = true) {
    setActivePage(page);
    if (updateHash && window.location.hash !== `#${page}`) {
        window.location.hash = page;
    }
    loadPage(page);
}

// Time display
function initTimeDisplay() {
    function updateTime() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        currentTimeEl.textContent = timeStr;
    }
    
    updateTime();
    setInterval(updateTime, 1000);
}

// API helpers
async function fetchAPI(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    try {
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        if (response.status === 401 || response.status === 403) {
            window.location.href = '/control-login';
            throw new Error('Control authentication required');
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API fetch failed: ${endpoint}`, error);
        throw error;
    }
}

// Page loading
async function loadPage(page) {
    const pageEl = document.getElementById(`page-${page}`);
    
    // Show loading state
    pageEl.innerHTML = `
        <div class="loading-state">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading ${page} data...</p>
        </div>
    `;
    
    try {
        switch (page) {
            case 'overview':
                await loadOverview();
                break;
            case 'quota':
                await loadQuota();
                break;
            case 'billing':
                await loadBilling();
                break;
            case 'errors':
                await loadErrors();
                break;
            case 'models':
                await loadModels();
                break;
            case 'system':
                await loadSystem();
                break;
            case 'usage':
                await loadUsage();
                break;
            case 'about':
                renderAbout();
                break;
            case 'proxy':
                await loadProxy();
                break;
            default:
                pageEl.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-cogs"></i>
                        <h3>Page under construction</h3>
                        <p>This page is not yet implemented.</p>
                    </div>
                `;
        }
    } catch (error) {
        pageEl.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-circle"></i>
                <h3>Failed to load data</h3>
                <p>${error.message}</p>
                <button class="btn-refresh" onclick="refreshCurrentPage()">
                    <i class="fas fa-sync-alt"></i>
                    Retry
                </button>
            </div>
        `;
    }
}

function refreshCurrentPage() {
    loadPage(currentPage);
}

async function loadTopology() {
    topologyData = await fetchAPI('/control-api/topology');
    renderTopology();
}

function renderTopology() {
    const pageEl = document.getElementById('page-topology');
    const summary = topologyData.summary || {};
    const inventory = topologyData.inventory || {};
    const nodes = inventory.nodes || [];
    const services = inventory.services || [];
    const dependencies = inventory.dependencies || [];

    pageEl.innerHTML = `
        <div class="page-grid topology-grid">
            <div class="card span-12">
                <div class="card-header">
                    <h2 class="card-title">System Topology</h2>
                    <p class="card-subtitle">Operational map of nodes, services, and dependencies</p>
                </div>
                <div class="kpi-grid four-up">
                    <div class="kpi-card">
                        <div class="kpi-eyebrow">Nodes</div>
                        <div class="kpi-value">${summary.node_count || 0}</div>
                        <div class="kpi-subtitle">${summary.operational_node_count || 0} operational</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-eyebrow">Services</div>
                        <div class="kpi-value">${summary.service_count || 0}</div>
                        <div class="kpi-subtitle">${summary.operational_service_count || 0} operational</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-eyebrow">Dependencies</div>
                        <div class="kpi-value">${summary.dependency_count || 0}</div>
                        <div class="kpi-subtitle">${summary.critical_dependency_count || 0} critical</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-eyebrow">Inventory</div>
                        <div class="kpi-value">${escapeHtml(topologyData.version || 'v1')}</div>
                        <div class="kpi-subtitle">${escapeHtml(topologyData.timestamp || '--')}</div>
                    </div>
                </div>
            </div>

            <div class="card span-5">
                <div class="card-header">
                    <h3 class="card-title">Nodes</h3>
                </div>
                <div class="stack-list compact">
                    ${nodes.map(node => `
                        <div class="stack-item">
                            <div>
                                <div class="stack-title">${escapeHtml(node.name)}</div>
                                <div class="stack-subtitle">${escapeHtml(node.role || 'unknown')}</div>
                            </div>
                            <span class="status-pill ${getStatusTone(node.status)}">${escapeHtml(node.status || 'unknown')}</span>
                        </div>
                    `).join('') || '<div class="empty-state-inline">No nodes</div>'}
                </div>
            </div>

            <div class="card span-7">
                <div class="card-header">
                    <h3 class="card-title">Services</h3>
                    <p class="card-subtitle">Grouped by node</p>
                </div>
                <div class="topology-service-groups">
                    ${nodes.map(node => {
                        const nodeServices = services.filter(service => service.node_id === node.id);
                        return `
                            <div class="topology-node-group">
                                <div class="topology-node-header">${escapeHtml(node.name)}</div>
                                <div class="topology-service-list">
                                    ${nodeServices.map(service => `
                                        <div class="topology-service-item">
                                            <div>
                                                <div class="stack-title">${escapeHtml(service.name)}</div>
                                                <div class="stack-subtitle">${escapeHtml(service.type || 'service')}</div>
                                            </div>
                                            <span class="status-pill ${getStatusTone(service.status)}">${escapeHtml(service.status || 'unknown')}</span>
                                        </div>
                                    `).join('') || '<div class="empty-state-inline">No services</div>'}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>

            <div class="card span-12">
                <div class="card-header">
                    <h3 class="card-title">Dependency Map</h3>
                    <p class="card-subtitle">Critical paths first</p>
                </div>
                <div class="table-shell">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Source</th>
                                <th>Target</th>
                                <th>Type</th>
                                <th>Critical</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${dependencies.map(dep => {
                                const source = services.find(s => s.id === dep.source_service_id)?.name || dep.source_service_id;
                                const target = services.find(s => s.id === dep.target_service_id)?.name || dep.target_service_id;
                                return `
                                    <tr>
                                        <td>${escapeHtml(source)}</td>
                                        <td>${escapeHtml(target)}</td>
                                        <td>${escapeHtml(dep.type || 'unknown')}</td>
                                        <td>${dep.critical ? '<span class="status-pill status-error">critical</span>' : '<span class="status-pill status-ok">normal</span>'}</td>
                                    </tr>
                                `;
                            }).join('') || '<tr><td colspan="4" class="empty-cell">No dependencies</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

async function runControlAction(action, target = null, timeout = 30) {
    return fetchAPI('/control-api/actions/run', {
        method: 'POST',
        body: JSON.stringify({ action, target, timeout })
    });
}

async function loadControlActionHistory(containerId = 'models-actions-history') {
    const container = document.getElementById(containerId);
    if (!container) return;

    try {
        const data = await fetchAPI('/control-api/actions?limit=12');
        const actions = data.actions || [];

        if (!actions.length) {
            container.innerHTML = '<div class="empty-state compact-empty">No control actions recorded yet.</div>';
            return;
        }

        container.innerHTML = `
            <table class="table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Action</th>
                        <th>Target</th>
                        <th>Status</th>
                        <th>Result</th>
                    </tr>
                </thead>
                <tbody>
                    ${actions.map(item => `
                        <tr>
                            <td>${formatTimestamp(item.timestamp)}</td>
                            <td>${item.action || '--'}</td>
                            <td>${formatShortLabel(item.target || '--', 24)}</td>
                            <td><span class="badge ${getStatusTone(item.status)}">${item.status || '--'}</span></td>
                            <td>${formatShortLabel(item.result || '--', 64)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (error) {
        container.innerHTML = `<div class="error-state compact-empty">Failed to load control action history: ${error.message}</div>`;
    }
}

function formatTimestamp(value) {
    if (!value) return '--';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString('vi-VN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function formatShortLabel(value, maxLength = 18) {
    if (!value) return '--';
    const text = String(value);
    return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
}

function formatCost(value) {
    const num = Number(value || 0);
    if (Number.isNaN(num)) return '$0.00';
    if (num === 0) return '$0.00';
    if (num < 0.001) return `$${num.toFixed(6)}`;
    if (num < 1) return `$${num.toFixed(4)}`;
    return `$${num.toFixed(2)}`;
}

function formatErrorSignature(value) {
    if (!value) return '--';
    const parts = String(value).split('|');
    if (parts.length < 5) return value;
    const [status, httpStatus, provider, model, ...messageParts] = parts;
    const message = messageParts.join('|');
    return `${status} · ${httpStatus} · ${provider} · ${formatShortLabel(model, 28)} · ${formatShortLabel(message, 72)}`;
}

function getStatusTone(status) {
    const value = String(status || '').toLowerCase();
    if (['healthy', 'ok', 'ready', 'active', 'up', 'success', 'clear'].includes(value)) return 'badge-success';
    if (['critical', 'error', 'down', 'offline', 'failed', 'unhealthy'].includes(value)) return 'badge-danger';
    if (['degraded', 'warning', 'warm', 'pending', 'unknown'].includes(value)) return 'badge-warning';
    return 'badge-default';
}

function formatLatency(value) {
    const num = Number(value);
    if (Number.isNaN(num)) return '--';
    return `${num.toFixed(num >= 100 ? 0 : 1)} ms`;
}

function formatKeyValuePairs(obj) {
    const entries = Object.entries(obj || {});
    if (!entries.length) return '--';
    return entries.map(([k, v]) => `${k}:${v}`).join(', ');
}

function formatPercent(value) {
    const num = Number(value || 0);
    if (Number.isNaN(num)) return '0%';
    return `${(num * 100).toFixed(num > 0 && num < 0.1 ? 1 : 0)}%`;
}

function renderStatusWithDot(status, tone) {
    return `<span class="status-pill ${tone}"><span class="status-light ${tone}"></span><span>${status}</span></span>`;
}

async function updateProxyMode(mode) {
    await fetchAPI('/control-api/proxy/mode', {
        method: 'PUT',
        body: JSON.stringify({ mode })
    });
}

async function updateProxyHedge(enabled, delaySeconds) {
    await fetchAPI('/control-api/proxy/hedge', {
        method: 'PUT',
        body: JSON.stringify({ enabled, delay_seconds: delaySeconds })
    });
}

async function toggleProxyBackend(id, enabled) {
    await fetchAPI(`/control-api/proxy/backends/${id}/${enabled ? 'enable' : 'disable'}`, {
        method: 'POST'
    });
}

async function updateProxyBackendWeight(id, weight) {
    await fetchAPI(`/control-api/proxy/backends/${id}/weight`, {
        method: 'PUT',
        body: JSON.stringify({ weight })
    });
}

async function runProxyBenchmark(testCases = ['T1', 'T2', 'T3', 'T4'], concurrency = 1, durationSeconds = 10) {
    const result = await fetchAPI('/control-api/proxy/benchmark/run', {
        method: 'POST',
        body: JSON.stringify({ test_cases: testCases, concurrency, duration_seconds: durationSeconds })
    });
    return result;
}

async function getBenchmarkStatus(runId) {
    return await fetchAPI(`/control-api/proxy/benchmark/status/${runId}`);
}

async function getBenchmarkResults(runId) {
    return await fetchAPI(`/control-api/proxy/benchmark/results/${runId}`);
}

async function cancelBenchmark(runId) {
    return await fetchAPI(`/control-api/proxy/benchmark/cancel/${runId}`, { method: 'POST' });
}

async function listBenchmarkRuns(limit = 10) {
    return await fetchAPI(`/control-api/proxy/benchmark/list?limit=${limit}`);
}

// Overview page
async function loadOverview() {
    try {
        const overview = await fetchAPI('/control-api/overview?usage_limit=50&recent_events_limit=5');
        overviewData = overview;
        renderOverview();
    } catch (error) {
        throw error;
    }
}

function renderOverview() {
    const pageEl = document.getElementById('page-overview');
    const data = overviewData;
    
    if (!data) return;
    
    const healthStatus = data.health?.summary?.status || 'unknown';
    const healthClass = healthStatus === 'healthy' ? 'good' : 
                       healthStatus === 'degraded' ? 'warning' : 'danger';
    
    const windowEvents = data.usage?.window_event_count || 0;
    const billableCost = data.billing?.summary?.billable_estimated_cost || '--';
    const blockedEvents = data.quota?.blocked_event_count || 0;
    
    const topProvider = data.billing?.summary?.provider_breakdown ? 
        Object.keys(data.billing.summary.provider_breakdown)[0] || 'N/A' : 'N/A';
    
    const topQuotaReason = data.quota?.reason_breakdown ?
        Object.keys(data.quota.reason_breakdown)[0] || 'N/A' : 'N/A';
    
    const recentErrors = data.alerts?.recent_errors || [];
    
    pageEl.innerHTML = `
        <div class="action-bar">
            <button class="btn-refresh" id="overview-health-refresh-btn">
                <i class="fas fa-heartbeat"></i>
                Refresh Health Snapshot
            </button>
            <button class="btn-refresh" id="overview-warmup-all-btn">
                <i class="fas fa-fire"></i>
                Warm Up All Models
            </button>
        </div>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-eyebrow">Health</div>
                <div class="kpi-title">System Status</div>
                <div class="kpi-value ${healthClass}">${healthStatus.toUpperCase()}</div>
                <div class="kpi-trend">
                    <i class="fas fa-heartbeat"></i>
                    <span>Last check: Just now</span>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-eyebrow">Usage</div>
                <div class="kpi-title">Window Events</div>
                <div class="kpi-value neutral">${windowEvents}</div>
                <div class="kpi-trend">
                    <i class="fas fa-chart-line"></i>
                    <span>Last 24h</span>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-eyebrow">Billing</div>
                <div class="kpi-title">Billable Cost</div>
                <div class="kpi-value neutral">$${billableCost}</div>
                <div class="kpi-trend">
                    <i class="fas fa-dollar-sign"></i>
                    <span>Estimated</span>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-eyebrow">Quota</div>
                <div class="kpi-title">Blocked Events</div>
                <div class="kpi-value ${blockedEvents > 0 ? 'warning' : 'neutral'}">${blockedEvents}</div>
                <div class="kpi-trend">
                    <i class="fas fa-shield-alt"></i>
                    <span>Quota enforcement</span>
                </div>
            </div>
        </div>
        
        <div class="panel-grid">
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Billing Summary</div>
                    <div class="panel-subtitle">Estimated costs</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row">
                        <span class="panel-label">Total Estimated Cost</span>
                        <span class="panel-value">$${data.billing?.summary?.total_estimated_cost || '--'}</span>
                    </div>
                    <div class="panel-row">
                        <span class="panel-label">Billable Events</span>
                        <span class="panel-value">${data.billing?.summary?.billable_events || 0}</span>
                    </div>
                    <div class="panel-row">
                        <span class="panel-label">Top Provider</span>
                        <span class="panel-value">${topProvider}</span>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Quota Watch</div>
                    <div class="panel-subtitle">Blocked activity</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row">
                        <span class="panel-label">Blocked Events</span>
                        <span class="panel-value">${blockedEvents}</span>
                    </div>
                    <div class="panel-row">
                        <span class="panel-label">Top Tenant</span>
                        <span class="panel-value">${data.quota?.tenant_breakdown ? Object.keys(data.quota.tenant_breakdown)[0] || 'N/A' : 'N/A'}</span>
                    </div>
                    <div class="panel-row">
                        <span class="panel-label">Top Reason</span>
                        <span class="panel-value">${topQuotaReason}</span>
                    </div>
                </div>
            </div>
            
            <div class="panel panel-fixed-errors">
                <div class="panel-header">
                    <div class="panel-title">Recent Errors</div>
                    <div class="panel-subtitle">Last 5 errors</div>
                </div>
                <div class="panel-content panel-scroll-y">
                    ${recentErrors.length > 0 ? 
                        recentErrors.slice(0, 5).map(error => {
                            const ts = error.timestamp ? new Date(error.timestamp) : null;
                            const timePart = ts && !Number.isNaN(ts.getTime()) ? ts.toLocaleTimeString('vi-VN') : '--';
                            const datePart = ts && !Number.isNaN(ts.getTime()) ? ts.toLocaleDateString('vi-VN') : '--';
                            return `
                            <div class="panel-row panel-row-stack">
                                <span class="panel-label recent-error-time"><span>${timePart}</span><span>${datePart}</span></span>
                                <span class="panel-value">${error.error || error.message || error.status || 'Unknown error'}</span>
                            </div>
                        `}).join('') : 
                        `<div class="panel-row">
                            <span class="panel-label">Status</span>
                            <span class="panel-value">No recent errors</span>
                        </div>`
                    }
                </div>
            </div>

        </div>
    `;

    document.getElementById('overview-health-refresh-btn')?.addEventListener('click', async () => {
        const btn = document.getElementById('overview-health-refresh-btn');
        btn.disabled = true;
        try {
            await runControlAction('health_refresh');
            await loadOverview();
        } catch (error) {
            alert(`Health refresh failed: ${error.message}`);
        } finally {
            btn.disabled = false;
        }
    });

    document.getElementById('overview-warmup-all-btn')?.addEventListener('click', async () => {
        const btn = document.getElementById('overview-warmup-all-btn');
        btn.disabled = true;
        try {
            const result = await runControlAction('model_warmup_all', null, 20);
            alert(result.message || 'Warm-up completed');
            await loadOverview();
        } catch (error) {
            alert(`Warm-up failed: ${error.message}`);
        } finally {
            btn.disabled = false;
        }
    });
}

// Quota page
async function loadQuota() {
    try {
        const data = await fetchAPI('/control-api/quota?limit=50&recent_limit=5');
        quotaData = data;
        renderQuota();
    } catch (error) {
        throw error;
    }
}

function renderQuota() {
    const pageEl = document.getElementById('page-quota');
    const data = quotaData;
    
    if (!data) return;
    
    const blockedCount = data.blocked_event_count || 0;
    const tenantBreakdown = data.tenant_breakdown || {};
    const apiKeyBreakdown = data.api_key_breakdown || {};
    const reasonBreakdown = data.reason_breakdown || {};
    const recentBlocked = data.recent_blocked || [];
    
    pageEl.innerHTML = `
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-eyebrow">Quota</div>
                <div class="kpi-title">Blocked Events</div>
                <div class="kpi-value ${blockedCount > 0 ? 'warning' : 'neutral'}">${blockedCount}</div>
                <div class="kpi-trend">
                    <i class="fas fa-ban"></i>
                    <span>HTTP 429 responses</span>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-eyebrow">Tenants</div>
                <div class="kpi-title">Affected Tenants</div>
                <div class="kpi-value neutral">${Object.keys(tenantBreakdown).length}</div>
                <div class="kpi-trend">
                    <i class="fas fa-users"></i>
                    <span>With blocked events</span>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-eyebrow">API Keys</div>
                <div class="kpi-title">Affected Keys</div>
                <div class="kpi-value neutral">${Object.keys(apiKeyBreakdown).length}</div>
                <div class="kpi-trend">
                    <i class="fas fa-key"></i>
                    <span>With blocked events</span>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-eyebrow">Reasons</div>
                <div class="kpi-title">Top Reason</div>
                <div class="kpi-value neutral">${Object.keys(reasonBreakdown)[0] || 'N/A'}</div>
                <div class="kpi-trend">
                    <i class="fas fa-exclamation-circle"></i>
                    <span>Most common block cause</span>
                </div>
            </div>
        </div>
        
        <div class="panel-grid">
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Tenant Breakdown</div>
                    <div class="panel-subtitle">Blocked events by tenant</div>
                </div>
                <div class="panel-content">
                    ${Object.entries(tenantBreakdown).length > 0 ? 
                        Object.entries(tenantBreakdown).slice(0, 5).map(([tenant, count]) => `
                            <div class="panel-row">
                                <span class="panel-label">${tenant}</span>
                                <span class="panel-value">${count}</span>
                            </div>
                        `).join('') : 
                        `<div class="panel-row">
                            <span class="panel-label">No tenant blocks</span>
                            <span class="panel-value">--</span>
                        </div>`
                    }
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">API Key Breakdown</div>
                    <div class="panel-subtitle">Blocked events by API key</div>
                </div>
                <div class="panel-content">
                    ${Object.entries(apiKeyBreakdown).length > 0 ? 
                        Object.entries(apiKeyBreakdown).slice(0, 5).map(([key, count]) => `
                            <div class="panel-row">
                                <span class="panel-label">${formatShortLabel(key, 12)}</span>
                                <span class="panel-value">${count}</span>
                            </div>
                        `).join('') : 
                        `<div class="panel-row">
                            <span class="panel-label">No API key blocks</span>
                            <span class="panel-value">--</span>
                        </div>`
                    }
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Reason Breakdown</div>
                    <div class="panel-subtitle">Why events were blocked</div>
                </div>
                <div class="panel-content">
                    ${Object.entries(reasonBreakdown).length > 0 ? 
                        Object.entries(reasonBreakdown).slice(0, 5).map(([reason, count]) => `
                            <div class="panel-row">
                                <span class="panel-label">${reason}</span>
                                <span class="panel-value">${count}</span>
                            </div>
                        `).join('') : 
                        `<div class="panel-row">
                            <span class="panel-label">No blocked events</span>
                            <span class="panel-value">--</span>
                        </div>`
                    }
                </div>
            </div>
        </div>
        
        ${recentBlocked.length > 0 ? `
            <div class="table-container" style="margin-top: 32px;">
                <div class="table-header">Recent Blocked Events</div>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Tenant</th>
                            <th>API Key</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${recentBlocked.slice(0, 10).map(event => `
                            <tr>
                                <td>${formatTimestamp(event.timestamp)}</td>
                                <td>${event.tenant_id || '--'}</td>
                                <td>${formatShortLabel(event.api_key_id, 8)}</td>
                                <td><span class="badge badge-warning">${event.quota_reason || event.reason || 'unknown'}</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        ` : ''}
    `;
}

// Billing page
async function loadBilling() {
    try {
        const data = await fetchAPI('/control-api/billing?limit=200');
        billingData = data;
        renderBilling();
    } catch (error) {
        throw error;
    }
}

function renderBilling() {
    const pageEl = document.getElementById('page-billing');
    const data = billingData;
    
    if (!data) return;
    
    const summary = data.summary || {};
    const tenantBreakdown = data.tenant_breakdown || {};
    const apiKeyBreakdown = data.api_key_breakdown || {};
    const providerBreakdown = data.provider_breakdown || {};
    const billableModeBreakdown = data.billable_mode_breakdown || {};
    
    pageEl.innerHTML = `
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-eyebrow">Billing</div>
                <div class="kpi-title">Total Estimated Cost</div>
                <div class="kpi-value neutral">${formatCost(summary.total_estimated_cost)}</div>
                <div class="kpi-trend">
                    <i class="fas fa-dollar-sign"></i>
                    <span>All events</span>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-eyebrow">Billable</div>
                <div class="kpi-title">Billable Cost</div>
                <div class="kpi-value neutral">${formatCost(summary.billable_estimated_cost)}</div>
                <div class="kpi-trend">
                    <i class="fas fa-receipt"></i>
                    <span>Chargeable</span>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-eyebrow">Events</div>
                <div class="kpi-title">Billable Events</div>
                <div class="kpi-value neutral">${summary.billable_events || 0}</div>
                <div class="kpi-trend">
                    <i class="fas fa-list-alt"></i>
                    <span>Chargeable count</span>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-eyebrow">Providers</div>
                <div class="kpi-title">Active Providers</div>
                <div class="kpi-value neutral">${Object.keys(providerBreakdown).length}</div>
                <div class="kpi-trend">
                    <i class="fas fa-network-wired"></i>
                    <span>With cost</span>
                </div>
            </div>
        </div>
        
        <div class="panel-grid">
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Tenant Breakdown</div>
                    <div class="panel-subtitle">Cost by tenant</div>
                </div>
                <div class="panel-content">
                    ${Object.entries(tenantBreakdown).length > 0 ? 
                        Object.entries(tenantBreakdown).slice(0, 5).map(([tenant, cost]) => `
                            <div class="panel-row">
                                <span class="panel-label">${tenant}</span>
                                <span class="panel-value">${formatCost(cost)}</span>
                            </div>
                        `).join('') : 
                        `<div class="panel-row">
                            <span class="panel-label">No tenant data</span>
                            <span class="panel-value">--</span>
                        </div>`
                    }
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">API Key Breakdown</div>
                    <div class="panel-subtitle">Cost by API key</div>
                </div>
                <div class="panel-content">
                    ${Object.entries(apiKeyBreakdown).length > 0 ? 
                        Object.entries(apiKeyBreakdown).slice(0, 5).map(([key, cost]) => `
                            <div class="panel-row">
                                <span class="panel-label">${formatShortLabel(key, 12)}</span>
                                <span class="panel-value">${formatCost(cost)}</span>
                            </div>
                        `).join('') : 
                        `<div class="panel-row">
                            <span class="panel-label">No API key data</span>
                            <span class="panel-value">--</span>
                        </div>`
                    }
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Provider Breakdown</div>
                    <div class="panel-subtitle">Cost by provider</div>
                </div>
                <div class="panel-content">
                    ${Object.entries(providerBreakdown).length > 0 ? 
                        Object.entries(providerBreakdown).slice(0, 5).map(([provider, cost]) => `
                            <div class="panel-row">
                                <span class="panel-label">${provider}</span>
                                <span class="panel-value">${formatCost(cost)}</span>
                            </div>
                        `).join('') : 
                        `<div class="panel-row">
                            <span class="panel-label">No provider data</span>
                            <span class="panel-value">--</span>
                        </div>`
                    }
                </div>
            </div>
        </div>
    `;
}

// Models page
async function loadModels() {
    try {
        const [data, usage, proxyState, proxyBackends, proxyMetrics] = await Promise.all([
            fetchAPI('/control-api/models'),
            fetchAPI('/control-api/usage?limit=40'),
            fetchAPI('/control-api/proxy/state').catch(() => null),
            fetchAPI('/control-api/proxy/backends').catch(() => null),
            fetchAPI('/control-api/proxy/metrics').catch(() => null)
        ]);
        proxyStateData = proxyState;
        proxyBackendsData = proxyBackends;
        proxyBenchmarkData = proxyMetrics;
        const proxySummary = proxyState?.summary || {};
        const proxyRuntime = {
            status: proxySummary.service_status || 'unknown',
            healthyCount: proxySummary.healthy_backend_count ?? proxyBackends?.summary?.healthy ?? 0,
            totalBackends: proxySummary.backend_count ?? proxyBackends?.summary?.count ?? 0,
            backend: Array.isArray(proxyState?.runtime?.backends) && proxyState.runtime.backends.length ? String(proxyState.runtime.backends[0]).replace('http://', '') : '--',
            hedgeEnabled: !!proxySummary.hedge_enabled,
            hedgeDelay: proxySummary.hedge_delay_seconds ?? null,
            tokenValidation: false,
            requestsTotal: proxySummary.requests_total ?? proxyMetrics?.requests_total ?? 0,
            successRate: proxySummary.success_rate ?? proxyMetrics?.success_rate ?? null,
            avgLatency: proxySummary.avg_latency ?? proxyMetrics?.avg_latency ?? null,
        };
        modelsData = { ...data, recent_usage: usage, proxy_runtime: proxyRuntime };
        renderModels();
    } catch (error) {
        throw error;
    }
}

function renderModels() {
    const pageEl = document.getElementById('page-models');
    const data = modelsData;
    if (!data) return;

    const summary = data.summary || {};
    const models = data.models || [];
    const providers = data.providers || [];
    const ollamaModels = data.ollama?.models || [];
    const healthStatus = data.load_balancer_metrics?.health_status || {};
    const recentUsage = Array.isArray(data.recent_usage?.events) ? data.recent_usage.events : [];
    const proxyRuntime = data.proxy_runtime || {};

    const localProviders = providers.filter(provider => String(provider.type).includes('ollama_local'));
    const remoteProviders = providers.filter(provider => String(provider.type).includes('ollama_remote'));
    const cloudProviders = providers.filter(provider => String(provider.type).includes('cli_proxy'));
    const apiRuntime = {
        status: 'healthy',
        role: 'canonical',
        deploy: 'docker',
        providers: summary.provider_count || 0,
        enabled: summary.enabled_provider_count || 0,
        healthy: summary.healthy_provider_count || 0,
        bias: remoteProviders.filter(p => p.enabled).length > 0 ? 'remote-first' : 'mixed',
        route: 'conditional'
    };
    const recentModelTraffic = recentUsage
        .filter(item => item.model || item.provider || item.provider_type)
        .slice(0, 15);

    pageEl.innerHTML = `
        <div class="action-bar">
            <button class="btn-refresh" id="models-refresh-actions-btn">
                <i class="fas fa-rotate"></i>
                Refresh Models View
            </button>
            <button class="btn-refresh" id="models-warmup-all-btn">
                <i class="fas fa-fire"></i>
                Warm Up All Models
            </button>
            <button class="btn-refresh" id="models-enable-remote-btn">
                <i class="fas fa-tower-broadcast"></i>
                Enable All Remote
            </button>
            <button class="btn-refresh" id="models-disable-cloud-btn">
                <i class="fas fa-cloud-slash"></i>
                Disable All Cloud
            </button>
            <button class="btn-refresh" id="models-isolate-local-btn">
                <i class="fas fa-house-signal"></i>
                Isolate Local Only
            </button>
        </div>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-eyebrow">Models</div>
                <div class="kpi-title">Configured Models</div>
                <div class="kpi-value neutral">${summary.model_count || 0}</div>
                <div class="kpi-trend"><i class="fas fa-robot"></i><span>Total tracked</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Warm</div>
                <div class="kpi-title">Ready Models</div>
                <div class="kpi-value good">${summary.warm_count || 0}</div>
                <div class="kpi-trend"><i class="fas fa-fire"></i><span>Warm and ready</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Providers</div>
                <div class="kpi-title">Healthy / Enabled</div>
                <div class="kpi-value ${summary.provider_count > 0 && summary.healthy_provider_count === summary.provider_count ? 'good' : 'warning'}">${summary.healthy_provider_count || 0}/${summary.provider_count || 0}</div>
                <div class="kpi-trend"><i class="fas fa-network-wired"></i><span>${summary.enabled_provider_count || 0} enabled · ${summary.disabled_provider_count || 0} disabled</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Ollama</div>
                <div class="kpi-title">Local Model Store</div>
                <div class="kpi-value ${summary.ollama_status === 'healthy' ? 'good' : 'warning'}">${(summary.ollama_status || 'unknown').toUpperCase()}</div>
                <div class="kpi-trend"><i class="fas fa-server"></i><span>${summary.ollama_model_count || 0} local models</span></div>
            </div>
        </div>

        <div class="panel-grid" style="margin-bottom: 24px;">
            <div class="panel" style="grid-column: 1 / -1; min-height: 420px;">
                <div class="panel-header">
                    <div>
                        <div class="panel-title">Serving Route Map</div>
                        <div class="panel-subtitle">Serving flow map</div>
                    </div>
                    <div class="panel-actions-inline">
                        <span class="status-badge status-neutral">Draft map</span>
                    </div>
                </div>
                <div class="panel-content" style="padding-top: 8px; overflow-x:auto;">
                    <div style="display:flex; flex-direction:column; gap:18px; min-width:1020px;">
                        <div style="display:flex; align-items:flex-start; gap:10px;">
                            <div style="display:flex; flex-direction:column; gap:7px; justify-content:flex-start; min-width:128px; padding:9px 12px; border:1px solid rgba(148,163,184,.2); border-radius:16px; background:rgba(15,23,42,.22);">
                                <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span style="width:9px; height:9px; border-radius:999px; background:#22c55e; display:inline-block;"></span>Health</div>
                                <div style="font-size:15px; font-weight:700; line-height:1.1;">API</div>
                            </div>
                            <div style="width:18px; height:0; border-top:1px dashed rgba(148,163,184,.28); margin-top:28px;"></div>
                            <div style="display:flex; flex-direction:column; align-items:center; gap:8px; min-width:153px;">
                                <div style="display:flex; flex-direction:column; gap:7px; justify-content:flex-start; width:100%; padding:9px 12px; border:1px solid rgba(148,163,184,.2); border-radius:16px; background:rgba(15,23,42,.22);">
                                    <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span style="width:9px; height:9px; border-radius:999px; background:${proxyRuntime.status === 'healthy' || proxyRuntime.healthyCount > 0 ? '#22c55e' : '#ef4444'}; display:inline-block;"></span>Health</div>
                                    <div style="font-size:15px; font-weight:700; line-height:1.1;">Proxy 8015</div>
                                </div>
                                <div style="width:0; height:3px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                <div style="display:flex; flex-direction:column; gap:5px; width:100%; padding:7px 9px; border:1px dashed rgba(148,163,184,.22); border-radius:12px; background:rgba(15,23,42,.12);">
                                    <div style="display:grid; grid-template-columns: 1fr auto; gap:4px 8px; font-size:10px; line-height:1.15; color:#cbd5e1;">
                                        <span>Status</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${proxyRuntime.status || '--'}</strong>
                                        <span>Backend</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${proxyRuntime.backend || '--'}</strong>
                                        <span>Healthy</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${proxyRuntime.healthyCount ?? '--'}/${proxyRuntime.totalBackends ?? '--'}</strong>
                                        <span>Hedge</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${proxyRuntime.hedgeEnabled ? 'ON' : 'OFF'}</strong>
                                        <span>Token</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${proxyRuntime.tokenValidation ? 'ENFORCED' : 'PASS'}</strong>
                                        <span>Req</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${proxyRuntime.requestsTotal ?? '--'}</strong>
                                        <span>Success</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${proxyRuntime.successRate != null ? `${Math.round(proxyRuntime.successRate * 100)}%` : '--'}</strong>
                                        <span>Lat</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${proxyRuntime.avgLatency != null ? `${proxyRuntime.avgLatency.toFixed(1)}s` : '--'}</strong>
                                    </div>
                                </div>
                            </div>
                            <div style="width:18px; height:0; border-top:1px dashed rgba(148,163,184,.28); margin-top:28px;"></div>
                            <div style="display:flex; flex-direction:column; align-items:center; gap:8px; min-width:162px;">
                                <div style="display:flex; flex-direction:column; gap:7px; justify-content:flex-start; width:100%; padding:9px 12px; border:1px solid rgba(148,163,184,.2); border-radius:16px; background:rgba(15,23,42,.22);">
                                    <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span style="width:9px; height:9px; border-radius:999px; background:#22c55e; display:inline-block;"></span>Health</div>
                                    <div style="font-size:15px; font-weight:700; line-height:1.1;">FastAPI 8000</div>
                                </div>
                                <div style="width:0; height:3px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                <div style="display:flex; flex-direction:column; gap:5px; width:100%; padding:7px 9px; border:1px dashed rgba(148,163,184,.22); border-radius:12px; background:rgba(15,23,42,.12);">
                                    <div style="display:grid; grid-template-columns: 1fr auto; gap:4px 8px; font-size:10px; line-height:1.15; color:#cbd5e1;">
                                        <span>Status</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${apiRuntime.status}</strong>
                                        <span>Role</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${apiRuntime.role}</strong>
                                        <span>Deploy</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${apiRuntime.deploy}</strong>
                                        <span>Providers</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${apiRuntime.providers}</strong>
                                        <span>Enabled</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${apiRuntime.enabled}</strong>
                                        <span>Healthy</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${apiRuntime.healthy}</strong>
                                        <span>Bias</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${apiRuntime.bias}</strong>
                                        <span>Route</span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">${apiRuntime.route}</strong>
                                    </div>
                                </div>
                            </div>
                            <div style="width:18px; height:0; border-top:1px dashed rgba(148,163,184,.28); margin-top:28px;"></div>
                            <div style="display:flex; flex-direction:column; gap:7px; justify-content:flex-start; min-width:153px; padding:9px 12px; border:1px dashed rgba(148,163,184,.25); border-radius:16px; background:rgba(15,23,42,.14); margin-top:0;">
                                <div style="color:#94a3b8; font-size:11px;">policy target</div>
                                <div style="font-size:14px; font-weight:700; line-height:1.1;">Routing Split</div>
                            </div>
                            <div style="width:18px; height:0; border-top:1px dashed rgba(148,163,184,.28); margin-top:28px;"></div>
                            <div style="display:flex; flex-direction:column; gap:6px; min-width:128px; padding:9px 11px; border:1px solid rgba(148,163,184,.18); border-radius:14px; background:rgba(15,23,42,.18);">
                                <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span style="width:8px; height:8px; border-radius:999px; background:#f8fafc; display:inline-block;"></span>Health</div>
                                <div style="font-size:13px; font-weight:700; line-height:1.1;">RAG-V2</div>
                            </div>
                        </div>

                        <div style="display:flex; flex-direction:column; gap:8px; padding-left:292px; margin-top:-10px; min-width:780px;">
                            <div style="width:0; height:22px; border-left:1px dashed rgba(148,163,184,.28); margin-left:154px;"></div>
                            <div style="width:720px; height:0; border-top:1px dashed rgba(148,163,184,.28);"></div>
                            <div style="display:grid; grid-template-columns: 160px 200px 160px 160px; gap:14px; align-items:start; width:720px;">
                                <div style="display:flex; flex-direction:column; align-items:center; gap:6px; width:160px;">
                                    <div style="width:0; height:8px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                    <div style="display:flex; flex-direction:column; gap:6px; width:100%; padding:9px 11px; border:1px dashed rgba(148,163,184,.22); border-radius:14px; background:rgba(15,23,42,.12);">
                                        <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span style="width:8px; height:8px; border-radius:999px; background:#22c55e; display:inline-block;"></span>Gate</div>
                                        <div style="font-size:12px; font-weight:700; line-height:1.2;">Identity / Access / Billing</div>
                                    </div>
                                </div>
                                <div style="display:flex; flex-direction:column; align-items:center; gap:6px; width:200px;">
                                    <div style="width:0; height:8px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                    <div style="display:flex; flex-direction:column; gap:6px; width:100%; padding:9px 11px; border:1px solid rgba(148,163,184,.18); border-radius:14px; background:rgba(15,23,42,.18); box-shadow:0 0 0 1px rgba(34,197,94,.08) inset;">
                                        <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span style="width:8px; height:8px; border-radius:999px; background:#22c55e; display:inline-block;"></span>Control Core</div>
                                        <div style="font-size:12px; font-weight:700; line-height:1.2;">Execution Lane Orchestration</div>
                                    </div>
                                    <div style="width:0; height:10px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                    <div style="display:flex; flex-direction:column; gap:5px; width:100%; padding:7px 9px; border:1px dashed rgba(148,163,184,.22); border-radius:12px; background:rgba(15,23,42,.12);">
                                        <div style="font-size:11px; color:#94a3b8; margin-bottom:2px;">Traffic Split</div>
                                        <div style="display:grid; grid-template-columns: auto 1fr auto; gap:6px 8px; align-items:center; font-size:10px; color:#cbd5e1;">
                                            <span>Core A</span><span style="height:24px; border:1px solid rgba(148,163,184,.18); border-radius:8px; background:rgba(15,23,42,.18);"></span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">%</strong>
                                            <span>Core B</span><span style="height:24px; border:1px solid rgba(148,163,184,.18); border-radius:8px; background:rgba(15,23,42,.18);"></span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">%</strong>
                                            <span>Core C</span><span style="height:24px; border:1px solid rgba(148,163,184,.18); border-radius:8px; background:rgba(15,23,42,.18);"></span><strong style="font-size:10px; color:#f8fafc; font-weight:600;">%</strong>
                                        </div>
                                    </div>
                                    <div style="width:0; height:10px; border-left:1px dashed rgba(148,163,184,.28); margin:0 auto;"></div>
                                </div>
                                <div style="display:flex; flex-direction:column; align-items:center; gap:6px; width:160px;">
                                    <div style="width:0; height:8px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                    <div style="display:flex; flex-direction:column; gap:6px; width:100%; padding:9px 11px; border:1px dashed rgba(148,163,184,.22); border-radius:14px; background:rgba(15,23,42,.12);">
                                        <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span style="width:8px; height:8px; border-radius:999px; background:#22c55e; display:inline-block;"></span>Truth</div>
                                        <div style="font-size:12px; font-weight:700; line-height:1.2;">Truth / Telemetry / Metering</div>
                                    </div>
                                </div>
                                <div style="display:flex; flex-direction:column; align-items:center; gap:6px; width:160px;">
                                    <div style="width:0; height:8px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                    <div style="display:flex; flex-direction:column; gap:6px; width:100%; padding:9px 11px; border:1px dashed rgba(148,163,184,.22); border-radius:14px; background:rgba(15,23,42,.12);">
                                        <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span style="width:8px; height:8px; border-radius:999px; background:#22c55e; display:inline-block;"></span>Adapter</div>
                                        <div style="font-size:12px; font-weight:700; line-height:1.2;">Adapter / Control Surface</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div style="display:flex; flex-direction:column; gap:6px; padding-left:505px; margin-top:14px; min-width:560px;">
                            <div style="display:flex; align-items:flex-start; gap:10px;">
                                <div style="width:120px; height:0; border-top:1px dashed rgba(148,163,184,.28);"></div>
                                <div style="width:120px; height:0; border-top:1px dashed rgba(148,163,184,.28);"></div>
                                <div style="width:140px; height:0; border-top:1px dashed rgba(148,163,184,.28);"></div>
                            </div>
                            <div style="display:flex; align-items:flex-start; gap:10px;">
                                <div style="display:flex; flex-direction:column; align-items:center; gap:2px; width:120px;">
                                    <div style="width:0; height:10px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                    <div style="display:flex; flex-direction:column; gap:5px; width:100%; padding:8px 10px; border:1px solid rgba(148,163,184,.18); border-radius:14px; background:rgba(15,23,42,.18); min-height:58px; justify-content:flex-start;">
                                        <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span style="width:8px; height:8px; border-radius:999px; background:#f8fafc; display:inline-block;"></span>Core A</div>
                                        <div style="font-size:11px; font-weight:700; line-height:1.2;">Ollama Group</div>
                                    </div>
                                </div>
                                <div style="display:flex; flex-direction:column; align-items:center; gap:2px; width:120px;">
                                    <div style="width:0; height:10px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                    <div style="display:flex; flex-direction:column; gap:5px; width:100%; padding:8px 10px; border:1px solid rgba(148,163,184,.18); border-radius:14px; background:rgba(15,23,42,.18); min-height:58px; justify-content:flex-start;">
                                        <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span style="width:8px; height:8px; border-radius:999px; background:#f8fafc; display:inline-block;"></span>Core B</div>
                                        <div style="font-size:11px; font-weight:700; line-height:1.2;">CLI Proxy API</div>
                                    </div>
                                </div>
                                <div style="display:flex; flex-direction:column; align-items:center; gap:2px; width:140px;">
                                    <div style="width:0; height:10px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                    <div style="display:flex; flex-direction:column; gap:5px; width:100%; padding:8px 10px; border:1px solid rgba(148,163,184,.18); border-radius:14px; background:rgba(15,23,42,.18); min-height:58px; justify-content:flex-start;">
                                        <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span style="width:8px; height:8px; border-radius:999px; background:#f8fafc; display:inline-block;"></span>Core C</div>
                                        <div style="font-size:11px; font-weight:700; line-height:1.2;">Fallback (GPT 5.4)</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="panel-grid">
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Model Readiness</div>
                    <div class="panel-subtitle">Warmup state + actions</div>
                </div>
                <div class="panel-content panel-scroll-y" style="max-height: 360px;">
                    ${models.length > 0 ? models.slice(0, 12).map(model => `
                        <div class="panel-row panel-row-stack">
                            <div>
                                <div class="panel-label">${model.name}</div>
                                <div class="panel-meta">last warmup: ${formatTimestamp(model.last_warmup ? new Date(model.last_warmup * 1000).toISOString() : null)}</div>
                            </div>
                            <div class="panel-actions-inline">
                                ${renderStatusWithDot(model.status || 'unknown', model.is_ready ? 'healthy' : (String(model.status || '').toLowerCase() === 'error' ? 'unhealthy' : 'neutral'))}
                                <button class="btn-mini" data-action="warm-model" data-target="${model.name}">Warm Up</button>
                            </div>
                        </div>
                    `).join('') : '<div class="panel-row"><span class="panel-label">No model data</span><span class="panel-value">--</span></div>'}
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Provider Routing Control</div>
                    <div class="panel-subtitle">Enable / disable live routing candidates</div>
                </div>
                <div class="panel-content panel-scroll-y" style="max-height: 360px;">
                    ${providers.length > 0 ? providers.slice(0, 12).map(provider => `
                        <div class="panel-row panel-row-stack">
                            <div>
                                <div class="panel-label">${provider.name}</div>
                                <div class="panel-meta">${provider.type} · ${formatShortLabel(provider.model, 28)} · weight ${provider.weight}</div>
                            </div>
                            <div class="panel-actions-inline">
                                ${renderStatusWithDot(provider.health || 'unknown', provider.health === 'healthy' ? 'healthy' : 'unhealthy')}
                                <button class="toggle-switch ${provider.enabled ? 'is-on' : 'is-off'}" data-action="toggle-provider" data-target="${provider.name}" data-enabled="${provider.enabled ? '1' : '0'}" aria-label="Toggle provider ${provider.name}">
                                    <span class="toggle-track"><span class="toggle-thumb"></span></span>
                                </button>
                            </div>
                        </div>
                    `).join('') : '<div class="panel-row"><span class="panel-label">No provider data</span><span class="panel-value">--</span></div>'}
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Provider Groups</div>
                    <div class="panel-subtitle">Operational posture by routing class</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row"><span class="panel-label">Local Ollama</span><span class="panel-value">${localProviders.filter(p => p.enabled).length}/${localProviders.length} enabled</span></div>
                    <div class="panel-row"><span class="panel-label">Remote Ollama</span><span class="panel-value">${remoteProviders.filter(p => p.enabled).length}/${remoteProviders.length} enabled</span></div>
                    <div class="panel-row"><span class="panel-label">Cloud / CLI</span><span class="panel-value">${cloudProviders.filter(p => p.enabled).length}/${cloudProviders.length} enabled</span></div>
                    <div class="panel-row"><span class="panel-label">Control Focus</span><span class="panel-value">Use this tab to shape effective routing posture</span></div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Routing Posture</div>
                    <div class="panel-subtitle">Effective readiness across provider fleet</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row"><span class="panel-label">Enabled + Healthy</span><span class="panel-value">${providers.filter(p => p.enabled && p.health === 'healthy').length}</span></div>
                    <div class="panel-row"><span class="panel-label">Enabled + Unhealthy</span><span class="panel-value">${providers.filter(p => p.enabled && p.health !== 'healthy').length}</span></div>
                    <div class="panel-row"><span class="panel-label">Disabled + Healthy</span><span class="panel-value">${providers.filter(p => !p.enabled && p.health === 'healthy').length}</span></div>
                    <div class="panel-row"><span class="panel-label">Disabled + Unhealthy</span><span class="panel-value">${providers.filter(p => !p.enabled && p.health !== 'healthy').length}</span></div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Ollama Models</div>
                    <div class="panel-subtitle">Local runtime inventory</div>
                </div>
                <div class="panel-content panel-scroll-y" style="max-height: 360px;">
                    ${ollamaModels.length > 0 ? ollamaModels.slice(0, 10).map(model => `
                        <div class="panel-row">
                            <span class="panel-label">${model.name}</span>
                            <span class="panel-value">${model.details?.parameter_size || '--'}</span>
                        </div>
                    `).join('') : '<div class="panel-row"><span class="panel-label">No local models</span><span class="panel-value">--</span></div>'}
                </div>
            </div>

            <div class="panel" style="grid-column: 1 / -1;">
                <div class="panel-header">
                    <div class="panel-title">Recent Model Traffic</div>
                    <div class="panel-subtitle">15 recent requests across local / remote / cloud lanes</div>
                </div>
                <div class="panel-content panel-scroll-y" style="max-height: 380px;">
                    ${recentModelTraffic.length > 0 ? recentModelTraffic.map(item => {
                        const modelName = item.model || item.provider || '--';
                        const providerType = item.provider_type || '--';
                        const routeClass = String(providerType).includes('remote') ? 'remote' : (String(providerType).includes('local') ? 'local' : 'cloud/other');
                        const fallbackClass = item.fallback_used ? 'fallback' : 'primary';
                        return `<div class="panel-row"><span class="panel-label">${escapeHtml(formatTimestamp(item.timestamp))} · ${escapeHtml(String(modelName))}</span><span class="panel-value">${escapeHtml(String(providerType))} · ${routeClass} · ${fallbackClass} · ${escapeHtml(String(item.status_normalized || item.status || '--'))}</span></div>`;
                    }).join('') : '<div class="panel-row"><span class="panel-label">No recent traffic</span><span class="panel-value">--</span></div>'}
                </div>
            </div>
        </div>

        <div class="table-container table-container-scroll" style="margin-top: 32px;">
            <div class="table-header">Provider Inventory</div>
            <div class="table-scroll-y">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Model</th>
                            <th>Weight</th>
                            <th>Health</th>
                            <th>Route</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${providers.map(provider => `
                            <tr>
                                <td>${provider.name}</td>
                                <td>${provider.type}</td>
                                <td>${provider.model}</td>
                                <td>${provider.weight}</td>
                                <td>${renderStatusWithDot(provider.health || 'unknown', provider.health === 'healthy' ? 'healthy' : 'unhealthy')}</td>
                                <td>${provider.enabled ? 'ON' : 'OFF'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="table-container table-container-scroll" style="margin-top: 32px;">
            <div class="table-header">Recent Control Actions</div>
            <div id="models-actions-history" class="table-loading table-scroll-y">Loading action history...</div>
        </div>
    `;

    document.getElementById('models-refresh-actions-btn')?.addEventListener('click', async () => {
        await loadModels();
    });

    document.getElementById('models-warmup-all-btn')?.addEventListener('click', async () => {
        const btn = document.getElementById('models-warmup-all-btn');
        btn.disabled = true;
        try {
            const result = await runControlAction('model_warmup_all', null, 20);
            alert(result.message || 'Warm-up completed');
            await loadModels();
        } catch (error) {
            alert(`Warm-up failed: ${error.message}`);
        } finally {
            btn.disabled = false;
        }
    });

    document.getElementById('models-enable-remote-btn')?.addEventListener('click', async () => {
        const targets = providers.filter(p => String(p.type).includes('ollama_remote') && !p.enabled);
        for (const provider of targets) {
            await runControlAction('provider_enable', provider.name);
        }
        await loadModels();
        alert(`Enabled ${targets.length} remote providers`);
    });

    document.getElementById('models-disable-cloud-btn')?.addEventListener('click', async () => {
        const targets = providers.filter(p => String(p.type).includes('cli_proxy') && p.enabled);
        for (const provider of targets) {
            await runControlAction('provider_disable', provider.name);
        }
        await loadModels();
        alert(`Disabled ${targets.length} cloud providers`);
    });

    document.getElementById('models-isolate-local-btn')?.addEventListener('click', async () => {
        const localTargets = providers.filter(p => String(p.type).includes('ollama_local'));
        const otherTargets = providers.filter(p => !String(p.type).includes('ollama_local'));
        for (const provider of localTargets) {
            if (!provider.enabled) await runControlAction('provider_enable', provider.name);
        }
        for (const provider of otherTargets) {
            if (provider.enabled) await runControlAction('provider_disable', provider.name);
        }
        await loadModels();
        alert('Routing posture switched to local-only');
    });

    pageEl.querySelectorAll('[data-action="warm-model"]').forEach(btn => {
        btn.addEventListener('click', async () => {
            btn.disabled = true;
            try {
                const result = await runControlAction('model_warmup', btn.dataset.target, 20);
                alert(result.message || 'Model warmed');
                await loadModels();
            } catch (error) {
                alert(`Model warm-up failed: ${error.message}`);
            } finally {
                btn.disabled = false;
            }
        });
    });

    pageEl.querySelectorAll('[data-action="toggle-provider"]').forEach(btn => {
        btn.addEventListener('click', async () => {
            btn.disabled = true;
            const isEnabled = btn.dataset.enabled === '1';
            try {
                const result = await runControlAction(isEnabled ? 'provider_disable' : 'provider_enable', btn.dataset.target);
                await loadModels();
                alert(result.message || (isEnabled ? 'Provider disabled' : 'Provider enabled'));
            } catch (error) {
                alert(`Provider toggle failed: ${error.message}`);
            } finally {
                btn.disabled = false;
            }
        });
    });

    loadControlActionHistory();
}

// System page
async function loadSystem() {
    try {
        const data = await fetchAPI('/control-api/system');
        systemData = data;
        renderSystem();
    } catch (error) {
        throw error;
    }
}

function renderSystem() {
    const pageEl = document.getElementById('page-system');
    const data = systemData;
    if (!data) return;

    const summary = data.summary || {};
    const nodes = data.health?.nodes || [];
    const alerts = data.alerts?.alerts || [];
    const workloads = data.workloads || {};
    const lbSummary = workloads.load_balancer?.summary || {};
    const surfaceHealth = [
        { name: 'api.tuetue.vn', role: 'runtime core', status: summary.overall_status || 'unknown' },
        { name: 'control.tuetue.vn', role: 'operator surface', status: 'healthy' },
        { name: 'console.tuetue.vn', role: 'developer portal', status: 'unknown' },
        { name: 'chat.tuetue.vn', role: 'product chat', status: 'unknown' }
    ];

    pageEl.innerHTML = `
        <div class="toast-container" id="toast-container"></div>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-eyebrow">System</div>
                <div class="kpi-title">Overall Status</div>
                <div class="kpi-value ${summary.overall_status === 'healthy' ? 'good' : (summary.overall_status === 'degraded' ? 'warning' : 'neutral')}">${String(summary.overall_status || 'unknown').toUpperCase()}</div>
                <div class="kpi-trend"><i class="fas fa-heartbeat"></i><span>Collector summary</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Nodes</div>
                <div class="kpi-title">Tracked Nodes</div>
                <div class="kpi-value neutral">${summary.node_count || 0}</div>
                <div class="kpi-trend"><i class="fas fa-server"></i><span>Infrastructure footprint</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">RAG</div>
                <div class="kpi-title">Documents</div>
                <div class="kpi-value neutral">${summary.rag_document_count || 0}</div>
                <div class="kpi-trend"><i class="fas fa-database"></i><span>Knowledge base size</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Alerts</div>
                <div class="kpi-title">Open Alerts</div>
                <div class="kpi-value ${(summary.alert_count || 0) > 0 ? 'warning' : 'good'}">${summary.alert_count || 0}</div>
                <div class="kpi-trend"><i class="fas fa-bell"></i><span>Current signals</span></div>
            </div>
        </div>

        <div class="action-grid" style="margin-bottom: 32px;">
            <div class="action-card">
                <div class="action-icon"><i class="fas fa-sync-alt"></i></div>
                <div class="action-title">Refresh Health</div>
                <div class="action-description">Force immediate health check of all backends</div>
                <button class="btn-action" data-action="health-refresh" data-confirm="false">Run Now</button>
            </div>
            <div class="action-card">
                <div class="action-icon"><i class="fas fa-fire"></i></div>
                <div class="action-title">Warm Up All Models</div>
                <div class="action-description">Pre‑warm all configured models for faster first‑response</div>
                <button class="btn-action btn-action-warning" data-action="model-warmup-all" data-confirm="true">Warm Up</button>
            </div>
            <div class="action-card">
                <div class="action-icon"><i class="fas fa-broom"></i></div>
                <div class="action-title">Clear Learn Queue</div>
                <div class="action-description">Empty the pending learn‑queue items (irreversible)</div>
                <button class="btn-action btn-action-danger" data-action="clear-learn-queue" data-confirm="true">Clear Queue</button>
            </div>
            <div class="action-card">
                <div class="action-icon"><i class="fas fa-archive"></i></div>
                <div class="action-title">Archive Old Events</div>
                <div class="action-description">Move events older than 30 days to cold storage</div>
                <button class="btn-action" data-action="archive-events" data-confirm="true">Archive</button>
            </div>
        </div>

        <div class="panel-grid" style="margin-bottom: 32px;">
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">System Priorities</div>
                    <div class="panel-subtitle">What this control plane should care about first</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row"><span class="panel-label">Primary Surface</span><span class="panel-value">api.tuetue.vn runtime core</span></div>
                    <div class="panel-row"><span class="panel-label">Operator Focus</span><span class="panel-value">control.tuetue.vn as active control plane</span></div>
                    <div class="panel-row"><span class="panel-label">Product Surface</span><span class="panel-value">chat.tuetue.vn health and route quality</span></div>
                    <div class="panel-row"><span class="panel-label">Developer Surface</span><span class="panel-value">console.tuetue.vn visibility and auth continuity</span></div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Operator Domains</div>
                    <div class="panel-subtitle">Control responsibility map</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row"><span class="panel-label">Runtime</span><span class="panel-value">API health, routing, latency, fallback</span></div>
                    <div class="panel-row"><span class="panel-label">Models</span><span class="panel-value">Warmup, provider posture, ollama inventory</span></div>
                    <div class="panel-row"><span class="panel-label">Data</span><span class="panel-value">RAG docs, queues, datasets, event archives</span></div>
                    <div class="panel-row"><span class="panel-label">Operations</span><span class="panel-value">Alerts, actions, maintenance, audit trail</span></div>
                </div>
            </div>
        </div>

        <div class="panel-grid">
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Surface Health</div>
                    <div class="panel-subtitle">Canonical product and control surfaces</div>
                </div>
                <div class="panel-content">
                    ${surfaceHealth.map(surface => `
                        <div class="panel-row">
                            <span class="panel-label">${surface.name}</span>
                            <span class="panel-value"><span class="badge ${getStatusTone(surface.status)}">${surface.status}</span> · ${surface.role}</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Node Health</div>
                    <div class="panel-subtitle">Service groups</div>
                </div>
                <div class="panel-content panel-scroll-y" style="max-height: 320px;">
                    ${nodes.length > 0 ? nodes.map(node => `
                        <div class="panel-row">
                            <span class="panel-label">${node.label} (${node.location})</span>
                            <span class="panel-value"><span class="badge ${getStatusTone(node.status)}">${node.status || 'unknown'}</span></span>
                        </div>
                    `).join('') : '<div class="panel-row"><span class="panel-label">No node data</span><span class="panel-value">--</span></div>'}
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Workload Summary</div>
                    <div class="panel-subtitle">Data + queue state</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row"><span class="panel-label">Learn Queue</span><span class="panel-value">${workloads.learn_queue?.length ?? workloads.learn_queue?.count ?? 0}</span></div>
                    <div class="panel-row"><span class="panel-label">Datasets</span><span class="panel-value">${workloads.datasets?.count ?? 0}</span></div>
                    <div class="panel-row"><span class="panel-label">Latest Dataset</span><span class="panel-value">${workloads.datasets?.latest || '--'}</span></div>
                    <div class="panel-row"><span class="panel-label">Vector Store Docs</span><span class="panel-value">${workloads.vector_store?.document_count ?? workloads.rag?.document_count ?? 0}</span></div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Alerts</div>
                    <div class="panel-subtitle">Current attention items</div>
                </div>
                <div class="panel-content panel-scroll-y" style="max-height: 320px;">
                    ${alerts.length > 0 ? alerts.slice(0, 10).map(alert => `
                        <div class="panel-row">
                            <span class="panel-label">${alert.message || 'Alert'}</span>
                            <span class="panel-value"><span class="badge ${getStatusTone(alert.severity)}">${alert.severity || 'info'}</span></span>
                        </div>
                    `).join('') : '<div class="panel-row"><span class="panel-label">No active alerts</span><span class="panel-value"><span class="badge badge-success">clear</span></span></div>'}
                </div>
            </div>
        </div>

        <div class="table-container table-container-scroll" style="margin-top: 32px;">
            <div class="table-header">Backend Health Summary</div>
            <div class="table-scroll-y">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Backend</th>
                            <th>Counts</th>
                            <th>Avg Latency</th>
                            <th>Last Latency</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${Object.entries(lbSummary).length > 0 ? Object.entries(lbSummary).map(([backend, info]) => `
                            <tr>
                                <td>${backend}</td>
                                <td>${formatKeyValuePairs(info.counts)}</td>
                                <td>${formatLatency(info.avg_latency_ms)}</td>
                                <td>${formatLatency(info.last_latency_ms)}</td>
                            </tr>
                        `).join('') : '<tr><td colspan="4">No backend activity yet</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="table-container table-container-scroll" style="margin-top: 32px;">
            <div class="table-header">Recent Operator Actions</div>
            <div id="system-actions-history" class="table-loading table-scroll-y">Loading action history...</div>
        </div>
    `;

    // Attach action card listeners
    pageEl.querySelectorAll('[data-action="health-refresh"]').forEach(btn => {
        btn.addEventListener('click', async () => {
            btn.disabled = true;
            try {
                const result = await runControlAction('health_refresh');
                showToast(result.message || 'Health refreshed', 'success');
                await loadSystem();
            } catch (error) {
                showToast(`Health refresh failed: ${error.message}`, 'error');
            } finally {
                btn.disabled = false;
            }
        });
    });

    pageEl.querySelectorAll('[data-action="model-warmup-all"]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const confirmed = await confirmAction('Warm up all models? This may take 20‑30 seconds.', false);
            if (!confirmed) return;
            btn.disabled = true;
            try {
                const result = await runControlAction('model_warmup_all', null, 20);
                showToast(result.message || 'All models warmed up', 'success');
                await loadSystem();
            } catch (error) {
                showToast(`Warm‑up failed: ${error.message}`, 'error');
            } finally {
                btn.disabled = false;
            }
        });
    });

    pageEl.querySelectorAll('[data-action="clear-learn-queue"]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const confirmed = await confirmAction('Clear the learn queue? This action is irreversible and will delete pending learning items.', true);
            if (!confirmed) return;
            btn.disabled = true;
            try {
                const result = await runControlAction('clear_learn_queue');
                showToast(result.message || 'Learn queue cleared', 'success');
                await loadSystem();
            } catch (error) {
                showToast(`Clear failed: ${error.message}`, 'error');
            } finally {
                btn.disabled = false;
            }
        });
    });

    pageEl.querySelectorAll('[data-action="archive-events"]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const confirmed = await confirmAction('Archive events older than 30 days? This moves them to cold storage.', false);
            if (!confirmed) return;
            btn.disabled = true;
            try {
                const result = await runControlAction('archive_events');
                showToast(result.message || 'Events archived', 'success');
                await loadSystem();
            } catch (error) {
                showToast(`Archive failed: ${error.message}`, 'error');
            } finally {
                btn.disabled = false;
            }
        });
    });

    pageEl.querySelectorAll('[data-action="health-refresh-inline"]').forEach(btn => {
        btn.addEventListener('click', async () => {
            btn.disabled = true;
            try {
                const result = await runControlAction('health_refresh');
                showToast(result.message || 'Health refreshed', 'success');
                await loadSystem();
            } catch (error) {
                showToast(`Health refresh failed: ${error.message}`, 'error');
            } finally {
                btn.disabled = false;
            }
        });
    });

    pageEl.querySelectorAll('[data-nav]').forEach(btn => {
        btn.addEventListener('click', () => switchPage(btn.dataset.nav));
    });

    loadControlActionHistory('system-actions-history');
}

// Toast and confirm utilities
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${message}</span><button class="toast-close">&times;</button>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('toast-show');
    }, 10);
    setTimeout(() => {
        toast.classList.remove('toast-show');
        setTimeout(() => {
            if (toast.parentNode) container.removeChild(toast);
        }, 300);
    }, 5000);
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.classList.remove('toast-show');
        setTimeout(() => {
            if (toast.parentNode) container.removeChild(toast);
        }, 300);
    });
}

function confirmAction(message, dangerous = false) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'confirm-overlay';
        overlay.innerHTML = `
            <div class="confirm-dialog ${dangerous ? 'confirm-dangerous' : ''}">
                <div class="confirm-title">${dangerous ? '⚠️ Dangerous Action' : 'Confirm Action'}</div>
                <div class="confirm-message">${message}</div>
                <div class="confirm-buttons">
                    <button class="confirm-cancel">Cancel</button>
                    <button class="confirm-ok">${dangerous ? 'Proceed Anyway' : 'OK'}</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        overlay.querySelector('.confirm-cancel').addEventListener('click', () => {
            document.body.removeChild(overlay);
            resolve(false);
        });
        overlay.querySelector('.confirm-ok').addEventListener('click', () => {
            document.body.removeChild(overlay);
            resolve(true);
        });
    });
}

// Usage page
async function loadUsage() {
    try {
        const data = await fetchAPI('/control-api/usage?limit=20');
        usageData = data;
        renderUsage();
    } catch (error) {
        throw error;
    }
}

function renderUsage() {
    const pageEl = document.getElementById('page-usage');
    const data = usageData;
    if (!data) return;

    const summary = data.summary || {};
    const highlights = data.highlights || {};
    const recentEvents = data.recent_events || [];
    const topUsers = summary.top_users || [];
    const topProviders = summary.top_providers || [];
    const statusBreakdown = data.breakdowns?.status_normalized || summary.status_breakdown || {};
    const topTenants = data.breakdowns?.top_tenants || [];
    const topApiKeys = data.breakdowns?.top_api_keys || [];

    pageEl.innerHTML = `
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-eyebrow">Usage</div>
                <div class="kpi-title">Total Events</div>
                <div class="kpi-value neutral">${highlights.total_events || 0}</div>
                <div class="kpi-trend"><i class="fas fa-chart-bar"></i><span>Ledger events</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Success</div>
                <div class="kpi-title">Successful Calls</div>
                <div class="kpi-value good">${highlights.success_events || 0}</div>
                <div class="kpi-trend"><i class="fas fa-check-circle"></i><span>Processed successfully</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Quota</div>
                <div class="kpi-title">Quota Exceeded</div>
                <div class="kpi-value ${(highlights.quota_exceeded_events || 0) > 0 ? 'warning' : 'good'}">${highlights.quota_exceeded_events || 0}</div>
                <div class="kpi-trend"><i class="fas fa-ban"></i><span>Normalized outcome</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Fallback</div>
                <div class="kpi-title">Fallback Rate</div>
                <div class="kpi-value neutral">${formatPercent(highlights.fallback_rate || 0)}</div>
                <div class="kpi-trend"><i class="fas fa-random"></i><span>${formatLatency(highlights.avg_processing_time_deduped || 0)} avg latency</span></div>
            </div>
        </div>

        <div class="panel-grid">
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Top Users</div>
                    <div class="panel-subtitle">Highest request volume</div>
                </div>
                <div class="panel-content">
                    ${topUsers.length > 0 ? topUsers.slice(0, 6).map(([user, count]) => `
                        <div class="panel-row">
                            <span class="panel-label">${formatShortLabel(user, 24)}</span>
                            <span class="panel-value">${count}</span>
                        </div>
                    `).join('') : '<div class="panel-row"><span class="panel-label">No user data</span><span class="panel-value">--</span></div>'}
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Top Providers</div>
                    <div class="panel-subtitle">Most selected backends</div>
                </div>
                <div class="panel-content">
                    ${topProviders.length > 0 ? topProviders.slice(0, 6).map(([provider, count]) => `
                        <div class="panel-row">
                            <span class="panel-label">${formatShortLabel(provider, 28)}</span>
                            <span class="panel-value">${count}</span>
                        </div>
                    `).join('') : '<div class="panel-row"><span class="panel-label">No provider data</span><span class="panel-value">--</span></div>'}
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Status Breakdown</div>
                    <div class="panel-subtitle">Outcome distribution</div>
                </div>
                <div class="panel-content">
                    ${Object.entries(statusBreakdown).length > 0 ? Object.entries(statusBreakdown).slice(0, 6).map(([status, count]) => `
                        <div class="panel-row">
                            <span class="panel-label">${status}</span>
                            <span class="panel-value"><span class="badge ${getStatusTone(status)}">${count}</span></span>
                        </div>
                    `).join('') : '<div class="panel-row"><span class="panel-label">No status data</span><span class="panel-value">--</span></div>'}
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Top Tenants</div>
                    <div class="panel-subtitle">Request volume by tenant</div>
                </div>
                <div class="panel-content">
                    ${topTenants.length > 0 ? topTenants.slice(0, 6).map(([tenant, count]) => `
                        <div class="panel-row">
                            <span class="panel-label">${formatShortLabel(tenant, 24)}</span>
                            <span class="panel-value">${count}</span>
                        </div>
                    `).join('') : '<div class="panel-row"><span class="panel-label">No tenant data</span><span class="panel-value">--</span></div>'}
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Top API Keys</div>
                    <div class="panel-subtitle">Request volume by API key</div>
                </div>
                <div class="panel-content">
                    ${topApiKeys.length > 0 ? topApiKeys.slice(0, 6).map(([key, count]) => `
                        <div class="panel-row">
                            <span class="panel-label">${formatShortLabel(key, 18)}</span>
                            <span class="panel-value">${count}</span>
                        </div>
                    `).join('') : '<div class="panel-row"><span class="panel-label">No API key data</span><span class="panel-value">--</span></div>'}
                </div>
            </div>
        </div>

        <div class="table-container table-container-scroll" style="margin-top: 32px;">
            <div class="table-header">Recent Usage Events</div>
            <div class="table-scroll-y">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>User</th>
                            <th>Provider</th>
                            <th>Model</th>
                            <th>Status</th>
                            <th>Tokens</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${recentEvents.length > 0 ? recentEvents.map(event => `
                            <tr>
                                <td>${formatTimestamp(event.timestamp)}</td>
                                <td>${formatShortLabel(event.user_id, 20)}</td>
                                <td>${formatShortLabel(event.provider || event.provider_type || '--', 24)}</td>
                                <td>${formatShortLabel(event.model, 24)}</td>
                                <td><span class="badge ${getStatusTone(event.status_normalized || event.status)}">${event.status_normalized || event.status || '--'}</span></td>
                                <td>${Number(event.total_tokens_est || 0).toLocaleString('en-US')}</td>
                            </tr>
                        `).join('') : '<tr><td colspan="6">No recent events</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

async function loadProxy() {
    try {
        const [proxyState, proxyBackends, proxyBenchmark, usage] = await Promise.all([
            fetchAPI('/control-api/proxy/state'),
            fetchAPI('/control-api/proxy/backends'),
            fetchAPI('/control-api/proxy/benchmark/latest'),
            fetchAPI('/control-api/usage?limit=30')
        ]);

        let proxyMetrics = null;
        try {
            proxyMetrics = await fetchAPI('/control-api/proxy/metrics');
        } catch (error) {
            proxyMetrics = null;
        }

        proxyStateData = proxyState;
        proxyBackendsData = proxyBackends;
        proxyBenchmarkData = proxyBenchmark;
        renderProxy(proxyMetrics, usage);
    } catch (error) {
        const pageEl = document.getElementById('page-proxy');
        if (pageEl) {
            pageEl.innerHTML = `
                <div class="panel-grid">
                    <div class="panel">
                        <div class="panel-header">
                            <div class="panel-title">Proxy Dashboard</div>
                            <div class="panel-subtitle">Load failed</div>
                        </div>
                        <div class="panel-content">
                            <div class="panel-row"><span class="panel-label">Status</span><span class="panel-value">Error</span></div>
                            <div class="panel-row"><span class="panel-label">Detail</span><span class="panel-value">${escapeHtml(error.message || String(error))}</span></div>
                        </div>
                    </div>
                </div>
            `;
        }
    }
}

function renderProxy(proxyMetrics, usageDataPayload) {
    const pageEl = document.getElementById('page-proxy');
    const proxyState = proxyStateData || {};
    const proxyBackends = proxyBackendsData || {};
    const proxyBenchmark = proxyBenchmarkData || {};
    const proxySummary = proxyState.summary || {};
    const proxyRuntime = proxyState.runtime || {};
    const proxyItems = proxyBackends.items || [];
    const benchmarkSummary = proxyBenchmark.summary || {};
    const usageItems = Array.isArray(usageDataPayload?.events) ? usageDataPayload.events : [];

    const totalRequests = proxyMetrics?.requests_total ?? proxySummary.requests_total ?? 0;
    const successRate = proxyMetrics?.success_rate != null ? `${(proxyMetrics.success_rate * 100).toFixed(1)}%` : '--';
    const avgLatency = proxyMetrics?.avg_latency != null ? `${Number(proxyMetrics.avg_latency).toFixed(2)} s` : '--';
    const uptime = proxyMetrics?.uptime_human || proxySummary.uptime_human || '--';
    const serviceStatus = proxySummary.status || proxyRuntime.status || 'unknown';
    const serviceTone = serviceStatus === 'healthy' ? 'good' : (serviceStatus === 'degraded' ? 'warning' : 'danger');
    const mode = proxyRuntime.mode || proxySummary.mode || '--';
    const hedgeEnabled = proxyRuntime.hedge?.enabled ?? proxySummary.hedge_enabled;
    const hedgeDelay = proxyRuntime.hedge?.delay_seconds ?? proxySummary.hedge_delay_seconds;
    const preferredBackend = proxyRuntime.preferred_backend || proxySummary.preferred_backend || '--';

    const recentProxyQueries = usageItems
        .filter(item => {
            const providerType = String(item.provider_type || '').toLowerCase();
            const model = String(item.model || item.provider || '').toLowerCase();
            const requestPath = String(item.request_path || '').toLowerCase();
            return requestPath.includes('/chat') || providerType.includes('ollama') || providerType.includes('cli') || model.includes('gemma') || model.includes('deepseek');
        })
        .slice(0, 15);

    pageEl.innerHTML = `
        <div class="action-bar">
            <button class="btn-refresh" id="proxy-refresh-btn">
                <i class="fas fa-sync-alt"></i>
                Refresh Proxy Snapshot
            </button>
            <button class="btn-refresh" id="proxy-open-dashboard-btn">
                <i class="fas fa-arrow-up-right-from-square"></i>
                Open Raw Proxy Dashboard
            </button>
            <button class="btn-refresh" id="proxy-run-benchmark-btn">
                <i class="fas fa-stopwatch"></i>
                Run Benchmark
            </button>
        </div>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-eyebrow">Proxy</div>
                <div class="kpi-title">Service Status</div>
                <div class="kpi-value ${serviceTone}">${String(serviceStatus).toUpperCase()}</div>
                <div class="kpi-trend"><i class="fas fa-route"></i><span>Port 8015 front door</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Traffic</div>
                <div class="kpi-title">Total Requests</div>
                <div class="kpi-value neutral">${totalRequests}</div>
                <div class="kpi-trend"><i class="fas fa-chart-line"></i><span>Live proxy metrics</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Reliability</div>
                <div class="kpi-title">Success Rate</div>
                <div class="kpi-value neutral">${successRate}</div>
                <div class="kpi-trend"><i class="fas fa-percent"></i><span>Observed responses</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Latency</div>
                <div class="kpi-title">Average Response</div>
                <div class="kpi-value neutral">${avgLatency}</div>
                <div class="kpi-trend"><i class="fas fa-clock"></i><span>Uptime: ${uptime}</span></div>
            </div>
        </div>

        <div class="panel-grid">
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Proxy Runtime</div>
                    <div class="panel-subtitle">Live routing state</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row"><span class="panel-label">Mode</span><span class="panel-value"><select id="proxy-mode-select" class="input-inline"><option value="stabilize" ${mode === 'stabilize' ? 'selected' : ''}>stabilize</option><option value="remote-first" ${mode === 'remote-first' ? 'selected' : ''}>remote-first</option><option value="balanced-lite" ${mode === 'balanced-lite' ? 'selected' : ''}>balanced-lite</option><option value="diagnostic" ${mode === 'diagnostic' ? 'selected' : ''}>diagnostic</option></select></span></div>
                    <div class="panel-row"><span class="panel-label">Preferred Backend</span><span class="panel-value">${escapeHtml(String(preferredBackend))}</span></div>
                    <div class="panel-row"><span class="panel-label">Hedge</span><span class="panel-value"><label><input type="checkbox" id="proxy-hedge-toggle" ${hedgeEnabled ? 'checked' : ''}/> enabled</label></span></div>
                    <div class="panel-row"><span class="panel-label">Hedge Delay</span><span class="panel-value"><input id="proxy-hedge-delay" class="input-inline" type="number" min="0" max="5" step="0.05" value="${hedgeDelay ?? 0.35}" /></span></div>
                    <div class="panel-row"><span class="panel-label">State Source</span><span class="panel-value">${escapeHtml(String(proxySummary.state_source || proxyRuntime.state_source || '--'))}</span></div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Benchmark Snapshot</div>
                    <div class="panel-subtitle">Direct vs proxy overhead</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row"><span class="panel-label">Status</span><span class="panel-value">${escapeHtml(String(benchmarkSummary.status || (proxyBenchmark.available ? 'available' : 'not_run')))}</span></div>
                    <div class="panel-row"><span class="panel-label">Last Run</span><span class="panel-value">${escapeHtml(String(benchmarkSummary.last_run || '--'))}</span></div>
                    <div class="panel-row"><span class="panel-label">Overhead</span><span class="panel-value">${benchmarkSummary.overhead_ms != null ? `${Number(benchmarkSummary.overhead_ms).toFixed(2)} ms` : '--'}</span></div>
                    <div class="panel-row"><span class="panel-label">Recommendation</span><span class="panel-value">${escapeHtml(String(benchmarkSummary.recommendation || '--'))}</span></div>
                    <div id="benchmark-progress-container" style="display:none;">
                        <div class="panel-row"><span class="panel-label">Progress</span><span class="panel-value"><progress id="benchmark-progress-bar" value="0" max="1" style="width: 200px;"></progress> <span id="benchmark-progress-text">0%</span></span></div>
                        <div class="panel-row"><span class="panel-label">Run ID</span><span class="panel-value" id="benchmark-run-id">--</span></div>
                        <div class="panel-row"><span class="panel-label">Actions</span><span class="panel-value"><button id="cancel-benchmark-btn" class="btn-refresh">Cancel</button></span></div>
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Backend Pool</div>
                    <div class="panel-subtitle">Current routing candidates</div>
                </div>
                <div class="panel-content">
                    ${proxyItems.length ? proxyItems.map(item => `
                        <div class="panel-row">
                            <span class="panel-label">${escapeHtml(String(item.id || item.name || 'backend'))} · ${escapeHtml(String(item.role || '--'))} · ${item.healthy ? 'healthy' : 'unhealthy'}</span>
                            <span class="panel-value"><label><input type="checkbox" class="proxy-backend-toggle" data-backend-id="${item.id}" ${item.enabled ? 'checked' : ''}/> on</label> <input type="number" class="input-inline proxy-backend-weight" data-backend-id="${item.id}" min="0" max="100" step="1" value="${item.weight ?? 0}" />% <button class="btn-refresh proxy-weight-apply" data-backend-id="${item.id}">Apply</button></span>
                        </div>
                    `).join('') : `<div class="panel-row"><span class="panel-label">Backends</span><span class="panel-value">No backend data</span></div>`}
                </div>
            </div>

            <div class="panel" style="grid-column: 1 / -1;">
                <div class="panel-header">
                    <div class="panel-title">Recent 15 Proxy-Relevant Queries</div>
                    <div class="panel-subtitle">Remote vs fallback visibility from recent usage events</div>
                </div>
                <div class="panel-content">
                    ${recentProxyQueries.length ? recentProxyQueries.map(item => {
                        const providerType = String(item.provider_type || '--');
                        const model = String(item.model || item.provider || '--');
                        const remoteFlag = providerType.includes('remote') || model.toLowerCase().includes('remote') ? 'remote' : 'local/cloud';
                        const fallbackFlag = item.fallback_used ? 'fallback' : 'primary';
                        const status = item.status_normalized || item.status || '--';
                        return `<div class="panel-row"><span class="panel-label">${escapeHtml(formatTimestamp(item.timestamp))} · ${escapeHtml(model)}</span><span class="panel-value">${escapeHtml(providerType)} · ${remoteFlag} · ${fallbackFlag} · ${escapeHtml(String(status))}</span></div>`;
                    }).join('') : `<div class="panel-row"><span class="panel-label">Queries</span><span class="panel-value">No recent query data</span></div>`}
                </div>
            </div>
        </div>
    `;

    document.getElementById('proxy-refresh-btn')?.addEventListener('click', async () => {
        await loadProxy();
        showToast('Proxy snapshot refreshed', 'success');
    });

    document.getElementById('proxy-open-dashboard-btn')?.addEventListener('click', () => {
        window.open('http://localhost:8015/proxy/dashboard', '_blank');
    });

    document.getElementById('proxy-run-benchmark-btn')?.addEventListener('click', async () => {
        const btn = document.getElementById('proxy-run-benchmark-btn');
        btn.disabled = true;
        try {
            const result = await runProxyBenchmark();
            document.getElementById('benchmark-run-id').textContent = result.run_id;
            document.getElementById('benchmark-progress-container').style.display = 'block';
            document.getElementById('benchmark-progress-bar').value = 0;
            document.getElementById('benchmark-progress-text').textContent = '0%';
            const interval = setInterval(async () => {
                try {
                    const status = await getBenchmarkStatus(result.run_id);
                    if (!status) {
                        clearInterval(interval);
                        return;
                    }
                    document.getElementById('benchmark-progress-bar').value = status.progress;
                    document.getElementById('benchmark-progress-text').textContent = `${Math.round(status.progress * 100)}%`;
                    if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
                        clearInterval(interval);
                        btn.disabled = false;
                        await loadProxy();
                    }
                } catch (err) {
                    console.error('Benchmark status poll error:', err);
                }
            }, 2000);
            document.getElementById('cancel-benchmark-btn').onclick = async () => {
                clearInterval(interval);
                await cancelBenchmark(result.run_id);
                btn.disabled = false;
                await loadProxy();
            };
        } catch (error) {
            btn.disabled = false;
            showToast('Failed to start proxy benchmark', 'error');
        }
    });

    document.getElementById('proxy-mode-select')?.addEventListener('change', async (e) => {
        try {
            await updateProxyMode(e.target.value);
            await loadProxy();
        } catch (error) {
            alert(`Proxy mode update failed: ${error.message}`);
        }
    });

    document.getElementById('proxy-hedge-toggle')?.addEventListener('change', async () => {
        const enabled = document.getElementById('proxy-hedge-toggle')?.checked || false;
        const delay = parseFloat(document.getElementById('proxy-hedge-delay')?.value || '0.35');
        try {
            await updateProxyHedge(enabled, delay);
            await loadProxy();
        } catch (error) {
            alert(`Proxy hedge update failed: ${error.message}`);
        }
    });

    document.getElementById('proxy-hedge-delay')?.addEventListener('change', async () => {
        const enabled = document.getElementById('proxy-hedge-toggle')?.checked || false;
        const delay = parseFloat(document.getElementById('proxy-hedge-delay')?.value || '0.35');
        try {
            await updateProxyHedge(enabled, delay);
            await loadProxy();
        } catch (error) {
            alert(`Proxy hedge delay update failed: ${error.message}`);
        }
    });

    document.querySelectorAll('.proxy-backend-toggle').forEach(toggle => {
        toggle.addEventListener('change', async (e) => {
            const backendId = e.target.getAttribute('data-backend-id');
            try {
                await toggleProxyBackend(backendId, e.target.checked);
                await loadProxy();
            } catch (error) {
                alert(`Backend toggle failed: ${error.message}`);
            }
        });
    });

    document.querySelectorAll('.proxy-weight-apply').forEach(button => {
        button.addEventListener('click', async (e) => {
            const backendId = e.target.getAttribute('data-backend-id');
            const input = document.querySelector(`.proxy-backend-weight[data-backend-id="${backendId}"]`);
            const weight = parseInt(input?.value || '0', 10);
            try {
                await updateProxyBackendWeight(backendId, weight);
                await loadProxy();
            } catch (error) {
                alert(`Backend weight update failed: ${error.message}`);
            }
        });
    });
}

function renderAbout() {
    const pageEl = document.getElementById('page-about');
    pageEl.innerHTML = `
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-eyebrow">About</div>
                <div class="kpi-title">TTAi Control</div>
                <div class="kpi-value neutral">v0.1</div>
                <div class="kpi-trend"><i class="fas fa-circle-info"></i><span>Operator dashboard</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Purpose</div>
                <div class="kpi-title">Control Surface</div>
                <div class="kpi-value neutral">Admin</div>
                <div class="kpi-trend"><i class="fas fa-shield-halved"></i><span>System operations</span></div>
            </div>
        </div>

        <div class="panel-grid">
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">What this dashboard is for</div>
                    <div class="panel-subtitle">High-level guidance</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row"><span class="panel-label">Monitor health</span><span class="panel-value">Providers, models, system</span></div>
                    <div class="panel-row"><span class="panel-label">Operate safely</span><span class="panel-value">Run guarded admin actions</span></div>
                    <div class="panel-row"><span class="panel-label">Review usage</span><span class="panel-value">Quota, billing, errors, traffic</span></div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">How to use</div>
                    <div class="panel-subtitle">Quick operator notes</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row"><span class="panel-label">Models tab</span><span class="panel-value">Warm up and toggle providers</span></div>
                    <div class="panel-row"><span class="panel-label">System tab</span><span class="panel-value">Run safe maintenance actions</span></div>
                    <div class="panel-row"><span class="panel-label">Usage / Errors</span><span class="panel-value">Inspect live behavior and failures</span></div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Important notes</div>
                    <div class="panel-subtitle">Current behavior</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row"><span class="panel-label">Healthy vs Enabled</span><span class="panel-value">Health and routing are separate states</span></div>
                    <div class="panel-row"><span class="panel-label">Guardrails</span><span class="panel-value">Sensitive actions ask for confirmation</span></div>
                    <div class="panel-row"><span class="panel-label">Feedback</span><span class="panel-value">Toasts show action result quickly</span></div>
                </div>
            </div>
        </div>
    `;
}

// Errors page
async function loadErrors() {
    try {
        const data = await fetchAPI('/control-api/errors?limit=50&top_n=5');
        errorsData = data;
        renderErrors();
    } catch (error) {
        throw error;
    }
}

function renderErrors() {
    const pageEl = document.getElementById('page-errors');
    const data = errorsData;
    
    if (!data) return;
    
    const errorCount = data.error_event_count || 0;
    const statusBreakdown = data.status_breakdown || {};
    const httpStatusBreakdown = data.http_status_breakdown || {};
    const providerBreakdown = data.provider_breakdown || {};
    const topErrorSignatures = data.top_error_signatures || [];
    const topProviderError = Object.keys(providerBreakdown)[0] || null;
    const topHttpError = Object.keys(httpStatusBreakdown)[0] || null;
    const needsAttention = errorCount > 0 || topErrorSignatures.length > 0;
    
    pageEl.innerHTML = `
        <div class="toast-container" id="toast-container"></div>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-eyebrow">Errors</div>
                <div class="kpi-title">Error Events</div>
                <div class="kpi-value ${errorCount > 0 ? 'warning' : 'neutral'}">${errorCount}</div>
                <div class="kpi-trend">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Last 24h</span>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-eyebrow">Status</div>
                <div class="kpi-title">Top Status</div>
                <div class="kpi-value neutral">${Object.keys(statusBreakdown)[0] || 'N/A'}</div>
                <div class="kpi-trend">
                    <i class="fas fa-code"></i>
                    <span>Most common</span>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-eyebrow">HTTP</div>
                <div class="kpi-title">Top HTTP Status</div>
                <div class="kpi-value neutral">${Object.keys(httpStatusBreakdown)[0] || 'N/A'}</div>
                <div class="kpi-trend">
                    <i class="fas fa-globe"></i>
                    <span>Most common</span>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-eyebrow">Provider</div>
                <div class="kpi-title">Top Provider</div>
                <div class="kpi-value neutral">${Object.keys(providerBreakdown)[0] || 'N/A'}</div>
                <div class="kpi-trend">
                    <i class="fas fa-network-wired"></i>
                    <span>Most errors</span>
                </div>
            </div>
        </div>
        
        <div class="panel-grid">
            <div class="panel operator-panel ${needsAttention ? 'operator-panel-warning' : ''}">
                <div class="panel-header">
                    <div class="panel-title">Operator Guidance</div>
                    <div class="panel-subtitle">Recommended next step</div>
                </div>
                <div class="panel-content">
                    <div class="operator-guidance-copy">${needsAttention ? `Errors are active${topProviderError ? ` and ${escapeHtml(topProviderError)} is currently leading` : ''}. Refresh health first, then inspect Models or System before making routing changes.` : 'No immediate error spike detected. Keep monitoring and refresh snapshots when needed.'}</div>
                    <div class="operator-guidance-actions">
                        <button class="btn-action" data-action="errors-refresh-health">Refresh Health</button>
                        <button class="btn-action" data-nav="models">Open Models</button>
                        <button class="btn-action" data-nav="system">Open System</button>
                    </div>
                    <div class="operator-guidance-meta">${topHttpError ? `Top HTTP status: ${escapeHtml(topHttpError)}` : 'No dominant HTTP error code'}${topProviderError ? ` · Top provider: ${escapeHtml(topProviderError)}` : ''}</div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Status Breakdown</div>
                    <div class="panel-subtitle">Errors by status</div>
                </div>
                <div class="panel-content">
                    ${Object.entries(statusBreakdown).length > 0 ? 
                        Object.entries(statusBreakdown).slice(0, 5).map(([status, count]) => `
                            <div class="panel-row">
                                <span class="panel-label">${status}</span>
                                <span class="panel-value">${count}</span>
                            </div>
                        `).join('') : 
                        `<div class="panel-row">
                            <span class="panel-label">No status data</span>
                            <span class="panel-value">--</span>
                        </div>`
                    }
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">HTTP Status Breakdown</div>
                    <div class="panel-subtitle">Errors by HTTP code</div>
                </div>
                <div class="panel-content">
                    ${Object.entries(httpStatusBreakdown).length > 0 ? 
                        Object.entries(httpStatusBreakdown).slice(0, 5).map(([code, count]) => `
                            <div class="panel-row">
                                <span class="panel-label">${code}</span>
                                <span class="panel-value">${count}</span>
                            </div>
                        `).join('') : 
                        `<div class="panel-row">
                            <span class="panel-label">No HTTP status data</span>
                            <span class="panel-value">--</span>
                        </div>`
                    }
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Provider Breakdown</div>
                    <div class="panel-subtitle">Errors by provider</div>
                </div>
                <div class="panel-content">
                    ${Object.entries(providerBreakdown).length > 0 ? 
                        Object.entries(providerBreakdown).slice(0, 5).map(([provider, count]) => `
                            <div class="panel-row">
                                <span class="panel-label">${provider}</span>
                                <span class="panel-value">${count}</span>
                            </div>
                        `).join('') : 
                        `<div class="panel-row">
                            <span class="panel-label">No provider data</span>
                            <span class="panel-value">--</span>
                        </div>`
                    }
                </div>
            </div>
        </div>
        
        ${topErrorSignatures.length > 0 ? `
            <div class="table-container" style="margin-top: 32px;">
                <div class="table-header">Top Error Signatures</div>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Signature</th>
                            <th>Count</th>
                            <th>Last Seen</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${topErrorSignatures.slice(0, 10).map(sig => `
                            <tr>
                                <td><span class="signature-text">${formatErrorSignature(sig.signature)}</span></td>
                                <td>${sig.count || 0}</td>
                                <td>${sig.last_seen || '--'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        ` : ''}
    `;

    pageEl.querySelectorAll('[data-action="errors-refresh-health"]').forEach(btn => {
        btn.addEventListener('click', async () => {
            btn.disabled = true;
            try {
                const result = await runControlAction('health_refresh');
                showToast(result.message || 'Health refreshed', 'success');
                await loadErrors();
            } catch (error) {
                showToast(`Health refresh failed: ${error.message}`, 'error');
            } finally {
                btn.disabled = false;
            }
        });
    });

    pageEl.querySelectorAll('[data-nav]').forEach(btn => {
        btn.addEventListener('click', () => switchPage(btn.dataset.nav));
    });
}
