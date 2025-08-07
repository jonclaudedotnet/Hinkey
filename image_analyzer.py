#!/usr/bin/env python3
"""
Comprehensive Image Analysis System
OCR, Color Analysis, Object Detection, Visual Embeddings
"""

import os
import sqlite3
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import hashlib
import json
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Core libraries
from PIL import Image, ExifTags
import pytesseract
from colorthief import ColorThief
from sklearn.cluster import KMeans

# AI/ML libraries  
import torch
from transformers import CLIPProcessor, CLIPModel
from ultralytics import YOLO
from sentence_transformers import SentenceTransformer

# Database
import chromadb
from chromadb.utils import embedding_functions

class ImageAnalyzer:
    """Comprehensive image analysis with OCR, colors, objects, and embeddings"""
    
    def __init__(self, db_path: str = "image_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.init_database()
        
        # Initialize AI models
        print("🤖 Loading AI models...")
        self.load_models()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./image_vectors")
        self.collection = self.chroma_client.get_or_create_collection(
            name="images",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )
        
        self.stats = {
            'files_processed': 0,
            'text_extracted': 0,
            'colors_extracted': 0,
            'objects_detected': 0,
            'embeddings_created': 0,
            'errors': []
        }
        
    def load_models(self):
        """Load all AI models"""
        try:
            # CLIP for visual understanding
            print("   Loading CLIP model...")
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            
            # YOLO for object detection
            print("   Loading YOLO model...")
            self.yolo_model = YOLO('yolov8n.pt')
            
            print("✅ All models loaded successfully")
            
        except Exception as e:
            print(f"⚠️ Model loading error: {e}")
            self.clip_model = None
            self.yolo_model = None
            
    def init_database(self):
        """Initialize image analysis database"""
        cursor = self.conn.cursor()
        
        # Main images table
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
                mode TEXT,
                
                -- EXIF data
                camera_make TEXT,
                camera_model TEXT,
                taken_datetime TEXT,
                gps_latitude REAL,
                gps_longitude REAL,
                
                -- OCR results
                extracted_text TEXT,
                text_confidence REAL,
                text_blocks_count INTEGER,
                
                -- Color analysis
                dominant_colors TEXT,
                color_palette TEXT,
                avg_brightness REAL,
                color_variance REAL,
                
                -- Object detection
                objects_detected TEXT,
                object_count INTEGER,
                faces_detected INTEGER,
                
                -- Visual embeddings
                clip_embedding TEXT,
                image_caption TEXT,
                
                -- Classification
                image_type TEXT,
                content_category TEXT,
                quality_score REAL,
                
                processed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Text regions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS text_regions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER,
                text_content TEXT,
                confidence REAL,
                bbox_x INTEGER,
                bbox_y INTEGER,
                bbox_width INTEGER,
                bbox_height INTEGER,
                FOREIGN KEY (image_id) REFERENCES images(id)
            )
        ''')
        
        # Objects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detected_objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER,
                object_class TEXT,
                confidence REAL,
                bbox_x REAL,
                bbox_y REAL,
                bbox_width REAL,
                bbox_height REAL,
                FOREIGN KEY (image_id) REFERENCES images(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_image_type ON images(image_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_category ON images(content_category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_name ON images(file_name)')
        
        self.conn.commit()
        
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def extract_exif_data(self, image: Image.Image) -> Dict:
        """Extract EXIF metadata from image"""
        exif_data = {}
        
        try:
            exif = image._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    
                    if tag == 'Make':
                        exif_data['camera_make'] = str(value)
                    elif tag == 'Model':
                        exif_data['camera_model'] = str(value)
                    elif tag == 'DateTime':
                        exif_data['taken_datetime'] = str(value)
                    elif tag == 'GPSInfo':
                        # Extract GPS coordinates if available
                        gps_info = value
                        if 2 in gps_info and 4 in gps_info:  # Latitude and Longitude
                            lat = self.convert_gps_coordinate(gps_info[2], gps_info[1])
                            lon = self.convert_gps_coordinate(gps_info[4], gps_info[3])
                            exif_data['gps_latitude'] = lat
                            exif_data['gps_longitude'] = lon
                            
        except Exception as e:
            pass
            
        return exif_data
        
    def convert_gps_coordinate(self, coord, ref):
        """Convert GPS coordinate to decimal degrees"""
        try:
            degrees = float(coord[0])
            minutes = float(coord[1])
            seconds = float(coord[2])
            
            decimal = degrees + minutes/60 + seconds/3600
            
            if ref in ['S', 'W']:
                decimal = -decimal
                
            return decimal
        except:
            return None
            
    def extract_text_ocr(self, image_path: Path) -> Dict:
        """Extract text using OCR"""
        text_data = {
            'text': '',
            'confidence': 0.0,
            'blocks': [],
            'block_count': 0
        }
        
        try:
            # Use pytesseract for OCR
            image = cv2.imread(str(image_path))
            if image is None:
                return text_data
                
            # Get detailed OCR data
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Extract text blocks with confidence > 30
            valid_text = []
            text_blocks = []
            
            for i in range(len(ocr_data['text'])):
                confidence = ocr_data['conf'][i]
                text = ocr_data['text'][i].strip()
                
                if confidence > 30 and text:
                    valid_text.append(text)
                    
                    text_blocks.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': {
                            'x': ocr_data['left'][i],
                            'y': ocr_data['top'][i],
                            'width': ocr_data['width'][i],
                            'height': ocr_data['height'][i]
                        }
                    })
                    
            text_data['text'] = ' '.join(valid_text)
            text_data['blocks'] = text_blocks
            text_data['block_count'] = len(text_blocks)
            
            if text_blocks:
                text_data['confidence'] = sum(b['confidence'] for b in text_blocks) / len(text_blocks)
                
        except Exception as e:
            self.stats['errors'].append({
                'file': str(image_path),
                'error': f"OCR error: {str(e)}"
            })
            
        return text_data
        
    def extract_colors(self, image_path: Path) -> Dict:
        """Extract color palette and analysis"""
        color_data = {
            'dominant_colors': [],
            'palette': [],
            'brightness': 0.0,
            'variance': 0.0
        }
        
        try:
            # Use ColorThief for dominant colors
            color_thief = ColorThief(str(image_path))
            
            # Get dominant color
            dominant_color = color_thief.get_color(quality=1)
            color_data['dominant_colors'] = [dominant_color]
            
            # Get color palette
            palette = color_thief.get_palette(color_count=5, quality=1)
            color_data['palette'] = palette
            
            # Additional analysis with OpenCV
            image = cv2.imread(str(image_path))
            if image is not None:
                # Convert to RGB
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Calculate brightness
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                color_data['brightness'] = float(np.mean(gray))
                
                # Calculate color variance
                color_data['variance'] = float(np.var(image_rgb))
                
        except Exception as e:
            self.stats['errors'].append({
                'file': str(image_path),
                'error': f"Color extraction error: {str(e)}"
            })
            
        return color_data
        
    def detect_objects(self, image_path: Path) -> Dict:
        """Detect objects using YOLO"""
        object_data = {
            'objects': [],
            'object_count': 0,
            'faces': 0
        }
        
        if not self.yolo_model:
            return object_data
            
        try:
            # Run YOLO detection
            results = self.yolo_model(str(image_path))
            
            detected_objects = []
            face_count = 0
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get class name
                        class_id = int(box.cls[0])
                        class_name = self.yolo_model.names[class_id]
                        confidence = float(box.conf[0])
                        
                        # Get bounding box
                        bbox = box.xyxy[0].tolist()
                        
                        detected_objects.append({
                            'class': class_name,
                            'confidence': confidence,
                            'bbox': {
                                'x': bbox[0],
                                'y': bbox[1],
                                'width': bbox[2] - bbox[0],
                                'height': bbox[3] - bbox[1]
                            }
                        })
                        
                        # Count faces (person class)
                        if class_name == 'person':
                            face_count += 1
                            
            object_data['objects'] = detected_objects
            object_data['object_count'] = len(detected_objects)
            object_data['faces'] = face_count
            
        except Exception as e:
            self.stats['errors'].append({
                'file': str(image_path),
                'error': f"Object detection error: {str(e)}"
            })
            
        return object_data
        
    def generate_visual_embedding(self, image_path: Path) -> Dict:
        """Generate CLIP embeddings and caption"""
        embedding_data = {
            'embedding': None,
            'caption': ''
        }
        
        if not self.clip_model:
            return embedding_data
            
        try:
            # Load and process image
            image = Image.open(image_path).convert('RGB')
            
            # Generate embedding
            inputs = self.clip_processor(images=image, return_tensors="pt")
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)
                embedding_data['embedding'] = image_features[0].tolist()
                
            # Simple caption generation (could be enhanced)
            # For now, we'll use a basic approach
            embedding_data['caption'] = f"Image containing visual content"
            
        except Exception as e:
            self.stats['errors'].append({
                'file': str(image_path),
                'error': f"Embedding generation error: {str(e)}"
            })
            
        return embedding_data
        
    def classify_image(self, image_path: Path, text_content: str, objects: List) -> Dict:
        """Classify image type and content category"""
        filename = image_path.name.lower()
        
        # Image type classification
        image_type = 'unknown'
        content_category = 'general'
        
        # Type based on filename patterns
        if any(pattern in filename for pattern in ['screenshot', 'screen', 'capture']):
            image_type = 'screenshot'
        elif any(pattern in filename for pattern in ['logo', 'brand']):
            image_type = 'logo'
        elif any(pattern in filename for pattern in ['photo', 'img', 'pic']):
            image_type = 'photograph'
        elif any(pattern in filename for pattern in ['diagram', 'chart', 'graph']):
            image_type = 'diagram'
        elif any(pattern in filename for pattern in ['doc', 'scan', 'pdf']):
            image_type = 'document'
        
        # Content category based on text and objects
        if text_content:
            text_lower = text_content.lower()
            if any(word in text_lower for word in ['invoice', 'bill', 'payment', '$']):
                content_category = 'financial'
            elif any(word in text_lower for word in ['email', 'message', 'letter']):
                content_category = 'communication'
            elif any(word in text_lower for word in ['menu', 'options', 'settings']):
                content_category = 'interface'
            elif len(text_content) > 100:
                content_category = 'document'
        
        # Object-based classification
        object_classes = [obj['class'] for obj in objects]
        if 'person' in object_classes:
            content_category = 'people'
        elif any(obj in object_classes for obj in ['car', 'truck', 'bus']):
            content_category = 'vehicles'
        elif any(obj in object_classes for obj in ['building', 'house']):
            content_category = 'architecture'
        
        return {
            'image_type': image_type,
            'content_category': content_category,
            'quality_score': 0.8  # Placeholder - could implement actual quality assessment
        }
        
    def process_image(self, image_path: Path) -> bool:
        """Process a single image with all analysis methods"""
        try:
            print(f"   📸 Processing: {image_path.name}")
            
            # Basic file info
            file_stat = image_path.stat()
            file_size = file_stat.st_size
            file_hash = self.get_file_hash(image_path)
            
            # Open image for basic info
            with Image.open(image_path) as img:
                width, height = img.size
                format_type = img.format
                mode = img.mode
                
                # Extract EXIF data
                exif_data = self.extract_exif_data(img)
                
            # OCR text extraction
            text_data = self.extract_text_ocr(image_path)
            if text_data['text']:
                self.stats['text_extracted'] += 1
                
            # Color analysis
            color_data = self.extract_colors(image_path)
            if color_data['dominant_colors']:
                self.stats['colors_extracted'] += 1
                
            # Object detection
            object_data = self.detect_objects(image_path)
            if object_data['objects']:
                self.stats['objects_detected'] += 1
                
            # Visual embeddings
            embedding_data = self.generate_visual_embedding(image_path)
            if embedding_data['embedding']:
                self.stats['embeddings_created'] += 1
                
            # Image classification
            classification = self.classify_image(
                image_path, 
                text_data['text'], 
                object_data['objects']
            )
            
            # Store in database
            cursor = self.conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO images 
                (file_path, file_name, file_size, file_hash, width, height, format, mode,
                 camera_make, camera_model, taken_datetime, gps_latitude, gps_longitude,
                 extracted_text, text_confidence, text_blocks_count,
                 dominant_colors, color_palette, avg_brightness, color_variance,
                 objects_detected, object_count, faces_detected,
                 clip_embedding, image_caption,
                 image_type, content_category, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(image_path), image_path.name, file_size, file_hash,
                width, height, format_type, mode,
                exif_data.get('camera_make'), exif_data.get('camera_model'),
                exif_data.get('taken_datetime'), exif_data.get('gps_latitude'),
                exif_data.get('gps_longitude'),
                text_data['text'], text_data['confidence'], text_data['block_count'],
                json.dumps(color_data['dominant_colors']), json.dumps(color_data['palette']),
                color_data['brightness'], color_data['variance'],
                json.dumps(object_data['objects']), object_data['object_count'],
                object_data['faces'],
                json.dumps(embedding_data['embedding']) if embedding_data['embedding'] else None,
                embedding_data['caption'],
                classification['image_type'], classification['content_category'],
                classification['quality_score']
            ))
            
            image_id = cursor.lastrowid
            
            # Store text regions
            for block in text_data['blocks']:
                cursor.execute('''
                    INSERT INTO text_regions 
                    (image_id, text_content, confidence, bbox_x, bbox_y, bbox_width, bbox_height)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    image_id, block['text'], block['confidence'],
                    block['bbox']['x'], block['bbox']['y'],
                    block['bbox']['width'], block['bbox']['height']
                ))
                
            # Store detected objects
            for obj in object_data['objects']:
                cursor.execute('''
                    INSERT INTO detected_objects
                    (image_id, object_class, confidence, bbox_x, bbox_y, bbox_width, bbox_height)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    image_id, obj['class'], obj['confidence'],
                    obj['bbox']['x'], obj['bbox']['y'],
                    obj['bbox']['width'], obj['bbox']['height']
                ))
                
            # Store in ChromaDB for vector search
            if text_data['text'] or embedding_data['caption']:
                search_text = f"{text_data['text']} {embedding_data['caption']} {classification['image_type']} {classification['content_category']}"
                
                self.collection.add(
                    documents=[search_text],
                    metadatas=[{
                        'file_path': str(image_path),
                        'file_name': image_path.name,
                        'image_type': classification['image_type'],
                        'content_category': classification['content_category'],
                        'has_text': bool(text_data['text']),
                        'object_count': object_data['object_count']
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
            print(f"      ❌ Error: {str(e)}")
            return False
            
    def generate_summary_report(self):
        """Generate comprehensive analysis report"""
        cursor = self.conn.cursor()
        
        print("\n📊 IMAGE ANALYSIS REPORT")
        print("=" * 60)
        
        print(f"\n📈 Processing Statistics:")
        print(f"   Total images processed: {self.stats['files_processed']}")
        print(f"   Text extracted: {self.stats['text_extracted']}")
        print(f"   Colors analyzed: {self.stats['colors_extracted']}")
        print(f"   Objects detected: {self.stats['objects_detected']}")
        print(f"   Embeddings created: {self.stats['embeddings_created']}")
        
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
            
        # Content categories
        print(f"\n📋 Content Categories:")
        cursor.execute('''
            SELECT content_category, COUNT(*) as count
            FROM images
            GROUP BY content_category
            ORDER BY count DESC
        ''')
        
        for category, count in cursor.fetchall():
            print(f"   {category}: {count} images")
            
        # Text extraction stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_with_text,
                AVG(text_confidence) as avg_confidence,
                SUM(text_blocks_count) as total_blocks
            FROM images
            WHERE extracted_text IS NOT NULL AND extracted_text != ''
        ''')
        
        text_stats = cursor.fetchone()
        if text_stats[0] > 0:
            print(f"\n📝 Text Extraction:")
            print(f"   Images with text: {text_stats[0]}")
            print(f"   Average confidence: {text_stats[1]:.1f}%")
            print(f"   Total text blocks: {text_stats[2]}")
            
        # Object detection stats
        cursor.execute('''
            SELECT 
                COUNT(*) as images_with_objects,
                SUM(object_count) as total_objects,
                SUM(faces_detected) as total_faces
            FROM images
            WHERE object_count > 0
        ''')
        
        obj_stats = cursor.fetchone()
        if obj_stats[0] > 0:
            print(f"\n🎯 Object Detection:")
            print(f"   Images with objects: {obj_stats[0]}")
            print(f"   Total objects detected: {obj_stats[1]}")
            print(f"   People detected: {obj_stats[2]}")
            
        # Most common objects
        cursor.execute('''
            SELECT object_class, COUNT(*) as count
            FROM detected_objects
            GROUP BY object_class
            ORDER BY count DESC
            LIMIT 5
        ''')
        
        common_objects = cursor.fetchall()
        if common_objects:
            print(f"\n🔍 Most Common Objects:")
            for obj_class, count in common_objects:
                print(f"   {obj_class}: {count} detections")
                
        # Sample extracted text
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
                preview = text[:100] + "..." if len(text) > 100 else text
                print(f"   {filename}: \"{preview}\"")
                
        # Errors
        if self.stats['errors']:
            print(f"\n⚠️ Processing Errors ({len(self.stats['errors'])} files):")
            for err in self.stats['errors'][:5]:
                print(f"   - {Path(err['file']).name}: {err['error']}")
                
    def process_all_images(self, directory: str):
        """Process all images in directory"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
        image_files = []
        
        print(f"🔍 Scanning for images in {directory}...")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if Path(file).suffix.lower() in image_extensions:
                    image_files.append(Path(root) / file)
                    
        print(f"✅ Found {len(image_files)} images to process\n")
        
        # Process each image
        for image_path in image_files:
            self.process_image(image_path)
            
        # Generate report
        self.generate_summary_report()
        
        print(f"\n💾 Results stored in:")
        print(f"   SQLite database: {self.db_path}")
        print(f"   Vector database: ./image_vectors/")

def main():
    """Main entry point"""
    print("🎨 COMPREHENSIVE IMAGE ANALYSIS SYSTEM")
    print("=" * 60)
    
    analyzer = ImageAnalyzer()
    analyzer.process_all_images("/home/jonclaude/agents/Hinkey/desktop_ingest_job")
    
    print("\n✅ Image analysis complete!")

if __name__ == "__main__":
    main()