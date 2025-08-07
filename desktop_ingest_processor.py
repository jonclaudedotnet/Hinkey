#!/usr/bin/env python3
"""
Desktop Ingest Folder Processor
Move and sort files by type, ingest scannable ones
"""

import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
from dataclasses import dataclass
from enum import Enum
import mimetypes

# Import our existing file categorization system
from batch_copy_system import FileOrganizer, FileCategory

@dataclass 
class ProcessingStats:
    total_files: int = 0
    moved_files: int = 0
    ingested_files: int = 0
    failed_files: int = 0
    categories: Dict[str, int] = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = {}

class DesktopIngestProcessor:
    """Process desktop ingest folder - move and sort files by type"""
    
    def __init__(self, source_folder: str, job_folder: str):
        self.source_folder = Path(source_folder)
        self.job_folder = Path(job_folder)
        self.stats = ProcessingStats()
        
        # Create job folder structure
        self.job_folder.mkdir(exist_ok=True)
        self.scannable_folder = self.job_folder / "scannable"
        self.non_scannable_folder = self.job_folder / "non_scannable"
        
        # Initialize ingestion database
        self.db_path = self.job_folder / "ingestion_progress.db"
        self.init_database()
        
        print(f"📁 Source: {self.source_folder}")
        print(f"📁 Job folder: {self.job_folder}")
        
    def init_database(self):
        """Initialize ingestion tracking database"""
        self.conn = sqlite3.connect(str(self.db_path))
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingested_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_path TEXT,
                moved_path TEXT,
                file_category TEXT,
                file_size INTEGER,
                is_scannable BOOLEAN,
                processed_timestamp TEXT,
                content_hash TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        self.conn.commit()
        
    def scan_source_files(self) -> List[Path]:
        """Scan source folder and return all files"""
        files = []
        
        print(f"\n🔍 Scanning {self.source_folder}...")
        
        for root, dirs, filenames in os.walk(self.source_folder):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                    
                file_path = Path(root) / filename
                files.append(file_path)
                
        self.stats.total_files = len(files)
        print(f"✅ Found {len(files)} files to process")
        return files
        
    def categorize_and_organize_file(self, file_path: Path) -> bool:
        """Move file to organized location based on type"""
        try:
            # Get file info
            file_size = file_path.stat().st_size
            category = FileOrganizer.categorize_file(file_path)
            is_scannable = FileOrganizer.is_scannable(file_path, file_size)
            
            # Determine destination folder structure
            if is_scannable:
                dest_base = self.scannable_folder / category.value
            else:
                dest_base = self.non_scannable_folder / category.value
                
            dest_base.mkdir(parents=True, exist_ok=True)
            
            # Create unique filename if collision
            dest_file = dest_base / file_path.name
            counter = 1
            while dest_file.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                dest_file = dest_base / f"{stem}_{counter}{suffix}"
                counter += 1
                
            # Move the file (faster than copy)
            shutil.move(str(file_path), str(dest_file))
            
            # Record in database
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO ingested_files 
                (original_path, moved_path, file_category, file_size, is_scannable, processed_timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                str(file_path), str(dest_file), category.value, 
                file_size, is_scannable, datetime.now().isoformat()
            ))
            self.conn.commit()
            
            # Update stats
            self.stats.moved_files += 1
            self.stats.categories[category.value] = self.stats.categories.get(category.value, 0) + 1
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error processing {file_path.name}: {e}")
            self.stats.failed_files += 1
            return False
            
    def ingest_scannable_files(self):
        """Ingest the scannable files using existing system"""
        print(f"\n📚 Starting ingestion of scannable files...")
        
        # Count scannable files
        scannable_files = []
        if self.scannable_folder.exists():
            for category_folder in self.scannable_folder.iterdir():
                if category_folder.is_dir():
                    for file_path in category_folder.rglob('*'):
                        if file_path.is_file():
                            scannable_files.append(file_path)
                            
        if not scannable_files:
            print("   ℹ️ No scannable files to ingest")
            return
            
        print(f"   📄 Found {len(scannable_files)} scannable files")
        
        # For now, just mark them as ready for ingestion
        # The actual content processing can be done separately
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE ingested_files 
            SET status = 'ready_for_ingestion'
            WHERE is_scannable = 1
        ''')
        self.conn.commit()
        
        self.stats.ingested_files = len(scannable_files)
        print(f"   ✅ {len(scannable_files)} files ready for content ingestion")
        
    def show_progress(self, current: int, total: int):
        """Show processing progress"""
        if current % 50 == 0 or current == total:
            percent = (current / total * 100) if total > 0 else 0
            print(f"   📊 Progress: {current}/{total} ({percent:.1f}%)")
            
    def process_all_files(self):
        """Main processing function"""
        print(f"\n🚀 Starting desktop ingest processing...")
        
        # Scan all files
        files = self.scan_source_files()
        if not files:
            print("❌ No files found to process!")
            return
            
        # Process each file
        print(f"\n📦 Moving and organizing {len(files)} files...")
        for i, file_path in enumerate(files, 1):
            self.categorize_and_organize_file(file_path)
            self.show_progress(i, len(files))
            
        # Ingest scannable files
        self.ingest_scannable_files()
        
        # Show final stats
        self.show_final_stats()
        
    def show_final_stats(self):
        """Show final processing statistics"""
        print(f"\n🏁 DESKTOP INGEST PROCESSING COMPLETE")
        print("=" * 60)
        print(f"📊 Total files processed: {self.stats.total_files}")
        print(f"✅ Successfully moved: {self.stats.moved_files}")
        print(f"📚 Ready for ingestion: {self.stats.ingested_files}")
        print(f"❌ Failed: {self.stats.failed_files}")
        
        print(f"\n📁 File categories:")
        for category, count in sorted(self.stats.categories.items()):
            print(f"   {category}: {count} files")
            
        print(f"\n📂 Organized structure created at:")
        print(f"   Scannable: {self.scannable_folder}")
        print(f"   Non-scannable: {self.non_scannable_folder}")
        
        # Check if source folder is empty
        remaining_files = list(self.source_folder.rglob('*'))
        remaining_files = [f for f in remaining_files if f.is_file()]
        
        if remaining_files:
            print(f"\n⚠️ {len(remaining_files)} files remain in source folder")
        else:
            print(f"\n✅ Source folder completely processed and empty!")

def main():
    """Main entry point"""
    print("🚀 DESKTOP INGEST FOLDER PROCESSOR")
    print("=" * 60)
    
    # Set paths
    source_folder = "/home/jonclaude/Desktop/ingest073025"
    job_folder = "/home/jonclaude/agents/Hinkey/desktop_ingest_job"
    
    # Verify source exists
    if not os.path.exists(source_folder):
        print(f"❌ Source folder not found: {source_folder}")
        return
        
    # Create processor and run
    processor = DesktopIngestProcessor(source_folder, job_folder)
    processor.process_all_files()
    
    print(f"\n🎉 All files moved and organized!")
    print(f"Next steps: Process scannable files for content ingestion")

if __name__ == "__main__":
    main()