#!/usr/bin/env python3
"""
Nexus File Organizer - Smart file copying and organization by criteria
Copy cached files to mounted drives based on type, content, metadata, etc.
"""

import os
import shutil
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import re

class NexusFileOrganizer:
    """Organize and copy files based on various criteria"""
    
    def __init__(self, cache_db_path: str = "./nexus_cache/cache_metadata.db"):
        self.cache_db = cache_db_path
        self.conn = sqlite3.connect(self.cache_db)
        self.conn.row_factory = sqlite3.Row
        
        # Organization strategies
        self.strategies = {
            'by_type': self.organize_by_type,
            'by_date': self.organize_by_date,
            'by_size': self.organize_by_size,
            'by_project': self.organize_by_project,
            'by_content': self.organize_by_content,
            'custom': self.organize_by_custom_query
        }
    
    def get_file_stats(self) -> Dict:
        """Get statistics about cached files"""
        cursor = self.conn.cursor()
        
        # Total files
        cursor.execute("SELECT COUNT(*) as total FROM cached_files WHERE status = 'cached'")
        total = cursor.fetchone()['total']
        
        # By extension
        cursor.execute("""
            SELECT 
                LOWER(SUBSTR(network_path, INSTR(network_path, '.') + 1)) as ext,
                COUNT(*) as count,
                SUM(file_size) as total_size
            FROM cached_files
            WHERE status = 'cached' AND INSTR(network_path, '.') > 0
            GROUP BY ext
            ORDER BY count DESC
        """)
        
        by_extension = {}
        for row in cursor.fetchall():
            by_extension[row['ext']] = {
                'count': row['count'],
                'total_size': row['total_size'] or 0
            }
        
        # By date range
        cursor.execute("""
            SELECT 
                DATE(datetime(last_modified, 'unixepoch')) as file_date,
                COUNT(*) as count
            FROM cached_files
            WHERE status = 'cached'
            GROUP BY file_date
            ORDER BY file_date DESC
            LIMIT 30
        """)
        
        by_date = {}
        for row in cursor.fetchall():
            by_date[row['file_date']] = row['count']
        
        return {
            'total_files': total,
            'by_extension': by_extension,
            'by_date': by_date
        }
    
    def organize_by_type(self, source_dir: Path, target_dir: Path, 
                        type_mapping: Optional[Dict] = None) -> Dict:
        """Organize files by type/extension"""
        
        if not type_mapping:
            # Default type mapping
            type_mapping = {
                'documents': ['.pdf', '.doc', '.docx', '.odt', '.rtf'],
                'spreadsheets': ['.xls', '.xlsx', '.csv', '.ods'],
                'presentations': ['.ppt', '.pptx', '.odp'],
                'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
                'code': ['.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.rb'],
                'web': ['.html', '.css', '.xml', '.json'],
                'archives': ['.zip', '.tar', '.gz', '.rar', '.7z'],
                'text': ['.txt', '.md', '.log', '.ini', '.cfg']
            }
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT network_path, local_path, file_size 
            FROM cached_files 
            WHERE status = 'cached'
        """)
        
        stats = {'copied': 0, 'skipped': 0, 'errors': 0, 'bytes_copied': 0}
        
        for row in cursor.fetchall():
            local_path = Path(row['local_path'])
            if not local_path.exists():
                stats['skipped'] += 1
                continue
            
            ext = local_path.suffix.lower()
            
            # Find category for this extension
            category = 'other'
            for cat, extensions in type_mapping.items():
                if ext in extensions:
                    category = cat
                    break
            
            # Create target directory structure
            target_subdir = target_dir / category
            target_subdir.mkdir(parents=True, exist_ok=True)
            
            # Preserve relative path structure
            relative_path = Path(row['network_path']).name
            target_path = target_subdir / relative_path
            
            # Handle duplicates
            if target_path.exists():
                base = target_path.stem
                ext = target_path.suffix
                counter = 1
                while target_path.exists():
                    target_path = target_subdir / f"{base}_{counter}{ext}"
                    counter += 1
            
            try:
                shutil.copy2(local_path, target_path)
                stats['copied'] += 1
                stats['bytes_copied'] += row['file_size']
            except Exception as e:
                print(f"❌ Error copying {local_path}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def organize_by_date(self, source_dir: Path, target_dir: Path,
                        date_format: str = "%Y/%Y-%m") -> Dict:
        """Organize files by modification date"""
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT network_path, local_path, last_modified, file_size
            FROM cached_files
            WHERE status = 'cached'
        """)
        
        stats = {'copied': 0, 'skipped': 0, 'errors': 0, 'bytes_copied': 0}
        
        for row in cursor.fetchall():
            local_path = Path(row['local_path'])
            if not local_path.exists():
                stats['skipped'] += 1
                continue
            
            # Create date-based subdirectory
            file_date = datetime.fromtimestamp(row['last_modified'])
            date_subdir = file_date.strftime(date_format)
            target_subdir = target_dir / date_subdir
            target_subdir.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            target_path = target_subdir / local_path.name
            
            try:
                shutil.copy2(local_path, target_path)
                stats['copied'] += 1
                stats['bytes_copied'] += row['file_size']
            except Exception as e:
                print(f"❌ Error copying {local_path}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def organize_by_size(self, source_dir: Path, target_dir: Path,
                        size_ranges: Optional[List] = None) -> Dict:
        """Organize files by size ranges"""
        
        if not size_ranges:
            # Default size ranges (in MB)
            size_ranges = [
                (0, 1, 'tiny'),          # < 1MB
                (1, 10, 'small'),        # 1-10MB
                (10, 100, 'medium'),     # 10-100MB
                (100, 1000, 'large'),    # 100MB-1GB
                (1000, float('inf'), 'huge')  # > 1GB
            ]
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT network_path, local_path, file_size
            FROM cached_files
            WHERE status = 'cached'
        """)
        
        stats = {'copied': 0, 'skipped': 0, 'errors': 0, 'bytes_copied': 0}
        
        for row in cursor.fetchall():
            local_path = Path(row['local_path'])
            if not local_path.exists():
                stats['skipped'] += 1
                continue
            
            # Determine size category
            size_mb = row['file_size'] / (1024 * 1024)
            category = 'unknown'
            
            for min_size, max_size, cat_name in size_ranges:
                if min_size <= size_mb < max_size:
                    category = cat_name
                    break
            
            # Create target directory
            target_subdir = target_dir / category
            target_subdir.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            target_path = target_subdir / local_path.name
            
            try:
                shutil.copy2(local_path, target_path)
                stats['copied'] += 1
                stats['bytes_copied'] += row['file_size']
            except Exception as e:
                print(f"❌ Error copying {local_path}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def organize_by_project(self, source_dir: Path, target_dir: Path,
                           project_patterns: Dict[str, List[str]]) -> Dict:
        """Organize files by project based on path patterns"""
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT network_path, local_path, file_size
            FROM cached_files
            WHERE status = 'cached'
        """)
        
        stats = {'copied': 0, 'skipped': 0, 'errors': 0, 'bytes_copied': 0}
        
        for row in cursor.fetchall():
            local_path = Path(row['local_path'])
            network_path = row['network_path']
            
            if not local_path.exists():
                stats['skipped'] += 1
                continue
            
            # Determine project based on patterns
            project = 'unclassified'
            for proj_name, patterns in project_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, network_path, re.IGNORECASE):
                        project = proj_name
                        break
                if project != 'unclassified':
                    break
            
            # Create project directory
            target_subdir = target_dir / project
            target_subdir.mkdir(parents=True, exist_ok=True)
            
            # Preserve some path structure
            relative_parts = Path(network_path).parts[-2:]  # Last 2 directory levels
            target_path = target_subdir / Path(*relative_parts)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                shutil.copy2(local_path, target_path)
                stats['copied'] += 1
                stats['bytes_copied'] += row['file_size']
            except Exception as e:
                print(f"❌ Error copying {local_path}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def organize_by_content(self, source_dir: Path, target_dir: Path,
                           content_rules: Dict[str, List[str]]) -> Dict:
        """Organize files by content (requires vector DB integration)"""
        # This would integrate with the vector search to organize by content
        # For now, returns a placeholder
        return {'status': 'Content-based organization requires vector DB integration'}
    
    def organize_by_custom_query(self, source_dir: Path, target_dir: Path,
                                sql_query: str, target_structure: str = "flat") -> Dict:
        """Organize files based on custom SQL query"""
        
        cursor = self.conn.cursor()
        cursor.execute(sql_query)
        
        stats = {'copied': 0, 'skipped': 0, 'errors': 0, 'bytes_copied': 0}
        
        for row in cursor.fetchall():
            if 'local_path' not in row.keys():
                print("❌ Query must include 'local_path' column")
                break
                
            local_path = Path(row['local_path'])
            if not local_path.exists():
                stats['skipped'] += 1
                continue
            
            # Determine target path based on structure type
            if target_structure == "flat":
                target_path = target_dir / local_path.name
            elif target_structure == "preserve":
                # Preserve original directory structure
                relative_path = Path(row.get('network_path', local_path)).relative_to('/')
                target_path = target_dir / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                # Custom structure based on query columns
                # Use other columns from query to build path
                target_path = target_dir / local_path.name
            
            try:
                shutil.copy2(local_path, target_path)
                stats['copied'] += 1
                stats['bytes_copied'] += row.get('file_size', 0)
            except Exception as e:
                print(f"❌ Error copying {local_path}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def execute_organization(self, strategy: str, target_dir: str, **kwargs) -> Dict:
        """Execute an organization strategy"""
        
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        if strategy not in self.strategies:
            return {'error': f'Unknown strategy: {strategy}'}
        
        print(f"🗂️  Organizing files using strategy: {strategy}")
        print(f"📁 Target directory: {target_path}")
        
        # Get source directory (cache root)
        source_dir = Path(self.cache_db).parent / "files"
        
        # Execute strategy
        organizer_func = self.strategies[strategy]
        stats = organizer_func(source_dir, target_path, **kwargs)
        
        return stats

def main():
    """Example usage of Nexus File Organizer"""
    print("🗂️  Nexus File Organizer")
    print("=" * 40)
    
    organizer = NexusFileOrganizer()
    
    # Show current file statistics
    stats = organizer.get_file_stats()
    print(f"\n📊 Cached Files Statistics:")
    print(f"   Total files: {stats['total_files']}")
    print(f"\n   By extension:")
    for ext, info in list(stats['by_extension'].items())[:10]:
        size_mb = info['total_size'] / (1024 * 1024)
        print(f"      .{ext}: {info['count']} files ({size_mb:.1f} MB)")
    
    # Example: Organize by type
    print("\n📂 Example: Organizing by file type...")
    result = organizer.execute_organization(
        strategy='by_type',
        target_dir='/mnt/organized/by_type'
    )
    print(f"   Files copied: {result.get('copied', 0)}")
    print(f"   Files skipped: {result.get('skipped', 0)}")
    print(f"   Errors: {result.get('errors', 0)}")
    
    # Example: Custom query
    print("\n🔍 Example: Custom organization (PDFs from 2024)...")
    custom_query = """
        SELECT network_path, local_path, file_size
        FROM cached_files
        WHERE status = 'cached'
        AND LOWER(network_path) LIKE '%.pdf'
        AND datetime(last_modified, 'unixepoch') >= '2024-01-01'
    """
    
    result = organizer.execute_organization(
        strategy='custom',
        target_dir='/mnt/organized/pdfs_2024',
        sql_query=custom_query
    )

if __name__ == "__main__":
    main()