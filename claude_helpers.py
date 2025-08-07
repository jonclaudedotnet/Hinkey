#!/usr/bin/env python3
"""
Claude Helper Functions - Easy interface for Claude to work with Dolores
"""

from claude_dolores_bridge import ask_dolores, wait_for_dolores, check_dolores_result
import time

def dolores_help(task_type: str, content: str, timeout: int = 30) -> str:
    """Ask Dolores for help and wait for response"""
    task_id = ask_dolores(task_type, content)
    result = wait_for_dolores(task_id, timeout)
    
    if result:
        return result
    else:
        return f"Dolores is still working on task #{task_id}. Check back later."

def dolores_analyze(content: str) -> str:
    """Have Dolores analyze content"""
    return dolores_help("analyze", content)

def dolores_code(task: str) -> str:
    """Have Dolores help with coding"""
    return dolores_help("code", task)

def dolores_research(query: str) -> str:
    """Have Dolores research something"""
    return dolores_help("research", query)

def dolores_process_transcript(filepath: str) -> str:
    """Have Dolores process a transcript file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return dolores_help("transcript_analysis", content)
    except FileNotFoundError:
        return f"File not found: {filepath}"

# Viewer mode functions
def open_dolores_window():
    """Open the professional Dolores Studio UI for podcast production"""
    import subprocess
    import os
    
    try:
        print("🎙️ Opening Dolores Studio UI...")
        subprocess.Popen([
            "python3", "dolores_studio_ui.py"
        ], cwd=os.getcwd())
        return "🎙️ Dolores Studio UI opened - Professional two-panel interface ready for podcast production"
    except Exception as e:
        print(f"Could not start Studio UI: {e}")
        # Fallback to simple viewer
        try:
            subprocess.Popen([
                "python3", "dolores_gtk_viewer.py"
            ], cwd=os.getcwd())
            return "Fallback: Simple GTK viewer opened"
        except Exception as e2:
            return f"Failed to open any viewer. Try: python3 dolores_studio_ui.py"

def open_dolores_terminal():
    """Open terminal viewer for Dolores responses"""
    import subprocess
    import os
    
    try:
        print("Opening Dolores Terminal Viewer...")
        subprocess.Popen([
            "gnome-terminal", "--", "python3", "dolores_viewer.py"
        ], cwd=os.getcwd())
        return "Terminal viewer opened"
    except Exception as e:
        try:
            # Try xterm as fallback
            subprocess.Popen([
                "xterm", "-e", "python3", "dolores_viewer.py"
            ], cwd=os.getcwd())
            return "Terminal viewer opened (xterm)"
        except Exception as e2:
            return f"Could not open terminal viewer. Run manually: python3 dolores_viewer.py"

# Quick test function
def test_dolores():
    """Test if Dolores is responding"""
    response = dolores_help("test", "Are you working?", timeout=10)
    return response

if __name__ == "__main__":
    print("Testing Dolores connection...")
    result = test_dolores()
    print(f"Dolores says: {result}")