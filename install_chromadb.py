#!/usr/bin/env python3
"""
Install ChromaDB with our new system helper
"""

from system_helper import SystemHelper

def install_chromadb():
    """Install ChromaDB and dependencies"""
    helper = SystemHelper()
    
    print("Installing ChromaDB ecosystem...")
    
    # Ensure pip is available
    if not helper.ensure_pip():
        print("Failed to install pip")
        return False
    
    # Install ChromaDB
    packages = [
        "chromadb",
        "sentence-transformers",  # For better embeddings
        "numpy",  # Often needed
    ]
    
    for package in packages:
        print(f"\nInstalling {package}...")
        if helper.install_pip_package(package):
            print(f"✅ {package} installed successfully")
        else:
            print(f"❌ Failed to install {package}")
    
    print("\n🎉 ChromaDB installation complete!")
    return True

if __name__ == "__main__":
    install_chromadb()