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

// DOM Elements
const navItems = document.querySelectorAll('.nav-item');
const pages = document.querySelectorAll('.page');
const pageTitle = document.querySelector('.page-title');
const refreshBtn = document.getElementById('refresh-btn');
const logoutBtn = document.getElementById('logout-btn');
const currentTimeEl = document.getElementById('current-time');

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
    const allowedPages = ['overview', 'quota', 'billing', 'errors', 'models', 'system', 'usage'];
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
        usage: 'Usage'
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

async function runControlAction(action, target = null, timeout = 30) {
    return fetchAPI('/control-api/actions/run', {
        method: 'POST',
        body: JSON.stringify({ action, target, timeout })
    });
}

async function loadControlActionHistory() {
    const container = document.getElementById('models-actions-history');
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

// Overview page
async function loadOverview() {
    try {
        const data = await fetchAPI('/control-api/overview?usage_limit=50&recent_events_limit=5');
        overviewData = data;
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
            
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Recent Errors</div>
                    <div class="panel-subtitle">Last 5 errors</div>
                </div>
                <div class="panel-content">
                    ${recentErrors.length > 0 ? 
                        recentErrors.slice(0, 5).map(error => `
                            <div class="panel-row">
                                <span class="panel-label">${formatTimestamp(error.timestamp)}</span>
                                <span class="panel-value">${error.error || error.message || error.status || 'Unknown error'}</span>
                            </div>
                        `).join('') : 
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
        const data = await fetchAPI('/control-api/models');
        modelsData = data;
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

        <div class="panel-grid">
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Model Readiness</div>
                    <div class="panel-subtitle">Warmup state + actions</div>
                </div>
                <div class="panel-content">
                    ${models.length > 0 ? models.slice(0, 8).map(model => `
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
                    <div class="panel-title">Provider Health</div>
                    <div class="panel-subtitle">Load balancer backends + toggles</div>
                </div>
                <div class="panel-content">
                    ${providers.length > 0 ? providers.slice(0, 8).map(provider => `
                        <div class="panel-row panel-row-stack">
                            <div>
                                <div class="panel-label">${provider.name}</div>
                                <div class="panel-meta">${provider.type} · ${formatShortLabel(provider.model, 28)} · weight ${provider.weight}</div>
                            </div>
                            <div class="panel-actions-inline">
                                ${renderStatusWithDot(provider.health || 'unknown', provider.health === 'healthy' ? 'healthy' : 'unhealthy')}
                                <button class="toggle-switch ${provider.enabled ? 'is-on' : 'is-off'}" data-action="toggle-provider" data-target="${provider.name}" data-enabled="${provider.enabled ? '1' : '0'}" aria-label="Toggle provider ${provider.name}">
                                    <span class="toggle-track">
                                        <span class="toggle-thumb"></span>
                                    </span>
                                </button>
                            </div>
                        </div>
                    `).join('') : '<div class="panel-row"><span class="panel-label">No provider data</span><span class="panel-value">--</span></div>'}
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Ollama Models</div>
                    <div class="panel-subtitle">Local runtime inventory</div>
                </div>
                <div class="panel-content">
                    ${ollamaModels.length > 0 ? ollamaModels.slice(0, 6).map(model => `
                        <div class="panel-row">
                            <span class="panel-label">${model.name}</span>
                            <span class="panel-value">${model.details?.parameter_size || '--'}</span>
                        </div>
                    `).join('') : '<div class="panel-row"><span class="panel-label">No local models</span><span class="panel-value">--</span></div>'}
                </div>
            </div>
        </div>

        <div class="table-container" style="margin-top: 32px;">
            <div class="table-header">Provider Inventory</div>
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

        <div class="table-container" style="margin-top: 32px;">
            <div class="table-header">Recent Control Actions</div>
            <div id="models-actions-history" class="table-loading">Loading action history...</div>
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

        <div class="panel-grid">
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Node Health</div>
                    <div class="panel-subtitle">Service groups</div>
                </div>
                <div class="panel-content">
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
                    <div class="panel-row"><span class="panel-label">Learn Queue</span><span class="panel-value">${workloads.learn_queue?.length ?? 0}</span></div>
                    <div class="panel-row"><span class="panel-label">Datasets</span><span class="panel-value">${workloads.datasets?.count ?? 0}</span></div>
                    <div class="panel-row"><span class="panel-label">Latest Dataset</span><span class="panel-value">${workloads.datasets?.latest || '--'}</span></div>
                    <div class="panel-row"><span class="panel-label">Vector Store Docs</span><span class="panel-value">${workloads.vector_store?.document_count ?? 0}</span></div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div class="panel-title">Alerts</div>
                    <div class="panel-subtitle">Current attention items</div>
                </div>
                <div class="panel-content">
                    ${alerts.length > 0 ? alerts.slice(0, 6).map(alert => `
                        <div class="panel-row">
                            <span class="panel-label">${alert.message || 'Alert'}</span>
                            <span class="panel-value"><span class="badge ${getStatusTone(alert.severity)}">${alert.severity || 'info'}</span></span>
                        </div>
                    `).join('') : '<div class="panel-row"><span class="panel-label">No active alerts</span><span class="panel-value"><span class="badge badge-success">clear</span></span></div>'}
                </div>
            </div>
        </div>

        <div class="table-container" style="margin-top: 32px;">
            <div class="table-header">Backend Health Summary</div>
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

        <div class="table-container" style="margin-top: 32px;">
            <div class="table-header">Recent Usage Events</div>
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
    const modelBreakdown = data.model_breakdown || {};
    const topErrorSignatures = data.top_error_signatures || [];
    const recentErrors = data.recent_errors || [];
    
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
}