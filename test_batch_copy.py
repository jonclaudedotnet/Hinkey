#!/usr/bin/env python3
"""
Test the batch copy system with local directories
"""

import os
import sys
from pathlib import Path

# Import the batch copy system
from batch_copy_system import BatchCopyController, MountManager, MountPoint

def setup_test_environment():
    """Create test directories with sample files"""
    test_source = Path("test_source")
    test_dest = Path("test_destination")
    
    # Create test source structure
    test_files = [
        "documents/report.pdf",
        "documents/notes.txt", 
        "code/script.py",
        "code/app.js",
        "images/photo.jpg",
        "config/settings.json",
        "data/records.csv",
        "binaries/tool.exe",
        "unknown/random.xyz"
    ]
    
    print("🔧 Setting up test environment...")
    
    for file_path in test_files:
        full_path = test_source / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create dummy file with some content
        with open(full_path, 'w') as f:
            f.write(f"Test content for {file_path}\n")
            f.write("=" * 50 + "\n")
            f.write(f"Category: {file_path.split('/')[0]}\n")
    
    # Create destination
    test_dest.mkdir(exist_ok=True)
    
    print(f"✅ Created test source with {len(test_files)} files")
    print(f"📁 Source: {test_source.absolute()}")
    print(f"📁 Destination: {test_dest.absolute()}")
    
    return test_source.absolute(), test_dest.absolute()

def main():
    """Test the batch copy system"""
    print("🧪 BATCH COPY SYSTEM TEST")
    print("=" * 60)
    
    # Setup test environment
    source_path, dest_path = setup_test_environment()
    
    # Override mount detection for testing
    class TestBatchController(BatchCopyController):
        def show_mount_selection(self):
            """Override to use test directories"""
            print("\n📁 Using test directories:")
            print(f"   Source: {source_path}")
            print(f"   Destination: {dest_path}")
            return str(source_path), str(dest_path)
    
    # Run test in automated mode
    print("\n🚀 Starting batch copy test...")
    controller = TestBatchController(batch_size=5)  # Small batch for testing
    
    # Automated test - bypass user input
    organized_dest = os.path.join(str(dest_path), "organized_files")
    file_count = controller.scan_source_directory(str(source_path), organized_dest)
    
    print(f"\n✅ Scanned {file_count} files")
    
    # Copy files
    controller.is_running = True
    batch_num = 0
    while controller.copy_batch():
        batch_num += 1
        stats = controller.db.get_progress_stats()
        print(f"Batch {batch_num} complete - Progress: {stats['progress_percent']:.1f}%")
    
    # Show results
    print("\n📊 Test Results:")
    dest_organized = dest_path / "organized_files"
    
    if dest_organized.exists():
        for category in ['scannable', 'non_scannable']:
            category_path = dest_organized / category
            if category_path.exists():
                print(f"\n📁 {category}:")
                for item in category_path.rglob('*'):
                    if item.is_file():
                        rel_path = item.relative_to(category_path)
                        print(f"   ✓ {rel_path}")

if __name__ == "__main__":
    main()