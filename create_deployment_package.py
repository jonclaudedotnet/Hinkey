#!/usr/bin/env python3
"""
Create Deployment Package - Package the entire Dolores ecosystem into a portable zip
"""

import zipfile
import os
from pathlib import Path
from datetime import datetime
import json

def create_deployment_package():
    """Create a complete deployment package of the Dolores ecosystem"""
    
    print("📦 Creating Dolores Ecosystem Deployment Package...")
    
    # Package info
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"dolores_ecosystem_v2_{timestamp}.zip"
    
    # Files to include in deployment
    core_files = [
        # Core system files
        'dolores_core.py',
        'dolores_host.py',
        'dolores_personality.py',
        'claude_dolores_bridge.py',
        'dolores_clean_display.py',
        
        # Training and conversation system
        'podcast_training_data_structure.py',
        'podcast_conversation_flows.py',
        'dolores_training_framework.py',
        
        # Database and storage
        'dolores_chromadb_upgrade.py',
        'document_processor.py',
        'synology_backup.py',
        
        # System management
        'startup_procedure.py',
        'shutdown_procedure.py',
        'system_helper.py',
        
        # Assistant systems
        'guide_assistant.py',
        
        # Documentation
        'CLAUDE.md',
        'AI_MEETING_PARTICIPANT_BIBLE.md',
        
        # Configuration (without sensitive data)
        'config.json'
    ]
    
    # Directories to include
    directories_to_include = [
        'dolores_knowledge',  # Knowledge base and conversations
        'claude_dolores_bridge'  # Communication logs
    ]
    
    # Create the deployment package
    with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        
        # Add core files
        print("📄 Adding core system files...")
        for file_path in core_files:
            if Path(file_path).exists():
                zipf.write(file_path)
                print(f"   ✅ {file_path}")
            else:
                print(f"   ⚠️  Missing: {file_path}")
        
        # Add directories
        print("📁 Adding knowledge and data directories...")
        for dir_path in directories_to_include:
            if Path(dir_path).exists():
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path)
                print(f"   ✅ {dir_path}/ (with all contents)")
            else:
                print(f"   ⚠️  Missing directory: {dir_path}")
        
        # Create deployment manifest
        manifest = {
            "package_name": "Dolores Ecosystem v2",
            "created": datetime.now().isoformat(),
            "creator": "Guide (Claude) with JC",
            "version": "2.0",
            "description": "Complete three-AI podcast hosting ecosystem with ChromaDB, training framework, and persistent memory",
            "components": {
                "dolores": "Primary podcast host AI (DeepSeek)",
                "guide": "System architect and coordinator (Claude)",
                "guide_assistant": "Technical helper (DeepSeek)",
                "communication_bridge": "AI-to-AI communication system",
                "knowledge_base": "189+ entries with ChromaDB semantic search",
                "training_system": "Skills, conversation flows, practice framework",
                "ui_system": "Clean display with real-time updates",
                "backup_system": "Synology NAS integration",
                "recovery_system": "Complete startup/shutdown procedures"
            },
            "deployment_requirements": [
                "Python 3.13+",
                "DeepSeek API key",
                "ChromaDB dependencies",
                "Linux environment (tested on Fedora)"
            ],
            "quick_start": [
                "1. Extract all files to target directory",
                "2. Update config.json with your DeepSeek API key",
                "3. Run: python3 startup_procedure.py",
                "4. System will auto-initialize all components"
            ],
            "key_commands": {
                "startup": "python3 startup_procedure.py",
                "status": "python3 startup_procedure.py status", 
                "shutdown": "python3 shutdown_procedure.py",
                "train_dolores": "python3 dolores_training_framework.py",
                "backup": "python3 synology_backup.py"
            }
        }
        
        # Add manifest to package
        manifest_json = json.dumps(manifest, indent=2)
        zipf.writestr('DEPLOYMENT_MANIFEST.json', manifest_json)
        print("   ✅ DEPLOYMENT_MANIFEST.json")
        
        # Add README for deployment
        readme_content = f"""# Dolores Ecosystem v2 - Deployment Package

## Quick Start
1. Extract all files to your target directory
2. Update `config.json` with your DeepSeek API key
3. Run: `python3 startup_procedure.py`
4. The system will auto-initialize all components

## What's Included
- Complete three-AI ecosystem (Dolores, Guide, Guide's Assistant)
- ChromaDB semantic search with 189+ knowledge entries  
- Training framework with podcast hosting skills
- Clean UI with real-time communication
- Automated backup system (Synology compatible)
- Complete startup/shutdown procedures

## System Requirements
- Python 3.13+
- DeepSeek API key
- Linux environment (tested on Fedora)

## Key Commands
- `python3 startup_procedure.py` - Full system startup
- `python3 startup_procedure.py status` - Check system status
- `python3 shutdown_procedure.py` - Graceful shutdown
- `python3 dolores_training_framework.py` - Train Dolores

## Documentation
See `CLAUDE.md` for complete system documentation.

Package created: {datetime.now().isoformat()}
Creator: Guide (Claude) with JC
"""
        
        zipf.writestr('README.md', readme_content)
        print("   ✅ README.md")
    
    # Get package stats
    package_size = Path(package_name).stat().st_size
    size_mb = package_size / (1024 * 1024)
    
    print(f"\n🎉 DEPLOYMENT PACKAGE CREATED")
    print("=" * 50)
    print(f"📦 Package: {package_name}")
    print(f"📏 Size: {size_mb:.1f} MB")
    print(f"📅 Created: {datetime.now().isoformat()}")
    
    print(f"\n✅ COMPLETE PORTABLE ECOSYSTEM")
    print("   - All three AIs (Dolores, Guide, Guide's Assistant)")
    print("   - Complete knowledge base with ChromaDB")
    print("   - Training framework and conversation flows")
    print("   - Startup/shutdown procedures")
    print("   - Communication bridge and UI")
    print("   - Documentation and deployment instructions")
    
    print(f"\n🚀 DEPLOYMENT READY")
    print("   Extract anywhere and run startup_procedure.py")
    print("   Fully self-contained and portable!")
    
    return package_name

if __name__ == "__main__":
    package = create_deployment_package()