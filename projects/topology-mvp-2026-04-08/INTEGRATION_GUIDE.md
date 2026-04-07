# Topology MVP Integration Guide

## What's been created
1. **Inventory schema** (`TOPOLOGY_INVENTORY_SCHEMA.json`) - structured definition of nodes, networks, services, ports, dependencies
2. **Seed data** (`inventory_simple.json`) - current environment inventory (simplified for MVP)
3. **Mermaid diagram** (`TTAI_SYSTEM_TOPOLOGY.md`) - static visual snapshot for documentation
4. **React Flow component** (`SystemTopologyTab.jsx`) - interactive topology tab for Control Dashboard
5. **Supporting scripts** (`generate_mermaid_simple.py`) - utility to generate diagrams from inventory

## How to integrate into Control Dashboard

### Step 1: Add React Flow dependency
If not already installed in the Control Dashboard project:
```bash
npm install reactflow
```

### Step 2: Copy component file
Copy `SystemTopologyTab.jsx` to your Control Dashboard components directory:
```
frontend-auth-ui/src/components/SystemTopologyTab.jsx
```

### Step 3: Add to navigation/routing
Add a new route in your dashboard routing:

```jsx
// In your main App.jsx or routing file
import SystemTopologyTab from './components/SystemTopologyTab';

// Add to routes
<Route path="/topology" element={<SystemTopologyTab />} />
```

### Step 4: Add to sidebar/navigation
Add a navigation item to your sidebar:

```jsx
// In your sidebar component
<li>
  <Link to="/topology" className="flex items-center p-2 text-gray-900 rounded-lg hover:bg-gray-100">
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
    <span className="ml-3">System Topology</span>
  </Link>
</li>
```

### Step 5: Create API endpoint (optional but recommended)
For production use, create a backend endpoint that serves the inventory data:

```python
# FastAPI endpoint example
@app.get("/api/v1/system/topology")
async def get_system_topology():
    # Load from file or generate dynamically
    with open("projects/topology-mvp-2026-04-08/inventory_simple.json") as f:
        inventory = json.load(f)
    return inventory
```

Then update the React component to fetch from this endpoint instead of using sample data.

## Current limitations (MVP)
1. **Static data** - Currently uses hardcoded sample data
2. **No auto-discovery** - Inventory must be manually updated
3. **Basic filtering** - Only simple status filters implemented
4. **No real-time updates** - Requires refresh to see changes

## Next steps for production
1. **API integration** - Connect to real backend endpoint
2. **Auto-refresh** - Poll for status updates
3. **Health checks** - Integrate with existing health monitoring
4. **Interactive features** - Click nodes for details, edit mode
5. **Import/export** - Load inventory from different sources

## Files to keep
- `TOPOLOGY_INVENTORY_SCHEMA.json` - Keep as reference for future extensions
- `inventory_simple.json` - Use as initial seed data
- `TTAI_SYSTEM_TOPOLOGY.md` - Keep for documentation
- `SystemTopologyTab.jsx` - Main component to integrate

## Files that can be removed after integration
- `generate_mermaid_simple.py` - Optional, keep if you want to regenerate diagrams
- `CURRENT_INVENTORY_SEED.json` - Superseded by `inventory_simple.json`

## Testing
1. Start your Control Dashboard
2. Navigate to `/topology`
3. Verify the graph loads and shows nodes/services
4. Test filtering buttons
5. Verify dependency edges show correctly

## Success criteria
- [ ] Graph loads without errors
- [ ] All 3 nodes visible
- [ ] Services grouped under correct nodes
- [ ] Dependency edges visible
- [ ] Status colors correct (green=operational, red=offline, gray=unknown)
- [ ] Filter buttons work
- [ ] Stats panel shows correct counts

## Notes
This MVP provides immediate operational value by visualizing the current system topology. It creates a foundation that can be extended with:
- Real-time health status
- Auto-discovery
- Historical views
- Alert integration
- Performance metrics overlay
