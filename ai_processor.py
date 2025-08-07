#!/usr/bin/env python3
"""
Adobe Illustrator (AI) File Processor
Extracts text content and metadata from AI files
"""

import os
import sqlite3
from pathlib import Path
from datetime import datetime
import re
import hashlib
from typing import Dict, List, Optional
import json
import subprocess

class AIProcessor:
    """Process Adobe Illustrator files and extract available data"""
    
    def __init__(self, db_path: str = "ai_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.init_database()
        self.stats = {
            'files_processed': 0,
            'text_extracted': 0,
            'metadata_extracted': 0,
            'creator_found': 0,
            'errors': []
        }
        
    def init_database(self):
        """Initialize AI file database schema"""
        cursor = self.conn.cursor()
        
        # Main AI files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE,
                file_name TEXT,
                file_size INTEGER,
                file_hash TEXT,
                creator TEXT,
                creation_date TEXT,
                modification_date TEXT,
                title TEXT,
                document_type TEXT,
                ai_version TEXT,
                extracted_text TEXT,
                fonts_used TEXT,
                colors_used TEXT,
                artboard_count INTEGER,
                layer_count INTEGER,
                processed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Text elements found
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_text_elements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ai_file_id INTEGER,
                text_content TEXT,
                font_name TEXT,
                font_size REAL,
                position_info TEXT,
                FOREIGN KEY (ai_file_id) REFERENCES ai_files(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_creator ON ai_files(creator)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_type ON ai_files(document_type)')
        
        self.conn.commit()
        
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def extract_ai_content(self, file_path: Path) -> Dict:
        """Extract content from AI file"""
        content = {
            'text_elements': [],
            'fonts': set(),
            'metadata': {},
            'version': None,
            'creator': None,
            'title': None
        }
        
        try:
            # AI files after version 9 are PDF-compatible
            # Try to read as binary and look for text patterns
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                file_content = b''
                chunk_size = 1024 * 1024  # 1MB chunks
                
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    file_content += chunk
                    
                    # Limit total read to 10MB for performance
                    if len(file_content) > 10 * 1024 * 1024:
                        break
                
                # Convert to string, ignoring errors
                text_content = file_content.decode('utf-8', errors='ignore')
                
                # Extract readable text (between BT and ET markers in PDF/AI)
                text_pattern = r'BT\s*(.*?)\s*ET'
                text_matches = re.findall(text_pattern, text_content, re.DOTALL)
                
                for match in text_matches:
                    # Extract actual text from PDF text commands
                    text_commands = re.findall(r'\((.*?)\)\s*Tj', match)
                    for text in text_commands:
                        # Unescape PDF string
                        clean_text = text.replace('\\(', '(').replace('\\)', ')').replace('\\\\', '\\')
                        if clean_text.strip() and len(clean_text) > 1:
                            content['text_elements'].append(clean_text)
                
                # Look for Creator info
                creator_match = re.search(r'%%Creator:\s*(.+?)[\r\n]', text_content)
                if creator_match:
                    content['creator'] = creator_match.group(1).strip()
                    
                # Look for Title
                title_match = re.search(r'%%Title:\s*(.+?)[\r\n]', text_content)
                if title_match:
                    content['title'] = title_match.group(1).strip()
                    
                # Look for Creation Date
                date_match = re.search(r'%%CreationDate:\s*(.+?)[\r\n]', text_content)
                if date_match:
                    content['metadata']['creation_date'] = date_match.group(1).strip()
                    
                # Look for AI version
                version_match = re.search(r'%%AI\d+_', text_content)
                if version_match:
                    content['version'] = version_match.group(0)
                    
                # Extract font references
                font_pattern = r'/([A-Za-z0-9\-]+)\s+findfont'
                fonts = re.findall(font_pattern, text_content)
                content['fonts'] = set(fonts)
                
                # Look for artboard info
                artboard_matches = re.findall(r'%%ArtboardOrigin', text_content)
                content['metadata']['artboard_count'] = len(artboard_matches) if artboard_matches else 1
                
        except Exception as e:
            self.stats['errors'].append({
                'file': str(file_path),
                'error': f"Content extraction error: {str(e)}"
            })
            
        return content
        
    def classify_ai_document(self, filename: str, text_elements: List[str]) -> str:
        """Classify AI document type based on filename and content"""
        filename_lower = filename.lower()
        combined_text = ' '.join(text_elements).lower()
        
        # Logo files
        if 'logo' in filename_lower:
            return 'logo'
            
        # Business cards
        elif any(keyword in filename_lower for keyword in ['card', 'business']):
            return 'business_card'
            
        # Postcards
        elif 'postcard' in filename_lower:
            return 'postcard'
            
        # Letterhead/Stationery
        elif any(keyword in filename_lower for keyword in ['letterhead', 'letter', 'stationery']):
            return 'letterhead'
            
        # Invoices
        elif 'invoice' in filename_lower or 'srt' in filename_lower:
            return 'invoice_template'
            
        # Signatures
        elif 'signature' in filename_lower:
            return 'signature'
            
        # Marketing materials
        elif any(keyword in filename_lower for keyword in ['flyer', 'brochure', 'marketing', 'ad', 'advertisement']):
            return 'marketing'
            
        # Check content for clues
        elif any(keyword in combined_text for keyword in ['invoice', 'bill to', 'amount']):
            return 'invoice_template'
        elif any(keyword in combined_text for keyword in ['email', 'phone', 'address']):
            return 'business_card'
            
        else:
            return 'graphic_design'
            
    def process_ai_file(self, file_path: Path) -> bool:
        """Process a single AI file"""
        try:
            print(f"   Processing: {file_path.name}")
            
            # Get file info
            file_stat = file_path.stat()
            file_size = file_stat.st_size
            file_hash = self.get_file_hash(file_path)
            modification_date = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            # Extract content
            content = self.extract_ai_content(file_path)
            
            # Classify document
            doc_type = self.classify_ai_document(file_path.name, content['text_elements'])
            
            # Combine all text
            all_text = '\n'.join(content['text_elements'])
            
            # Store in database
            cursor = self.conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO ai_files 
                (file_path, file_name, file_size, file_hash,
                 creator, creation_date, modification_date, title,
                 document_type, ai_version, extracted_text, fonts_used,
                 artboard_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(file_path),
                file_path.name,
                file_size,
                file_hash,
                content.get('creator'),
                content['metadata'].get('creation_date'),
                modification_date,
                content.get('title'),
                doc_type,
                content.get('version'),
                all_text[:5000] if all_text else None,
                json.dumps(list(content['fonts'])) if content['fonts'] else None,
                content['metadata'].get('artboard_count', 1)
            ))
            
            ai_file_id = cursor.lastrowid
            
            # Store text elements
            for text in content['text_elements'][:100]:  # Limit to first 100 text elements
                cursor.execute('''
                    INSERT INTO ai_text_elements (ai_file_id, text_content)
                    VALUES (?, ?)
                ''', (ai_file_id, text))
                
            self.conn.commit()
            
            # Update stats
            self.stats['files_processed'] += 1
            if content['text_elements']:
                self.stats['text_extracted'] += 1
            if content.get('creator') or content['metadata']:
                self.stats['metadata_extracted'] += 1
            if content.get('creator'):
                self.stats['creator_found'] += 1
                
            return True
            
        except Exception as e:
            self.stats['errors'].append({
                'file': str(file_path),
                'error': str(e)
            })
            print(f"      ❌ Error: {str(e)}")
            return False
            
    def generate_summary_report(self):
        """Generate summary report"""
        cursor = self.conn.cursor()
        
        print("\n📊 AI FILE PROCESSING REPORT")
        print("=" * 60)
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total files processed: {self.stats['files_processed']}")
        print(f"   Text extracted: {self.stats['text_extracted']}")
        print(f"   Metadata extracted: {self.stats['metadata_extracted']}")
        print(f"   Creator info found: {self.stats['creator_found']}")
        
        # Document types
        print(f"\n🎨 Document Types:")
        cursor.execute('''
            SELECT document_type, COUNT(*) as count
            FROM ai_files
            GROUP BY document_type
            ORDER BY count DESC
        ''')
        
        for doc_type, count in cursor.fetchall():
            print(f"   {doc_type}: {count} files")
            
        # Creators
        print(f"\n👤 Creators/Software:")
        cursor.execute('''
            SELECT creator, COUNT(*) as count
            FROM ai_files
            WHERE creator IS NOT NULL
            GROUP BY creator
            ORDER BY count DESC
            LIMIT 5
        ''')
        
        for creator, count in cursor.fetchall():
            # Truncate long creator strings
            creator_display = creator[:50] + "..." if len(creator) > 50 else creator
            print(f"   {creator_display}: {count} files")
            
        # Files with text
        cursor.execute('''
            SELECT file_name, LENGTH(extracted_text) as text_length
            FROM ai_files
            WHERE extracted_text IS NOT NULL AND LENGTH(extracted_text) > 10
            ORDER BY text_length DESC
            LIMIT 5
        ''')
        
        text_files = cursor.fetchall()
        if text_files:
            print(f"\n📝 Files with Most Text Content:")
            for name, length in text_files:
                print(f"   {name}: {length} characters")
                
        # Common fonts
        print(f"\n🔤 Commonly Used Fonts:")
        all_fonts = []
        cursor.execute('SELECT fonts_used FROM ai_files WHERE fonts_used IS NOT NULL')
        for (fonts_json,) in cursor.fetchall():
            if fonts_json:
                fonts = json.loads(fonts_json)
                all_fonts.extend(fonts)
                
        if all_fonts:
            from collections import Counter
            font_counts = Counter(all_fonts)
            for font, count in font_counts.most_common(5):
                print(f"   {font}: {count} files")
                
        # Errors
        if self.stats['errors']:
            print(f"\n⚠️ Processing Errors ({len(self.stats['errors'])} files):")
            for err in self.stats['errors'][:3]:
                print(f"   - {Path(err['file']).name}: {err['error']}")
                
    def process_all_files(self, directory: str):
        """Process all AI files in directory"""
        ai_files = []
        
        print(f"🔍 Scanning for AI files in {directory}...")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.ai') and not file.startswith('._'):
                    ai_files.append(Path(root) / file)
                    
        print(f"✅ Found {len(ai_files)} AI files to process\n")
        
        # Process each file
        for file_path in ai_files:
            self.process_ai_file(file_path)
            
        # Generate report
        self.generate_summary_report()
        
        # Show sample text
        self.show_sample_content()
        
    def show_sample_content(self):
        """Show sample of extracted text"""
        cursor = self.conn.cursor()
        
        print(f"\n📄 Sample Extracted Text:")
        cursor.execute('''
            SELECT file_name, text_content
            FROM ai_text_elements
            JOIN ai_files ON ai_text_elements.ai_file_id = ai_files.id
            WHERE LENGTH(text_content) > 5
            ORDER BY LENGTH(text_content) DESC
            LIMIT 10
        ''')
        
        shown = set()
        for name, text in cursor.fetchall():
            if text not in shown and len(text) < 100:
                print(f"   {name}: \"{text}\"")
                shown.add(text)

def main():
    """Main entry point"""
    print("🎨 ADOBE ILLUSTRATOR FILE PROCESSOR")
    print("=" * 60)
    
    processor = AIProcessor()
    processor.process_all_files("/home/jonclaude/agents/Hinkey/desktop_ingest_job")
    
    print("\n✅ AI file processing complete!")

if __name__ == "__main__":
    main()