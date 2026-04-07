import React, { useState, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

// Sample data - in production, this would come from an API
const sampleInventory = {
  nodes: [
    { id: 'node-vhp', name: 'vannt-home-pc', role: 'development', status: 'operational' },
    { id: 'node-vwo', name: 'vannt-work-op', role: 'compute', status: 'operational' },
    { id: 'node-dell', name: 'Dell Zx0Q', role: 'production', status: 'operational' },
  ],
  services: [
    { id: 'svc-fastapi-8000', name: 'FastAPI Original', type: 'api', node_id: 'node-vhp', status: 'offline' },
    { id: 'svc-hybrid-8005', name: 'TTAi Hybrid v2.0', type: 'api', node_id: 'node-vhp', status: 'operational' },
    { id: 'svc-debug-8013', name: 'TTAi Debug', type: 'api', node_id: 'node-vhp', status: 'operational' },
    { id: 'svc-lb-8015', name: 'Load Balancer', type: 'load_balancer', node_id: 'node-vhp', status: 'operational' },
    { id: 'svc-rag-8075', name: 'RAG Service', type: 'memory', node_id: 'node-vhp', status: 'unknown' },
    { id: 'svc-dashboard-8090', name: 'Control Dashboard', type: 'dashboard', node_id: 'node-vhp', status: 'unknown' },
    { id: 'svc-cliproxy-8317', name: 'CLI Proxy', type: 'cli_proxy', node_id: 'node-vhp', status: 'operational' },
    { id: 'svc-ollama-public', name: 'Ollama Public', type: 'ai_inference', node_id: 'node-vhp', status: 'operational' },
    { id: 'svc-ollama-memory', name: 'Ollama Memory', type: 'ai_inference', node_id: 'node-vhp', status: 'operational' },
    { id: 'svc-wordpress', name: 'WordPress', type: 'cms', node_id: 'node-dell', status: 'offline' },
    { id: 'svc-fastapi-prod', name: 'FastAPI Prod', type: 'api', node_id: 'node-dell', status: 'offline' },
    { id: 'svc-postgres', name: 'PostgreSQL', type: 'database', node_id: 'node-dell', status: 'operational' },
    { id: 'svc-mysql', name: 'MySQL', type: 'database', node_id: 'node-dell', status: 'operational' },
    { id: 'svc-redis', name: 'Redis', type: 'cache', node_id: 'node-dell', status: 'operational' },
    { id: 'svc-ollama-remote', name: 'Ollama Remote', type: 'ai_inference', node_id: 'node-vwo', status: 'operational' },
    { id: 'svc-fastapi-remote', name: 'TTAi Remote API', type: 'api', node_id: 'node-vwo', status: 'operational' },
  ],
  dependencies: [
    { source_service_id: 'svc-lb-8015', target_service_id: 'svc-debug-8013', type: 'api_call', critical: true },
    { source_service_id: 'svc-lb-8015', target_service_id: 'svc-fastapi-remote', type: 'api_call', critical: false },
    { source_service_id: 'svc-hybrid-8005', target_service_id: 'svc-cliproxy-8317', type: 'api_call', critical: true },
    { source_service_id: 'svc-hybrid-8005', target_service_id: 'svc-ollama-public', type: 'api_call', critical: true },
    { source_service_id: 'svc-rag-8075', target_service_id: 'svc-ollama-memory', type: 'api_call', critical: true },
    { source_service_id: 'svc-wordpress', target_service_id: 'svc-mysql', type: 'database', critical: true },
    { source_service_id: 'svc-fastapi-prod', target_service_id: 'svc-postgres', type: 'database', critical: true },
  ],
};

const statusColor = (status) => {
  switch (status) {
    case 'operational': return '#10a37f';
    case 'degraded': return '#f59e0b';
    case 'offline': return '#ef4444';
    case 'unknown': return '#6b7280';
    default: return '#6b7280';
  }
};

const nodeTypeColor = (type) => {
  switch (type) {
    case 'api': return '#3b82f6';
    case 'database': return '#8b5cf6';
    case 'cache': return '#ec4899';
    case 'ai_inference': return '#06b6d4';
    case 'memory': return '#84cc16';
    case 'load_balancer': return '#f97316';
    case 'cli_proxy': return '#6366f1';
    case 'dashboard': return '#14b8a6';
    case 'cms': return '#a855f7';
    default: return '#6b7280';
  }
};

const SystemTopologyTab = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    // In production, fetch from API
    // const fetchInventory = async () => {
    //   const response = await fetch('/api/v1/system/topology');
    //   const data = await response.json();
    //   return data;
    // };
    
    // For now, use sample data
    const inventory = sampleInventory;
    buildFlow(inventory);
    setLoading(false);
  }, []);

  const buildFlow = (inventory) => {
    const newNodes = [];
    const newEdges = [];
    let x = 100;
    let y = 100;

    // Create node groups
    inventory.nodes.forEach((node, idx) => {
      newNodes.push({
        id: node.id,
        type: 'default',
        position: { x: x + idx * 400, y: 50 },
        data: {
          label: (
            <div className="p-2 border rounded-lg shadow-sm bg-white">
              <div className="font-bold">{node.name}</div>
              <div className="text-sm text-gray-600">{node.role}</div>
              <div className={`text-sm font-medium ${node.status === 'operational' ? 'text-green-600' : 
                node.status === 'offline' ? 'text-red-600' : 'text-yellow-600'}`}>
                Status: {node.status}
              </div>
            </div>
          ),
        },
        style: {
          backgroundColor: statusColor(node.status),
          border: '2px solid #e5e7eb',
          borderRadius: '8px',
        },
      });

      // Add services for this node
      const nodeServices = inventory.services.filter(s => s.node_id === node.id);
      nodeServices.forEach((service, sIdx) => {
        const serviceY = y + sIdx * 80;
        newNodes.push({
          id: service.id,
          type: 'default',
          position: { x: x + idx * 400, y: serviceY },
          data: {
            label: (
              <div className="p-2 border rounded shadow bg-white max-w-xs">
                <div className="font-medium">{service.name}</div>
                <div className="text-xs text-gray-500">{service.type}</div>
                <div className={`text-xs font-medium ${service.status === 'operational' ? 'text-green-600' : 
                  service.status === 'offline' ? 'text-red-600' : 'text-gray-600'}`}>
                  {service.status}
                </div>
              </div>
            ),
          },
          style: {
            backgroundColor: nodeTypeColor(service.type),
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            width: 180,
          },
        });

        // Connect service to its node
        newEdges.push({
          id: `edge-${node.id}-${service.id}`,
          source: node.id,
          target: service.id,
          type: 'smoothstep',
          animated: false,
          style: { stroke: '#9ca3af', strokeWidth: 1 },
        });
      });
    });

    // Add dependency edges
    inventory.dependencies.forEach((dep, idx) => {
      newEdges.push({
        id: `dep-${idx}`,
        source: dep.source_service_id,
        target: dep.target_service_id,
        type: 'smoothstep',
        label: dep.type,
        animated: dep.critical,
        style: {
          stroke: dep.critical ? '#ef4444' : '#3b82f6',
          strokeWidth: dep.critical ? 3 : 2,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: dep.critical ? '#ef4444' : '#3b82f6',
        },
      });
    });

    setNodes(newNodes);
    setEdges(newEdges);
  };

  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
    // Filter logic would go here
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading topology...</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="mb-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-gray-800">System Topology</h2>
            <p className="text-gray-600 text-sm">
              Interactive map of TTAi/OpenClaw nodes, services, and dependencies
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => handleFilterChange('all')}
              className={`px-3 py-1 rounded ${filter === 'all' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'}`}
            >
              All
            </button>
            <button
              onClick={() => handleFilterChange('operational')}
              className={`px-3 py-1 rounded ${filter === 'operational' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}
            >
              Operational
            </button>
            <button
              onClick={() => handleFilterChange('offline')}
              className={`px-3 py-1 rounded ${filter === 'offline' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}`}
            >
              Offline
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 border rounded-lg overflow-hidden bg-gray-50">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          attributionPosition="bottom-right"
        >
          <MiniMap />
          <Controls />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      </div>

      <div className="mt-4 p-4 bg-white border rounded-lg">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 border rounded">
            <div className="text-sm text-gray-500">Nodes</div>
            <div className="text-2xl font-bold">{sampleInventory.nodes.length}</div>
            <div className="text-sm text-green-600">
              {sampleInventory.nodes.filter(n => n.status === 'operational').length} operational
            </div>
          </div>
          <div className="p-3 border rounded">
            <div className="text-sm text-gray-500">Services</div>
            <div className="text-2xl font-bold">{sampleInventory.services.length}</div>
            <div className="text-sm text-green-600">
              {sampleInventory.services.filter(s => s.status === 'operational').length} operational
            </div>
          </div>
          <div className="p-3 border rounded">
            <div className="text-sm text-gray-500">Dependencies</div>
            <div className="text-2xl font-bold">{sampleInventory.dependencies.length}</div>
            <div className="text-sm text-red-600">
              {sampleInventory.dependencies.filter(d => d.critical).length} critical
            </div>
          </div>
          <div className="p-3 border rounded">
            <div className="text-sm text-gray-500">Last Updated</div>
            <div className="text-lg font-bold">Just now</div>
            <div className="text-sm text-gray-500">Static snapshot</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemTopologyTab;
