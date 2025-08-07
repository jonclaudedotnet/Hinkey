#!/usr/bin/env python3
"""
Document Processor - Extract text from md, txt, docx, and pdf files
For feeding Jon's knowledge base to Dolores
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib
from datetime import datetime

# Text extraction utilities
def extract_text_from_file(filepath: Path) -> Tuple[str, Dict[str, any]]:
    """Extract text and metadata from various file types"""
    
    file_ext = filepath.suffix.lower()
    metadata = {
        'filename': filepath.name,
        'path': str(filepath),
        'size': filepath.stat().st_size,
        'modified': datetime.fromtimestamp(filepath.stat().st_mtime),
        'type': file_ext
    }
    
    try:
        if file_ext in ['.txt', '.md']:
            # Simple text files
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
        elif file_ext == '.docx':
            # Word documents
            try:
                import docx
                doc = docx.Document(filepath)
                content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            except ImportError:
                # Fallback to basic zip extraction
                import zipfile
                import xml.etree.ElementTree as ET
                
                with zipfile.ZipFile(filepath, 'r') as docx_zip:
                    xml_content = docx_zip.read('word/document.xml')
                    tree = ET.fromstring(xml_content)
                    
                    # Extract text from XML
                    namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    paragraphs = tree.findall('.//w:t', namespace)
                    content = ' '.join([p.text for p in paragraphs if p.text])
                    
        elif file_ext == '.pdf':
            # PDF files (text only)
            try:
                import PyPDF2
                with open(filepath, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    content = ''
                    for page in pdf_reader.pages:
                        content += page.extract_text() + '\n'
            except ImportError:
                # Try pdfplumber as alternative
                try:
                    import pdfplumber
                    with pdfplumber.open(filepath) as pdf:
                        content = '\n'.join([page.extract_text() for page in pdf.pages if page.extract_text()])
                except ImportError:
                    content = f"[PDF extraction failed - install PyPDF2 or pdfplumber]"
                    
        else:
            content = f"[Unsupported file type: {file_ext}]"
            
        # Extract key information from content
        metadata['word_count'] = len(content.split())
        metadata['line_count'] = len(content.splitlines())
        
        # Look for special markers in content
        if file_ext == '.md':
            # Extract markdown headers
            headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
            metadata['headers'] = headers[:5]  # First 5 headers
            
        # Check for code content
        if any(marker in content for marker in ['def ', 'class ', 'function ', 'import ']):
            metadata['has_code'] = True
            
        return content, metadata
        
    except Exception as e:
        return f"[Error reading file: {str(e)}]", metadata


class DocumentProcessor:
    """Process documents for Dolores's knowledge base"""
    
    def __init__(self, dolores_memory=None):
        self.supported_extensions = {'.txt', '.md', '.docx', '.pdf'}
        self.processed_files = set()
        self.memory = dolores_memory
        
    def process_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, any]:
        """Process all supported documents in a directory"""
        
        directory = Path(directory_path)
        if not directory.exists():
            return {'error': f"Directory not found: {directory_path}"}
            
        results = {
            'total_files': 0,
            'processed': 0,
            'errors': 0,
            'total_words': 0,
            'file_types': {},
            'notable_findings': []
        }
        
        # Find all supported files
        if recursive:
            files = [f for f in directory.rglob('*') if f.suffix.lower() in self.supported_extensions]
        else:
            files = [f for f in directory.iterdir() if f.is_file() and f.suffix.lower() in self.supported_extensions]
            
        results['total_files'] = len(files)
        
        for filepath in files:
            try:
                content, metadata = extract_text_from_file(filepath)
                
                if content and not content.startswith('[Error'):
                    results['processed'] += 1
                    results['total_words'] += metadata.get('word_count', 0)
                    
                    # Track file types
                    file_type = metadata['type']
                    results['file_types'][file_type] = results['file_types'].get(file_type, 0) + 1
                    
                    # Store in Dolores's memory if available
                    if self.memory and metadata.get('word_count', 0) > 10:
                        # Determine category based on content
                        category = self._categorize_content(filepath, content)
                        
                        # Store with context
                        self.memory.remember(
                            content=content[:1000],  # First 1000 chars
                            category=category,
                            context=f"File: {filepath.name}",
                            source='file_import',
                            importance=self._calculate_importance(metadata)
                        )
                        
                    # Check for notable content
                    if metadata.get('has_code'):
                        results['notable_findings'].append(f"Code found in: {filepath.name}")
                    
                    if 'headers' in metadata and metadata['headers']:
                        results['notable_findings'].append(f"Document structure: {filepath.name} - {metadata['headers'][0]}")
                        
                else:
                    results['errors'] += 1
                    
            except Exception as e:
                results['errors'] += 1
                print(f"Error processing {filepath}: {e}")
                
        return results
    
    def _categorize_content(self, filepath: Path, content: str) -> str:
        """Categorize content based on file path and content"""
        
        path_lower = str(filepath).lower()
        content_lower = content.lower()
        
        # Check path-based categories
        if 'project' in path_lower:
            return 'projects'
        elif 'personal' in path_lower:
            return 'personal'
        elif 'work' in path_lower:
            return 'professional'
        elif 'note' in path_lower:
            return 'notes'
            
        # Content-based categorization
        if any(word in content_lower for word in ['family', 'wife', 'caitlin', 'personal']):
            return 'personal'
        elif any(word in content_lower for word in ['code', 'function', 'class', 'import']):
            return 'technical'
        elif any(word in content_lower for word in ['meeting', 'agenda', 'minutes']):
            return 'meetings'
            
        return 'general'
    
    def _calculate_importance(self, metadata: Dict) -> int:
        """Calculate importance score (1-10) based on metadata"""
        
        importance = 5  # Default
        
        # Recent files are more important
        days_old = (datetime.now() - metadata['modified']).days
        if days_old < 7:
            importance += 2
        elif days_old < 30:
            importance += 1
            
        # Larger documents might be more comprehensive
        word_count = metadata.get('word_count', 0)
        if word_count > 1000:
            importance += 1
        if word_count > 5000:
            importance += 1
            
        # Code files are important for understanding projects
        if metadata.get('has_code'):
            importance += 1
            
        return min(importance, 10)
    
    def process_single_file(self, filepath: str) -> Tuple[str, Dict]:
        """Process a single file and return content + metadata"""
        return extract_text_from_file(Path(filepath))


# Test the processor
if __name__ == "__main__":
    processor = DocumentProcessor()
    
    # Test single file
    test_file = Path("./CLAUDE.md")
    if test_file.exists():
        content, metadata = processor.process_single_file(test_file)
        print(f"Processed {test_file}:")
        print(f"  Words: {metadata.get('word_count', 0)}")
        print(f"  Lines: {metadata.get('line_count', 0)}")
        print(f"  First 100 chars: {content[:100]}...")
        
    # Test directory processing
    results = processor.process_directory(".", recursive=False)
    print(f"\nDirectory scan results:")
    print(f"  Total files: {results['total_files']}")
    print(f"  Processed: {results['processed']}")
    print(f"  Total words: {results['total_words']}")
    print(f"  File types: {results['file_types']}")