#!/usr/bin/env python3
import json
import os
import subprocess
from datetime import datetime

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'kb_sync_config.json')

def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

def git_sync(repo_path, commands):
    try:
        for cmd in commands:
            subprocess.run(cmd, cwd=repo_path, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Sync failed: {e}")
        return False

def main():
    config = load_config()
    sync_cfg = config['sync_config']
    
    print(f"Starting KB sync at {datetime.now()}")
    
    # Update last sync time
    sync_cfg['last_sync'] = datetime.now().isoformat()
    
    for node in sync_cfg['nodes']:
        print(f"\nSyncing node: {node['name']} ({node['host']})")
        
        if node['sync_method'] == 'git':
            commands = [
                node['sync_commands']['pre_sync'],
                node['sync_commands']['post_sync']
            ]
            if git_sync(node['kb_path'], commands):
                print("Sync completed successfully")
            else:
                print("Sync encountered errors")
    
    # Save updated config
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\nSync completed at {sync_cfg['last_sync']}")

if __name__ == '__main__':
    main()