# Topology MVP - 2026-04-08

## Goal
Create a usable system topology foundation for the TTAi/OpenClaw environment before 9:00 AM.

## Deliverables
1. **Topology inventory schema** - structured definition of nodes, networks, services, ports, dependencies
2. **Seed data** - current environment inventory based on existing documentation
3. **Mermaid system map** - visual snapshot for documentation
4. **Control Dashboard tab** - interactive 2D topology view using React Flow

## Scope
### Included
- 3 main nodes: vannt-home-pc, vannt-work-op, Dell Zx0Q (vannt-home-zq)
- Key services: FastAPI instances, load balancer, WordPress, RAG service, CLI Proxy, Control Dashboard, Ollama instances
- Ports, network zones (local, Tailscale, public)
- Basic health/status overlays
- Dependency edges

### Not included (for MVP)
- Auto-discovery
- 3D visualization
- Complex animation
- Time-series replay
- Full automation

## Success criteria
- Inventory schema is complete and extensible
- Seed data accurately reflects current system
- Mermaid diagram is readable and useful
- Dashboard tab loads and shows interactive map
- All work committed before 9:00 AM

## Timeline
- 00:55–01:30: Inventory schema + seed data
- 01:30–02:00: Mermaid diagram + docs
- 02:00–03:30: Dashboard integration
- 03:30–04:00: Testing + final commit
