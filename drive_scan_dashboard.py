#!/usr/bin/env python3
"""
Enhanced Drive Scanning Dashboard
Real-time monitoring for local and network drive document scanning
"""

import os
import sys
import time
import json
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
from typing import Dict, Optional

class DriveScanDashboard:
    """Enhanced dashboard for monitoring drive scanning operations"""
    
    def __init__(self):
        self.running = True
        self.start_time = time.time()
        
        # Status file locations
        self.status_file = Path("./ingestion_status.json")
        self.cache_db = Path("./smb_nexus_cache/smb_cache_metadata.db")
        self.vector_db = Path("./chromadb_smb/chroma.sqlite3")
        
        # Initialize stats
        self.stats = {
            'scan_type': 'Unknown',
            'total_paths': 0,
            'paths_completed': 0,
            'current_path': '',
            'directories_scanned': 0,
            'files_found': 0,
            'files_cached': 0,
            'files_processed': 0,
            'files_vectorized': 0,
            'current_file': '',
            'errors': 0,
            'cache_size_mb': 0,
            'vector_db_size_mb': 0,
            'processing_rate': 0,
            'eta_minutes': 0,
            'last_activity': '',
            'memory_usage_mb': 0
        }
        
        # Color codes for terminal
        self.colors = {
            'header': '\033[95m',
            'blue': '\033[94m',
            'cyan': '\033[96m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'bold': '\033[1m',
            'underline': '\033[4m',
            'end': '\033[0m'
        }
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in MB"""
        try:
            return file_path.stat().st_size / (1024 * 1024) if file_path.exists() else 0
        except:
            return 0
    
    def get_cache_stats(self) -> Dict:
        """Get statistics from cache database"""
        cache_stats = {'files_by_share': [], 'total_cached': 0, 'cache_size_mb': 0}
        
        if not self.cache_db.exists():
            return cache_stats
            
        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()
            
            # Get file counts by share/path
            cursor.execute("""
                SELECT 
                    COALESCE(share, 'Local') as location,
                    COUNT(*) as file_count,
                    SUM(file_size) as total_size
                FROM smb_cached_files 
                GROUP BY share 
                ORDER BY file_count DESC
            """)
            
            for location, count, size in cursor.fetchall():
                cache_stats['files_by_share'].append({
                    'location': location,
                    'files': count,
                    'size_mb': (size or 0) / (1024 * 1024)
                })
                cache_stats['total_cached'] += count
                cache_stats['cache_size_mb'] += (size or 0) / (1024 * 1024)
            
            conn.close()
            
        except Exception as e:
            cache_stats['error'] = str(e)
        
        return cache_stats
    
    def get_system_info(self) -> Dict:
        """Get system resource information"""
        try:
            # Get memory usage
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            
            # Get disk usage for current directory
            disk_usage = psutil.disk_usage('.')
            disk_free_gb = disk_usage.free / (1024 * 1024 * 1024)
            
            return {
                'memory_mb': memory_mb,
                'disk_free_gb': disk_free_gb,
                'cpu_percent': psutil.cpu_percent(interval=0.1)
            }
        except ImportError:
            return {'memory_mb': 0, 'disk_free_gb': 0, 'cpu_percent': 0}
    
    def read_status_file(self):
        """Read status from scanning process"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    status = json.load(f)
                    
                # Update our stats with the latest data
                self.stats.update(status)
                
                # Determine scan type based on current activity
                if 'smb' in str(status.get('current_file', '')).lower():
                    self.stats['scan_type'] = 'Network (SMB)'
                elif status.get('current_file'):
                    self.stats['scan_type'] = 'Local Drive'
                    
            except Exception as e:
                self.stats['status_error'] = str(e)
    
    def calculate_progress_metrics(self):
        """Calculate progress and performance metrics"""
        elapsed = time.time() - self.start_time
        
        if elapsed > 0:
            # Processing rates
            if self.stats['files_processed'] > 0:
                self.stats['processing_rate'] = self.stats['files_processed'] / elapsed
                
            # ETA calculation (rough estimate)
            if self.stats['processing_rate'] > 0 and self.stats['files_found'] > 0:
                remaining = max(0, self.stats['files_found'] - self.stats['files_processed'])
                self.stats['eta_minutes'] = remaining / (self.stats['processing_rate'] * 60)
        
        # Update last activity
        if self.stats.get('current_file'):
            file_name = Path(self.stats['current_file']).name
            self.stats['last_activity'] = f"Processing: {file_name}"
        elif self.stats.get('current_directory'):
            self.stats['last_activity'] = f"Scanning: {self.stats['current_directory']}"
        else:
            self.stats['last_activity'] = "Initializing..."
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m {int(seconds%60)}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
    
    def format_size(self, size_mb: float) -> str:
        """Format file size in human readable format"""
        if size_mb < 1:
            return f"{size_mb*1024:.0f} KB"
        elif size_mb < 1024:
            return f"{size_mb:.1f} MB"
        else:
            return f"{size_mb/1024:.1f} GB"
    
    def get_progress_bar(self, current: int, total: int, width: int = 40) -> str:
        """Generate a progress bar"""
        if total == 0:
            return "█" * width
        
        filled = int(width * current / total)
        bar = "█" * filled + "░" * (width - filled)
        percentage = (current / total) * 100
        return f"{bar} {percentage:.1f}%"
    
    def display_header(self):
        """Display dashboard header"""
        elapsed = time.time() - self.start_time
        
        print(f"{self.colors['bold']}{self.colors['cyan']}🖥️  DRIVE SCANNING DASHBOARD{self.colors['end']}")
        print("=" * 70)
        print(f"Started: {datetime.fromtimestamp(self.start_time).strftime('%H:%M:%S')}")
        print(f"Runtime: {self.format_duration(elapsed)}")
        print(f"Scan Type: {self.colors['green']}{self.stats['scan_type']}{self.colors['end']}")
        print("=" * 70)
    
    def display_scan_progress(self):
        """Display scanning progress"""
        print(f"\n{self.colors['bold']}📂 SCAN PROGRESS{self.colors['end']}")
        print("-" * 50)
        
        # Files overview
        files_found = self.stats['files_found']
        files_processed = self.stats['files_processed']
        files_vectorized = self.stats['files_vectorized']
        
        print(f"Files Found:      {self.colors['cyan']}{files_found:,}{self.colors['end']}")
        print(f"Files Processed:  {self.colors['green']}{files_processed:,}{self.colors['end']}")
        print(f"Files Indexed:    {self.colors['blue']}{files_vectorized:,}{self.colors['end']}")
        print(f"Errors:          {self.colors['red'] if self.stats['errors'] > 0 else self.colors['green']}{self.stats['errors']:,}{self.colors['end']}")
        
        # Progress bar
        if files_found > 0:
            progress_bar = self.get_progress_bar(files_processed, files_found)
            print(f"\nProgress: {progress_bar}")
    
    def display_performance_metrics(self):
        """Display performance and system metrics"""
        print(f"\n{self.colors['bold']}⚡ PERFORMANCE{self.colors['end']}")
        print("-" * 50)
        
        # Processing rates
        print(f"Processing Rate:  {self.stats['processing_rate']:.1f} files/sec")
        print(f"Directories:     {self.stats['directories_scanned']:,}")
        
        # Storage info
        cache_size = self.get_file_size_mb(self.cache_db)
        vector_size = self.get_file_size_mb(self.vector_db)
        
        print(f"Cache Size:      {self.format_size(cache_size)}")
        print(f"Vector DB:       {self.format_size(vector_size)}")
        
        # ETA
        if self.stats['eta_minutes'] > 0:
            print(f"ETA:            {self.format_duration(self.stats['eta_minutes'] * 60)}")
    
    def display_current_activity(self):
        """Display current scanning activity"""
        print(f"\n{self.colors['bold']}🔄 CURRENT ACTIVITY{self.colors['end']}")
        print("-" * 50)
        
        if self.stats['current_file']:
            file_name = Path(self.stats['current_file']).name
            print(f"Processing: {self.colors['yellow']}{file_name[:45]}...{self.colors['end']}")
        
        if self.stats.get('current_directory'):
            dir_path = self.stats['current_directory']
            print(f"Directory:  {self.colors['cyan']}{dir_path[:45]}...{self.colors['end']}")
        
        # Show last update time
        if self.stats.get('last_update'):
            last_update = datetime.fromtimestamp(self.stats['last_update'])
            time_diff = datetime.now() - last_update
            if time_diff.total_seconds() < 60:
                status_color = self.colors['green']
            else:
                status_color = self.colors['yellow']
            
            print(f"Last Update: {status_color}{last_update.strftime('%H:%M:%S')}{self.colors['end']}")
    
    def display_location_breakdown(self):
        """Display breakdown by scan locations"""
        cache_stats = self.get_cache_stats()
        
        if cache_stats['files_by_share']:
            print(f"\n{self.colors['bold']}📍 LOCATIONS SCANNED{self.colors['end']}")
            print("-" * 50)
            
            for location_info in cache_stats['files_by_share'][:5]:
                location = location_info['location']
                files = location_info['files']
                size = self.format_size(location_info['size_mb'])
                print(f"{location[:20]:20} {files:>6,} files ({size})")
    
    def display_system_resources(self):
        """Display system resource usage"""
        sys_info = self.get_system_info()
        
        print(f"\n{self.colors['bold']}💻 SYSTEM RESOURCES{self.colors['end']}")
        print("-" * 50)
        print(f"Memory Usage:    {sys_info['memory_mb']:.0f} MB")
        print(f"CPU Usage:       {sys_info['cpu_percent']:.1f}%")
        print(f"Disk Free:       {sys_info['disk_free_gb']:.1f} GB")
    
    def display_dashboard(self):
        """Display the complete dashboard"""
        self.clear_screen()
        
        # Main sections
        self.display_header()
        self.display_scan_progress()
        self.display_performance_metrics()
        self.display_current_activity()
        self.display_location_breakdown()
        self.display_system_resources()
        
        # Footer
        print(f"\n{self.colors['bold']}{'=' * 70}{self.colors['end']}")
        print(f"{self.colors['cyan']}Press Ctrl+C to stop monitoring (scanning continues){self.colors['end']}")
        print(f"Auto-refresh: every 2 seconds")
    
    def monitor_loop(self):
        """Main monitoring loop with enhanced error handling"""
        print(f"{self.colors['cyan']}🚀 Starting Drive Scan Dashboard...{self.colors['end']}")
        
        # Initial delay to let scanning start
        time.sleep(1)
        
        while self.running:
            try:
                # Update all data
                self.read_status_file()
                self.calculate_progress_metrics()
                
                # Display dashboard
                self.display_dashboard()
                
                # Wait before next update
                time.sleep(2)
                
            except KeyboardInterrupt:
                self.running = False
                self.clear_screen()
                print(f"\n{self.colors['green']}📊 Dashboard stopped.{self.colors['end']}")
                print(f"{self.colors['cyan']}Drive scanning continues in background.{self.colors['end']}")
                break
                
            except Exception as e:
                print(f"{self.colors['red']}Dashboard error: {e}{self.colors['end']}")
                time.sleep(3)

def start_local_drive_scan(scan_paths: list):
    """Start scanning local drives with dashboard"""
    print(f"🔍 Starting local drive scan...")
    print(f"📁 Paths: {', '.join(scan_paths)}")
    
    # Create a modified version of nexus_document_ingestion for local paths
    scan_command = [
        sys.executable, 
        "nexus_document_ingestion.py"
    ]
    
    # Start scanning process in background
    try:
        process = subprocess.Popen(
            scan_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"✅ Scan process started (PID: {process.pid})")
        
        # Give it time to initialize
        time.sleep(2)
        
        # Start dashboard
        dashboard = DriveScanDashboard()
        dashboard.monitor_loop()
        
    except Exception as e:
        print(f"❌ Failed to start scanning: {e}")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "monitor":
            # Just monitor existing scan
            dashboard = DriveScanDashboard()
            dashboard.monitor_loop()
            
        elif sys.argv[1] == "local":
            # Start local drive scan
            default_paths = [
                "/home/jonclaude/Documents",
                "/home/jonclaude/Projects", 
                "/home/jonclaude/agents"
            ]
            start_local_drive_scan(default_paths)
            
        else:
            print("Usage:")
            print("  python3 drive_scan_dashboard.py monitor  # Monitor existing scan")
            print("  python3 drive_scan_dashboard.py local    # Scan local drives")
    else:
        # Default: just monitor
        dashboard = DriveScanDashboard()
        dashboard.monitor_loop()

if __name__ == "__main__":
    main()