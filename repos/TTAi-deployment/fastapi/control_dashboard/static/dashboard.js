// TTAi Control Dashboard JavaScript
const API_BASE = '/api';
const ADMIN_API_BASE = '/api/v1/admin';
const CONTROL_API_BASE = '/control-api';
const CONTROL_TOKEN = 'ttai-control-token'; // legacy control collector token
const ADMIN_TOKEN = 'f6883d3eb388cff8fcad7d7952c568f6fd8995afa6f4581209215d582e2efe59'; // production admin token for dashboard MVP

// DOM Elements
const overallStatusEl = document.getElementById('overallStatus');
const lastUpdatedEl = document.getElementById('lastUpdated');
const modelSelectorsEl = document.getElementById('modelSelectors');
const gpuMetricsEl = document.getElementById('gpuMetrics');
const vectorStatsEl = document.getElementById('vectorStats');
const backupBtn = document.getElementById('backupBtn');
const serviceListEl = document.getElementById('serviceList');
const refreshBtn = document.getElementById('refreshBtn');
const overviewSummaryEl = document.getElementById('overviewSummary');
const billingSummaryEl = document.getElementById('billingSummary');
const quotaBlockedSummaryEl = document.getElementById('quotaBlockedSummary');
const errorSummaryEl = document.getElementById('errorSummary');
const proxyStatusCardEl = document.getElementById('proxyStatusCard');
const proxyBackendTableEl = document.getElementById('proxyBackendTable');
const proxyBenchmarkPanelEl = document.getElementById('proxyBenchmarkPanel');

// Headers for API calls
const headers = {
    'X-Control-Token': CONTROL_TOKEN,
    'Content-Type': 'application/json'
};

const adminHeaders = {
    'Authorization': `Bearer ${ADMIN_TOKEN}`,
    'Content-Type': 'application/json'
};

// Format timestamp
function formatTimeAgo(timestamp) {
    if (!timestamp) return 'Never';
    const diff = Date.now() - new Date(timestamp).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
}

// Format bytes to MB/GB
function formatBytes(bytes) {
    if (!bytes) return '0 MB';
    const mb = bytes / (1024 * 1024);
    if (mb > 1024) {
        return `${(mb / 1024).toFixed(1)} GB`;
    }
    return `${mb.toFixed(1)} MB`;
}

// Update overall status
function updateOverallStatus(status) {
    overallStatusEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    overallStatusEl.className = `status-badge ${status}`;
}

// Update last updated timestamp
function updateTimestamp() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
    lastUpdatedEl.textContent = `Last updated: ${timeStr}`;
}

function renderSummaryList(container, items) {
    if (!container) return;
    container.innerHTML = '';
    if (!items || items.length === 0) {
        container.innerHTML = '<div class="summary-item"><span class="label">No data</span><span class="value">--</span></div>';
        return;
    }
    items.forEach(item => {
        const row = document.createElement('div');
        row.className = 'summary-item';
        row.innerHTML = `<span class="label">${item.label}</span><span class="value">${item.value}</span>`;
        container.appendChild(row);
    });
}

function formatProxyStatus(status) {
    if (!status) return '--';
    return status.charAt(0).toUpperCase() + status.slice(1);
}

async function loadProxyState() {
    if (!proxyStatusCardEl) return;
    try {
        const response = await fetch(`${CONTROL_API_BASE}/proxy/state`, { headers: adminHeaders });
        if (!response.ok) throw new Error('Failed to load proxy state');
        const data = await response.json();
        const summary = data.summary || {};
        const runtime = data.runtime || {};
        proxyStatusCardEl.innerHTML = `
            <div class="summary-item"><span class="label">Status</span><span class="value">${formatProxyStatus(summary.service_status)}</span></div>
            <div class="summary-item"><span class="label">Mode</span><span class="value">${summary.mode || '--'}</span></div>
            <div class="summary-item"><span class="label">Preferred</span><span class="value">${summary.preferred_backend || '--'}</span></div>
            <div class="summary-item"><span class="label">Hedge</span><span class="value">${summary.hedge_enabled ? 'On' : 'Off'}</span></div>
            <div class="summary-item"><span class="label">Healthy Backends</span><span class="value">${summary.healthy_backend_count ?? '--'}/${summary.backend_count ?? '--'}</span></div>
            <div class="summary-item"><span class="label">Source</span><span class="value">${runtime.source || '--'}</span></div>
        `;
    } catch (error) {
        console.error('Error loading proxy state:', error);
        proxyStatusCardEl.innerHTML = '<div class="summary-item"><span class="label">Proxy state</span><span class="value">Error</span></div>';
    }
}

