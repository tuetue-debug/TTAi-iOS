// TTAi Control Dashboard - Main JavaScript

// Configuration
const API_BASE = window.location.origin; // Same origin as FastAPI

// State
let currentPage = 'overview';
let overviewData = null;
let quotaData = null;
let billingData = null;
let errorsData = null;

// DOM Elements
const navItems = document.querySelectorAll('.nav-item');
const pages = document.querySelectorAll('.page');
const pageTitle = document.querySelector('.page-title');
const refreshBtn = document.getElementById('refresh-btn');
const currentTimeEl = document.getElementById('current-time');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initTimeDisplay();
    loadPage(currentPage);
    
    refreshBtn.addEventListener('click', () => {
        refreshCurrentPage();
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

function switchPage(page) {
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
                <div class="kpi-value neutral">$${summary.total_estimated_cost || '0.00'}</div>
                <div class="kpi-trend">
                    <i class="fas fa-dollar-sign"></i>
                    <span>All events</span>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-eyebrow">Billable</div>
                <div class="kpi-title">Billable Cost</div>
                <div class="kpi-value neutral">$${summary.billable_estimated_cost || '0.00'}</div>
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
                                <span class="panel-value">$${cost.toFixed(2)}</span>
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
                                <span class="panel-label">${key.substring(0, 12)}...</span>
                                <span class="panel-value">$${cost.toFixed(2)}</span>
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
                                <span class="panel-value">$${cost.toFixed(2)}</span>
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
                                <td>${sig.signature || '--'}</td>
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