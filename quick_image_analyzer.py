#!/usr/bin/env python3
"""
Quick Image Analysis System
Fast OCR, Color Analysis, and Indexing
"""

import os
import sqlite3
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import hashlib
import json
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Core libraries
from PIL import Image
import pytesseract
from colorthief import ColorThief
import chromadb

class QuickImageAnalyzer:
    """Fast image analysis focused on OCR and color extraction"""
    
    def __init__(self, db_path: str = "quick_image_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.init_database()
        
        # Initialize ChromaDB for text search
        self.chroma_client = chromadb.PersistentClient(path="./quick_image_vectors")
        self.collection = self.chroma_client.get_or_create_collection(name="images")
        
        self.stats = {
            'files_processed': 0,
            'text_extracted': 0,
            'colors_extracted': 0,
            'errors': []
        }
        
    def init_database(self):
        """Initialize streamlined database"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE,
                file_name TEXT,
                file_size INTEGER,
                file_hash TEXT,
                width INTEGER,
                height INTEGER,
                format TEXT,
                
                -- OCR results
                extracted_text TEXT,
                text_confidence REAL,
                
                -- Color analysis
                dominant_color TEXT,
                color_palette TEXT,
                avg_brightness REAL,
                
                -- Classification
                image_type TEXT,
                has_text BOOLEAN,
                
                processed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_image_type ON images(image_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_has_text ON images(has_text)')
        
        self.conn.commit()
        
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def extract_text_fast(self, image_path: Path) -> Dict:
        """Fast OCR text extraction"""
        text_data = {
            'text': '',
            'confidence': 0.0
        }
        
        try:
            # Use pytesseract with simplified config for speed
            image = cv2.imread(str(image_path))
            if image is None:
                return text_data
                
            # Simple OCR extraction
            text = pytesseract.image_to_string(image).strip()
            
            if text:
                text_data['text'] = text
                text_data['confidence'] = 85.0  # Simplified confidence
                
        except Exception as e:
            self.stats['errors'].append({
                'file': str(image_path),
                'error': f"OCR error: {str(e)}"
            })
            
        return text_data
        
    def extract_colors_fast(self, image_path: Path) -> Dict:
        """Fast color extraction"""
        color_data = {
            'dominant_color': None,
            'palette': [],
            'brightness': 0.0
        }
        
        try:
            # Get dominant color
            color_thief = ColorThief(str(image_path))
            dominant_color = color_thief.get_color(quality=10)  # Lower quality for speed
            color_data['dominant_color'] = dominant_color
            
            # Get 3-color palette
            palette = color_thief.get_palette(color_count=3, quality=10)
            color_data['palette'] = palette
            
            # Quick brightness calculation
            image = cv2.imread(str(image_path))
            if image is not None:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                color_data['brightness'] = float(np.mean(gray))
                
        except Exception as e:
            self.stats['errors'].append({
                'file': str(image_path),
                'error': f"Color error: {str(e)}"
            })
            
        return color_data
        
    def classify_image_fast(self, image_path: Path, text_content: str) -> str:
        """Quick image classification"""
        filename = image_path.name.lower()
        
        # Simple classification based on filename and content
        if any(pattern in filename for pattern in ['screenshot', 'screen']):
            return 'screenshot'
        elif any(pattern in filename for pattern in ['logo', 'brand']):
            return 'logo'
        elif any(pattern in filename for pattern in ['postcard', 'card']):
            return 'business_card'
        elif text_content and len(text_content) > 50:
            return 'document'
        else:
            return 'image'
            
    def process_image_fast(self, image_path: Path) -> bool:
        """Fast image processing"""
        try:
            print(f"   📸 {image_path.name}")
            
            # Basic file info
            file_stat = image_path.stat()
            file_size = file_stat.st_size
            file_hash = self.get_file_hash(image_path)
            
            # Get image dimensions
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    format_type = img.format
            except:
                width = height = 0
                format_type = 'UNKNOWN'
                
            # OCR text extraction
            text_data = self.extract_text_fast(image_path)
            has_text = bool(text_data['text'])
            if has_text:
                self.stats['text_extracted'] += 1
                
            # Color analysis
            color_data = self.extract_colors_fast(image_path)
            if color_data['dominant_color']:
                self.stats['colors_extracted'] += 1
                
            # Classification
            image_type = self.classify_image_fast(image_path, text_data['text'])
            
            # Store in database
            cursor = self.conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO images 
                (file_path, file_name, file_size, file_hash, width, height, format,
                 extracted_text, text_confidence, dominant_color, color_palette, 
                 avg_brightness, image_type, has_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(image_path), image_path.name, file_size, file_hash,
                width, height, format_type,
                text_data['text'], text_data['confidence'],
                json.dumps(color_data['dominant_color']) if color_data['dominant_color'] else None,
                json.dumps(color_data['palette']),
                color_data['brightness'], image_type, has_text
            ))
            
            image_id = cursor.lastrowid
            
            # Store in ChromaDB for text search
            if text_data['text']:
                search_text = f"{text_data['text']} {image_type} {image_path.name}"
                
                self.collection.add(
                    documents=[search_text],
                    metadatas=[{
                        'file_path': str(image_path),
                        'file_name': image_path.name,
                        'image_type': image_type,
                        'has_text': has_text
                    }],
                    ids=[f"img_{image_id}"]
                )
            
            self.conn.commit()
            self.stats['files_processed'] += 1
            
            return True
            
        except Exception as e:
            self.stats['errors'].append({
                'file': str(image_path),
                'error': str(e)
            })
            return False
            
    def generate_report(self):
        """Generate quick analysis report"""
        cursor = self.conn.cursor()
        
        print("\n📊 QUICK IMAGE ANALYSIS REPORT")
        print("=" * 60)
        
        print(f"\n📈 Processing Results:")
        print(f"   Images processed: {self.stats['files_processed']}")
        print(f"   Text extracted: {self.stats['text_extracted']}")
        print(f"   Colors analyzed: {self.stats['colors_extracted']}")
        
        # Image types
        print(f"\n🖼️ Image Types:")
        cursor.execute('''
            SELECT image_type, COUNT(*) as count
            FROM images
            GROUP BY image_type
            ORDER BY count DESC
        ''')
        
        for img_type, count in cursor.fetchall():
            print(f"   {img_type}: {count} images")
            
        # Text extraction samples
        cursor.execute('''
            SELECT file_name, extracted_text
            FROM images
            WHERE extracted_text IS NOT NULL 
            AND LENGTH(extracted_text) > 10
            ORDER BY LENGTH(extracted_text) DESC
            LIMIT 5
        ''')
        
        sample_text = cursor.fetchall()
        if sample_text:
            print(f"\n📄 Sample Extracted Text:")
            for filename, text in sample_text:
                preview = text[:80] + "..." if len(text) > 80 else text
                preview = preview.replace('\n', ' ')
                print(f"   {filename}: \"{preview}\"")
                
        # Color analysis
        cursor.execute('''
            SELECT AVG(avg_brightness) as avg_brightness
            FROM images
            WHERE avg_brightness > 0
        ''')
        
        brightness_avg = cursor.fetchone()[0]
        if brightness_avg:
            print(f"\n🎨 Color Analysis:")
            print(f"   Average brightness: {brightness_avg:.1f}")
            
        # Errors
        if self.stats['errors']:
            print(f"\n⚠️ Errors: {len(self.stats['errors'])} files had issues")
            
        print(f"\n💾 Data stored in:")
        print(f"   Database: {self.db_path}")
        print(f"   Vector search: ./quick_image_vectors/")
        
    def search_images(self, query: str, limit: int = 5) -> List[Dict]:
        """Search images by text content"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            search_results = []
            if results['metadatas']:
                for i, metadata in enumerate(results['metadatas'][0]):
                    search_results.append({
                        'file_name': metadata['file_name'],
                        'file_path': metadata['file_path'],
                        'image_type': metadata['image_type'],
                        'similarity': 1.0 - results['distances'][0][i] if results['distances'] else 0.5
                    })
                    
            return search_results
        except:
            return []
            
    def process_all_images(self, directory: str):
        """Process all images quickly"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
        image_files = []
        
        print(f"🔍 Scanning for images...")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if Path(file).suffix.lower() in image_extensions:
                    image_files.append(Path(root) / file)
                    
        print(f"✅ Found {len(image_files)} images")
        print(f"\n🚀 Processing images...")
        
        # Process efficiently
        for image_path in image_files:
            self.process_image_fast(image_path)
            
        # Generate report
        self.generate_report()

def main():
    """Main entry point"""
    print("⚡ QUICK IMAGE ANALYSIS SYSTEM")
    print("=" * 60)
    
    analyzer = QuickImageAnalyzer()
    analyzer.process_all_images("/home/jonclaude/agents/Hinkey/desktop_ingest_job")
    
    # Demo search
    print(f"\n🔍 Testing search capabilities...")
    results = analyzer.search_images("SeaRobin Tech logo")
    if results:
        print("   Search results for 'SeaRobin Tech logo':")
        for result in results[:3]:
            print(f"   - {result['file_name']} ({result['image_type']})")
    
    print("\n✅ Quick analysis complete!")

if __name__ == "__main__":
    main()