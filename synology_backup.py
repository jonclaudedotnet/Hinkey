#!/usr/bin/env python3
"""
Synology Backup System - Persistent backup for Dolores's knowledge
"""

import os
import json
import sqlite3
import shutil
import tarfile
from pathlib import Path
from datetime import datetime
import subprocess
from typing import Dict, List, Optional

class SynologyBackup:
    """Backup Dolores's knowledge to Synology NAS"""
    
    def __init__(self, synology_config: Dict[str, str]):
        self.synology_host = synology_config.get('host', 'synology.local')
        self.synology_user = synology_config.get('user', 'jon')
        self.synology_path = synology_config.get('path', '/volume1/backups/dolores')
        self.knowledge_dir = Path('./dolores_knowledge')
        self.backup_staging = Path('./backup_staging')
        
    def create_backup_archive(self) -> str:
        """Create a complete backup archive of Dolores's knowledge"""
        
        print("📦 Creating Dolores backup archive...")
        
        # Create staging directory
        self.backup_staging.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"dolores_backup_{timestamp}"
        backup_dir = self.backup_staging / backup_name
        backup_dir.mkdir(exist_ok=True)
        
        # Copy all knowledge files
        print("  📁 Copying knowledge database...")
        if self.knowledge_dir.exists():
            shutil.copytree(self.knowledge_dir, backup_dir / 'dolores_knowledge', dirs_exist_ok=True)
        
        # Copy Claude-Dolores bridge data
        bridge_dir = Path('./claude_dolores_bridge')
        if bridge_dir.exists():
            print("  🌉 Copying bridge data...")
            shutil.copytree(bridge_dir, backup_dir / 'claude_dolores_bridge', dirs_exist_ok=True)
        
        # Copy configuration files
        print("  ⚙️  Copying configuration...")
        config_files = ['config.json', 'CLAUDE.md', 'dolores_personality.py']
        for config_file in config_files:
            if Path(config_file).exists():
                shutil.copy2(config_file, backup_dir)
        
        # Create metadata file
        metadata = {
            'backup_timestamp': timestamp,
            'backup_date': datetime.now().isoformat(),
            'knowledge_stats': self._get_knowledge_stats(),
            'backup_contents': os.listdir(backup_dir),
            'system_info': {
                'platform': 'Fedora Linux',
                'dolores_version': '1.0',
                'backup_tool_version': '1.0'
            }
        }
        
        with open(backup_dir / 'backup_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create compressed archive
        archive_path = self.backup_staging / f"{backup_name}.tar.gz"
        print(f"  🗜️  Compressing to {archive_path.name}...")
        
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(backup_dir, arcname=backup_name)
        
        # Clean up staging directory
        shutil.rmtree(backup_dir)
        
        print(f"✅ Backup archive created: {archive_path}")
        return str(archive_path)
    
    def _get_knowledge_stats(self) -> Dict:
        """Get current knowledge statistics"""
        stats = {
            'total_memories': 0,
            'database_size': 0,
            'total_files': 0
        }
        
        try:
            # Get database stats
            db_path = self.knowledge_dir / 'dolores_memory.db'
            if db_path.exists():
                stats['database_size'] = db_path.stat().st_size
                
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM knowledge")
                stats['total_memories'] = cursor.fetchone()[0]
                conn.close()
            
            # Count total files
            if self.knowledge_dir.exists():
                stats['total_files'] = sum(1 for _ in self.knowledge_dir.rglob('*') if _.is_file())
                
        except Exception as e:
            print(f"Warning: Could not get stats: {e}")
            
        return stats
    
    def sync_to_synology(self, archive_path: str) -> bool:
        """Sync backup archive to Synology NAS"""
        
        print(f"\n📡 Syncing to Synology NAS...")
        print(f"  Host: {self.synology_host}")
        print(f"  Path: {self.synology_path}")
        
        # Method 1: Using rsync (preferred)
        try:
            rsync_cmd = [
                'rsync',
                '-avz',
                '--progress',
                archive_path,
                f"{self.synology_user}@{self.synology_host}:{self.synology_path}/"
            ]
            
            print(f"  🔄 Running: {' '.join(rsync_cmd)}")
            result = subprocess.run(rsync_cmd, check=True)
            
            if result.returncode == 0:
                print("✅ Successfully synced to Synology!")
                return True
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Rsync failed: {e}")
        except FileNotFoundError:
            print("❌ Rsync not found. Trying alternative method...")
        
        # Method 2: Using SCP
        try:
            scp_cmd = [
                'scp',
                archive_path,
                f"{self.synology_user}@{self.synology_host}:{self.synology_path}/"
            ]
            
            print(f"  🔄 Trying SCP: {' '.join(scp_cmd)}")
            result = subprocess.run(scp_cmd, check=True)
            
            if result.returncode == 0:
                print("✅ Successfully copied to Synology via SCP!")
                return True
                
        except Exception as e:
            print(f"❌ SCP failed: {e}")
        
        # Method 3: Mount and copy
        print("\n💡 Alternative: Mount Synology share manually:")
        print(f"  mkdir -p ~/synology_mount")
        print(f"  mount -t cifs //{self.synology_host}/backups ~/synology_mount -o user={self.synology_user}")
        print(f"  cp {archive_path} ~/synology_mount/dolores/")
        
        return False
    
    def automated_backup(self) -> bool:
        """Perform complete automated backup"""
        
        print("🤖 DOLORES BACKUP SYSTEM")
        print("=" * 60)
        
        # Create backup
        archive_path = self.create_backup_archive()
        
        # Get archive size
        archive_size = Path(archive_path).stat().st_size / (1024 * 1024)
        print(f"\n📊 Archive size: {archive_size:.1f} MB")
        
        # Sync to Synology
        success = self.sync_to_synology(archive_path)
        
        # Keep local backup history (last 5)
        self._cleanup_old_backups()
        
        return success
    
    def _cleanup_old_backups(self, keep_count: int = 5):
        """Keep only the most recent backups locally"""
        
        if not self.backup_staging.exists():
            return
            
        backups = sorted(self.backup_staging.glob("dolores_backup_*.tar.gz"))
        
        if len(backups) > keep_count:
            for old_backup in backups[:-keep_count]:
                print(f"  🗑️  Removing old local backup: {old_backup.name}")
                old_backup.unlink()
    
    def restore_from_backup(self, backup_file: str) -> bool:
        """Restore Dolores's knowledge from a backup"""
        
        print(f"🔄 Restoring from backup: {backup_file}")
        
        if not Path(backup_file).exists():
            print(f"❌ Backup file not found: {backup_file}")
            return False
        
        try:
            # Extract to temporary directory
            temp_dir = Path('./restore_temp')
            temp_dir.mkdir(exist_ok=True)
            
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.extractall(temp_dir)
            
            # Find the backup directory
            backup_dirs = list(temp_dir.glob("dolores_backup_*"))
            if not backup_dirs:
                print("❌ Invalid backup structure")
                return False
                
            backup_dir = backup_dirs[0]
            
            # Backup current state
            if self.knowledge_dir.exists():
                backup_current = f"./dolores_knowledge_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.move(str(self.knowledge_dir), backup_current)
                print(f"  📁 Current knowledge backed up to: {backup_current}")
            
            # Restore knowledge
            if (backup_dir / 'dolores_knowledge').exists():
                shutil.move(str(backup_dir / 'dolores_knowledge'), str(self.knowledge_dir))
                print("  ✅ Knowledge database restored")
            
            # Restore bridge data
            if (backup_dir / 'claude_dolores_bridge').exists():
                bridge_dir = Path('./claude_dolores_bridge')
                if bridge_dir.exists():
                    shutil.rmtree(bridge_dir)
                shutil.move(str(backup_dir / 'claude_dolores_bridge'), str(bridge_dir))
                print("  ✅ Bridge data restored")
            
            # Restore configs
            for config_file in backup_dir.glob("*.json"):
                shutil.copy2(config_file, '.')
                print(f"  ✅ Restored: {config_file.name}")
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            print("✅ Restore completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False


# Backup configuration
def load_synology_config() -> Dict[str, str]:
    """Load Synology configuration"""
    
    config_file = Path('synology_config.json')
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    else:
        # Default configuration
        default_config = {
            'host': 'synology.local',
            'user': 'jon',
            'path': '/volume1/backups/dolores'
        }
        
        # Save default config
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        print(f"📝 Created default config: {config_file}")
        print("   Edit this file with your Synology details")
        
        return default_config


def main():
    """Main backup interface"""
    
    print("🔒 DOLORES SYNOLOGY BACKUP SYSTEM")
    print("=" * 60)
    
    # Load configuration
    config = load_synology_config()
    backup_system = SynologyBackup(config)
    
    while True:
        print("\nOptions:")
        print("1. Create and sync backup now")
        print("2. Create local backup only")
        print("3. Restore from backup")
        print("4. Configure Synology settings")
        print("5. Exit")
        
        choice = input("\nChoice (1-5): ").strip()
        
        if choice == '1':
            backup_system.automated_backup()
            
        elif choice == '2':
            archive = backup_system.create_backup_archive()
            print(f"\n📦 Local backup created: {archive}")
            
        elif choice == '3':
            backup_file = input("Path to backup file: ").strip()
            if backup_file:
                backup_system.restore_from_backup(backup_file)
                
        elif choice == '4':
            print("\nCurrent Synology configuration:")
            print(json.dumps(config, indent=2))
            print("\nEdit synology_config.json to change settings")
            
        elif choice == '5':
            print("👋 Goodbye!")
            break


if __name__ == "__main__":
    main()