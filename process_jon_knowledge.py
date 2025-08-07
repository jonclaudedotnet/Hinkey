#!/usr/bin/env python3
"""
Process Jon's Knowledge Base - Feed documents to Dolores via her DeepSeek API
"""

import os
import sys
from pathlib import Path
from claude_dolores_bridge import ask_dolores, wait_for_dolores
from document_processor import DocumentProcessor, extract_text_from_file
from dolores_memory_v2 import DoloresMemoryV2
import time

def process_with_dolores(filepath: Path, content: str, metadata: dict) -> str:
    """Have Dolores analyze and learn from a document"""
    
    # Prepare document summary for Dolores
    doc_summary = f"""
Document: {filepath.name}
Path: {metadata['path']}
Type: {metadata['type']}
Modified: {metadata['modified']}
Word Count: {metadata.get('word_count', 0)}

Content Preview (first 500 chars):
{content[:500]}...

Please analyze this document and:
1. Extract key information about Jon, his projects, or interests
2. Identify any personal details, technical skills, or patterns
3. Note connections to other knowledge you have
4. Format findings as LEARN entries

Focus on understanding Jon better through his work."""

    # Ask Dolores to process
    task_id = ask_dolores("document_analysis", doc_summary, f"Processing {filepath.name}")
    
    # Wait for response
    result = wait_for_dolores(task_id, timeout=30)
    return result or "Processing timeout"

def process_directory_with_dolores(directory_path: str, file_limit: int = 10):
    """Process a directory of documents through Dolores"""
    
    print(f"🔍 Scanning directory: {directory_path}")
    
    # Initialize processors
    processor = DocumentProcessor()
    memory = DoloresMemoryV2()
    
    # Get initial stats
    initial_stats = memory.get_memory_stats()
    initial_memories = initial_stats['total_memories']
    
    # Find documents
    directory = Path(directory_path)
    if not directory.exists():
        print(f"❌ Directory not found: {directory_path}")
        return
        
    # Get supported files
    supported_files = []
    for ext in processor.supported_extensions:
        supported_files.extend(directory.rglob(f'*{ext}'))
    
    # Limit files for initial processing
    files_to_process = supported_files[:file_limit]
    
    print(f"📄 Found {len(supported_files)} documents, processing first {len(files_to_process)}")
    print("-" * 60)
    
    processed_count = 0
    total_words = 0
    
    for i, filepath in enumerate(files_to_process, 1):
        print(f"\n[{i}/{len(files_to_process)}] Processing: {filepath.name}")
        
        try:
            # Extract content
            content, metadata = extract_text_from_file(filepath)
            
            if content and not content.startswith('[Error'):
                # Show preview
                print(f"  📊 {metadata.get('word_count', 0)} words, {metadata['type']} file")
                
                # Have Dolores analyze it
                print("  🤖 Asking Dolores to analyze...")
                result = process_with_dolores(filepath, content, metadata)
                
                if result:
                    print("  ✅ Dolores learned from this document")
                    
                    # Store key content in memory
                    if metadata.get('word_count', 0) > 50:
                        memory.remember(
                            content=f"From {filepath.name}: {content[:500]}",
                            category='documents',
                            context=str(filepath),
                            source='file_import'
                        )
                    
                processed_count += 1
                total_words += metadata.get('word_count', 0)
                
                # Don't overwhelm DeepSeek API
                time.sleep(2)
                
            else:
                print(f"  ⚠️  Error: {content}")
                
        except Exception as e:
            print(f"  ❌ Failed: {str(e)}")
    
    # Final statistics
    print("\n" + "=" * 60)
    print("📊 PROCESSING COMPLETE")
    print(f"  Files processed: {processed_count}/{len(files_to_process)}")
    print(f"  Total words analyzed: {total_words:,}")
    
    # Check memory growth
    final_stats = memory.get_memory_stats()
    new_memories = final_stats['total_memories'] - initial_memories
    
    print(f"\n🧠 DOLORES'S GROWTH:")
    print(f"  New memories created: {new_memories}")
    print(f"  Total memories now: {final_stats['total_memories']}")
    print(f"  Storage used: {final_stats['storage_used_mb']:.1f} MB")
    
    if final_stats.get('top_topics'):
        print(f"\n🔝 TOP TOPICS:")
        for topic, freq in list(final_stats['top_topics'].items())[:5]:
            print(f"  - {topic}: {freq} mentions")

def interactive_mode():
    """Interactive mode for processing documents"""
    
    print("🎯 JON'S KNOWLEDGE BASE PROCESSOR")
    print("Feed your documents to Dolores for learning")
    print("-" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Process current directory")
        print("2. Process specific directory")
        print("3. Process single file")
        print("4. Connect to Mac Mini (SSH)")
        print("5. Show Dolores's memory stats")
        print("6. Exit")
        
        choice = input("\nChoice (1-6): ").strip()
        
        if choice == '1':
            limit = input("How many files to process? (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            process_directory_with_dolores(".", limit)
            
        elif choice == '2':
            path = input("Directory path: ").strip()
            limit = input("How many files to process? (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            process_directory_with_dolores(path, limit)
            
        elif choice == '3':
            filepath = input("File path: ").strip()
            if os.path.exists(filepath):
                content, metadata = extract_text_from_file(Path(filepath))
                print(f"\nFile: {metadata['filename']}")
                print(f"Words: {metadata.get('word_count', 0)}")
                result = process_with_dolores(Path(filepath), content, metadata)
                print(f"\nDolores says: {result}")
            else:
                print("File not found!")
                
        elif choice == '4':
            print("\nTo connect to Mac Mini:")
            print("1. Set up SSH keys: ssh-keygen -t rsa")
            print("2. Copy to Mac: ssh-copy-id jon@macmini.local")
            print("3. Mount: sshfs jon@macmini.local:/path/to/projects ~/mac_projects")
            print("\nThen process the mounted directory with option 2")
            
        elif choice == '5':
            memory = DoloresMemoryV2()
            stats = memory.get_memory_stats()
            print(f"\n🧠 DOLORES'S MEMORY:")
            print(f"Total memories: {stats['total_memories']}")
            print(f"Categories: {stats['categories']}")
            print(f"Storage: {stats['storage_used_mb']:.1f} MB")
            
        elif choice == '6':
            print("👋 Goodbye!")
            break
            
        else:
            print("Invalid choice")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode
        process_directory_with_dolores(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10)
    else:
        # Interactive mode
        interactive_mode()