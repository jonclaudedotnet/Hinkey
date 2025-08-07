#!/usr/bin/env python3
import os
from pathlib import Path
from claude_dolores_bridge import ask_dolores, wait_for_dolores
from document_processor import extract_text_from_file

def process_files_individually():
    extract_path = "/home/jonclaude/agents/Hinkey/jon_knowledge_temp"
    
    # Get all files
    all_files = []
    for root, dirs, files in os.walk(extract_path):
        for file in files:
            file_path = Path(os.path.join(root, file))
            all_files.append(file_path)
    
    print(f"Processing {len(all_files)} files individually for deep learning...")
    
    for i, file_path in enumerate(all_files, 1):
        print(f"\nProcessing file {i}/{len(all_files)}: {file_path.name}")
        
        try:
            # Extract text and metadata
            content, metadata = extract_text_from_file(file_path)
            
            if not content.strip():
                print(f"Skipping empty file: {file_path.name}")
                continue
            
            # Send to Dolores with context
            task_id = ask_dolores(
                "detailed_file_processing",
                f"File: {file_path.name}\nModified: {metadata['modified']}\nSize: {metadata['size']} bytes\n\nContent:\n{content}",
                f"Processing JC's file: {file_path.name} - extract all personal, family, project, and temporal information"
            )
            
            result = wait_for_dolores(task_id, timeout=30)
            if result:
                print(f"✓ Processed: {file_path.name}")
                print(f"Dolores learned: {result[:200]}...")
            else:
                print(f"✗ No response for: {file_path.name}")
                
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
    
    print("\n=== Knowledge Processing Complete ===")

if __name__ == "__main__":
    process_files_individually()