async function loadProxyBackends() {
    if (!proxyBackendTableEl) return;
    try {
        const response = await fetch(`${CONTROL_API_BASE}/proxy/backends`, { headers: adminHeaders });
        if (!response.ok) throw new Error('Failed to load proxy backends');
        const data = await response.json();
        const items = data.items || [];
        if (!items.length) {
            proxyBackendTableEl.innerHTML = '<div class="summary-item"><span class="label">Backends</span><span class="value">No data</span></div>';
            return;
        }
        proxyBackendTableEl.innerHTML = items.map(item => `
            <div class="summary-item">
                <span class="label">${item.id} · ${item.role} · ${item.healthy ? 'Healthy' : 'Unhealthy'}</span>
                <span class="value">${item.weight ?? 0}% · ${item.latency_ms ?? '--'} ms</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading proxy backends:', error);
        proxyBackendTableEl.innerHTML = '<div class="summary-item"><span class="label">Backends</span><span class="value">Error</span></div>';
    }
}

async function loadProxyBenchmark() {
    if (!proxyBenchmarkPanelEl) return;
    try {
        const response = await fetch(`${CONTROL_API_BASE}/proxy/benchmark/latest`, { headers: adminHeaders });
        if (!response.ok) throw new Error('Failed to load proxy benchmark');
        const data = await response.json();
        const summary = data.summary || {};
        const notes = (data.notes || []).slice(0, 2).join(' · ');
        proxyBenchmarkPanelEl.innerHTML = `
            <div class="summary-item"><span class="label">Status</span><span class="value">${summary.status || (data.available ? 'available' : 'not_run')}</span></div>
            <div class="summary-item"><span class="label">Last Run</span><span class="value">${summary.last_run || '--'}</span></div>
            <div class="summary-item"><span class="label">Notes</span><span class="value">${notes || '--'}</span></div>
        `;
    } catch (error) {
        console.error('Error loading proxy benchmark:', error);
        proxyBenchmarkPanelEl.innerHTML = '<div class="summary-item"><span class="label">Benchmark</span><span class="value">Error</span></div>';
    }
}

async function loadAdminOverview() {
    try {
        const [overviewRes, errorsRes, quotaRes, billingRes] = await Promise.all([
            fetch(`${CONTROL_API_BASE}/overview?usage_limit=50&recent_events_limit=5`, { headers: adminHeaders }),
            fetch(`${CONTROL_API_BASE}/errors?limit=50&top_n=5`, { headers: adminHeaders }),
            fetch(`${CONTROL_API_BASE}/quota?limit=50&recent_limit=5`, { headers: adminHeaders }),
            fetch(`${CONTROL_API_BASE}/billing?limit=50`, { headers: adminHeaders })
        ]);

        if (!overviewRes.ok || !errorsRes.ok || !quotaRes.ok || !billingRes.ok) {
            throw new Error('Failed to load control dashboard data');
        }

        const overview = await overviewRes.json();
        const errors = await errorsRes.json();
        const quota = await quotaRes.json();
        const billing = await billingRes.json();

        if (overviewSummaryEl) {
            const metrics = overviewSummaryEl.querySelectorAll('.metric-value');
            metrics[0].textContent = overview.health?.summary?.status || overview.health?.summary?.overall_status || '--';
            metrics[1].textContent = overview.usage?.window_event_count ?? overview.usage?.count ?? '--';
            metrics[2].textContent = billing.summary?.estimated_cost ?? overview.billing?.summary?.estimated_cost ?? '--';
            metrics[3].textContent = overview.quota?.blocked_event_count ?? quota.blocked_event_count ?? '--';
        }

        renderSummaryList(billingSummaryEl, [
            { label: 'Estimated Cost', value: billing.summary?.estimated_cost ?? overview.billing?.summary?.estimated_cost ?? '--' },
            { label: 'Billable Events', value: billing.summary?.billable_events ?? overview.billing?.summary?.billable_events ?? '--' },
            { label: 'Top Provider', value: Object.keys(billing.provider_breakdown || overview.billing?.summary?.provider_breakdown || {})[0] || '--' },
            { label: 'Top API Key', value: Object.keys(billing.api_key_breakdown || overview.billing?.summary?.api_key_breakdown || {})[0] || '--' }
        ]);

        renderSummaryList(quotaBlockedSummaryEl, [
            { label: 'Blocked Events', value: quota.blocked_event_count ?? '--' },
            { label: 'Top Tenant', value: Object.keys(quota.tenant_breakdown || {})[0] || '--' },
            { label: 'Top API Key', value: Object.keys(quota.api_key_breakdown || {})[0] || '--' },
            { label: 'Top Reason', value: Object.keys(quota.reason_breakdown || {})[0] || '--' }
        ]);

        renderSummaryList(errorSummaryEl, [
            { label: 'Error Events', value: errors.error_event_count ?? '--' },
            { label: 'Top Status', value: Object.keys(errors.status_breakdown || {})[0] || '--' },
            { label: 'Top HTTP Status', value: Object.keys(errors.http_status_breakdown || {})[0] || '--' },
            { label: 'Top Provider', value: Object.keys(errors.provider_breakdown || {})[0] || '--' }
        ]);
    } catch (error) {
        console.error('Error loading admin overview:', error);
        renderSummaryList(billingSummaryEl, [{ label: 'Control overview failed', value: 'Error' }]);
        renderSummaryList(quotaBlockedSummaryEl, [{ label: 'Quota summary failed', value: 'Error' }]);
        renderSummaryList(errorSummaryEl, [{ label: 'Error summary failed', value: 'Error' }]);
    }
}

// Load and display model selectors
async function loadModels() {
    try {
        const response = await fetch(`${API_BASE}/models`, { headers });
        const data = await response.json();
        
        modelSelectorsEl.innerHTML = '';
        
        for (const [hostId, hostData] of Object.entries(data.model_status)) {
            const container = document.createElement('div');
            container.className = 'model-selector';
            
            const label = document.createElement('label');
            label.className = 'host-label';
            label.textContent = `${hostData.name} (${hostData.active_model})`;
            container.appendChild(label);
            
            const select = document.createElement('select');
            select.className = 'model-dropdown';
            select.dataset.hostId = hostId;
            
            // Add model options
            hostData.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = `${model.label} (${model.size_gb || '?'}GB)`;
                option.selected = model.id === hostData.active_model;
                select.appendChild(option);
            });
            
            // Add change event listener
            select.addEventListener('change', async (e) => {
                const hostId = e.target.dataset.hostId;
                const modelId = e.target.value;
                
                try {
                    const response = await fetch(`${API_BASE}/models/select`, {
                        method: 'POST',
                        headers,
                        body: JSON.stringify({ host_id: hostId, model_id: modelId })
                    });
                    
                    if (response.ok) {
                        alert(`✅ Model changed to ${modelId} on ${hostId}`);
                        loadModels(); // Reload to reflect change
                    } else {
                        alert('❌ Failed to change model');
                    }
                } catch (error) {
                    console.error('Error changing model:', error);
                    alert('❌ Error changing model');
                }
            });
            
            container.appendChild(select);
            modelSelectorsEl.appendChild(container);
        }
    } catch (error) {
        console.error('Error loading models:', error);
        modelSelectorsEl.innerHTML = '<div class="error">Failed to load models</div>';
    }
}

// Load GPU metrics
async function loadGPUMetrics() {
    try {
        const response = await fetch(`${API_BASE}/workloads`, { headers });
        const data = await response.json();
        
        const gpuData = data.model_status?.['remote-gpu']?.gpu_stats;
        if (gpuData) {
            const metrics = gpuMetricsEl.querySelectorAll('.metric');
            metrics[0].querySelector('.metric-value').textContent = gpuData.temperature || '--';
            metrics[1].querySelector('.metric-value').textContent = gpuData.utilization || '--';
            metrics[2].querySelector('.metric-value').textContent = 
                `${(gpuData.memory_used / 1024).toFixed(1)}/${(gpuData.memory_total / 1024).toFixed(1)}`;
            metrics[3].querySelector('.metric-value').textContent = gpuData.power_draw || '--';
        }
    } catch (error) {
        console.error('Error loading GPU metrics:', error);
    }
}

// Load vector store stats
async function loadVectorStats() {
    try {
        const response = await fetch(`${API_BASE}/workloads`, { headers });
        const data = await response.json();
        
        const vectorData = data.vector_store;
        if (vectorData) {
            const stats = vectorStatsEl.querySelectorAll('.metric');
            stats[0].querySelector('.metric-value').textContent = vectorData.total_documents || '--';
            stats[1].querySelector('.metric-value').textContent = formatTimeAgo(vectorData.last_ingest);
            stats[2].querySelector('.metric-value').textContent = formatBytes(vectorData.backup_size);
            stats[3].querySelector('.metric-value').textContent = formatTimeAgo(vectorData.last_backup);
        }
    } catch (error) {
        console.error('Error loading vector stats:', error);
    }
}

// Load service health
async function loadServiceHealth() {
    try {
        const response = await fetch(`${API_BASE}/health-summary`, { headers });
        const data = await response.json();
        
        updateOverallStatus(data.overall_status || 'healthy');
        
        serviceListEl.innerHTML = '';
        data.nodes?.forEach(node => {
            node.services?.forEach(service => {
                const li = document.createElement('li');
                li.className = 'service-item';
                
                const serviceName = document.createElement('div');
                serviceName.className = 'service-name';
                
                const statusDot = document.createElement('div');
                statusDot.className = `service-status ${service.status}`;
                
                const nameSpan = document.createElement('span');
                nameSpan.textContent = service.name;
                
                serviceName.appendChild(statusDot);
                serviceName.appendChild(nameSpan);
                
                const portSpan = document.createElement('div');
                portSpan.className = 'service-port';
                portSpan.textContent = service.port || '--';
                
                li.appendChild(serviceName);
                li.appendChild(portSpan);
                serviceListEl.appendChild(li);
            });
        });
    } catch (error) {
        console.error('Error loading service health:', error);
        serviceListEl.innerHTML = '<li class="service-item">Failed to load services</li>';
    }
}

// Trigger vector backup
async function triggerBackup() {
    try {
        backupBtn.disabled = true;
        backupBtn.textContent = 'Backing up...';
        
        const response = await fetch(`${API_BASE}/vector/backup`, {
            method: 'POST',
            headers
        });
        
        if (response.ok) {
            const result = await response.json();
            alert(`✅ Backup triggered successfully!\nLast backup: ${formatTimeAgo(result.last_backup)}`);
            loadVectorStats(); // Reload stats
        } else {
            alert('❌ Failed to trigger backup');
        }
    } catch (error) {
        console.error('Error triggering backup:', error);
        alert('❌ Error triggering backup');
    } finally {
        backupBtn.disabled = false;
        backupBtn.textContent = '🔄 Trigger Vector Backup';
    }
}

// Refresh all data
async function refreshAll() {
    updateTimestamp();
    
    // Add loading animation to refresh button
    refreshBtn.style.transform = 'rotate(180deg)';
    
    try {
        await Promise.all([
            loadAdminOverview(),
            loadModels(),
            loadGPUMetrics(),
            loadVectorStats(),
            loadServiceHealth(),
            loadProxyState(),
            loadProxyBackends(),
            loadProxyBenchmark()
        ]);
    } catch (error) {
        console.error('Error refreshing data:', error);
    } finally {
        // Reset refresh button
        setTimeout(() => {
            refreshBtn.style.transform = '';
        }, 300);
    }
}

// Initialize dashboard
async function initDashboard() {
    // Set up event listeners
    backupBtn.addEventListener('click', triggerBackup);
    refreshBtn.addEventListener('click', refreshAll);
    
    // Auto-refresh every 30 seconds
    setInterval(refreshAll, 30000);
    
    // Initial load
    await refreshAll();
}

// Start dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', initDashboard);