#!/usr/bin/env python3
"""
Woodside Nexus: Custom Ingestion System
Creates family/client-specific sections with timestamped job folders
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import logging

class NexusCustomIngestion:
    """Custom ingestion system for family/client-specific sections"""
    
    def __init__(self, nexus_base: str = "/home/jonclaude/agents/Hinkey"):
        self.nexus_base = Path(nexus_base)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('nexus_ingestion.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def create_custom_section(self, source_folder: str, section_name: str) -> Path:
        """Create custom nexus section with timestamped job folder"""
        
        # Generate timestamp for job folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_folder_name = f"{section_name.lower().replace(' ', '_')}_ingest_{timestamp}"
        
        # Create paths
        source_path = Path(source_folder)
        section_path = self.nexus_base / "nexus_sections" / section_name.replace(' ', '_')
        job_path = section_path / job_folder_name
        
        # Create directory structure
        section_path.mkdir(parents=True, exist_ok=True)
        job_path.mkdir(parents=True, exist_ok=True)
        
        # Create organized subdirectories
        scannable_path = job_path / "scannable"
        non_scannable_path = job_path / "non_scannable"
        
        # File type categories
        categories = [
            "documents", "images", "videos", "audio", "archives", 
            "code", "data", "config", "binaries", "unknown"
        ]
        
        for category in categories:
            (scannable_path / category).mkdir(parents=True, exist_ok=True)
            (non_scannable_path / category).mkdir(parents=True, exist_ok=True)
            
        self.logger.info(f"Created Nexus section: {section_name}")
        self.logger.info(f"Job folder: {job_path}")
        
        return job_path, source_path
        
    def move_and_organize_files(self, source_path: Path, job_path: Path, section_name: str):
        """Move files from source to organized job folder"""
        
        if not source_path.exists():
            self.logger.error(f"Source folder not found: {source_path}")
            return False
            
        self.logger.info(f"Starting ingestion of {section_name} from {source_path}")
        
        # Count files first
        all_files = list(source_path.rglob('*'))
        files_to_process = [f for f in all_files if f.is_file() and not f.name.startswith('.')]
        
        self.logger.info(f"Found {len(files_to_process)} files to ingest")
        
        # File type mappings
        file_mappings = {
            # Documents
            'documents': {'.pdf', '.doc', '.docx', '.txt', '.md', '.odt', '.rtf', '.pptx', '.ppt', '.mht'},
            # Images  
            'images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff', '.tif', '.jg', '.jbf', '.ai', '.psd', '.sketch', '.fig', '.eps'},
            # Videos
            'videos': {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'},
            # Audio
            'audio': {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.wma', '.aac'},
            # Archives
            'archives': {'.zip', '.rar', '.tar', '.gz', '.7z', '.bz2', '.xz'},
            # Code
            'code': {'.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.rb', '.go', '.rs', '.php', '.html', '.css', '.download'},
            # Data
            'data': {'.csv', '.xml', '.sql', '.db', '.sqlite', '.json', '.yaml', '.yml', '.xls', '.xlsx'},
            # Config
            'config': {'.ini', '.conf', '.cfg', '.toml', '.properties', '.url', '.lnk'},
            # Binaries
            'binaries': {'.exe', '.dll', '.so', '.dylib', '.bin', '.app', '.dmg', '.msi'}
        }
        
        # Size limits for scannable classification (in MB)
        scannable_limits = {
            'documents': 50,
            'images': 20,
            'data': 100,
            'code': 10,
            'config': 5
        }
        
        stats = {
            'moved': 0,
            'errors': 0,
            'categories': {}
        }
        
        for file_path in files_to_process:
            try:
                # Determine file category
                file_ext = file_path.suffix.lower()
                category = 'unknown'
                
                # Handle case-insensitive extensions and special cases
                for cat, extensions in file_mappings.items():
                    if file_ext in extensions:
                        category = cat
                        break
                
                # Special handling for .js.download files
                if file_path.name.lower().endswith('.js.download'):
                    category = 'code'
                
                # Determine if scannable
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                size_limit = scannable_limits.get(category, float('inf'))
                is_scannable = file_size_mb <= size_limit and category not in ['binaries', 'archives']
                
                # Determine destination
                if is_scannable:
                    dest_base = job_path / "scannable" / category
                else:
                    dest_base = job_path / "non_scannable" / category
                    
                # Create unique filename if collision
                dest_file = dest_base / file_path.name
                counter = 1
                while dest_file.exists():
                    stem = file_path.stem
                    suffix = file_path.suffix
                    dest_file = dest_base / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                # Move the file
                shutil.move(str(file_path), str(dest_file))
                
                # Update stats
                stats['moved'] += 1
                stats['categories'][category] = stats['categories'].get(category, 0) + 1
                
                if stats['moved'] % 50 == 0:
                    self.logger.info(f"Progress: {stats['moved']}/{len(files_to_process)} files moved")
                    
            except Exception as e:
                self.logger.error(f"Error moving {file_path}: {e}")
                stats['errors'] += 1
                
        self.logger.info(f"Ingestion complete: {stats['moved']} files moved, {stats['errors']} errors")
        self.logger.info(f"Categories: {stats['categories']}")
        
        return stats
        
    def run_full_nexus_processing(self, job_path: Path, section_name: str):
        """Run complete Woodside Nexus processing on ingested files"""
        
        self.logger.info(f"Starting full Nexus processing for {section_name}")
        
        # Change to nexus directory for processing
        os.chdir(str(job_path.parent.parent.parent))
        
        processing_commands = [
            # Excel/Invoice analysis
            f"python3 excel_invoice_processor.py --directory '{job_path}'",
            # PDF processing  
            f"python3 pdf_processor.py --directory '{job_path}'",
            # Word document analysis
            f"python3 word_processor.py --directory '{job_path}'",
            # Image analysis
            f"python3 quick_image_analyzer.py --directory '{job_path}'",
            # Video cataloging
            f"python3 quick_video_cataloger.py --directory '{job_path}'",
            # AI file processing
            f"python3 ai_processor.py --directory '{job_path}'"
        ]
        
        self.logger.info("Full processing will be handled by individual processors")
        self.logger.info(f"Job folder ready at: {job_path}")
        
        return job_path
        
    def ingest_breuler_family(self, source_folder: str = "/home/jonclaude/Desktop/Breulers"):
        """Specific ingestion for Breuler Family"""
        
        print("🌊 WOODSIDE NEXUS: BREULER FAMILY INGESTION")
        print("=" * 60)
        
        # Create custom section
        job_path, source_path = self.create_custom_section(source_folder, "Breuler_Family")
        
        # Move and organize files
        stats = self.move_and_organize_files(source_path, job_path, "Breuler Family")
        
        if stats and stats['moved'] > 0:
            print(f"\n✅ Breuler Family files successfully ingested!")
            print(f"📁 Job folder: {job_path}")
            print(f"📊 Files moved: {stats['moved']}")
            print(f"🗂️ Categories: {stats['categories']}")
            
            # Ready for full processing
            self.run_full_nexus_processing(job_path, "Breuler Family")
            
            print(f"\n🧠 Nexus Section Created:")
            print(f"   Section: Breuler Family")
            print(f"   Location: {job_path}")
            print(f"   Ready for: Excel, PDF, Image, Video, AI file analysis")
            print(f"   Siobhan will learn: All Breuler family relationships and content")
            
        return job_path

def main():
    """Main ingestion interface"""
    
    nexus = NexusCustomIngestion()
    
    # Process Breuler Family
    job_path = nexus.ingest_breuler_family()
    
    print(f"\n🌊 Woodside Nexus expansion complete!")
    print(f"📈 Breuler Family section ready for analysis")

if __name__ == "__main__":
    main()