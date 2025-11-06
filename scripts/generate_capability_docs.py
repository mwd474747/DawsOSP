"""
Generate Capability Documentation

Purpose: Automatically generate capability documentation from contracts
Created: January 14, 2025
Priority: P1 (Foundation for Phase 2)

Usage:
    python scripts/generate_capability_docs.py
"""

import inspect
import json
from pathlib import Path
from typing import Dict, Any

def extract_capability_contracts():
    """Extract all capability contracts from agents."""
    contracts = {}
    
    try:
        # Import all agents
        from app.agents.financial_analyst import FinancialAnalyst
        from app.agents.macro_hound import MacroHound
        from app.agents.data_harvester import DataHarvester
        from app.agents.claude_agent import ClaudeAgent
        
        from app.core.capability_contract import extract_all_contracts
        
        agents = [FinancialAnalyst, MacroHound, DataHarvester, ClaudeAgent]
        
        for agent_class in agents:
            agent_contracts = extract_all_contracts(agent_class)
            contracts.update(agent_contracts)
    
    except ImportError as e:
        print(f"Warning: Could not import agents: {e}")
        return {}
    
    return contracts


def generate_docs(contracts: Dict[str, Dict[str, Any]]) -> str:
    """Generate markdown documentation."""
    md = "# Capability Contracts\n\n"
    md += "Auto-generated from capability decorators.\n\n"
    md += f"**Total Capabilities:** {len(contracts)}\n\n"
    md += "---\n\n"
    
    # Group by agent
    agent_groups = {}
    for name, contract in contracts.items():
        agent = name.split(".")[0]
        if agent not in agent_groups:
            agent_groups[agent] = []
        agent_groups[agent].append((name, contract))
    
    # Sort by agent, then by capability name
    for agent in sorted(agent_groups.keys()):
        md += f"## {agent.capitalize()} Capabilities\n\n"
        
        capabilities = sorted(agent_groups[agent], key=lambda x: x[0])
        
        for name, contract in capabilities:
            md += f"### {name}\n\n"
            
            # Status badge
            status = contract.get('implementation_status', 'unknown')
            status_badge = {
                'real': '✅ Real',
                'stub': '⚠️ Stub',
                'partial': '🔄 Partial',
            }.get(status, '❓ Unknown')
            md += f"**Status:** {status_badge}\n\n"
            
            if contract.get('description'):
                md += f"{contract['description']}\n\n"
            
            # Inputs
            md += "#### Inputs\n\n"
            inputs = contract.get('inputs', {})
            if inputs:
                for param, param_type in inputs.items():
                    type_name = param_type.__name__ if hasattr(param_type, '__name__') else str(param_type)
                    md += f"- `{param}`: `{type_name}`\n"
            else:
                md += "- None\n"
            md += "\n"
            
            # Outputs
            md += "#### Outputs\n\n"
            outputs = contract.get('outputs', {})
            if outputs:
                for field, field_type in outputs.items():
                    type_name = field_type.__name__ if hasattr(field_type, '__name__') else str(field_type)
                    md += f"- `{field}`: `{type_name}`\n"
            else:
                md += "- None\n"
            md += "\n"
            
            # Dependencies
            dependencies = contract.get('dependencies', [])
            if dependencies:
                md += "#### Dependencies\n\n"
                for dep in dependencies:
                    md += f"- `{dep}`\n"
                md += "\n"
            
            # Metadata
            if contract.get('fetches_positions'):
                md += "**Note:** This capability fetches positions internally.\n\n"
            
            md += "---\n\n"
    
    return md


def main():
    """Main entry point."""
    print("Generating capability documentation...")
    
    contracts = extract_capability_contracts()
    
    if not contracts:
        print("Warning: No capability contracts found. Make sure agents have @capability decorators.")
        return
    
    print(f"Found {len(contracts)} capability contracts")
    
    docs = generate_docs(contracts)
    
    output_path = Path("CAPABILITY_CONTRACTS.md")
    output_path.write_text(docs)
    
    print(f"Generated {len(contracts)} capability contracts in {output_path}")
    
    # Also generate JSON for programmatic access
    json_path = Path("CAPABILITY_CONTRACTS.json")
    json_path.write_text(json.dumps(contracts, indent=2, default=str))
    print(f"Generated JSON in {json_path}")


if __name__ == "__main__":
    main()

