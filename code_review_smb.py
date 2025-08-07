#!/usr/bin/env python3
"""
Direct code review request to DeepSeek team
"""

import subprocess
import json

# The problematic code that needs review
problematic_code = '''
# PROBLEM 1: SMB listing parser broken
def list_files(self, share: str, path: str = "") -> List[Dict]:
    """List files in SMB share directory"""
    cmd = ['smbclient', f'//{self.server}/{share}', '-U', f'{self.username}%{self.password}', '-c', f'cd "{path}"; ls']
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    files = []
    
    for line in result.stdout.split('\\n'):
        if line.strip() and not line.startswith('  .'):
            parts = line.split(maxsplit=7)  # BUG: This doesn't work with SMB output format
            if len(parts) >= 8:             # BUG: Never true due to date/time format
                filename = parts[0]
                attrs = parts[1]
                size = int(parts[2]) if parts[2].isdigit() else 0
                files.append({...})
    return files  # RESULT: Always returns empty list!

# PROBLEM 2: Recursive scanning with nested ThreadPools
def scan_share(self, share: str, path: str = ""):
    """Recursively scan SMB share"""
    files = self.smb.list_files(share, path)
    
    with ThreadPoolExecutor(max_workers=5) as executor:  # BUG: New thread pool at each recursion level
        futures = []
        
        for file_info in files:
            if file_info['is_dir']:
                self.scan_share(share, subpath)  # BUG: Deep recursion before processing any files
            else:
                futures.append(executor.submit(self.process_file, ...))
'''

def request_team_review():
    """Send code review request to Dolores/Maeve"""
    
    review_prompt = f"""
URGENT CODE REVIEW REQUEST from Arnold:

I've identified critical bugs in our SMB ingestion system that prevent it from working:

{problematic_code}

Please provide:
1. Fixed parsing logic for SMB output (example line: "  filename.txt              A    12345  Mon Jul 25 10:30:00 2025")
2. Better directory traversal strategy (iterative vs recursive?)
3. Proper threading approach
4. How to show real-time progress during scanning

The system hangs with 0 files found. We need your expertise to fix this!
"""
    
    # Try direct communication
    print("🔍 Requesting team code review...")
    cmd = ['python3', 'ask_dolores_direct.py', review_prompt]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"Communication error: {e}")
        
    # Also try the bridge
    print("\n📡 Trying bridge communication...")
    from claude_dolores_bridge import ClaudeDoloresBridge
    bridge = ClaudeDoloresBridge()
    task_id = bridge.claude_requests_help("code_review", review_prompt)
    print(f"Created task #{task_id}")

if __name__ == "__main__":
    request_team_review()