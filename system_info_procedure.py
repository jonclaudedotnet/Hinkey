#!/usr/bin/env python3
"""
System Information Procedure - Gather and share system specs with Dolores
"""

import subprocess
import json
from claude_dolores_bridge import ask_dolores
from datetime import datetime

def run_command(cmd):
    """Run command and return output safely"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error running '{cmd}': {e}"

def gather_system_info():
    """Collect comprehensive system information"""
    
    print("🔍 Gathering system information...")
    
    system_info = {
        "timestamp": datetime.now().isoformat(),
        "os_release": run_command("cat /etc/fedora-release"),
        "kernel": run_command("uname -r"),
        "architecture": run_command("uname -m"),
        "hostname": run_command("hostname"),
        "uptime": run_command("uptime -p"),
        "cpu_info": run_command("lscpu | head -15"),
        "memory": run_command("free -h"),
        "disk_space": run_command("df -h /"),
        "graphics": run_command("lspci | grep -i vga"),
        "audio_devices": run_command("pactl list sources short"),
        "network": run_command("ip route | head -3"),
        "python_version": run_command("python3 --version"),
        "installed_packages": {
            "gtk": run_command("rpm -q gtk3"),
            "sqlite": run_command("rpm -q sqlite"),
            "git": run_command("git --version"),
        },
        "display_info": run_command("xrandr | grep connected"),
        "current_user": run_command("whoami"),
        "working_directory": run_command("pwd"),
        "environment": {
            "PATH": run_command("echo $PATH"),
            "DISPLAY": run_command("echo $DISPLAY"),
        }
    }
    
    return system_info

def format_system_summary(info):
    """Create a readable summary for Dolores"""
    
    summary = f"""📋 SYSTEM INFORMATION UPDATE - {info['timestamp'][:10]}

🖥️  **Operating System**: {info['os_release']}
⚙️   **Kernel**: {info['kernel']} ({info['architecture']})
🏠  **Hostname**: {info['hostname']}
⏰  **Uptime**: {info['uptime']}

💾  **Memory**: 
{info['memory']}

💽  **Disk Space**: 
{info['disk_space']}

🎮  **Graphics**: {info['graphics']}

🎤  **Audio Sources**: 
{info['audio_devices']}

🖼️   **Displays**: 
{info['display_info']}

🐍  **Python**: {info['python_version']}

👤  **User**: {info['current_user']}
📁  **Working Directory**: {info['working_directory']}

**Key Packages Available**:
- GTK3: {info['installed_packages']['gtk']}
- SQLite: {info['installed_packages']['sqlite']}
- Git: {info['installed_packages']['git']}

This is the system you're running on. All our AI components (Dolores learning, Siobhan display, communication bridge) are operating in this environment."""

    return summary

def share_with_dolores(system_summary):
    """Send system information to Dolores"""
    
    print("📡 Sharing system information with Dolores...")
    
    task_id = ask_dolores(
        "system_update", 
        f"Arnold here. System information update for your knowledge base:\n\n{system_summary}",
        "System environment documentation"
    )
    
    print(f"✅ System info shared with Dolores (Task #{task_id})")
    return task_id

def main():
    """Main procedure"""
    print("🚀 System Information Procedure")
    print("=" * 40)
    
    # Gather information
    system_info = gather_system_info()
    
    # Format for sharing
    summary = format_system_summary(system_info)
    
    # Save to file for reference
    with open("system_info_latest.json", "w") as f:
        json.dump(system_info, f, indent=2)
    
    print("💾 System info saved to system_info_latest.json")
    
    # Share with Dolores
    task_id = share_with_dolores(summary)
    
    print("\n🎯 Procedure Complete")
    print(f"📊 System information documented and shared")
    print(f"🤖 Dolores updated with current environment details")
    
    return task_id

if __name__ == "__main__":
    main()