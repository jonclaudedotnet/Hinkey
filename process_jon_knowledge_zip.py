#!/usr/bin/env python3
import zipfile
import os
from pathlib import Path
from claude_dolores_bridge import ask_dolores, wait_for_dolores
from document_processor import extract_text_from_file

def process_knowledge_zip():
    zip_path = "/home/jonclaude/agents/Hinkey/DOLORES_JON_CLAUDE_KNOWLEDGE_PACKAGE.zip"
    extract_path = "/home/jonclaude/agents/Hinkey/jon_knowledge_temp"
    
    if not os.path.exists(zip_path):
        print("Zip file not found!")
        return
    
    # Create extraction directory
    os.makedirs(extract_path, exist_ok=True)
    
    # Extract the zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
        print(f"Extracted {len(zip_ref.namelist())} files from knowledge package")
    
    # Get list of extracted files
    all_files = []
    for root, dirs, files in os.walk(extract_path):
        for file in files:
            file_path = os.path.join(root, file)
            all_files.append(file_path)
    
    print(f"Found {len(all_files)} files to process")
    
    # Send initial message to Dolores about the knowledge package
    task_id = ask_dolores(
        "knowledge_package_processing",
        f"JC has shared his knowledge package containing {len(all_files)} files. This is pre-parsed information about him, his family, and his projects. I'm about to process these files systematically to build your knowledge base. Remember to track temporal information (dates, project timelines) as he emphasized.",
        "Guide preparing to process JC's knowledge package"
    )
    
    result = wait_for_dolores(task_id, timeout=20)
    if result:
        print("Dolores is ready for knowledge processing:")
        print(result)
    
    return all_files

if __name__ == "__main__":
    files = process_knowledge_zip()