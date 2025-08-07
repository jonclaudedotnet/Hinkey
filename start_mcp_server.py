#!/usr/bin/env python3
"""
DOCMACK MCP Server - Enable AI Team Communication
"""

from fastmcp import FastMCP
import json
import subprocess
import os
from datetime import datetime
import glob
from pathlib import Path

mcp = FastMCP("DOCMACK AI Team Server")

@mcp.tool()
def find_ingestion_processes() -> str:
    """Find what ingestion processes are currently running"""
    try:
        # Look for running Python processes
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        
        # Look for processes with 'ingest', 'synology', 'process' in name
        processes = []
        for line in result.stdout.split('\n'):
            if any(word in line.lower() for word in ['ingest', 'synology', 'process', 'scan', 'smb', 'nexus']):
                processes.append(line.strip())
        
        return f"Found {len(processes)} potential ingestion processes:\n" + "\n".join(processes)
    except Exception as e:
        return f"Error finding processes: {e}"

@mcp.tool()
def check_databases() -> str:
    """Check for databases or data storage related to ingestion"""
    try:
        # Look for common database files in Hinkey directory
        base_path = "/home/jonclaude/agents/Hinkey"
        found_dbs = []
        
        # Search patterns
        patterns = ['*.db', '*.sqlite', '*ingest*.json', '*status*.json', '*cache*']
        
        for pattern in patterns:
            for file_path in glob.glob(os.path.join(base_path, "**", pattern), recursive=True):
                file_size = os.path.getsize(file_path)
                found_dbs.append(f"{file_path} ({file_size} bytes)")
        
        return f"Found {len(found_dbs)} database/status files:\n" + "\n".join(found_dbs[:20])
    except Exception as e:
        return f"Error checking databases: {e}"

@mcp.tool()
def check_ingestion_status() -> str:
    """Check current ingestion status from status files"""
    try:
        status_file = "/home/jonclaude/agents/Hinkey/ingestion_status.json"
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status = json.load(f)
            return f"Current ingestion status:\n{json.dumps(status, indent=2)}"
        else:
            return "No ingestion status file found"
    except Exception as e:
        return f"Error reading ingestion status: {e}"

@mcp.tool()
def check_ports() -> str:
    """Check what services are running on ports"""
    try:
        result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
        return f"Active ports:\n{result.stdout}"
    except Exception as e:
        return f"Error checking ports: {e}"

@mcp.tool()  
def get_system_info() -> str:
    """Get basic system information"""
    try:
        info = {
            "hostname": subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip(),
            "ip": "10.0.0.200",
            "timestamp": datetime.now().isoformat(),
            "user": os.getenv('USER', 'unknown'),
            "working_directory": os.getcwd(),
            "hinkey_path": "/home/jonclaude/agents/Hinkey"
        }
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error getting system info: {e}"

@mcp.tool()
def find_hinkey_scripts() -> str:
    """Find all Python scripts in the Hinkey directory"""
    try:
        hinkey_path = "/home/jonclaude/agents/Hinkey"
        scripts = []
        
        for file_path in glob.glob(os.path.join(hinkey_path, "*.py")):
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            scripts.append(f"{file_name} ({file_size} bytes, modified: {mod_time})")
        
        return f"Found {len(scripts)} Python scripts in Hinkey:\n" + "\n".join(scripts)
    except Exception as e:
        return f"Error finding scripts: {e}"

@mcp.tool()
def check_smb_cache() -> str:
    """Check SMB cache status and contents"""
    try:
        cache_path = "/home/jonclaude/agents/Hinkey/smb_nexus_cache"
        if os.path.exists(cache_path):
            # Count files in cache
            file_count = 0
            total_size = 0
            
            for root, dirs, files in os.walk(cache_path):
                file_count += len(files)
                for file in files:
                    try:
                        total_size += os.path.getsize(os.path.join(root, file))
                    except OSError:
                        pass
            
            info = {
                "cache_path": cache_path,
                "cached_files": file_count,
                "total_size_mb": round(total_size / (1024*1024), 2),
                "directories": len([d for d in os.listdir(cache_path) if os.path.isdir(os.path.join(cache_path, d))])
            }
            
            return f"SMB Cache Status:\n{json.dumps(info, indent=2)}"
        else:
            return "No SMB cache directory found"
    except Exception as e:
        return f"Error checking SMB cache: {e}"

@mcp.tool()
def get_dolores_memory_stats() -> str:
    """Get Dolores memory statistics"""
    try:
        # Try to import and get stats
        import sys
        sys.path.append('/home/jonclaude/agents/Hinkey')
        
        from dolores_core import DoloresMemory
        memory = DoloresMemory()
        stats = memory.get_memory_stats()
        
        return f"Dolores Memory Stats:\n{json.dumps(stats, indent=2)}"
    except Exception as e:
        return f"Error getting Dolores stats: {e}"

if __name__ == "__main__":
    print("🖥️  DOCMACK MCP Server Starting...")
    print("🔌 MacMini can now connect to find ingestion engine")
    print("🌐 Server running via stdio for MCP protocol")
    print("🤖 AI Team coordination enabled")
    
    # Start MCP server (uses stdio protocol)
    mcp.run()