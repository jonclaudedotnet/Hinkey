#!/usr/bin/env python3
"""Quick test to debug SMB listing"""

import subprocess

def test_listing():
    cmd = [
        'smbclient', '//10.0.0.141/SYNSRT',
        '-U', 'jonclaude%1D3fd4138e!!',
        '-c', 'ls'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("RAW OUTPUT:")
    print(result.stdout)
    print("\nPARSING TEST:")
    
    for line in result.stdout.split('\n'):
        if line.strip() and not line.startswith('  .'):
            print(f"Line: {repr(line)}")
            parts = line.split(maxsplit=7)
            print(f"Parts ({len(parts)}): {parts[:3] if len(parts) >= 3 else parts}")
            print()

if __name__ == "__main__":
    test_listing()