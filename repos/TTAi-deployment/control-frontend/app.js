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
let trafficSplitData = null;

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
        updateSidebarStatus(true);
    } catch (error) {
        updateSidebarStatus(false);
        return;
    }

    const initialHashPage = (window.location.hash || '#overview').replace('#', '');
    const allowedPages = ['overview', 'quota', 'billing', 'errors', 'models', 'system', 'usage', 'users', 'proxy', 'providers', 'about'];
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

    document.addEventListener('keydown', (e) => {
        if (e.key === 'r' || e.key === 'R') {
            const tag = document.activeElement?.tagName;
            if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
            refreshCurrentPage();
        }
    });

    initAutoRefresh();
});

// Sidebar connection status
function updateSidebarStatus(connected) {
    const dot = document.getElementById('sidebar-status-dot');
    const text = document.getElementById('sidebar-status-text');
    if (!dot || !text) return;
    if (connected) {
        dot.className = 'status-dot online';
        text.textContent = 'API Connected';
    } else {
        dot.className = 'status-dot offline';
        text.textContent = 'Disconnected';
    }
}

// Auto-refresh
let _autoRefreshInterval = 0;
let _autoRefreshRemaining = 0;

function initAutoRefresh() {
    const select = document.getElementById('auto-refresh-select');
    const countdownEl = document.getElementById('auto-refresh-countdown');
    if (!select) return;

    select.addEventListener('change', () => {
        _autoRefreshInterval = parseInt(select.value, 10);
        _autoRefreshRemaining = _autoRefreshInterval;
        if (countdownEl) countdownEl.textContent = _autoRefreshInterval > 0 ? `${_autoRefreshInterval}s` : '';
    });

    setInterval(() => {
        if (_autoRefreshInterval <= 0) return;
        _autoRefreshRemaining--;
        if (countdownEl) countdownEl.textContent = `${_autoRefreshRemaining}s`;
        if (_autoRefreshRemaining <= 0) {
            _autoRefreshRemaining = _autoRefreshInterval;
            refreshCurrentPage();
        }
    }, 1000);
}

function _resetAutoRefreshCountdown() {
    _autoRefreshRemaining = _autoRefreshInterval;
}

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
        users: 'Users',
        proxy: 'Proxy',
        providers: 'Providers',
        about: 'About'
    };
    pageTitle.textContent = pageTitles[page] || 'Dashboard';
    document.title = `${pageTitles[page] || 'Dashboard'} — TTAi Control`;

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
            updateSidebarStatus(false);
            window.location.href = '/control-login';
            throw new Error('Control authentication required');
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        if (error instanceof TypeError) {
            updateSidebarStatus(false);
        }
        console.error(`API fetch failed: ${endpoint}`, error);
        throw error;
    }
}

// Page loading — stale-while-revalidate caching
function _hasCachedData(page) {
    const cache = {
        overview: overviewData, quota: quotaData, billing: billingData,
        errors: errorsData, models: modelsData, system: systemData,
        usage: usageData, users: usersData, proxy: proxyStateData,
        providers: providersData, about: true
    };
    return !!cache[page];
}

function _renderCached(page) {
    switch (page) {
        case 'overview': renderOverview(); break;
        case 'quota': renderQuota(); break;
        case 'billing': renderBilling(); break;
        case 'errors': renderErrors(); break;
        case 'models': renderModels(); break;
        case 'system': renderSystem(); break;
        case 'usage': renderUsage(); break;
        case 'users': renderUsers(); break;
        case 'providers': renderProviders(); break;
        case 'about': renderAbout(); break;
        // proxy skipped — complex multi-source state
    }
}

