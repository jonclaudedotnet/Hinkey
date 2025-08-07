#!/usr/bin/env python3
"""
PDF Document Processor
Extracts text and metadata from PDFs, stores in database
"""

import os
import sqlite3
import PyPDF2
import pdfplumber
from pathlib import Path
from datetime import datetime
import re
import hashlib
from typing import Dict, List, Optional
import json

class PDFProcessor:
    """Process PDF files and extract structured data"""
    
    def __init__(self, db_path: str = "pdf_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.init_database()
        self.stats = {
            'files_processed': 0,
            'text_extracted': 0,
            'metadata_extracted': 0,
            'invoices_found': 0,
            'contracts_found': 0,
            'errors': []
        }
        
    def init_database(self):
        """Initialize PDF database schema"""
        cursor = self.conn.cursor()
        
        # Main PDFs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pdfs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE,
                file_name TEXT,
                file_size INTEGER,
                page_count INTEGER,
                file_hash TEXT,
                creation_date TEXT,
                modification_date TEXT,
                author TEXT,
                title TEXT,
                subject TEXT,
                document_type TEXT,
                extracted_text TEXT,
                key_entities TEXT,
                processed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Extracted entities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pdf_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pdf_id INTEGER,
                entity_type TEXT,
                entity_value TEXT,
                confidence REAL,
                page_number INTEGER,
                FOREIGN KEY (pdf_id) REFERENCES pdfs(id)
            )
        ''')
        
        # Document relationships
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pdf_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pdf_id INTEGER,
                related_type TEXT,
                related_value TEXT,
                relationship_type TEXT,
                FOREIGN KEY (pdf_id) REFERENCES pdfs(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_document_type ON pdfs(document_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_name ON pdfs(file_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entity_type ON pdf_entities(entity_type)')
        
        self.conn.commit()
        
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def extract_metadata(self, file_path: Path) -> Dict:
        """Extract PDF metadata"""
        metadata = {
            'page_count': 0,
            'author': None,
            'title': None,
            'subject': None,
            'creation_date': None,
            'modification_date': None
        }
        
        try:
            with open(file_path, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                metadata['page_count'] = len(pdf.pages)
                
                if pdf.metadata:
                    info = pdf.metadata
                    metadata['author'] = info.get('/Author', None)
                    metadata['title'] = info.get('/Title', None)
                    metadata['subject'] = info.get('/Subject', None)
                    
                    # Convert dates
                    if '/CreationDate' in info:
                        try:
                            metadata['creation_date'] = str(info['/CreationDate'])
                        except:
                            pass
                            
                    if '/ModDate' in info:
                        try:
                            metadata['modification_date'] = str(info['/ModDate'])
                        except:
                            pass
                            
        except Exception as e:
            self.stats['errors'].append({
                'file': str(file_path),
                'error': f"Metadata extraction error: {str(e)}"
            })
            
        return metadata
        
    def extract_text(self, file_path: Path) -> str:
        """Extract text content from PDF"""
        text = ""
        
        try:
            # Try pdfplumber first (better for tables and complex layouts)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        
            # If no text extracted, try PyPDF2
            if not text.strip():
                with open(file_path, 'rb') as file:
                    pdf = PyPDF2.PdfReader(file)
                    for page in pdf.pages:
                        try:
                            text += page.extract_text() + "\n"
                        except:
                            pass
                            
        except Exception as e:
            self.stats['errors'].append({
                'file': str(file_path),
                'error': f"Text extraction error: {str(e)}"
            })
            
        return text.strip()
        
    def classify_document(self, text: str, filename: str) -> str:
        """Classify document type based on content and filename"""
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Invoice indicators
        if any(keyword in text_lower for keyword in ['invoice', 'bill to', 'invoice number', 'amount due', 'payment terms']):
            return 'invoice'
        elif any(keyword in filename_lower for keyword in ['invoice', 'inv', 'bill']):
            return 'invoice'
            
        # Contract indicators  
        elif any(keyword in text_lower for keyword in ['agreement', 'contract', 'terms and conditions', 'party', 'whereas']):
            return 'contract'
        elif any(keyword in filename_lower for keyword in ['contract', 'agreement', 'mou']):
            return 'contract'
            
        # Receipt indicators
        elif any(keyword in text_lower for keyword in ['receipt', 'payment received', 'transaction']):
            return 'receipt'
            
        # Report indicators
        elif any(keyword in text_lower for keyword in ['report', 'analysis', 'summary', 'findings']):
            return 'report'
            
        # Letter/correspondence
        elif any(keyword in text_lower for keyword in ['dear', 'sincerely', 'regards']):
            return 'correspondence'
            
        # Forms
        elif any(keyword in text_lower for keyword in ['form', 'application', 'fill out']):
            return 'form'
            
        # Financial statements
        elif any(keyword in text_lower for keyword in ['balance sheet', 'income statement', 'financial statement']):
            return 'financial_statement'
            
        else:
            return 'general_document'
            
    def extract_entities(self, text: str) -> List[Dict]:
        """Extract key entities from text"""
        entities = []
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        for email in emails:
            entities.append({
                'type': 'email',
                'value': email,
                'confidence': 0.9
            })
            
        # Extract phone numbers
        phone_pattern = r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{4,6}'
        phones = re.findall(phone_pattern, text)
        for phone in phones:
            if len(phone) >= 10:  # Basic validation
                entities.append({
                    'type': 'phone',
                    'value': phone,
                    'confidence': 0.8
                })
                
        # Extract dollar amounts
        dollar_pattern = r'\$[\d,]+\.?\d*'
        amounts = re.findall(dollar_pattern, text)
        for amount in amounts:
            entities.append({
                'type': 'money',
                'value': amount,
                'confidence': 0.9
            })
            
        # Extract dates
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}'
        ]
        
        for pattern in date_patterns:
            dates = re.findall(pattern, text, re.IGNORECASE)
            for date in dates:
                entities.append({
                    'type': 'date',
                    'value': date,
                    'confidence': 0.85
                })
                
        # Extract potential invoice numbers
        invoice_patterns = [
            r'(?:Invoice|Inv|Bill)[\s#:]*([A-Z0-9-]+)',
            r'SRT\d+',
            r'#\d{4,}'
        ]
        
        for pattern in invoice_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'type': 'invoice_number',
                    'value': match,
                    'confidence': 0.7
                })
                
        return entities
        
    def process_pdf_file(self, file_path: Path) -> bool:
        """Process a single PDF file"""
        try:
            # Get file info
            file_size = file_path.stat().st_size
            file_hash = self.get_file_hash(file_path)
            
            # Extract metadata
            metadata = self.extract_metadata(file_path)
            
            # Extract text
            text = self.extract_text(file_path)
            
            # Classify document
            doc_type = self.classify_document(text, file_path.name)
            
            # Extract entities
            entities = self.extract_entities(text)
            
            # Store in database
            cursor = self.conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO pdfs 
                (file_path, file_name, file_size, page_count, file_hash,
                 creation_date, modification_date, author, title, subject,
                 document_type, extracted_text, key_entities)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(file_path),
                file_path.name,
                file_size,
                metadata['page_count'],
                file_hash,
                metadata['creation_date'],
                metadata['modification_date'],
                metadata['author'],
                metadata['title'],
                metadata['subject'],
                doc_type,
                text[:10000] if text else None,  # Limit text storage
                json.dumps(entities)
            ))
            
            pdf_id = cursor.lastrowid
            
            # Store entities
            for entity in entities:
                cursor.execute('''
                    INSERT INTO pdf_entities (pdf_id, entity_type, entity_value, confidence)
                    VALUES (?, ?, ?, ?)
                ''', (pdf_id, entity['type'], entity['value'], entity['confidence']))
                
            self.conn.commit()
            
            # Update stats
            self.stats['files_processed'] += 1
            if text:
                self.stats['text_extracted'] += 1
            if metadata['page_count'] > 0:
                self.stats['metadata_extracted'] += 1
                
            if doc_type == 'invoice':
                self.stats['invoices_found'] += 1
            elif doc_type == 'contract':
                self.stats['contracts_found'] += 1
                
            return True
            
        except Exception as e:
            self.stats['errors'].append({
                'file': str(file_path),
                'error': str(e)
            })
            return False
            
    def generate_summary_report(self):
        """Generate summary report of PDF processing"""
        cursor = self.conn.cursor()
        
        print("\n📊 PDF PROCESSING REPORT")
        print("=" * 60)
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total files processed: {self.stats['files_processed']}")
        print(f"   Text extracted: {self.stats['text_extracted']}")
        print(f"   Metadata extracted: {self.stats['metadata_extracted']}")
        print(f"   Invoices found: {self.stats['invoices_found']}")
        print(f"   Contracts found: {self.stats['contracts_found']}")
        
        # Document type breakdown
        print(f"\n📄 Document Types:")
        cursor.execute('''
            SELECT document_type, COUNT(*) as count
            FROM pdfs
            GROUP BY document_type
            ORDER BY count DESC
        ''')
        
        for doc_type, count in cursor.fetchall():
            print(f"   {doc_type}: {count} files")
            
        # Top entities
        print(f"\n🔍 Top Extracted Entities:")
        cursor.execute('''
            SELECT entity_type, COUNT(*) as count
            FROM pdf_entities
            GROUP BY entity_type
            ORDER BY count DESC
            LIMIT 5
        ''')
        
        for entity_type, count in cursor.fetchall():
            print(f"   {entity_type}: {count} occurrences")
            
        # Errors
        if self.stats['errors']:
            print(f"\n⚠️ Processing Errors ({len(self.stats['errors'])} files):")
            for err in self.stats['errors'][:5]:
                print(f"   - {Path(err['file']).name}: {err['error']}")
                
    def process_all_files(self, directory: str):
        """Process all PDF files in directory"""
        pdf_files = []
        
        print(f"🔍 Scanning for PDF files in {directory}...")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(Path(root) / file)
                    
        print(f"✅ Found {len(pdf_files)} PDF files to process")
        
        # Process each file
        for i, file_path in enumerate(pdf_files, 1):
            if i % 10 == 0:
                print(f"   Processing: {i}/{len(pdf_files)} files...")
                
            self.process_pdf_file(file_path)
            
        # Generate report
        self.generate_summary_report()
        
        # Save detailed results
        self.save_detailed_results()
        
    def save_detailed_results(self):
        """Save detailed results for analysis"""
        output_dir = Path("pdf_analysis_results")
        output_dir.mkdir(exist_ok=True)
        
        # Export document summary
        cursor = self.conn.cursor()
        
        # Document list with key info
        with open(output_dir / "pdf_summary.txt", "w") as f:
            cursor.execute('''
                SELECT file_name, document_type, page_count, file_size
                FROM pdfs
                ORDER BY document_type, file_name
            ''')
            
            f.write("PDF Document Summary\n")
            f.write("=" * 60 + "\n\n")
            
            current_type = None
            for name, doc_type, pages, size in cursor.fetchall():
                if doc_type != current_type:
                    f.write(f"\n{doc_type.upper()}\n")
                    f.write("-" * 40 + "\n")
                    current_type = doc_type
                    
                size_mb = size / (1024 * 1024)
                f.write(f"{name} - {pages} pages, {size_mb:.1f} MB\n")
                
        print(f"\n💾 Results saved to {output_dir}/")

def main():
    """Main entry point"""
    print("📄 PDF DOCUMENT PROCESSOR")
    print("=" * 60)
    
    processor = PDFProcessor()
    processor.process_all_files("/home/jonclaude/agents/Hinkey/desktop_ingest_job")
    
    print("\n✅ PDF processing complete!")

if __name__ == "__main__":
    main()