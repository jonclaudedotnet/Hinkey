#!/usr/bin/env python3
"""Test SMB connection and authentication"""

import subprocess
import sys

def test_connection(server, username, password, share=None):
    """Test SMB connection with different approaches"""
    
    print(f"🔍 Testing SMB connection to {server}")
    print(f"👤 Username: {username}")
    print("-" * 50)
    
    # Test 1: List shares
    print("\n1️⃣ Testing share listing...")
    cmd = ['smbclient', '-L', f'//{server}/', '-U', f'{username}%{password}']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Share listing successful!")
        print("Available shares:")
        for line in result.stdout.split('\n'):
            if 'Disk' in line and '\t' in line:
                print(f"   - {line.split()[0]}")
    else:
        print("❌ Share listing failed!")
        print(f"Error: {result.stderr}")
        return False
    
    # Test 2: Access specific share if provided
    if share:
        print(f"\n2️⃣ Testing access to share: {share}")
        cmd = ['smbclient', f'//{server}/{share}', '-U', f'{username}%{password}', '-c', 'ls']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Share access successful!")
            print("First few entries:")
            lines = result.stdout.split('\n')[:5]
            for line in lines:
                if line.strip():
                    print(f"   {line}")
        else:
            print("❌ Share access failed!")
            print(f"Error: {result.stderr}")
    
    return True

if __name__ == "__main__":
    # SMB configuration
    server = "10.0.0.141"
    username = "jonclaude"
    password = "1D3fd4138e!!"
    
    # Test connection
    if test_connection(server, username, password, "SYNSRT"):
        print("\n✅ SMB connection test passed!")
    else:
        print("\n❌ SMB connection test failed!")
        print("\nTroubleshooting tips:")
        print("1. Check if the server is reachable: ping", server)
        print("2. Verify username and password are correct")
        print("3. Check if SMB1/SMB2/SMB3 protocol is supported")
        print("4. Try connecting from file manager first")