async function loadPage(page) {
    const pageEl = document.getElementById(`page-${page}`);
    const lastUpdatedEl = document.getElementById('page-last-updated');
    const hasCached = _hasCachedData(page);

    if (hasCached) {
        // Render stale data immediately, then refresh silently
        _renderCached(page);
        if (lastUpdatedEl) lastUpdatedEl.textContent = 'Refreshing...';
    } else {
        if (lastUpdatedEl) lastUpdatedEl.textContent = '';
        pageEl.innerHTML = `
            <div class="loading-state">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading ${page} data...</p>
            </div>
        `;
    }

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
            case 'users':
                await loadUsers();
                break;
            case 'providers':
                await loadProviders();
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
        if (lastUpdatedEl) {
            lastUpdatedEl.textContent = `Updated ${new Date().toLocaleTimeString('vi-VN')}`;
        }
        _resetAutoRefreshCountdown();
    } catch (error) {
        if (hasCached) {
            // Keep stale render, just show toast
            if (lastUpdatedEl) lastUpdatedEl.textContent = 'Refresh failed';
            showToast(`Refresh failed: ${error.message}`, 'error');
        } else {
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
            <div style="max-height:240px;overflow-y:auto;">
            <table class="table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Action</th>
                        <th>Target</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${actions.map(item => `
                        <tr>
                            <td>${formatTimestamp(item.timestamp)}</td>
                            <td>${item.action || '--'}</td>
                            <td>${formatShortLabel(item.target || '--', 28)}</td>
                            <td><span class="badge ${getStatusTone(item.status)}">${item.status || '--'}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            </div>
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
    const healthCheckedAt = data.health?.summary?.last_checked || data.health?.summary?.checked_at || null;
    const lastCheckLabel = healthCheckedAt
        ? `Checked ${formatTimestamp(healthCheckedAt)}`
        : `Checked ${new Date().toLocaleTimeString('vi-VN')}`;
    
    const windowEvents = data.usage?.window_event_count || 0;
    const billableCost = data.billing?.summary?.billable_estimated_cost || '--';
    const blockedEvents = data.quota?.blocked_event_count || 0;
    
    const topProvider = data.billing?.summary?.provider_breakdown ? 
        Object.keys(data.billing.summary.provider_breakdown)[0] || 'N/A' : 'N/A';
    
    const topQuotaReason = data.quota?.reason_breakdown ?
        Object.keys(data.quota.reason_breakdown)[0] || 'N/A' : 'N/A';
    
    const recentErrors = data.alerts?.recent_errors || [];
    const recentEvents = data.usage?.recent_events || [];
    const usageSummary = data.usage?.summary || {};
    const totalEvents = usageSummary.total_events || 0;
    const successEvents = usageSummary.success_events || 0;
    const successRate = totalEvents > 0 ? ((successEvents / totalEvents) * 100).toFixed(1) : null;
    const successRateClass = successRate !== null ? (parseFloat(successRate) >= 95 ? 'good' : parseFloat(successRate) >= 80 ? 'warning' : 'danger') : 'neutral';
    const avgLatency = usageSummary.avg_processing_time != null ? Number(usageSummary.avg_processing_time).toFixed(2) : null;
    const totalTokens = usageSummary.total_tokens_est || 0;
    const fallbackEvents = usageSummary.fallback_events || 0;
    const modelBreakdown = data.billing?.summary?.model_breakdown || {};
    const topModels = Object.entries(modelBreakdown).slice(0, 4);

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
                    <span>${lastCheckLabel}</span>
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
                <div class="kpi-value neutral">${formatCost(data.billing?.summary?.billable_estimated_cost)}</div>
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
            <div class="panel panel-compact">
                <div class="panel-header">
                    <div class="panel-title">Billing Summary</div>
                    <div class="panel-subtitle">Estimated costs</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row">
                        <span class="panel-label">Total Estimated Cost</span>
                        <span class="panel-value">${formatCost(data.billing?.summary?.total_estimated_cost)}</span>
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

            <div class="panel panel-compact">
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

            <div class="panel panel-compact panel-fixed-errors">
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

            <div class="panel panel-compact">
                <div class="panel-header">
                    <div class="panel-title">Recent Activity</div>
                    <div class="panel-subtitle">Last requests</div>
                </div>
                <div class="panel-content">
                    ${recentEvents.length > 0 ?
                        recentEvents.slice(0, 5).map(ev => {
                            const ts = ev.timestamp ? new Date(ev.timestamp) : null;
                            const timeStr = ts && !Number.isNaN(ts.getTime()) ? ts.toLocaleTimeString('vi-VN') : '--';
                            const model = ev.model ? ev.model.split('/').pop().substring(0, 22) : 'N/A';
                            const isOk = ev.status === 'success';
                            const dot = isOk
                                ? `<span style="color:var(--accent-green)">●</span>`
                                : `<span style="color:var(--accent-red)">●</span>`;
                            return `<div class="panel-row">
                                <span class="panel-label" style="font-size:11px;color:var(--text-muted)">${timeStr}</span>
                                <span class="panel-value" style="font-size:12px;gap:6px;display:flex;align-items:center">${dot} ${escapeHtml(model)}</span>
                            </div>`;
                        }).join('') :
                        `<div class="panel-row"><span class="panel-label">Status</span><span class="panel-value">No recent events</span></div>`
                    }
                </div>
            </div>

            <div class="panel panel-compact">
                <div class="panel-header">
                    <div class="panel-title">Top Models</div>
                    <div class="panel-subtitle">By estimated cost</div>
                </div>
                <div class="panel-content">
                    ${topModels.length > 0 ?
                        topModels.map(([model, cost]) => `
                        <div class="panel-row">
                            <span class="panel-label">${escapeHtml(model.split('/').pop().substring(0, 20))}</span>
                            <span class="panel-value">${formatCost(cost)}</span>
                        </div>`).join('') :
                        `<div class="panel-row"><span class="panel-label">Status</span><span class="panel-value">No data</span></div>`
                    }
                </div>
            </div>

            <div class="panel panel-compact">
                <div class="panel-header">
                    <div class="panel-title">Performance</div>
                    <div class="panel-subtitle">Request metrics</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row">
                        <span class="panel-label">Success Rate</span>
                        <span class="panel-value ${successRateClass}">${successRate !== null ? successRate + '%' : '--'}</span>
                    </div>
                    <div class="panel-row">
                        <span class="panel-label">Avg Latency</span>
                        <span class="panel-value">${avgLatency !== null ? avgLatency + 's' : '--'}</span>
                    </div>
                    <div class="panel-row">
                        <span class="panel-label">Total Tokens Est.</span>
                        <span class="panel-value">${totalTokens.toLocaleString()}</span>
                    </div>
                    <div class="panel-row">
                        <span class="panel-label">Fallback Events</span>
                        <span class="panel-value ${fallbackEvents > 0 ? 'warning' : 'neutral'}">${fallbackEvents}</span>
                    </div>
                </div>
            </div>

        </div>
    `;

    document.getElementById('overview-health-refresh-btn')?.addEventListener('click', async () => {
        const btn = document.getElementById('overview-health-refresh-btn');
        btn.disabled = true;
        try {
            await runControlAction('health_refresh');
            showToast('Health snapshot refreshed', 'success');
            await loadOverview();
        } catch (error) {
            showToast(`Health refresh failed: ${error.message}`, 'error');
        } finally {
            btn.disabled = false;
        }
    });

    document.getElementById('overview-warmup-all-btn')?.addEventListener('click', async () => {
        const btn = document.getElementById('overview-warmup-all-btn');
        btn.disabled = true;
        try {
            const result = await runControlAction('model_warmup_all', null, 20);
            showToast(result.message || 'Warm-up completed', 'success');
            await loadOverview();
        } catch (error) {
            showToast(`Warm-up failed: ${error.message}`, 'error');
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
    const modelBreakdown = data.model_breakdown || {};
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

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Model Breakdown</div>
                    <div class="panel-subtitle">Cost by model</div>
                </div>
                <div class="panel-content">
                    ${Object.entries(modelBreakdown).length > 0 ?
                        Object.entries(modelBreakdown).slice(0, 5).map(([model, cost]) => `
                            <div class="panel-row">
                                <span class="panel-label">${formatShortLabel(model, 22)}</span>
                                <span class="panel-value">${formatCost(cost)}</span>
                            </div>
                        `).join('') :
                        `<div class="panel-row">
                            <span class="panel-label">No model data</span>
                            <span class="panel-value">--</span>
                        </div>`
                    }
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Billing Mode Breakdown</div>
                    <div class="panel-subtitle">Events by billing tier</div>
                </div>
                <div class="panel-content">
                    ${Object.entries(billableModeBreakdown).length > 0 ?
                        Object.entries(billableModeBreakdown).slice(0, 6).map(([mode, count]) => {
                            const tone = mode === 'billable' ? 'badge-success' : mode === 'free' ? 'badge-info' : 'badge-default';
                            return `
                            <div class="panel-row">
                                <span class="panel-label"><span class="badge ${tone}">${mode}</span></span>
                                <span class="panel-value">${Number(count).toLocaleString('en-US')} events</span>
                            </div>`;
                        }).join('') :
                        `<div class="panel-row">
                            <span class="panel-label">No mode data</span>
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
        const [data, usage, proxyState, proxyBackends, proxyMetrics, trafficSplit, embeddingStatus, ragHealth] = await Promise.all([
            fetchAPI('/control-api/models'),
            fetchAPI('/control-api/usage?limit=40'),
            fetchAPI('/control-api/proxy/state').catch(() => null),
            fetchAPI('/control-api/proxy/backends').catch(() => null),
            fetchAPI('/control-api/proxy/metrics').catch(() => null),
            fetchAPI('/control-api/traffic-split').catch(() => null),
            fetchAPI('/control-api/embedding-status').catch(() => null),
            fetchAPI('/control-api/rag/health').catch(() => null)
        ]);
        proxyStateData = proxyState;
        proxyBackendsData = proxyBackends;
        proxyBenchmarkData = proxyMetrics;
        trafficSplitData = trafficSplit;
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
        modelsData = { ...data, recent_usage: usage, proxy_runtime: proxyRuntime, embedding_status: embeddingStatus, rag_health: ragHealth };
        renderModels();
    } catch (error) {
        throw error;
    }
}

function renderModels() {
    const pageEl = document.getElementById('page-models');
    const data = modelsData;
    if (!data) return;

    const trafficSplit = trafficSplitData || { core_a: 60, core_b: 30, core_c: 10 };
    const summary = data.summary || {};
    const embeddingStatus = data.embedding_status || null;
    const models = data.models || [];
    const providers = data.providers || [];
    const ollamaModels = data.ollama?.models || [];
    const remoteOllama = data.remote_ollama || { host: 'vannt-work-op', slots: [] };
    const remoteSlot11434 = remoteOllama.slots.find(slot => Number(slot.port) === 11434) || { model: 'gemma4:e4b', enabled: true, healthy: false, warm: false, available_models: ['tuetue4:e4b', 'gemma4:e4b', 'deepseek-r1:8b', 'qwen3-vl:8b', 'gemma3:12b'], backing_port: 11534 };
    const remoteSlot11435 = remoteOllama.slots.find(slot => Number(slot.port) === 11435) || { model: null, enabled: false, healthy: false, warm: false, available_models: ['off'], backing_port: 11534 };
    const remotePrimaryLabel = remoteSlot11434.backing_port ? `Cổng ${remoteSlot11434.backing_port}` : 'Cổng 11534';
    const uniqueModels = (models = []) => [...new Set((Array.isArray(models) ? models : []).filter(Boolean))].filter(model => model !== 'off');
    const remoteSlot11434Options = uniqueModels(remoteSlot11434.available_models);
    const remoteSlot11435Options = uniqueModels(remoteSlot11435.available_models);
    const showSecondaryRemoteSlot = remoteSlot11435.enabled || (!!remoteSlot11435.model && remoteSlot11435.model !== 'off') || remoteSlot11435Options.length > 0;
    const healthStatus = data.load_balancer_metrics?.health_status || {};
    const recentUsage = Array.isArray(data.recent_usage?.recent_events) ? data.recent_usage.recent_events : (Array.isArray(data.recent_usage?.events) ? data.recent_usage.events : []);
    const proxyRuntime = data.proxy_runtime || {};

    const localProviders = providers.filter(provider => String(provider.type).includes('ollama_local'));
    const remoteProviders = providers.filter(provider => String(provider.type).includes('ollama_remote'));

    const _ollamaWarmColor = s => s.warm_status === 'warm' ? '#22c55e' : s.warm_status === 'cold' ? '#f59e0b' : '#334155';
    const _ollamaWarmLabel = s => s.warm_status === 'warm' ? 'Warm' : s.warm_status === 'cold' ? 'Cold' : 'Unknown';
    const _ollamaTimeInfo = s => {
        const _ts = iso => { if (!iso) return null; const d = new Date(iso.endsWith('Z') ? iso : iso + 'Z'); return isNaN(d) ? null : d; };
        const _fmt = d => d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const _ago = d => { const m = Math.floor((Date.now() - d) / 60000); return m < 1 ? '<1m' : m < 60 ? m + 'm' : Math.floor(m / 60) + 'h' + (m % 60 ? (m % 60) + 'm' : ''); };
        const rows = [];
        const warmedAt = _ts(s.last_warmed_at);
        const checkedAt = _ts(s.last_checked_at);
        if (warmedAt) rows.push(`<span style="color:#22c55e">▲</span> warm ${_fmt(warmedAt)} <span style="color:#64748b">${_ago(warmedAt)} ago</span>${s.last_warm_latency_ms != null ? ' · ' + s.last_warm_latency_ms + 'ms' : ''}`);
        if (s.last_cold_latency_ms != null) rows.push(`<span style="color:#f59e0b">▼</span> cold probe · ${s.last_cold_latency_ms}ms`);
        if (checkedAt) rows.push(`<span style="color:#475569">✓</span> checked ${_fmt(checkedAt)}`);
        return rows.map(r => `<div style="line-height:1.6">${r}</div>`).join('');
    };
    const cloudProviders = providers.filter(provider => String(provider.type).includes('cli_proxy'));
    const gptDirectProviders = providers.filter(provider => String(provider.type).includes('gpt_direct'));

    // --- Light color helpers ---
    // 3-state health: green=ok, red=enabled-but-unhealthy, grey=disabled/unknown
    const _liveLight = (ok, anyEnabled) => ok ? '#22c55e' : anyEnabled ? '#ef4444' : '#334155';
    // 4-state with traffic: amber=healthy-but-0%-traffic (bypassed), red=unhealthy, grey=disabled
    const _trafficLight = (ok, anyEnabled, pct) => {
        if (!anyEnabled) return '#334155';
        if ((pct ?? -1) === 0) return '#f59e0b';
        return ok ? '#22c55e' : '#ef4444';
    };

    // Core A: Ollama group (local + remote)
    const coreAOk = summary.ollama_status === 'healthy'
        || localProviders.some(p => p.enabled && p.health === 'healthy')
        || remoteProviders.some(p => p.enabled && p.health === 'healthy');
    const coreAEnabled = localProviders.some(p => p.enabled) || remoteProviders.some(p => p.enabled);
    const coreALight = _trafficLight(coreAOk, coreAEnabled, trafficSplit.core_a);

    // Core B: CLI Proxy
    const coreBOk = cloudProviders.some(p => p.enabled && p.health === 'healthy');
    const coreBEnabled = cloudProviders.some(p => p.enabled);
    const coreBLight = _trafficLight(coreBOk, coreBEnabled, trafficSplit.core_b);
    const coreBCount = cloudProviders.filter(p => p.enabled).length;

    // Core C: GPT Direct
    const coreCOk = gptDirectProviders.some(p => p.enabled && p.health === 'healthy');
    const coreCEnabled = gptDirectProviders.some(p => p.enabled);
    const coreCLight = _trafficLight(coreCOk, coreCEnabled, trafficSplit.core_c);
    const coreCLabel = gptDirectProviders.length > 0
        ? gptDirectProviders.filter(p => p.enabled).map(p => (p.model || p.name || '').split(':')[0]).filter(Boolean).join(', ') || 'GPT Direct'
        : 'GPT Direct';

    // Local Ollama
    const localOllamaH = summary.ollama_status === 'healthy';
    const localOllamaHLight = localOllamaH ? '#22c55e' : summary.ollama_status === 'unhealthy' ? '#ef4444' : '#334155';
    const localOllamaWLight = localOllamaH && ollamaModels.length > 0 ? '#22c55e' : '#334155';
    const localOllamaWLabel = localOllamaH && ollamaModels.length > 0 ? 'Warm' : 'Cool';
    const localOllamaModelLabel = ollamaModels.length > 0 ? `${ollamaModels.length} models` : 'no models';

    // RAG-V2
    const ragHealthData = data.rag_health || null;
    const ragOk = ragHealthData?.healthy === true || ragHealthData?.status === 'healthy';
    const ragLight = ragHealthData ? (ragOk ? '#22c55e' : '#ef4444') : '#334155';
    const ragLabel = ragHealthData ? (ragOk ? 'Healthy' : 'Error') : 'No data';

    // Route map derived lights
    const _ctrlCoreLight = (proxyRuntime.status === 'healthy' || proxyRuntime.healthyCount > 0) ? '#22c55e' : proxyRuntime.status ? '#ef4444' : '#334155';

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
            <div class="kpi-card">
                <div class="kpi-eyebrow">Embedding</div>
                <div class="kpi-title">Embed Provider</div>
                <div class="kpi-value ${embeddingStatus?.healthy ? 'good' : (embeddingStatus ? 'warning' : 'neutral')}">${embeddingStatus?.healthy ? 'OK' : (embeddingStatus ? 'DOWN' : 'N/A')}</div>
                <div class="kpi-trend"><i class="fas fa-vector-square"></i><span>${embeddingStatus?.model || embeddingStatus?.provider || 'unavailable'}</span></div>
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
                        <span class="status-badge status-neutral">Live</span>
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
                                    <div style="font-size:15px; font-weight:700; line-height:1.1;">Proxy v2 (8325)</div>
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
                                <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span style="width:8px; height:8px; border-radius:999px; background:${ragLight}; display:inline-block;"></span>${ragLabel}</div>
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
                                        <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span style="width:8px; height:8px; border-radius:999px; background:${_ctrlCoreLight}; display:inline-block;"></span>Control Core</div>
                                        <div style="font-size:12px; font-weight:700; line-height:1.2;">Execution Lane Orchestration</div>
                                    </div>
                                    <div style="width:0; height:10px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                    <div style="display:flex; flex-direction:column; gap:5px; width:100%; padding:7px 9px; border:1px dashed rgba(148,163,184,.22); border-radius:12px; background:rgba(15,23,42,.12);">
                                        <div style="font-size:11px; color:#94a3b8; margin-bottom:2px;">Traffic Split</div>
                                        <div style="display:grid; grid-template-columns: auto 1fr auto; gap:6px 8px; align-items:center; font-size:10px; color:#cbd5e1;">
                                            <span>Core A</span><input id="traffic-split-core-a" type="number" min="0" max="100" value="${trafficSplit.core_a}" style="height:24px; width:56px; justify-self:end; text-align:right; border:1px solid rgba(148,163,184,.18); border-radius:8px; background:rgba(15,23,42,.18); color:#f8fafc; padding:0 6px;"><strong style="font-size:10px; color:#f8fafc; font-weight:600;">%</strong>
                                            <span>Core B</span><input id="traffic-split-core-b" type="number" min="0" max="100" value="${trafficSplit.core_b}" style="height:24px; width:56px; justify-self:end; text-align:right; border:1px solid rgba(148,163,184,.18); border-radius:8px; background:rgba(15,23,42,.18); color:#f8fafc; padding:0 6px;"><strong style="font-size:10px; color:#f8fafc; font-weight:600;">%</strong>
                                            <span>Core C</span><input id="traffic-split-core-c" type="number" min="0" max="100" value="${trafficSplit.core_c}" readonly style="height:24px; width:56px; justify-self:end; text-align:right; border:1px solid rgba(148,163,184,.18); border-radius:8px; background:rgba(15,23,42,.10); color:#94a3b8; padding:0 6px;"><strong style="font-size:10px; color:#f8fafc; font-weight:600;">%</strong>
                                        </div>
                                        <div style="display:flex; justify-content:flex-end; margin-top:8px;">
                                            <button class="btn-mini" id="traffic-split-save">Save</button>
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

                        <div style="display:flex; flex-direction:column; gap:8px; width:380px; margin-top:-10px; margin-left:386px;">
                            <div style="width:100%; height:0; border-top:1px dashed rgba(148,163,184,.28);"></div>
                            <div style="display:grid; grid-template-columns:0.96fr 0.96fr 1.2fr; align-items:flex-start; column-gap:16px; width:100%;">
                                <div style="display:flex; flex-direction:column; align-items:center; gap:3px; width:100%; min-width:0;">
                                    <div style="width:0; height:10px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                    <div style="display:flex; flex-direction:column; gap:5px; width:100%; min-width:0; padding:8px 10px; border:1px solid rgba(148,163,184,.18); border-radius:14px; background:rgba(15,23,42,.18); min-height:58px; justify-content:flex-start;">
                                        <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span id="core-a-status-light" style="width:8px; height:8px; border-radius:999px; background:${coreALight}; display:inline-block;"></span>Core A</div>
                                        <div style="font-size:11px; font-weight:700; line-height:1.2;">Ollama Group</div>
                                        <div style="font-size:9px; color:var(--text-muted)">${trafficSplit.core_a ?? '--'}% traffic</div>
                                    </div>
                                    <div style="width:0; height:18px; border-left:1px dashed rgba(148,163,184,.24);"></div>
                                    <div style="display:flex; flex-direction:column; gap:8px; width:286px; margin-left:14px; margin-top:4px; align-self:flex-start;">
                                        <div style="display:grid; grid-template-columns:0.9fr 1.1fr; gap:14px; width:100%; align-items:start;">
                                            <div style="display:flex; flex-direction:column; gap:8px; min-height:112px; padding:10px; border:1px dashed rgba(148,163,184,.22); border-radius:12px; background:rgba(15,23,42,.12); justify-content:flex-start;">
                                                <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                                                    <div style="font-size:11px; font-weight:700; color:#f8fafc; line-height:1.2;">Local Ollama</div>
                                                    <div style="font-size:10px; color:#94a3b8;">vannt-home-pc</div>
                                                </div>
                                                <select style="width:100%; height:30px; border-radius:8px; border:1px solid rgba(148,163,184,.18); background:rgba(2,6,23,.55); color:#e2e8f0; font-size:11px; padding:0 8px;">
                                                    <option value="off">off</option>
                                                    ${ollamaModels.map(m => `<option value="${escapeHtml(m.name || m)}">${escapeHtml(m.name || m)}</option>`).join('')}
                                                    ${ollamaModels.length === 0 ? '<option disabled>no models found</option>' : ''}
                                                </select>
                                                <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                                                    <span style="font-size:9px; color:var(--text-muted)">${localOllamaModelLabel}</span>
                                                    <div style="display:flex; align-items:center; gap:8px; font-size:10px; color:#94a3b8;">
                                                        <span style="display:flex; align-items:center; gap:4px;"><span style="width:8px; height:8px; border-radius:999px; background:${localOllamaWLight}; display:inline-block;"></span>${localOllamaWLabel}</span>
                                                        <span style="display:flex; align-items:center; gap:4px;"><span style="width:8px; height:8px; border-radius:999px; background:${localOllamaHLight}; display:inline-block;"></span>Healthy</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div style="display:flex; flex-direction:column; gap:8px; min-height:190px; padding:10px; border:1px dashed rgba(148,163,184,.22); border-radius:12px; background:rgba(15,23,42,.12); justify-content:flex-start;">
                                                <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; white-space:nowrap;">
                                                    <div style="font-size:11px; font-weight:700; color:#f8fafc; line-height:1.2;">Remote Ollama</div>
                                                    <div style="font-size:10px; color:#94a3b8;">${remoteOllama.host || 'vannt-work-op'}</div>
                                                </div>
                                                <div style="display:flex; flex-direction:column; gap:7px;">
                                                    <div style="display:flex; flex-direction:column; gap:5px;">
                                                        <div style="font-size:10px; color:#94a3b8;">${remotePrimaryLabel}</div>
                                                        <select id="remote-ollama-slot-11434" style="width:100%; height:30px; border-radius:8px; border:1px solid rgba(148,163,184,.18); background:rgba(2,6,23,.55); color:#e2e8f0; font-size:11px; padding:0 8px;">
                                                            <option value="off" ${!remoteSlot11434.enabled || !remoteSlot11434.model ? 'selected' : ''}>off</option>
                                                            ${remoteSlot11434Options.map(model => `<option value="${model}" ${remoteSlot11434.model === model && remoteSlot11434.enabled ? 'selected' : ''}>${model}</option>`).join('')}
                                                        </select>
                                                        <div style="display:flex; flex-direction:column; gap:4px;">
                                                            <div style="display:flex; align-items:center; gap:6px;">
                                                                <button class="btn-mini" data-action="remote-ollama-save" data-port="11434">Apply</button>
                                                                <button class="btn-mini" data-action="remote-ollama-probe" data-port="11434">Probe</button>
                                                                <button class="btn-mini" data-action="remote-ollama-warm" data-port="11434">Warm</button>
                                                            </div>
                                                            <div style="display:flex; align-items:center; gap:8px; font-size:10px; color:#94a3b8;">
                                                                <span style="display:flex; align-items:center; gap:4px;"><span id="remote-11434-warm-light" style="width:8px; height:8px; border-radius:999px; background:${_ollamaWarmColor(remoteSlot11434)}; display:inline-block;"></span><span id="remote-11434-warm-text">${_ollamaWarmLabel(remoteSlot11434)}</span></span>
                                                                <span style="display:flex; align-items:center; gap:4px;"><span id="remote-11434-healthy-light" style="width:8px; height:8px; border-radius:999px; background:${remoteSlot11434.healthy ? '#22c55e' : '#334155'}; display:inline-block;"></span>Healthy</span>
                                                            </div>
                                                            <div id="remote-11434-time-info" style="font-size:10px; color:var(--text-muted); margin-top:2px;">${_ollamaTimeInfo(remoteSlot11434)}</div>
                                                        </div>
                                                    </div>
                                                    ${showSecondaryRemoteSlot ? `
                                                    <div style="display:flex; flex-direction:column; gap:5px;">
                                                        <div style="font-size:10px; color:#94a3b8;">Cổng 11435</div>
                                                        <select id="remote-ollama-slot-11435" style="width:100%; height:30px; border-radius:8px; border:1px solid rgba(148,163,184,.18); background:rgba(2,6,23,.55); color:#e2e8f0; font-size:11px; padding:0 8px;">
                                                            <option value="off" ${!remoteSlot11435.enabled || !remoteSlot11435.model ? 'selected' : ''}>off</option>
                                                            ${remoteSlot11435Options.map(model => `<option value="${model}" ${remoteSlot11435.model === model && remoteSlot11435.enabled ? 'selected' : ''}>${model}</option>`).join('')}
                                                        </select>
                                                        <div style="display:flex; flex-direction:column; gap:4px;">
                                                            <div style="display:flex; align-items:center; gap:6px;">
                                                                <button class="btn-mini" data-action="remote-ollama-save" data-port="11435">Apply</button>
                                                                <button class="btn-mini" data-action="remote-ollama-probe" data-port="11435">Probe</button>
                                                                <button class="btn-mini" data-action="remote-ollama-warm" data-port="11435">Warm</button>
                                                            </div>
                                                            <div style="display:flex; align-items:center; gap:8px; font-size:10px; color:#94a3b8;">
                                                                <span style="display:flex; align-items:center; gap:4px;"><span id="remote-11435-warm-light" style="width:8px; height:8px; border-radius:999px; background:${_ollamaWarmColor(remoteSlot11435)}; display:inline-block;"></span><span id="remote-11435-warm-text">${_ollamaWarmLabel(remoteSlot11435)}</span></span>
                                                                <span style="display:flex; align-items:center; gap:4px;"><span id="remote-11435-healthy-light" style="width:8px; height:8px; border-radius:999px; background:${remoteSlot11435.healthy ? '#22c55e' : '#334155'}; display:inline-block;"></span>Healthy</span>
                                                            </div>
                                                            <div id="remote-11435-time-info" style="font-size:10px; color:var(--text-muted); margin-top:2px;">${_ollamaTimeInfo(remoteSlot11435)}</div>
                                                        </div>
                                                    </div>
                                                    ` : ''}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div style="display:flex; flex-direction:column; align-items:center; gap:3px; width:100%; min-width:0;">
                                    <div style="width:0; height:10px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                    <div style="display:flex; flex-direction:column; gap:5px; width:100%; min-width:0; padding:8px 10px; border:1px solid rgba(148,163,184,.18); border-radius:14px; background:rgba(15,23,42,.18); min-height:58px; justify-content:flex-start;">
                                        <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span id="core-b-status-light" style="width:8px; height:8px; border-radius:999px; background:${coreBLight}; display:inline-block;"></span>Core B</div>
                                        <div style="font-size:11px; font-weight:700; line-height:1.2;">CLI Proxy API</div>
                                        <div style="font-size:9px; color:var(--text-muted)">${trafficSplit.core_b ?? '--'}% · ${coreBCount} provider${coreBCount !== 1 ? 's' : ''}</div>
                                    </div>
                                </div>
                                <div style="display:flex; flex-direction:column; align-items:center; gap:3px; width:100%; min-width:0;">
                                    <div style="width:0; height:10px; border-left:1px dashed rgba(148,163,184,.28);"></div>
                                    <div style="display:flex; flex-direction:column; gap:5px; width:100%; min-width:0; padding:8px 10px; border:1px solid rgba(148,163,184,.18); border-radius:14px; background:rgba(15,23,42,.18); min-height:58px; justify-content:flex-start;">
                                        <div style="display:flex; align-items:center; gap:6px; color:#94a3b8; font-size:11px;"><span id="core-c-status-light" style="width:8px; height:8px; border-radius:999px; background:${coreCLight}; display:inline-block;"></span>Core C</div>
                                        <div style="font-size:11px; font-weight:700; line-height:1.2;">GPT Direct</div>
                                        <div style="font-size:9px; color:var(--text-muted)">${trafficSplit.core_c ?? '--'}% · ${coreCLabel}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
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
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${providers.map(provider => `
                            <tr>
                                <td>${escapeHtml(provider.name)}</td>
                                <td>${escapeHtml(provider.type)}</td>
                                <td>${escapeHtml(provider.model)}</td>
                                <td>${provider.weight}</td>
                                <td>${renderStatusWithDot(provider.health || 'unknown', provider.health === 'healthy' ? 'healthy' : 'unhealthy')}</td>
                                <td><span class="badge ${provider.enabled ? 'badge-success' : 'badge-default'}">${provider.enabled ? 'ON' : 'OFF'}</span></td>
                                <td><button class="btn-mini ${provider.enabled ? 'btn-mini-danger' : ''}" data-action="toggle-provider" data-target="${escapeHtml(provider.name)}" data-enabled="${provider.enabled ? '1' : '0'}">${provider.enabled ? 'Disable' : 'Enable'}</button></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="table-container" style="margin-top: 32px;">
            <div class="table-header">Recent Control Actions</div>
            <div id="models-actions-history" class="table-loading">Loading...</div>
        </div>
    `;

    pageEl.querySelectorAll('[data-action="warm-model"]').forEach(btn => {
        btn.addEventListener('click', async () => {
            btn.disabled = true;
            try {
                const result = await runControlAction('model_warmup', btn.dataset.target, 20);
                showToast(result.message || 'Model warmed up', 'success');
                await loadModels();
            } catch (error) {
                showToast(`Model warm-up failed: ${error.message}`, 'error');
            } finally {
                btn.disabled = false;
            }
        });
    });

    const coreAInput = document.getElementById('traffic-split-core-a');
    const coreBInput = document.getElementById('traffic-split-core-b');
    const coreCInput = document.getElementById('traffic-split-core-c');
    const saveBtn = document.getElementById('traffic-split-save');

    function recalcTrafficSplit() {
        if (!coreAInput || !coreBInput || !coreCInput) return { a: 0, b: 0, c: 100 };
        const a = Math.max(0, Math.min(100, Number(coreAInput.value || 0)));
        const b = Math.max(0, Math.min(100, Number(coreBInput.value || 0)));
        const c = 100 - a - b;
        coreCInput.value = c >= 0 ? c : 0;
        coreCInput.style.color = c >= 0 ? '#94a3b8' : '#ef4444';
        return { a, b, c };
    }

    coreAInput?.addEventListener('input', recalcTrafficSplit);
    coreBInput?.addEventListener('input', recalcTrafficSplit);
    recalcTrafficSplit();

    saveBtn?.addEventListener('click', async () => {
        const { a, b, c } = recalcTrafficSplit();
        if (c < 0) {
            showToast('Core A + Core B must be ≤ 100', 'warning');
            return;
        }
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';
        try {
            const result = await fetchAPI('/control-api/traffic-split', {
                method: 'PUT',
                body: JSON.stringify({ core_a: a, core_b: b })
            });
            trafficSplitData = result;
            coreAInput.value = result.core_a;
            coreBInput.value = result.core_b;
            coreCInput.value = result.core_c;
            saveBtn.textContent = 'Saved';
            setTimeout(() => {
                saveBtn.textContent = 'Save';
                saveBtn.disabled = false;
            }, 900);
        } catch (error) {
            showToast(`Failed to update traffic split: ${error.message}`, 'error');
            saveBtn.textContent = 'Save';
            saveBtn.disabled = false;
        }
    });

    // Update core status lights based on provider health
    function updateCoreStatusLights() {
        const healthStatus = modelsData?.load_balancer_metrics?.health_status || {};
        
        function setCoreLight(elementId, providerNames) {
            const light = document.getElementById(elementId);
            if (!light) return;
            if (!providerNames || providerNames.length === 0) {
                light.style.background = '#94a3b8';
                return;
            }
            const knownProviders = providerNames.filter(name => healthStatus[name] !== undefined);
            if (knownProviders.length === 0) {
                light.style.background = '#94a3b8';
                return;
            }
            const healthyCount = knownProviders.filter(name => healthStatus[name] === true).length;
            if (healthyCount > 0) {
                light.style.background = '#22c55e';
            } else if (knownProviders.length > 0) {
                light.style.background = '#f59e0b';
            } else {
                light.style.background = '#ef4444';
            }
        }

        // Core A: Ollama groups (local + remote)
        setCoreLight('core-a-status-light', [
            'gemma3:4b-local', 'qwen3:4b-local', 'deepseek-r1:8b-local',
            'gemma4:e4b-remote', 'gemma3:4b-remote', 'deepseek-r1:8b-remote'
        ]);

        // Core B: CLI Proxy providers
        setCoreLight('core-b-status-light', ['cliproxy-deepseek', 'cliproxy-gpt', 'cliproxy-gemini']);

        // Core C: GPT Direct
        setCoreLight('core-c-status-light', ['gpt-5.2-direct']);
    }

    // Call after DOM is ready
    setTimeout(updateCoreStatusLights, 100);

    pageEl.querySelectorAll('[data-action="remote-ollama-save"]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const port = btn.dataset.port;
            const select = document.getElementById(`remote-ollama-slot-${port}`);
            if (!select) return;
            const model = select.value;
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.textContent = 'Saving...';
            try {
                await fetchAPI(`/control-api/remote-ollama/slots/${port}`, {
                    method: 'PUT',
                    body: JSON.stringify({
                        model: model === 'off' ? null : model,
                        enabled: model !== 'off'
                    })
                });
                btn.textContent = 'Saved';
                await loadModels();
            } catch (error) {
                showToast(`Failed to update remote slot ${port}: ${error.message}`, 'error');
                btn.textContent = originalText;
            } finally {
                setTimeout(() => {
                    btn.disabled = false;
                    btn.textContent = originalText;
                }, 700);
            }
        });
    });
    function _applyOllamaSlotUI(port, result) {
        const ws = result.warm_status || (result.warm ? 'warm' : 'unknown');
        const warmColor = ws === 'warm' ? '#22c55e' : ws === 'cold' ? '#f59e0b' : '#334155';
        const warmLabel = ws === 'warm' ? 'Warm' : ws === 'cold' ? 'Cold' : 'Unknown';
        const warmLight = document.getElementById(`remote-${port}-warm-light`);
        const warmText = document.getElementById(`remote-${port}-warm-text`);
        const healthyLight = document.getElementById(`remote-${port}-healthy-light`);
        const timeInfo = document.getElementById(`remote-${port}-time-info`);
        if (warmLight) warmLight.style.background = warmColor;
        if (warmText) warmText.textContent = warmLabel;
        if (result.healthy !== undefined && healthyLight)
            healthyLight.style.background = result.healthy ? '#22c55e' : '#334155';
        if (timeInfo) timeInfo.innerHTML = _ollamaTimeInfo(result);
    }

    pageEl.querySelectorAll('[data-action="remote-ollama-probe"]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const port = btn.dataset.port;
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.textContent = 'Probing...';
            try {
                const result = await fetchAPI(`/control-api/remote-ollama/slots/${port}/probe`, { method: 'POST' });
                _applyOllamaSlotUI(port, result);
                btn.textContent = 'Done';
                if (result.message) console.log('Probe result:', result.message);
            } catch (error) {
                console.warn(`Probe failed for slot ${port}:`, error);
                btn.textContent = 'Probe';
            } finally {
                setTimeout(() => { btn.disabled = false; btn.textContent = originalText; }, 1500);
            }
        });
    });

    pageEl.querySelectorAll('[data-action="remote-ollama-warm"]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const port = btn.dataset.port;
            btn.disabled = true;
            btn.textContent = 'Warming...';
            try {
                const result = await fetchAPI(`/control-api/remote-ollama/slots/${port}/warm`, { method: 'POST' });
                _applyOllamaSlotUI(port, result);
                const label = result.warm_status === 'warm' ? 'Done ✓' : 'Done';
                showToast(result.message || `Slot ${port} warm-up done`, result.warm_status === 'warm' ? 'success' : 'info');
                btn.textContent = label;
            } catch (error) {
                showToast(`Warm failed: ${error.message}`, 'error');
                btn.textContent = 'Warm';
            } finally {
                setTimeout(() => { btn.disabled = false; btn.textContent = 'Warm'; }, 2000);
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
                showToast(result.message || (isEnabled ? 'Provider disabled' : 'Provider enabled'), 'success');
            } catch (error) {
                showToast(`Provider toggle failed: ${error.message}`, 'error');
            } finally {
                btn.disabled = false;
            }
        });
    });

    loadControlActionHistory();
}

// System page
let _surfacePings = {};

async function probeSurface(url) {
    const controller = new AbortController();
    const tid = setTimeout(() => controller.abort(), 4000);
    try {
        await fetch(url, { mode: 'no-cors', signal: controller.signal });
        return 'healthy';
    } catch {
        return 'unreachable';
    } finally {
        clearTimeout(tid);
    }
}

async function loadSystem() {
    systemData = await fetchAPI('/control-api/system');
    renderSystem();

    // Background: surface probes + memory + RAG health
    Promise.allSettled([
        probeSurface('https://console.tuetue.vn'),
        probeSurface('https://chat.tuetue.vn'),
        fetchAPI('/control-api/system/memory').catch(() => null),
        fetchAPI('/control-api/rag/health').catch(() => null)
    ]).then(([consolePing, chatPing, memResult, ragResult]) => {
        _surfacePings = {
            console: consolePing.status === 'fulfilled' ? consolePing.value : 'unknown',
            chat: chatPing.status === 'fulfilled' ? chatPing.value : 'unknown'
        };

        // Patch surface health cells
        const pageEl = document.getElementById('page-system');
        if (pageEl.classList.contains('active')) {
            const surfaces = { 'console.tuetue.vn': _surfacePings.console, 'chat.tuetue.vn': _surfacePings.chat };
            pageEl.querySelectorAll('.panel-row').forEach(row => {
                const label = row.querySelector('.panel-label')?.textContent?.trim();
                if (label && surfaces[label] !== undefined) {
                    const tone = getStatusTone(surfaces[label]);
                    const valueEl = row.querySelector('.panel-value');
                    if (valueEl) {
                        const roleSpan = valueEl.querySelector('.badge');
                        const roleText = roleSpan ? valueEl.textContent.replace(roleSpan.textContent, '').replace(/^\s*·\s*/, '').trim() : '';
                        valueEl.innerHTML = `<span class="badge ${tone}">${surfaces[label]}</span>${roleText ? ' · ' + roleText : ''}`;
                    }
                }
            });
        }

        // Patch memory panel
        const mem = memResult.status === 'fulfilled' ? memResult.value : null;
        if (mem) {
            const fmt = v => v != null ? `${Number(v).toFixed(1)} MB` : '—';
            const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
            setEl('mem-openclaw', fmt(mem.openclaw_mb));
            setEl('mem-rag', fmt(mem.rag_mb));
            setEl('mem-total', fmt(mem.total_mb));
            setEl('mem-ts', mem.timestamp ? new Date(mem.timestamp).toLocaleTimeString('vi-VN') : '—');
        } else {
            const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
            setEl('mem-openclaw', 'unavailable'); setEl('mem-rag', 'unavailable');
            setEl('mem-total', 'unavailable'); setEl('mem-ts', '—');
        }

        // Patch RAG health panel
        const rag = ragResult.status === 'fulfilled' ? ragResult.value : null;
        if (rag) {
            const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
            const tone = rag.status === 'ok' ? 'badge-success' : 'badge-danger';
            const svcTone = rag.service_status === 'operational' ? 'badge-success' : (rag.service_status === 'degraded' ? 'badge-warning' : 'badge-danger');
            const statusEl = document.getElementById('rag-status');
            if (statusEl) statusEl.innerHTML = `<span class="badge ${tone}">${rag.status || '—'}</span>`;
            const svcEl = document.getElementById('rag-service-status');
            if (svcEl) svcEl.innerHTML = `<span class="badge ${svcTone}">${rag.service_status || '—'}</span>`;
            const detEl = document.getElementById('rag-details');
            if (detEl) detEl.textContent = rag.details ? JSON.stringify(rag.details).slice(0, 80) : '—';
        } else {
            const statusEl = document.getElementById('rag-status');
            if (statusEl) statusEl.innerHTML = `<span class="badge badge-default">unavailable</span>`;
        }
    });
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
        { name: 'console.tuetue.vn', role: 'developer portal', status: _surfacePings.console || 'probing' },
        { name: 'chat.tuetue.vn', role: 'product chat', status: _surfacePings.chat || 'probing' }
    ];

    pageEl.innerHTML = `
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
                    <div class="panel-title">Memory Usage</div>
                    <div class="panel-subtitle">Service memory snapshot</div>
                </div>
                <div class="panel-content" id="system-memory-panel">
                    <div class="panel-row"><span class="panel-label">OpenClaw</span><span class="panel-value" id="mem-openclaw">—</span></div>
                    <div class="panel-row"><span class="panel-label">RAG Service</span><span class="panel-value" id="mem-rag">—</span></div>
                    <div class="panel-row"><span class="panel-label">Total</span><span class="panel-value" id="mem-total">—</span></div>
                    <div class="panel-row"><span class="panel-label">Sampled</span><span class="panel-value" id="mem-ts" style="font-size:11px; color:var(--text-muted);">loading…</span></div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">RAG Health</div>
                    <div class="panel-subtitle">Knowledge base service status</div>
                </div>
                <div class="panel-content" id="system-rag-panel">
                    <div class="panel-row"><span class="panel-label">Status</span><span class="panel-value" id="rag-status">loading…</span></div>
                    <div class="panel-row"><span class="panel-label">Service</span><span class="panel-value" id="rag-service-status">—</span></div>
                    <div class="panel-row"><span class="panel-label">Details</span><span class="panel-value" id="rag-details" style="font-size:11px;">—</span></div>
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
let _usageLimit = 20;

async function loadUsage(limit = null) {
    if (limit !== null) _usageLimit = limit;
    const data = await fetchAPI(`/control-api/usage?limit=${_usageLimit}`);
    usageData = data;
    renderUsage();
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
            <div class="table-header" style="display:flex; align-items:center; justify-content:space-between;">
                <span>Recent Usage Events</span>
                <span style="font-size:13px; font-weight:400; color:var(--text-muted);">Showing ${_usageLimit} events</span>
            </div>
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
            <div style="padding: 14px 20px; border-top: 1px solid var(--border); display:flex; gap:10px; align-items:center;">
                <button class="btn-mini" id="usage-load-more-50">Load 50</button>
                <button class="btn-mini" id="usage-load-more-100">Load 100</button>
                <button class="btn-mini" id="usage-load-more-reset" style="color:var(--text-muted); border-color:rgba(148,163,184,0.2);">Reset</button>
            </div>
        </div>
    `;

    document.getElementById('usage-load-more-50')?.addEventListener('click', async () => {
        await loadUsage(50);
    });
    document.getElementById('usage-load-more-100')?.addEventListener('click', async () => {
        await loadUsage(100);
    });
    document.getElementById('usage-load-more-reset')?.addEventListener('click', async () => {
        await loadUsage(20);
    });
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
    const avgLatency = proxyMetrics?.avg_latency != null ? `${Number(proxyMetrics.avg_latency).toFixed(2)} ms` : '--';
    const uptime = proxyMetrics?.uptime_human || proxySummary.uptime_human || '--';
    const liveHealthy = proxyMetrics?.backends && Object.values(proxyMetrics.backends).some(item => item && item.healthy);
    const serviceStatus = proxySummary.service_status || proxySummary.status || (liveHealthy ? 'healthy' : null) || proxyRuntime.service_status || proxyRuntime.status || 'unknown';
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
                <div class="kpi-trend"><i class="fas fa-route"></i><span>Port 8325 front door</span></div>
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
        const proxyUrl = `${window.location.protocol}//${window.location.hostname}:8325/`;
        window.open(proxyUrl, '_blank');
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
            showToast(`Proxy mode set to ${e.target.value}`, 'success');
            await loadProxy();
        } catch (error) {
            showToast(`Proxy mode update failed: ${error.message}`, 'error');
        }
    });

    document.getElementById('proxy-hedge-toggle')?.addEventListener('change', async () => {
        const enabled = document.getElementById('proxy-hedge-toggle')?.checked || false;
        const delay = parseFloat(document.getElementById('proxy-hedge-delay')?.value || '0.35');
        try {
            await updateProxyHedge(enabled, delay);
            showToast(`Hedging ${enabled ? 'enabled' : 'disabled'}`, 'success');
            await loadProxy();
        } catch (error) {
            showToast(`Proxy hedge update failed: ${error.message}`, 'error');
        }
    });

    document.getElementById('proxy-hedge-delay')?.addEventListener('change', async () => {
        const enabled = document.getElementById('proxy-hedge-toggle')?.checked || false;
        const delay = parseFloat(document.getElementById('proxy-hedge-delay')?.value || '0.35');
        try {
            await updateProxyHedge(enabled, delay);
            showToast(`Hedge delay set to ${delay}s`, 'success');
            await loadProxy();
        } catch (error) {
            showToast(`Hedge delay update failed: ${error.message}`, 'error');
        }
    });

    document.querySelectorAll('.proxy-backend-toggle').forEach(toggle => {
        toggle.addEventListener('change', async (e) => {
            const backendId = e.target.getAttribute('data-backend-id');
            try {
                await toggleProxyBackend(backendId, e.target.checked);
                showToast(`Backend ${backendId} ${e.target.checked ? 'enabled' : 'disabled'}`, 'success');
                await loadProxy();
            } catch (error) {
                showToast(`Backend toggle failed: ${error.message}`, 'error');
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
                showToast(`Weight for ${backendId} set to ${weight}%`, 'success');
                await loadProxy();
            } catch (error) {
                showToast(`Backend weight update failed: ${error.message}`, 'error');
            }
        });
    });
}

// Providers page
let providersData = null;
let _providersHours = 24;

async function loadProviders() {
    const [metrics, recent, stats] = await Promise.allSettled([
        fetchAPI('/control-api/providers/metrics'),
        fetchAPI(`/control-api/chat/providers/recent?limit=20`),
        fetchAPI(`/control-api/chat/providers/stats?hours=${_providersHours}`)
    ]);
    providersData = {
        metrics: metrics.status === 'fulfilled' ? metrics.value : null,
        recent: recent.status === 'fulfilled' ? recent.value : null,
        stats: stats.status === 'fulfilled' ? stats.value : null
    };
    renderProviders();
}

function renderProviders() {
    const pageEl = document.getElementById('page-providers');
    if (!providersData) return;

    const { metrics, recent, stats } = providersData;
    const summary = metrics?.summary || {};
    const recentEvents = recent?.events || [];
    const providerStats = stats?.stats || {};

    const totalReq = summary.total_requests ?? 0;
    const successRate = summary.success_rate != null ? `${(Number(summary.success_rate) * 100).toFixed(1)}%` : '--';
    const avgLatency = summary.avg_latency != null ? `${Number(summary.avg_latency).toFixed(0)} ms` : '--';
    const provDist = summary.provider_distribution || {};
    const topProvider = Object.keys(provDist)[0] || '--';

    const perfRows = Object.entries(provDist).map(([name, count]) => {
        const pStats = providerStats[name] || {};
        const sr = pStats.success_rate != null ? `${(Number(pStats.success_rate) * 100).toFixed(1)}%` : '--';
        const lat = pStats.avg_latency != null ? `${Number(pStats.avg_latency).toFixed(0)} ms` : '--';
        const pct = totalReq > 0 ? `${((count / totalReq) * 100).toFixed(1)}%` : '--';
        return { name, count, sr, lat, pct };
    });

    pageEl.innerHTML = `
        <div style="display:flex; gap:10px; align-items:center; margin-bottom:16px; flex-wrap:wrap;">
            <span style="font-size:12px; color:var(--text-muted);">Time window:</span>
            ${[24, 48, 168].map(h => `
                <button class="btn-action ${_providersHours === h ? '' : ''}" data-hours="${h}"
                    style="padding:4px 14px; font-size:12px; ${_providersHours === h ? 'background:var(--accent-purple); color:#fff;' : ''}">
                    ${h === 168 ? '7d' : h + 'h'}
                </button>`).join('')}
        </div>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-eyebrow">Requests</div>
                <div class="kpi-title">Total Requests</div>
                <div class="kpi-value neutral">${totalReq.toLocaleString('en-US')}</div>
                <div class="kpi-trend"><i class="fas fa-exchange-alt"></i><span>Provider selections</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Reliability</div>
                <div class="kpi-title">Success Rate</div>
                <div class="kpi-value ${summary.success_rate >= 0.95 ? 'good' : (summary.success_rate >= 0.8 ? 'warning' : 'danger')}">${successRate}</div>
                <div class="kpi-trend"><i class="fas fa-check-circle"></i><span>Across all providers</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Latency</div>
                <div class="kpi-title">Avg Response</div>
                <div class="kpi-value neutral">${avgLatency}</div>
                <div class="kpi-trend"><i class="fas fa-tachometer-alt"></i><span>Mean selection latency</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Top</div>
                <div class="kpi-title">Leading Provider</div>
                <div class="kpi-value neutral" style="font-size:18px;">${escapeHtml(formatShortLabel(topProvider, 16))}</div>
                <div class="kpi-trend"><i class="fas fa-trophy"></i><span>Most selected</span></div>
            </div>
        </div>

        <div class="panel-grid" style="margin-bottom:28px;">
            <div class="panel" style="grid-column: 1 / -1;">
                <div class="panel-header">
                    <div class="panel-title">Provider Performance</div>
                    <div class="panel-subtitle">Success rate and latency per provider (${_providersHours === 168 ? '7-day' : _providersHours + 'h'} window)</div>
                </div>
                <div class="panel-content">
                    ${perfRows.length > 0 ? `
                    <table class="table" style="margin-top:0;">
                        <thead><tr><th>Provider</th><th>Requests</th><th>Share</th><th>Success Rate</th><th>Avg Latency</th></tr></thead>
                        <tbody>
                            ${perfRows.map(r => `
                                <tr>
                                    <td><strong>${escapeHtml(r.name)}</strong></td>
                                    <td>${r.count.toLocaleString('en-US')}</td>
                                    <td>${r.pct}</td>
                                    <td><span class="badge ${r.sr !== '--' && parseFloat(r.sr) >= 95 ? 'badge-success' : (r.sr !== '--' && parseFloat(r.sr) >= 80 ? 'badge-warning' : 'badge-danger')}">${r.sr}</span></td>
                                    <td>${r.lat}</td>
                                </tr>`).join('')}
                        </tbody>
                    </table>` : '<div class="panel-row"><span class="panel-label">No provider metrics available</span><span class="panel-value">--</span></div>'}
                </div>
            </div>
        </div>

        <div class="table-container">
            <div class="table-header">Recent Provider Selections <span style="font-size:11px; color:var(--text-muted); font-weight:400;">(last 20 events)</span></div>
            ${recentEvents.length > 0 ? `
            <table class="table">
                <thead><tr><th>Time</th><th>Provider</th><th>Model</th><th>Latency</th><th>Status</th><th>Fallback</th></tr></thead>
                <tbody>
                    ${recentEvents.slice(0, 20).map(ev => `
                        <tr>
                            <td>${formatTimestamp(ev.timestamp || ev.created_at)}</td>
                            <td>${escapeHtml(ev.provider || ev.provider_type || '--')}</td>
                            <td>${escapeHtml(formatShortLabel(ev.model || '--', 24))}</td>
                            <td>${ev.latency_ms != null ? Number(ev.latency_ms).toFixed(0) + ' ms' : (ev.latency != null ? Number(ev.latency * 1000).toFixed(0) + ' ms' : '--')}</td>
                            <td><span class="badge ${getStatusTone(ev.status || ev.status_normalized)}">${escapeHtml(ev.status || ev.status_normalized || '--')}</span></td>
                            <td>${ev.fallback_used ? '<span class="badge badge-warning">fallback</span>' : '<span style="color:var(--text-muted);">—</span>'}</td>
                        </tr>`).join('')}
                </tbody>
            </table>` : '<div class="empty-state" style="padding:32px 0;"><i class="fas fa-plug"></i><h3>No recent provider events</h3></div>'}
        </div>
    `;

    pageEl.querySelectorAll('[data-hours]').forEach(btn => {
        btn.addEventListener('click', () => {
            _providersHours = parseInt(btn.dataset.hours, 10);
            loadProviders();
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
                <div class="kpi-value neutral">v0.2</div>
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
                    <div class="panel-title">Tab Reference</div>
                    <div class="panel-subtitle">What each tab does</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row"><span class="panel-label">Overview</span><span class="panel-value">Health, cost, quota, recent errors at a glance</span></div>
                    <div class="panel-row"><span class="panel-label">Quota</span><span class="panel-value">Blocked events by tenant, key, reason</span></div>
                    <div class="panel-row"><span class="panel-label">Billing</span><span class="panel-value">Estimated cost by tenant, provider, model</span></div>
                    <div class="panel-row"><span class="panel-label">Errors</span><span class="panel-value">Error signatures, status/HTTP breakdown, recent events</span></div>
                    <div class="panel-row"><span class="panel-label">Models</span><span class="panel-value">Serving route map, provider inventory, warm-up</span></div>
                    <div class="panel-row"><span class="panel-label">System</span><span class="panel-value">Memory, RAG health, surface health, workloads</span></div>
                    <div class="panel-row"><span class="panel-label">Providers</span><span class="panel-value">Per-provider success rate, latency, recent selections</span></div>
                    <div class="panel-row"><span class="panel-label">Usage</span><span class="panel-value">Event ledger with status breakdown and user/provider stats</span></div>
                    <div class="panel-row"><span class="panel-label">Users</span><span class="panel-value">Registered accounts with tier, provider, status filter</span></div>
                    <div class="panel-row"><span class="panel-label">Proxy</span><span class="panel-value">Proxy v2 runtime controls, backend pool, benchmark</span></div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Operator Notes</div>
                    <div class="panel-subtitle">Key behaviors to know</div>
                </div>
                <div class="panel-content">
                    <div class="panel-row"><span class="panel-label">Healthy ≠ Enabled</span><span class="panel-value">Health and routing are independent states</span></div>
                    <div class="panel-row"><span class="panel-label">Confirmations</span><span class="panel-value">Destructive actions require explicit confirm</span></div>
                    <div class="panel-row"><span class="panel-label">Keyboard R</span><span class="panel-value">Refresh current tab (skip if input focused)</span></div>
                    <div class="panel-row"><span class="panel-label">Stale cache</span><span class="panel-value">Cached data shown instantly, refreshed silently</span></div>
                    <div class="panel-row"><span class="panel-label">Surface probes</span><span class="panel-value">Console / Chat health probed async after page load</span></div>
                </div>
            </div>
        </div>
    `;
}

// Users page
let usersData = null;

async function loadUsers() {
    const data = await fetchAPI('/api/users');
    usersData = data;
    renderUsers();
}

function renderUsers() {
    const pageEl = document.getElementById('page-users');
    const data = usersData;
    if (!data) return;

    const users = data.users || (Array.isArray(data) ? data : []);
    const total = data.total ?? users.length;
    const activeCount = users.filter(u => u.is_active !== false).length;

    pageEl.innerHTML = `
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-eyebrow">Users</div>
                <div class="kpi-title">Total Users</div>
                <div class="kpi-value neutral">${total}</div>
                <div class="kpi-trend"><i class="fas fa-users"></i><span>Registered accounts</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Active</div>
                <div class="kpi-title">Active Users</div>
                <div class="kpi-value good">${activeCount}</div>
                <div class="kpi-trend"><i class="fas fa-user-check"></i><span>Not suspended</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-eyebrow">Suspended</div>
                <div class="kpi-title">Suspended</div>
                <div class="kpi-value ${total - activeCount > 0 ? 'warning' : 'neutral'}">${total - activeCount}</div>
                <div class="kpi-trend"><i class="fas fa-user-slash"></i><span>is_active = false</span></div>
            </div>
        </div>

        <div style="display:flex; gap:10px; margin-top:20px; margin-bottom:12px; flex-wrap:wrap;">
            <input id="users-filter-email" type="text" placeholder="Filter by email..." class="input-inline" style="flex:1; min-width:200px; height:34px;">
            <select id="users-filter-tier" class="auto-refresh-select" style="height:34px;">
                <option value="">All tiers</option>
                <option value="free">Free</option>
                <option value="trial">Trial</option>
                <option value="pro">Pro</option>
            </select>
            <select id="users-filter-status" class="auto-refresh-select" style="height:34px;">
                <option value="">All statuses</option>
                <option value="active">Active</option>
                <option value="suspended">Suspended</option>
            </select>
            <span id="users-filter-count" style="font-size:13px; color:var(--text-muted); align-self:center;"></span>
        </div>

        <div class="table-container table-container-scroll">
            <div class="table-scroll-y">
                <table class="table" id="users-table">
                    <thead>
                        <tr>
                            <th>User ID</th>
                            <th>Email</th>
                            <th>Tier</th>
                            <th>Provider</th>
                            <th>Status</th>
                            <th>Created</th>
                        </tr>
                    </thead>
                    <tbody id="users-tbody">
                        ${_renderUserRows(users)}
                    </tbody>
                </table>
            </div>
        </div>
    `;

    function applyUsersFilter() {
        const emailQ = (document.getElementById('users-filter-email')?.value || '').toLowerCase();
        const tierQ = document.getElementById('users-filter-tier')?.value || '';
        const statusQ = document.getElementById('users-filter-status')?.value || '';
        const filtered = users.filter(u => {
            const email = (u.email || '').toLowerCase();
            const tier = u.tier || 'free';
            const isActive = u.is_active !== false;
            const status = isActive ? 'active' : 'suspended';
            if (emailQ && !email.includes(emailQ)) return false;
            if (tierQ && tier !== tierQ) return false;
            if (statusQ && status !== statusQ) return false;
            return true;
        });
        const tbody = document.getElementById('users-tbody');
        const countEl = document.getElementById('users-filter-count');
        if (tbody) tbody.innerHTML = _renderUserRows(filtered);
        if (countEl) countEl.textContent = filtered.length < users.length ? `${filtered.length} of ${users.length}` : '';
    }

    document.getElementById('users-filter-email')?.addEventListener('input', applyUsersFilter);
    document.getElementById('users-filter-tier')?.addEventListener('change', applyUsersFilter);
    document.getElementById('users-filter-status')?.addEventListener('change', applyUsersFilter);
}

function _renderUserRows(users) {
    if (!users.length) return '<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:40px;">No users found</td></tr>';
    return users.map(u => `
        <tr>
            <td><code style="font-size:12px;">${escapeHtml(formatShortLabel(u.user_id || u.id || '--', 20))}</code></td>
            <td>${escapeHtml(u.email || '--')}</td>
            <td><span class="badge ${u.tier === 'pro' ? 'badge-success' : u.tier === 'trial' ? 'badge-warning' : 'badge-default'}">${escapeHtml(u.tier || 'free')}</span></td>
            <td>${escapeHtml(u.auth_provider || u.provider || '--')}</td>
            <td><span class="badge ${u.is_active === false ? 'badge-danger' : 'badge-success'}">${u.is_active === false ? 'suspended' : 'active'}</span></td>
            <td>${formatTimestamp(u.created_at)}</td>
        </tr>
    `).join('');
}

// Errors page
let errorEventsData = null;

async function loadErrors() {
    try {
        const [errSummary, usageSnap] = await Promise.allSettled([
            fetchAPI('/control-api/errors?limit=50&top_n=5'),
            fetchAPI('/control-api/usage?limit=30')
        ]);
        if (errSummary.status === 'rejected') throw errSummary.reason;
        errorsData = errSummary.value;
        if (usageSnap.status === 'fulfilled') {
            const allEvents = usageSnap.value.recent_events || [];
            const errorStatuses = ['error', 'fail', 'failed', 'quota_exceeded', 'blocked', 'timeout', 'rate_limited'];
            errorEventsData = allEvents.filter(ev => {
                const s = String(ev.status_normalized || ev.status || '').toLowerCase();
                return errorStatuses.some(es => s.includes(es));
            });
        }
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
                                <td>${formatTimestamp(sig.last_seen)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        ` : ''}

        ${(() => {
            const directErrors = (data.recent_errors || []);
            const fallbackErrors = errorEventsData || [];
            const events = directErrors.length > 0 ? directErrors : fallbackErrors;
            const sourceLabel = directErrors.length > 0 ? 'from /errors endpoint' : 'filtered from usage';
            if (events.length === 0) return '<div class="empty-state" style="margin-top:32px;"><i class="fas fa-check-circle"></i><h3>No recent error events</h3></div>';
            return `
            <div class="table-container" style="margin-top: 32px;">
                <div class="table-header">Recent Error Events <span style="font-size:11px; color:var(--text-muted); font-weight:400;">${sourceLabel}</span></div>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>User</th>
                            <th>Provider</th>
                            <th>Model</th>
                            <th>Status</th>
                            <th>HTTP</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${events.slice(0, 20).map(ev => `
                            <tr>
                                <td>${formatTimestamp(ev.timestamp)}</td>
                                <td><code style="font-size:11px;">${escapeHtml(formatShortLabel(ev.user_id || '--', 20))}</code></td>
                                <td>${escapeHtml(formatShortLabel(ev.provider || ev.provider_type || '--', 20))}</td>
                                <td>${escapeHtml(formatShortLabel(ev.model || '--', 24))}</td>
                                <td><span class="badge ${getStatusTone(ev.status_normalized || ev.status)}">${escapeHtml(ev.status_normalized || ev.status || '--')}</span></td>
                                <td>${ev.http_status || '--'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>`;
        })()}
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
