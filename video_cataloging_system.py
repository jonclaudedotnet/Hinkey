#!/usr/bin/env python3
"""
Video Cataloging System
Based on DeepSeek's comprehensive analysis approach
"""

import os
import sqlite3
import cv2
import subprocess
import json
from pathlib import Path
from datetime import datetime
import hashlib
import logging
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

class VideoCatalogSystem:
    """Comprehensive video analysis and cataloging"""
    
    def __init__(self, db_path: str = "video_catalog.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.init_database()
        self.stats = {
            'videos_processed': 0,
            'metadata_extracted': 0,
            'frames_analyzed': 0,
            'transcriptions_attempted': 0,
            'errors': []
        }
        
    def init_database(self):
        """Initialize comprehensive video database"""
        cursor = self.conn.cursor()
        
        # Main videos table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE,
                file_name TEXT,
                file_size INTEGER,
                file_hash TEXT,
                duration REAL,
                resolution TEXT,
                fps REAL,
                codec TEXT,
                creation_date TEXT,
                modification_date TEXT,
                
                -- Analysis results
                keyframes_extracted INTEGER DEFAULT 0,
                has_audio BOOLEAN DEFAULT 0,
                audio_transcribed BOOLEAN DEFAULT 0,
                objects_detected INTEGER DEFAULT 0,
                text_detected BOOLEAN DEFAULT 0,
                
                -- Content classification
                video_type TEXT,
                content_category TEXT,
                quality_score REAL,
                
                processed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Keyframes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keyframes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER,
                frame_number INTEGER,
                timestamp_seconds REAL,
                frame_path TEXT,
                dominant_colors TEXT,
                brightness REAL,
                objects_detected TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(id)
            )
        ''')
        
        # Transcriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER,
                text_content TEXT,
                start_time REAL,
                end_time REAL,
                confidence REAL,
                speaker_id TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(id)
            )
        ''')
        
        # OCR text from video frames
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_text (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER,
                timestamp_seconds REAL,
                text_content TEXT,
                confidence REAL,
                bbox TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_type ON videos(video_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_duration ON videos(duration)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_name ON videos(file_name)')
        
        self.conn.commit()
        
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of video file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large video files
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def extract_video_metadata(self, video_path: Path) -> Dict:
        """Extract comprehensive metadata using ffprobe"""
        metadata = {
            'duration': 0,
            'resolution': 'unknown',
            'fps': 0,
            'codec': 'unknown',
            'has_audio': False,
            'creation_date': None,
            'audio_codec': None
        }
        
        try:
            # Use ffprobe to get detailed metadata
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Extract format information
                if 'format' in data:
                    format_info = data['format']
                    metadata['duration'] = float(format_info.get('duration', 0))
                    
                    # Look for creation time in tags
                    tags = format_info.get('tags', {})
                    for key in ['creation_time', 'date', 'creation_date']:
                        if key in tags:
                            metadata['creation_date'] = tags[key]
                            break
                
                # Extract stream information
                if 'streams' in data:
                    for stream in data['streams']:
                        if stream['codec_type'] == 'video':
                            metadata['resolution'] = f"{stream.get('width', 0)}x{stream.get('height', 0)}"
                            metadata['codec'] = stream.get('codec_name', 'unknown')
                            
                            # Calculate FPS
                            fps_str = stream.get('r_frame_rate', '0/1')
                            if '/' in fps_str:
                                num, den = fps_str.split('/')
                                if float(den) != 0:
                                    metadata['fps'] = float(num) / float(den)
                                    
                        elif stream['codec_type'] == 'audio':
                            metadata['has_audio'] = True
                            metadata['audio_codec'] = stream.get('codec_name', 'unknown')
                            
        except Exception as e:
            self.stats['errors'].append({
                'file': str(video_path),
                'error': f"Metadata extraction error: {str(e)}"
            })
            
        return metadata
        
    def extract_keyframes(self, video_path: Path, interval_seconds: int = 10) -> List[Dict]:
        """Extract keyframes from video for analysis"""
        keyframes = []
        
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return keyframes
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30  # Default assumption
                
            frame_interval = int(fps * interval_seconds)
            frame_count = 0
            keyframe_count = 0
            
            # Create directory for keyframes
            keyframes_dir = Path("video_keyframes") / video_path.stem
            keyframes_dir.mkdir(parents=True, exist_ok=True)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                if frame_count % frame_interval == 0:
                    timestamp = frame_count / fps
                    
                    # Save keyframe
                    frame_filename = f"frame_{keyframe_count:04d}_{timestamp:.1f}s.jpg"
                    frame_path = keyframes_dir / frame_filename
                    cv2.imwrite(str(frame_path), frame)
                    
                    # Analyze frame
                    brightness = cv2.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))[0]
                    
                    keyframes.append({
                        'frame_number': frame_count,
                        'timestamp': timestamp,
                        'frame_path': str(frame_path),
                        'brightness': brightness
                    })
                    
                    keyframe_count += 1
                    self.stats['frames_analyzed'] += 1
                    
                    # Limit keyframes for performance
                    if keyframe_count >= 20:
                        break
                        
                frame_count += 1
                
            cap.release()
            
        except Exception as e:
            self.stats['errors'].append({
                'file': str(video_path),
                'error': f"Keyframe extraction error: {str(e)}"
            })
            
        return keyframes
        
    def classify_video(self, video_path: Path, metadata: Dict) -> Dict:
        """Classify video type and content category"""
        filename = video_path.name.lower()
        
        # Video type classification
        video_type = 'unknown'
        content_category = 'general'
        quality_score = 0.5
        
        # Type based on filename patterns
        if any(pattern in filename for pattern in ['img_', 'dsc_', 'mov_']):
            video_type = 'mobile_video'
        elif any(pattern in filename for pattern in ['screen', 'record', 'capture']):
            video_type = 'screen_recording'
        elif filename.startswith('[') and filename.endswith('].mov'):
            video_type = 'numbered_sequence'
        elif 'hevc' in filename:
            video_type = 'high_efficiency'
            quality_score = 0.8
        
        # Content category based on metadata
        duration = metadata.get('duration', 0)
        resolution = metadata.get('resolution', '')
        
        if duration < 30:
            content_category = 'short_clip'
        elif duration > 300:  # 5 minutes
            content_category = 'long_form'
        elif 'hevc' in filename:
            content_category = 'high_quality'
        
        # Quality assessment
        if '1080' in resolution or '720' in resolution:
            quality_score += 0.2
        if metadata.get('fps', 0) >= 30:
            quality_score += 0.1
        if metadata.get('has_audio'):
            quality_score += 0.1
            
        return {
            'video_type': video_type,
            'content_category': content_category,
            'quality_score': min(quality_score, 1.0)
        }
        
    def process_video(self, video_path: Path) -> bool:
        """Process a single video file"""
        try:
            print(f"   🎬 Processing: {video_path.name}")
            
            # Basic file info
            file_stat = video_path.stat()
            file_size = file_stat.st_size
            file_hash = self.get_file_hash(video_path)
            modification_date = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            # Extract metadata
            metadata = self.extract_video_metadata(video_path)
            if metadata['duration'] > 0:
                self.stats['metadata_extracted'] += 1
                
            # Extract keyframes
            keyframes = self.extract_keyframes(video_path)
            
            # Classify video
            classification = self.classify_video(video_path, metadata)
            
            # Store in database
            cursor = self.conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO videos 
                (file_path, file_name, file_size, file_hash, duration, resolution, fps, codec,
                 creation_date, modification_date, keyframes_extracted, has_audio,
                 video_type, content_category, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(video_path), video_path.name, file_size, file_hash,
                metadata['duration'], metadata['resolution'], metadata['fps'], metadata['codec'],
                metadata['creation_date'], modification_date, len(keyframes), metadata['has_audio'],
                classification['video_type'], classification['content_category'], classification['quality_score']
            ))
            
            video_id = cursor.lastrowid
            
            # Store keyframes
            for keyframe in keyframes:
                cursor.execute('''
                    INSERT INTO keyframes 
                    (video_id, frame_number, timestamp_seconds, frame_path, brightness)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    video_id, keyframe['frame_number'], keyframe['timestamp'],
                    keyframe['frame_path'], keyframe['brightness']
                ))
                
            self.conn.commit()
            self.stats['videos_processed'] += 1
            
            return True
            
        except Exception as e:
            self.stats['errors'].append({
                'file': str(video_path),
                'error': str(e)
            })
            print(f"      ❌ Error: {str(e)}")
            return False
            
    def generate_catalog_report(self):
        """Generate comprehensive video catalog report"""
        cursor = self.conn.cursor()
        
        print("\n📊 VIDEO CATALOG REPORT")
        print("=" * 60)
        
        print(f"\n📈 Processing Statistics:")
        print(f"   Videos processed: {self.stats['videos_processed']}")
        print(f"   Metadata extracted: {self.stats['metadata_extracted']}")
        print(f"   Keyframes analyzed: {self.stats['frames_analyzed']}")
        
        # Video types
        print(f"\n🎬 Video Types:")
        cursor.execute('''
            SELECT video_type, COUNT(*) as count, AVG(duration) as avg_duration
            FROM videos
            GROUP BY video_type
            ORDER BY count DESC
        ''')
        
        for video_type, count, avg_duration in cursor.fetchall():
            duration_str = f"{avg_duration:.1f}s" if avg_duration else "unknown"
            print(f"   {video_type}: {count} videos (avg: {duration_str})")
            
        # Content categories
        print(f"\n📋 Content Categories:")
        cursor.execute('''
            SELECT content_category, COUNT(*) as count, SUM(duration) as total_duration
            FROM videos
            GROUP BY content_category
            ORDER BY count DESC
        ''')
        
        for category, count, total_duration in cursor.fetchall():
            duration_str = f"{total_duration/60:.1f} min" if total_duration else "unknown"
            print(f"   {category}: {count} videos ({duration_str} total)")
            
        # Duration analysis
        cursor.execute('''
            SELECT 
                COUNT(*) as total_videos,
                SUM(duration) as total_duration,
                AVG(duration) as avg_duration,
                MIN(duration) as min_duration,
                MAX(duration) as max_duration
            FROM videos
            WHERE duration > 0
        ''')
        
        stats = cursor.fetchone()
        if stats[0] > 0:
            print(f"\n⏱️ Duration Analysis:")
            print(f"   Total runtime: {stats[1]/3600:.1f} hours")
            print(f"   Average length: {stats[2]:.1f} seconds")
            print(f"   Shortest: {stats[3]:.1f}s, Longest: {stats[4]:.1f}s")
            
        # Quality distribution
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN quality_score >= 0.8 THEN 'High Quality'
                    WHEN quality_score >= 0.6 THEN 'Good Quality'
                    WHEN quality_score >= 0.4 THEN 'Fair Quality'
                    ELSE 'Low Quality'
                END as quality_tier,
                COUNT(*) as count
            FROM videos
            GROUP BY quality_tier
        ''')
        
        print(f"\n🎯 Quality Distribution:")
        for tier, count in cursor.fetchall():
            print(f"   {tier}: {count} videos")
            
        # Sample interesting videos
        cursor.execute('''
            SELECT file_name, duration, resolution, video_type, quality_score
            FROM videos
            WHERE duration > 0
            ORDER BY quality_score DESC, duration DESC
            LIMIT 10
        ''')
        
        print(f"\n🌟 Notable Videos:")
        for filename, duration, resolution, video_type, quality in cursor.fetchall():
            print(f"   {filename[:40]:<40} | {duration:>6.1f}s | {resolution} | {video_type} | Q:{quality:.2f}")
            
        # Errors
        if self.stats['errors']:
            print(f"\n⚠️ Processing Errors ({len(self.stats['errors'])} files):")
            for err in self.stats['errors'][:5]:
                print(f"   - {Path(err['file']).name}: {err['error']}")
                
    def search_videos(self, query: str = None, video_type: str = None, min_duration: float = 0) -> List[Dict]:
        """Search videos by various criteria"""
        cursor = self.conn.cursor()
        
        conditions = []
        params = []
        
        if query:
            conditions.append("file_name LIKE ?")
            params.append(f"%{query}%")
            
        if video_type:
            conditions.append("video_type = ?")
            params.append(video_type)
            
        if min_duration > 0:
            conditions.append("duration >= ?")
            params.append(min_duration)
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        cursor.execute(f'''
            SELECT file_name, duration, resolution, video_type, quality_score, file_path
            FROM videos
            WHERE {where_clause}
            ORDER BY quality_score DESC, duration DESC
        ''', params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'filename': row[0],
                'duration': row[1],
                'resolution': row[2],
                'type': row[3],
                'quality': row[4],
                'path': row[5]
            })
            
        return results
        
    def process_all_videos(self, directory: str):
        """Process all videos in directory"""
        video_extensions = {'.mov', '.mp4', '.avi', '.wmv', '.flv', '.webm', '.mkv', '.m4v'}
        video_files = []
        
        print(f"🔍 Scanning for videos in {directory}...")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if Path(file).suffix.lower() in video_extensions:
                    video_files.append(Path(root) / file)
                    
        print(f"✅ Found {len(video_files)} videos to process\n")
        
        # Process each video
        for video_path in video_files:
            self.process_video(video_path)
            
        # Generate report
        self.generate_catalog_report()
        
        print(f"\n💾 Video catalog saved to: {self.db_path}")
        print(f"🎞️ Keyframes saved to: ./video_keyframes/")

def main():
    """Main entry point"""
    print("🎬 VIDEO CATALOGING SYSTEM")
    print("=" * 60)
    
    cataloger = VideoCatalogSystem()
    cataloger.process_all_videos("/home/jonclaude/agents/Hinkey/desktop_ingest_job")
    
    # Demo search
    print(f"\n🔍 Search Examples:")
    
    # Find high-quality videos
    hq_videos = cataloger.search_videos(video_type="high_efficiency")
    if hq_videos:
        print(f"\n📹 High Efficiency Videos ({len(hq_videos)} found):")
        for video in hq_videos[:5]:
            print(f"   {video['filename']} - {video['duration']:.1f}s - Q:{video['quality']:.2f}")
    
    # Find long videos
    long_videos = cataloger.search_videos(min_duration=60)
    if long_videos:
        print(f"\n⏱️ Videos over 1 minute ({len(long_videos)} found):")
        for video in long_videos[:5]:
            print(f"   {video['filename']} - {video['duration']:.1f}s - {video['resolution']}")
    
    print("\n✅ Video cataloging complete!")

if __name__ == "__main__":
    main()