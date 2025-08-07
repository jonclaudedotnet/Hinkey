#!/usr/bin/env python3
"""
Batch Copy System with Smart Organization
Based on AI Team Architecture Recommendations
"""

import os
import shutil
import sqlite3
import hashlib
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import threading
from dataclasses import dataclass
from enum import Enum

# File type categories for organization
class FileCategory(Enum):
    DOCUMENTS = "documents"
    CODE = "code"
    IMAGES = "images"
    VIDEOS = "videos"
    AUDIO = "audio"
    ARCHIVES = "archives"
    CONFIG = "config"
    DATA = "data"
    BINARIES = "binaries"
    UNKNOWN = "unknown"

@dataclass
class MountPoint:
    """Represents a mounted drive"""
    path: str
    label: str
    total_size: int
    available_size: int
    is_network: bool
    
class FileOrganizer:
    """Determines file organization based on type and size"""
    
    # File extension mappings
    CATEGORY_MAPPINGS = {
        FileCategory.DOCUMENTS: {'.pdf', '.doc', '.docx', '.txt', '.md', '.odt', '.rtf'},
        FileCategory.CODE: {'.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.rb', '.go', '.rs'},
        FileCategory.IMAGES: {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico'},
        FileCategory.VIDEOS: {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'},
        FileCategory.AUDIO: {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.wma', '.aac'},
        FileCategory.ARCHIVES: {'.zip', '.rar', '.tar', '.gz', '.7z', '.bz2', '.xz'},
        FileCategory.CONFIG: {'.json', '.yaml', '.yml', '.ini', '.conf', '.cfg', '.toml'},
        FileCategory.DATA: {'.csv', '.xml', '.sql', '.db', '.sqlite'},
        FileCategory.BINARIES: {'.exe', '.dll', '.so', '.dylib', '.bin', '.app'},
    }
    
    # Size limits for scanning eligibility (in MB)
    SIZE_LIMITS = {
        FileCategory.DOCUMENTS: 50,  # 50MB max for documents
        FileCategory.CODE: 10,       # 10MB max for code files
        FileCategory.CONFIG: 5,      # 5MB max for config
        FileCategory.DATA: 100,      # 100MB max for data files
    }
    
    @classmethod
    def categorize_file(cls, file_path: Path) -> FileCategory:
        """Determine file category based on extension"""
        ext = file_path.suffix.lower()
        
        for category, extensions in cls.CATEGORY_MAPPINGS.items():
            if ext in extensions:
                return category
                
        return FileCategory.UNKNOWN
    
    @classmethod
    def is_scannable(cls, file_path: Path, size_bytes: int) -> bool:
        """Determine if file should be scanned based on type and size"""
        category = cls.categorize_file(file_path)
        
        # Skip binaries and unknown files
        if category in [FileCategory.BINARIES, FileCategory.UNKNOWN]:
            return False
            
        # Check size limits
        size_mb = size_bytes / (1024 * 1024)
        limit = cls.SIZE_LIMITS.get(category, float('inf'))
        
        return size_mb <= limit

class BatchCopyDatabase:
    """Database for tracking copy progress and file metadata"""
    
    def __init__(self, db_path: str = "batch_copy_progress.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self._init_database()
        
    def _init_database(self):
        """Initialize database schema"""
        with self.lock:
            cursor = self.conn.cursor()
            
            # Files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_path TEXT UNIQUE,
                    dest_path TEXT,
                    file_hash TEXT,
                    file_size INTEGER,
                    file_category TEXT,
                    is_scannable BOOLEAN,
                    status TEXT DEFAULT 'pending',
                    batch_id INTEGER,
                    copied_timestamp TEXT,
                    error_message TEXT
                )
            ''')
            
            # Batches table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_mount TEXT,
                    dest_mount TEXT,
                    batch_size INTEGER,
                    status TEXT DEFAULT 'pending',
                    started_timestamp TEXT,
                    completed_timestamp TEXT,
                    files_count INTEGER,
                    files_copied INTEGER,
                    total_size_bytes INTEGER
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON files(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_batch ON files(batch_id)')
            
            self.conn.commit()
    
    def record_file(self, source_path: str, dest_path: str, file_size: int, 
                   category: FileCategory, is_scannable: bool) -> int:
        """Record a file to be copied"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO files 
                (source_path, dest_path, file_size, file_category, is_scannable)
                VALUES (?, ?, ?, ?, ?)
            ''', (source_path, dest_path, file_size, category.value, is_scannable))
            self.conn.commit()
            return cursor.lastrowid
    
    def get_pending_files(self, limit: int = 1000) -> List[Dict]:
        """Get next batch of pending files"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, source_path, dest_path, file_size, file_category
                FROM files
                WHERE status = 'pending'
                LIMIT ?
            ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_file_status(self, file_id: int, status: str, error_msg: str = None):
        """Update file copy status"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE files 
                SET status = ?, error_message = ?, copied_timestamp = ?
                WHERE id = ?
            ''', (status, error_msg, datetime.now().isoformat(), file_id))
            self.conn.commit()
    
    def get_progress_stats(self) -> Dict:
        """Get overall progress statistics"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_files,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_files,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_files,
                    SUM(file_size) as total_size,
                    SUM(CASE WHEN status = 'completed' THEN file_size ELSE 0 END) as completed_size,
                    COUNT(DISTINCT file_category) as category_count
                FROM files
            ''')
            
            result = cursor.fetchone()
            return {
                'total_files': result[0] or 0,
                'completed_files': result[1] or 0,
                'failed_files': result[2] or 0,
                'total_size': result[3] or 0,
                'completed_size': result[4] or 0,
                'category_count': result[5] or 0,
                'progress_percent': (result[1] / result[0] * 100) if result[0] > 0 else 0
            }

class MountManager:
    """Manages mounted drives and paths"""
    
    @staticmethod
    def get_available_mounts() -> List[MountPoint]:
        """Detect available mount points"""
        mounts = []
        
        # Check common mount locations
        mount_dirs = [
            '/home/jonclaude/mnt',
            '/mnt',
            '/media'
        ]
        
        for mount_dir in mount_dirs:
            if not os.path.exists(mount_dir):
                continue
                
            for entry in os.listdir(mount_dir):
                path = os.path.join(mount_dir, entry)
                if os.path.ismount(path) or os.path.isdir(path):
                    try:
                        stat = os.statvfs(path)
                        total_size = stat.f_blocks * stat.f_frsize
                        available_size = stat.f_available * stat.f_frsize
                        
                        # Check if network mount
                        is_network = any(keyword in path.lower() 
                                       for keyword in ['searobin', 'synology', 'smb', 'nfs'])
                        
                        mounts.append(MountPoint(
                            path=path,
                            label=os.path.basename(path),
                            total_size=total_size,
                            available_size=available_size,
                            is_network=is_network
                        ))
                    except Exception as e:
                        print(f"Error checking mount {path}: {e}")
                        
        return mounts

class BatchCopyController:
    """Main controller for batch copy operations"""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.db = BatchCopyDatabase()
        self.mount_manager = MountManager()
        self.is_running = False
        self.current_batch = 0
        
    def show_mount_selection(self) -> Tuple[str, str]:
        """Interactive mount selection"""
        mounts = self.mount_manager.get_available_mounts()
        
        if not mounts:
            print("❌ No mount points found!")
            return None, None
            
        print("\n📁 Available Mount Points:")
        print("=" * 60)
        for i, mount in enumerate(mounts, 1):
            size_gb = mount.total_size / (1024**3)
            avail_gb = mount.available_size / (1024**3)
            mount_type = "Network" if mount.is_network else "Local"
            
            print(f"{i}. {mount.label} ({mount_type})")
            print(f"   Path: {mount.path}")
            print(f"   Size: {size_gb:.1f} GB total, {avail_gb:.1f} GB available")
            
        # Get user selection
        try:
            source_idx = int(input("\n🔹 Select SOURCE mount (number): ")) - 1
            dest_idx = int(input("🔸 Select DESTINATION mount (number): ")) - 1
            
            if 0 <= source_idx < len(mounts) and 0 <= dest_idx < len(mounts):
                return mounts[source_idx].path, mounts[dest_idx].path
            else:
                print("❌ Invalid selection!")
                return None, None
        except ValueError:
            print("❌ Invalid input!")
            return None, None
    
    def scan_source_directory(self, source_path: str, dest_base: str):
        """Scan source directory and prepare copy list"""
        print(f"\n🔍 Scanning source: {source_path}")
        
        file_count = 0
        scannable_count = 0
        
        for root, dirs, files in os.walk(source_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                source_file = os.path.join(root, file)
                
                try:
                    # Get file info
                    stat = os.stat(source_file)
                    file_size = stat.st_size
                    
                    # Determine category and destination
                    file_path = Path(source_file)
                    category = FileOrganizer.categorize_file(file_path)
                    is_scannable = FileOrganizer.is_scannable(file_path, file_size)
                    
                    # Build organized destination path
                    rel_path = os.path.relpath(source_file, source_path)
                    if is_scannable:
                        dest_file = os.path.join(dest_base, "scannable", category.value, rel_path)
                    else:
                        dest_file = os.path.join(dest_base, "non_scannable", category.value, rel_path)
                    
                    # Record in database
                    self.db.record_file(source_file, dest_file, file_size, category, is_scannable)
                    
                    file_count += 1
                    if is_scannable:
                        scannable_count += 1
                        
                    if file_count % 100 == 0:
                        print(f"   📊 Scanned {file_count} files ({scannable_count} scannable)...")
                        
                except Exception as e:
                    print(f"   ⚠️ Error scanning {file}: {e}")
                    
        print(f"\n✅ Scan complete: {file_count} files found ({scannable_count} scannable)")
        return file_count
    
    def copy_batch(self) -> bool:
        """Copy one batch of files"""
        pending_files = self.db.get_pending_files(self.batch_size)
        
        if not pending_files:
            return False
            
        self.current_batch += 1
        print(f"\n📦 Processing batch {self.current_batch} ({len(pending_files)} files)")
        
        success_count = 0
        fail_count = 0
        
        for file_info in pending_files:
            source = file_info['source_path']
            dest = file_info['dest_path']
            
            try:
                # Create destination directory
                dest_dir = os.path.dirname(dest)
                os.makedirs(dest_dir, exist_ok=True)
                
                # Copy file
                shutil.copy2(source, dest)
                
                # Update database
                self.db.update_file_status(file_info['id'], 'completed')
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ Failed to copy {os.path.basename(source)}: {e}")
                self.db.update_file_status(file_info['id'], 'failed', str(e))
                fail_count += 1
                
            # Progress indicator
            if (success_count + fail_count) % 10 == 0:
                print(f"   Progress: {success_count + fail_count}/{len(pending_files)}")
                
        print(f"   ✅ Batch complete: {success_count} success, {fail_count} failed")
        return True
    
    def run(self):
        """Main execution loop"""
        # Select mounts
        source_mount, dest_mount = self.show_mount_selection()
        if not source_mount or not dest_mount:
            return
            
        print(f"\n🚀 Starting batch copy:")
        print(f"   Source: {source_mount}")
        print(f"   Destination: {dest_mount}")
        print(f"   Batch size: {self.batch_size}")
        
        # Scan source
        organized_dest = os.path.join(dest_mount, "organized_files")
        file_count = self.scan_source_directory(source_mount, organized_dest)
        
        if file_count == 0:
            print("❌ No files to copy!")
            return
            
        # Confirm
        response = input(f"\n❓ Ready to copy {file_count} files? (y/n): ")
        if response.lower() != 'y':
            print("❌ Copy cancelled")
            return
            
        # Start copying
        self.is_running = True
        start_time = time.time()
        
        try:
            while self.is_running:
                if not self.copy_batch():
                    break
                    
                # Show progress
                stats = self.db.get_progress_stats()
                print(f"\n📊 Overall Progress: {stats['completed_files']}/{stats['total_files']} " +
                      f"({stats['progress_percent']:.1f}%)")
                
        except KeyboardInterrupt:
            print("\n⚠️ Copy interrupted - progress saved, can resume later")
            
        finally:
            self.is_running = False
            elapsed = time.time() - start_time
            stats = self.db.get_progress_stats()
            
            print(f"\n🏁 Copy session complete:")
            print(f"   Time: {elapsed/60:.1f} minutes")
            print(f"   Files copied: {stats['completed_files']}")
            print(f"   Failed: {stats['failed_files']}")
            print(f"   Progress: {stats['progress_percent']:.1f}%")

def main():
    """Main entry point"""
    print("🚀 BATCH COPY SYSTEM WITH SMART ORGANIZATION")
    print("=" * 60)
    
    controller = BatchCopyController(batch_size=1000)
    controller.run()

if __name__ == "__main__":
    main()