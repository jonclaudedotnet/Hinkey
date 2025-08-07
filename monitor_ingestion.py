#!/usr/bin/env python3
"""Simple ingestion monitor - shows current status"""

import json
import time
import os
from pathlib import Path

def monitor():
    status_file = Path("./ingestion_status.json")
    
    print("📊 SMB INGESTION MONITOR")
    print("=" * 40)
    print("Watching for status updates...")
    print("=" * 40)
    
    last_stats = {}
    
    while True:
        try:
            if status_file.exists():
                with open(status_file, 'r') as f:
                    stats = json.load(f)
                
                # Clear screen for clean display
                os.system('clear')
                
                print("📊 SMB INGESTION MONITOR")
                print("=" * 40)
                print(f"Current Share: {stats.get('current_share', 'None')}")
                print(f"Shares: {stats.get('shares_scanned', 0)}/{stats.get('shares_found', 0)}")
                print("-" * 40)
                print(f"Files Found:     {stats.get('files_found', 0):,}")
                print(f"Files Cached:    {stats.get('files_cached', 0):,}")
                print(f"Files Processed: {stats.get('files_processed', 0):,}")
                print(f"Files Indexed:   {stats.get('files_vectorized', 0):,}")
                print(f"Directories:     {stats.get('directories_scanned', 0):,}")
                print(f"Errors:          {stats.get('errors', 0):,}")
                print("-" * 40)
                
                current_file = stats.get('current_file', '')
                if current_file:
                    print(f"Processing: {Path(current_file).name}")
                else:
                    print("Status: Scanning directories...")
                
                # Show what changed
                if last_stats:
                    new_files = stats.get('files_found', 0) - last_stats.get('files_found', 0)
                    if new_files > 0:
                        print(f"\n✨ Found {new_files} new files!")
                
                last_stats = stats.copy()
                
            else:
                print("Waiting for ingestion to start...")
            
            time.sleep(1)  # Update every second
            
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    monitor()