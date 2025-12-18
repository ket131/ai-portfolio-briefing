# lambda/mcp_config.py
"""MCP server configuration for Alpha Vantage"""
import os
from typing import List, Dict

def get_mcp_servers() -> List[Dict]:
    """
    Get MCP server configurations for Anthropic API
    
    Returns:
        List of MCP server configs (currently just Alpha Vantage)
    
    Raises:
        ValueError: If required environment variables missing
    """
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY not set")
    
    # Alpha Vantage MCP server
    servers = [
        {
            "type": "url",
            "url": f"https://mcp.alphavantage.co/mcp?apikey={api_key}",
            "name": "alphavantage"
        }
    ]
    
    # Future: Plaid MCP (when available)
    # if os.environ.get('PLAID_MCP_ENABLED', 'false') == 'true':
    #     servers.append(get_plaid_mcp_config())
    
    return servers