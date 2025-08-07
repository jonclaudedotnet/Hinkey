#!/usr/bin/env python3
"""
Quick Video Cataloger
Fast metadata extraction and basic analysis
"""

import os
import sqlite3
import subprocess
import json
from pathlib import Path
from datetime import datetime
import hashlib
from typing import Dict, List

class QuickVideoCataloger:
    """Fast video metadata extraction and cataloging"""
    
    def __init__(self, db_path: str = "quick_video_catalog.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.init_database()
        self.stats = {
            'videos_processed': 0,
            'metadata_extracted': 0,
            'errors': []
        }
        
    def init_database(self):
        """Initialize streamlined video database"""
        cursor = self.conn.cursor()
        
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
                has_audio BOOLEAN,
                creation_date TEXT,
                modification_date TEXT,
                video_type TEXT,
                file_extension TEXT,
                processed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_duration ON videos(duration)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_type ON videos(video_type)')
        
        self.conn.commit()
        
    def get_file_hash_quick(self, file_path: Path) -> str:
        """Calculate hash from first 64KB for speed"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            chunk = f.read(65536)  # Read first 64KB only
            sha256_hash.update(chunk)
        return sha256_hash.hexdigest()[:16]  # Shortened hash
        
    def extract_metadata_fast(self, video_path: Path) -> Dict:
        """Fast metadata extraction using ffprobe"""
        metadata = {
            'duration': 0,
            'resolution': 'unknown',
            'fps': 0,
            'codec': 'unknown',
            'has_audio': False,
            'creation_date': None
        }
        
        try:
            # Quick ffprobe command with timeout
            cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                '-show_entries', 'format=duration:stream=width,height,codec_name,r_frame_rate',
                '-of', 'json', str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Extract duration
                if 'format' in data and 'duration' in data['format']:
                    metadata['duration'] = float(data['format']['duration'])
                
                # Extract video stream info
                if 'streams' in data and len(data['streams']) > 0:
                    stream = data['streams'][0]
                    width = stream.get('width', 0)
                    height = stream.get('height', 0)
                    metadata['resolution'] = f"{width}x{height}"
                    metadata['codec'] = stream.get('codec_name', 'unknown')
                    
                    # Calculate FPS
                    fps_str = stream.get('r_frame_rate', '0/1')
                    if '/' in fps_str:
                        num, den = fps_str.split('/')[:2]
                        if float(den) != 0:
                            metadata['fps'] = round(float(num) / float(den), 2)
            
            # Quick check for audio
            audio_cmd = ['ffprobe', '-v', 'quiet', '-select_streams', 'a', 
                        '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', str(video_path)]
            audio_result = subprocess.run(audio_cmd, capture_output=True, text=True, timeout=5)
            metadata['has_audio'] = 'audio' in audio_result.stdout
                        
        except Exception as e:
            self.stats['errors'].append({
                'file': str(video_path),
                'error': f"Metadata error: {str(e)}"
            })
            
        return metadata
        
    def classify_video_quick(self, video_path: Path, metadata: Dict) -> str:
        """Quick video classification"""
        filename = video_path.name.lower()
        
        if any(pattern in filename for pattern in ['img_', 'dsc_']):
            return 'mobile_photo'
        elif filename.startswith('[') and filename.endswith('].mov'):
            return 'numbered_sequence'
        elif 'hevc' in filename:
            return 'high_efficiency'
        elif metadata.get('duration', 0) < 10:
            return 'short_clip'
        elif metadata.get('duration', 0) > 300:
            return 'long_video'
        else:
            return 'standard_video'
            
    def process_video_quick(self, video_path: Path) -> bool:
        """Quick video processing"""
        try:
            print(f"   🎬 {video_path.name}")
            
            # File info
            file_stat = video_path.stat()
            file_size = file_stat.st_size
            file_hash = self.get_file_hash_quick(video_path)
            modification_date = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            # Extract metadata
            metadata = self.extract_metadata_fast(video_path)
            if metadata['duration'] > 0:
                self.stats['metadata_extracted'] += 1
                
            # Classify
            video_type = self.classify_video_quick(video_path, metadata)
            
            # Store in database
            cursor = self.conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO videos 
                (file_path, file_name, file_size, file_hash, duration, resolution, fps, codec,
                 has_audio, creation_date, modification_date, video_type, file_extension)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(video_path), video_path.name, file_size, file_hash,
                metadata['duration'], metadata['resolution'], metadata['fps'], metadata['codec'],
                metadata['has_audio'], metadata['creation_date'], modification_date,
                video_type, video_path.suffix.lower()
            ))
            
            self.conn.commit()
            self.stats['videos_processed'] += 1
            
            return True
            
        except Exception as e:
            self.stats['errors'].append({
                'file': str(video_path),
                'error': str(e)
            })
            return False
            
    def generate_quick_report(self):
        """Generate video catalog report"""
        cursor = self.conn.cursor()
        
        print("\n📊 QUICK VIDEO CATALOG REPORT")
        print("=" * 60)
        
        print(f"\n📈 Processing Results:")
        print(f"   Videos processed: {self.stats['videos_processed']}")
        print(f"   Metadata extracted: {self.stats['metadata_extracted']}")
        print(f"   Errors: {len(self.stats['errors'])}")
        
        # Video types
        print(f"\n🎬 Video Types:")
        cursor.execute('''
            SELECT video_type, COUNT(*) as count, AVG(duration) as avg_duration, SUM(file_size) as total_size
            FROM videos
            GROUP BY video_type
            ORDER BY count DESC
        ''')
        
        for video_type, count, avg_duration, total_size in cursor.fetchall():
            duration_str = f"{avg_duration:.1f}s" if avg_duration else "0s"
            size_mb = (total_size / 1024 / 1024) if total_size else 0
            print(f"   {video_type}: {count} videos (avg: {duration_str}, {size_mb:.1f} MB)")
            
        # Duration analysis
        cursor.execute('''
            SELECT 
                COUNT(*) as total_videos,
                SUM(duration) as total_duration,
                AVG(duration) as avg_duration,
                MIN(duration) as min_duration,
                MAX(duration) as max_duration,
                SUM(file_size) / 1024 / 1024 as total_size_mb
            FROM videos
            WHERE duration > 0
        ''')
        
        stats = cursor.fetchone()
        if stats[0] > 0:
            print(f"\n⏱️ Collection Overview:")
            print(f"   Total videos: {stats[0]}")
            print(f"   Total runtime: {stats[1]/60:.1f} minutes ({stats[1]/3600:.1f} hours)")
            print(f"   Average length: {stats[2]:.1f} seconds")
            print(f"   Total size: {stats[5]:.1f} MB ({stats[5]/1024:.1f} GB)")
            print(f"   Range: {stats[3]:.1f}s to {stats[4]:.1f}s")
            
        # Resolution analysis
        cursor.execute('''
            SELECT resolution, COUNT(*) as count
            FROM videos
            WHERE resolution != 'unknown'
            GROUP BY resolution
            ORDER BY count DESC
            LIMIT 5
        ''')
        
        print(f"\n📐 Common Resolutions:")
        for resolution, count in cursor.fetchall():
            print(f"   {resolution}: {count} videos")
            
        # Audio analysis
        cursor.execute('''
            SELECT has_audio, COUNT(*) as count
            FROM videos
            GROUP BY has_audio
        ''')
        
        print(f"\n🔊 Audio Analysis:")
        for has_audio, count in cursor.fetchall():
            audio_str = "With audio" if has_audio else "No audio"
            print(f"   {audio_str}: {count} videos")
            
        # Top 10 longest videos
        cursor.execute('''
            SELECT file_name, duration, resolution, file_size / 1024 / 1024 as size_mb
            FROM videos
            WHERE duration > 0
            ORDER BY duration DESC
            LIMIT 10
        ''')
        
        print(f"\n🏆 Longest Videos:")
        for filename, duration, resolution, size_mb in cursor.fetchall():
            duration_str = f"{duration/60:.1f}min" if duration > 60 else f"{duration:.1f}s"
            print(f"   {filename[:50]:<50} | {duration_str:>8} | {resolution} | {size_mb:.1f}MB")
            
    def search_videos_quick(self, query: str = None, min_duration: float = 0, has_audio: bool = None) -> List[Dict]:
        """Quick video search"""
        cursor = self.conn.cursor()
        
        conditions = ["duration > 0"]  # Only videos with valid duration
        params = []
        
        if query:
            conditions.append("file_name LIKE ?")
            params.append(f"%{query}%")
            
        if min_duration > 0:
            conditions.append("duration >= ?")
            params.append(min_duration)
            
        if has_audio is not None:
            conditions.append("has_audio = ?")
            params.append(has_audio)
            
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f'''
            SELECT file_name, duration, resolution, video_type, file_size / 1024 / 1024 as size_mb
            FROM videos
            WHERE {where_clause}
            ORDER BY duration DESC
        ''', params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'filename': row[0],
                'duration': row[1],
                'resolution': row[2],
                'type': row[3],
                'size_mb': row[4]
            })
            
        return results
        
    def process_all_videos(self, directory: str):
        """Process all videos efficiently"""
        video_extensions = {'.mov', '.mp4', '.avi', '.wmv', '.flv', '.webm', '.mkv', '.m4v'}
        video_files = []
        
        print(f"🔍 Scanning for videos...")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if Path(file).suffix.lower() in video_extensions:
                    video_files.append(Path(root) / file)
                    
        print(f"✅ Found {len(video_files)} videos")
        print(f"\n🚀 Processing videos quickly...")
        
        # Process efficiently
        for video_path in video_files:
            self.process_video_quick(video_path)
            
        # Generate report
        self.generate_quick_report()
        
        print(f"\n💾 Catalog saved to: {self.db_path}")

def main():
    """Main entry point"""
    print("⚡ QUICK VIDEO CATALOGER")
    print("=" * 60)
    
    cataloger = QuickVideoCataloger()
    cataloger.process_all_videos("/home/jonclaude/agents/Hinkey/desktop_ingest_job")
    
    # Demo searches
    print(f"\n🔍 Search Examples:")
    
    # Find long videos
    long_videos = cataloger.search_videos_quick(min_duration=60)
    if long_videos:
        print(f"\n⏱️ Videos over 1 minute ({len(long_videos)} found):")
        for video in long_videos[:5]:
            duration_str = f"{video['duration']/60:.1f}min" if video['duration'] > 60 else f"{video['duration']:.1f}s"
            print(f"   {video['filename'][:50]} - {duration_str} - {video['size_mb']:.1f}MB")
    
    # Find videos with audio
    audio_videos = cataloger.search_videos_quick(has_audio=True)
    if audio_videos:
        print(f"\n🔊 Videos with audio ({len(audio_videos)} found):")
        for video in audio_videos[:5]:
            duration_str = f"{video['duration']/60:.1f}min" if video['duration'] > 60 else f"{video['duration']:.1f}s"
            print(f"   {video['filename'][:50]} - {duration_str}")
    
    print("\n✅ Quick video cataloging complete!")

if __name__ == "__main__":
    main()