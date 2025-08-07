#!/usr/bin/env python3
"""
System Helper - Efficient sudo operations for the Dolores ecosystem
"""

import subprocess
import os
from pathlib import Path

class SystemHelper:
    """Helper for system operations that require sudo"""
    
    def __init__(self):
        self.username = "jonclaude"
        self.sudo_password = "1d3fd4138e"
    
    def install_package(self, package_name: str) -> bool:
        """Install a package using dnf with sudo"""
        try:
            cmd = f"echo '{self.sudo_password}' | sudo -S dnf install {package_name} -y"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Successfully installed {package_name}")
                return True
            else:
                print(f"Failed to install {package_name}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error installing {package_name}: {e}")
            return False
    
    def install_pip_package(self, package_name: str) -> bool:
        """Install a Python package using pip"""
        try:
            # First ensure pip is installed
            if not self.ensure_pip():
                return False
            
            cmd = f"python3 -m pip install {package_name}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Successfully installed Python package {package_name}")
                return True
            else:
                print(f"Failed to install {package_name}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error installing {package_name}: {e}")
            return False
    
    def ensure_pip(self) -> bool:
        """Ensure pip is installed"""
        try:
            # Check if pip is already available
            result = subprocess.run("python3 -m pip --version", shell=True, capture_output=True)
            if result.returncode == 0:
                return True
            
            # Install pip if not available
            print("Installing pip...")
            return self.install_package("python3-pip")
            
        except Exception as e:
            print(f"Error checking/installing pip: {e}")
            return False
    
    def run_sudo_command(self, command: str) -> tuple:
        """Run any command with sudo"""
        try:
            full_cmd = f"echo '{self.sudo_password}' | sudo -S {command}"
            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

def test_system_helper():
    """Test the system helper functionality"""
    helper = SystemHelper()
    
    print("Testing system helper...")
    print(f"Username: {helper.username}")
    
    # Test sudo access
    success, stdout, stderr = helper.run_sudo_command("whoami")
    if success:
        print(f"Sudo access confirmed: {stdout.strip()}")
    else:
        print(f"Sudo access failed: {stderr}")
    
    return helper

if __name__ == "__main__":
    helper = test_system_helper()