#!/usr/bin/env python3
"""
Real-time Ingestion Dashboard for SMB Document Scanning
Provides live status updates with a clean terminal interface
"""

import os
import sys
import time
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
import subprocess
import json

class IngestionDashboard:
    """Real-time monitoring dashboard for document ingestion"""
    
    def __init__(self):
        self.running = True
        self.cache_db = Path("./smb_nexus_cache/smb_cache_metadata.db")
        self.status_file = Path("./ingestion_status.json")
        self.start_time = time.time()
        
        # Stats tracking
        self.stats = {
            'shares_found': 0,
            'shares_scanned': 0,
            'current_share': '',
            'directories_scanned': 0,
            'files_found': 0,
            'files_cached': 0,
            'files_processed': 0,
            'files_vectorized': 0,
            'current_file': '',
            'errors': 0,
            'cache_size_mb': 0,
            'rate_files_per_min': 0,
            'eta_minutes': 0
        }
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_cache_stats(self):
        """Get statistics from cache database"""
        if not self.cache_db.exists():
            return
            
        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()
            
            # Get file counts
            cursor.execute("SELECT COUNT(*) FROM smb_cached_files")
            self.stats['files_cached'] = cursor.fetchone()[0]
            
            # Get total cache size
            cursor.execute("SELECT SUM(file_size) FROM smb_cached_files")
            total_size = cursor.fetchone()[0] or 0
            self.stats['cache_size_mb'] = total_size / (1024 * 1024)
            
            # Get current processing info
            cursor.execute("""
                SELECT share, COUNT(*) 
                FROM smb_cached_files 
                GROUP BY share 
                ORDER BY COUNT(*) DESC
            """)
            share_counts = cursor.fetchall()
            
            conn.close()
            
            return share_counts
            
        except Exception:
            pass
    
    def read_status_file(self):
        """Read status from ingestion process"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    status = json.load(f)
                    self.stats.update(status)
            except Exception:
                pass
    
    def calculate_rates(self):
        """Calculate processing rates and ETA"""
        elapsed = time.time() - self.start_time
        if elapsed > 0 and self.stats['files_processed'] > 0:
            self.stats['rate_files_per_min'] = (self.stats['files_processed'] / elapsed) * 60
            
            # Rough ETA based on typical file counts
            if self.stats['rate_files_per_min'] > 0:
                estimated_total = self.stats['files_found'] * 10  # Conservative estimate
                remaining = estimated_total - self.stats['files_processed']
                self.stats['eta_minutes'] = remaining / self.stats['rate_files_per_min']
    
    def display_dashboard(self):
        """Display the dashboard"""
        self.clear_screen()
        
        # Header
        print("🌐 SMB DOCUMENT INGESTION DASHBOARD")
        print("=" * 60)
        print(f"Started: {datetime.fromtimestamp(self.start_time).strftime('%H:%M:%S')}")
        print(f"Elapsed: {self.format_duration(time.time() - self.start_time)}")
        print("=" * 60)
        
        # Share Progress
        print("\n📁 SHARE PROGRESS")
        print("-" * 40)
        if self.stats['current_share']:
            print(f"Current Share: {self.stats['current_share']}")
        print(f"Shares Scanned: {self.stats['shares_scanned']}/{self.stats['shares_found']}")
        
        # File Statistics
        print("\n📊 FILE STATISTICS")
        print("-" * 40)
        print(f"Files Found:      {self.stats['files_found']:,}")
        print(f"Files Cached:     {self.stats['files_cached']:,}")
        print(f"Files Processed:  {self.stats['files_processed']:,}")
        print(f"Files Indexed:    {self.stats['files_vectorized']:,}")
        print(f"Errors:          {self.stats['errors']:,}")
        
        # Performance
        print("\n⚡ PERFORMANCE")
        print("-" * 40)
        print(f"Processing Rate:  {self.stats['rate_files_per_min']:.1f} files/min")
        print(f"Cache Size:      {self.stats['cache_size_mb']:.1f} MB")
        print(f"Directories:     {self.stats['directories_scanned']:,}")
        
        # Current Activity
        print("\n🔄 CURRENT ACTIVITY")
        print("-" * 40)
        if self.stats['current_file']:
            file_name = Path(self.stats['current_file']).name
            print(f"Processing: {file_name[:50]}...")
        else:
            print("Scanning directories...")
        
        # Share breakdown
        share_counts = self.get_cache_stats()
        if share_counts:
            print("\n📈 SHARE BREAKDOWN")
            print("-" * 40)
            for share, count in share_counts[:5]:
                print(f"{share:20} {count:,} files")
        
        # ETA
        if self.stats['eta_minutes'] > 0:
            print(f"\n⏱️  Estimated Time Remaining: {self.format_duration(self.stats['eta_minutes'] * 60)}")
        
        # Footer
        print("\n" + "=" * 60)
        print("Press Ctrl+C to stop monitoring (ingestion continues)")
    
    def format_duration(self, seconds):
        """Format duration in human readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self.read_status_file()
                self.get_cache_stats()
                self.calculate_rates()
                self.display_dashboard()
                time.sleep(2)  # Update every 2 seconds
            except KeyboardInterrupt:
                self.running = False
                print("\n\n📊 Dashboard stopped. Ingestion continues in background.")
                break
            except Exception as e:
                print(f"Dashboard error: {e}")
                time.sleep(5)

def start_ingestion_with_dashboard():
    """Start ingestion process with dashboard monitoring"""
    print("🚀 Starting SMB Document Ingestion with Dashboard...")
    
    # Start ingestion in background
    ingestion_process = subprocess.Popen(
        [sys.executable, "smb_nexus_ingestion.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give it a moment to start
    time.sleep(2)
    
    # Start dashboard
    dashboard = IngestionDashboard()
    
    try:
        dashboard.monitor_loop()
    finally:
        # Check if ingestion is still running
        if ingestion_process.poll() is None:
            print("\n✅ Ingestion continues in background")
            print(f"   Process ID: {ingestion_process.pid}")
        else:
            print("\n⚠️ Ingestion process completed or stopped")

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        # Just monitor existing process
        dashboard = IngestionDashboard()
        dashboard.monitor_loop()
    else:
        # Start new ingestion with monitoring
        start_ingestion_with_dashboard()

if __name__ == "__main__":
    main()