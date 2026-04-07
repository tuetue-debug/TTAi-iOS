import json
from pathlib import Path

PROJECT = Path(__file__).parent
INVENTORY = PROJECT / "CURRENT_INVENTORY_SEED.json"
OUT_MERMAID = PROJECT / "TTAI_SYSTEM_TOPOLOGY.md"

def load_inventory():
    with open(INVENTORY, 'r', encoding='utf-8') as f:
        return json.load(f)

def status_color(status):
    colors = {
        "operational": "green",
        "degraded": "orange",
        "offline": "red",
        "unknown": "gray"
    }
    return colors.get(status, "gray")

def exposure_symbol(exposure):
    symbols = {
        "local_only": "🔒",
        "tailscale": "🔗",
        "lan": "🏠",
        "public": "🌐"
    }
    return symbols.get(exposure, "❓")

def generate_mermaid(inv):
    lines = []
    lines.append("```mermaid")
    lines.append("graph TD")
    lines.append("")
    
    # Add nodes
    node_map = {}
    for node in inv["nodes"]:
        node_id = node["id"]
        name = node["name"]
        role = node["role"]
        status = node["status"]
        color = status_color(status)
        node_map[node_id] = name
        lines.append(f'    {node_id}["{name}<br/>{role}<br/>Status: {status}"]')
        lines.append(f'    style {node_id} fill:{color}')
    
    lines.append("")
    
    # Add services grouped by node
    service_map = {}
    for service in inv["services"]:
        svc_id = service["id"]
        name = service["name"]
        svc_type = service["type"]
        node_id = service["node_id"]
        status = service["status"]
        exposure = service["exposure"]
        color = status_color(status)
        symbol = exposure_symbol(exposure)
        
        service_map[svc_id] = name
        lines.append(f'    {svc_id}["{symbol} {name}<br/>{svc_type}<br/>Status: {status}"]')
        lines.append(f'    style {svc_id} fill:{color}')
        lines.append(f'    {node_id} --> {svc_id}')
    
    lines.append("")
    
    # Add dependencies
    for dep in inv.get("dependencies", []):
        source = dep["source_service_id"]
        target = dep["target_service_id"]
        dep_type = dep["type"]
        critical = dep.get("critical", False)
        line_style = "-->"
        if critical:
            line_style = "==>"
        lines.append(f'    {source} {line_style}|{dep_type}| {target}')
    
    lines.append("")
    
    # Add legend
    lines.append("    subgraph Legend")
    lines.append('        L_operational["Operational"]')
    lines.append('        style L_operational fill:green')
    lines.append('        L_degraded["Degraded"]')
    lines.append('        style L_degraded fill:orange')
    lines.append('        L_offline["Offline"]')
    lines.append('        style L_offline fill:red')
    lines.append('        L_unknown["Unknown"]')
    lines.append('        style L_unknown fill:gray')
    lines.append("    end")
    
    lines.append("")
    lines.append('    subgraph "Exposure Symbols"')
    lines.append('        E_local["🔒 Local Only"]')
    lines.append('        E_tailscale["🔗 Tailscale"]')
    lines.append('        E_lan["🏠 LAN"]')
    lines.append('        E_public["🌐 Public"]')
    lines.append("    end")
    
    lines.append("```")
    
    return "\n".join(lines)

def main():
    inv = load_inventory()
    mermaid = generate_mermaid(inv)
    
    # Create markdown document
    md_content = f"""# TTAi System Topology Map

Generated from inventory: {INVENTORY.name}
Timestamp: {inv['timestamp']}

## Interactive View
This diagram shows the current TTAi/OpenClaw system topology with nodes, services, and dependencies.

{mermaid}

## Key
- **Node colors**: Green = operational, Orange = degraded, Red = offline, Gray = unknown
- **Service symbols**: 🔒 = local only, 🔗 = Tailscale, 🏠 = LAN, 🌐 = public
- **Dependency lines**: Regular arrow = normal dependency, Thick arrow = critical dependency

## Current Status Summary
- **Nodes**: {len(inv['nodes'])} total ({sum(1 for n in inv['nodes'] if n['status'] == 'operational')} operational)
- **Services**: {len(inv['services'])} total ({sum(1 for s in inv['services'] if s['status'] == 'operational')} operational)
- **Ports**: {len(inv['ports'])} total ({sum(1 for p in inv['ports'] if p['status'] == 'listening')} listening)
- **Dependencies**: {len(inv.get('dependencies', []))} defined

## Notes
This is a static snapshot. For real-time status and interactive exploration, use the Control Dashboard System Topology tab.
"""
    
    with open(OUT_MERMAID, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"Mermaid diagram generated: {OUT_MERMAID}")

if __name__ == "__main__":
    main()
