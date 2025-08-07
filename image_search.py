#!/usr/bin/env python3
"""
Image Search Interface
Search images by filename, type, or content
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict

class ImageSearchEngine:
    """Search interface for processed images"""
    
    def __init__(self, db_path: str = "quick_image_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
    def search_by_filename(self, query: str) -> List[Dict]:
        """Search images by filename pattern"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT file_name, file_path, image_type, width, height, avg_brightness
            FROM images
            WHERE file_name LIKE ?
            ORDER BY file_name
        ''', (f'%{query}%',))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'file_name': row[0],
                'file_path': row[1],
                'image_type': row[2],
                'dimensions': f"{row[3]}x{row[4]}" if row[3] and row[4] else "unknown",
                'brightness': row[5] if row[5] else 0
            })
        
        return results
        
    def search_by_type(self, image_type: str) -> List[Dict]:
        """Search images by type"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT file_name, file_path, width, height, avg_brightness
            FROM images
            WHERE image_type = ?
            ORDER BY file_name
        ''', (image_type,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'file_name': row[0],
                'file_path': row[1],
                'dimensions': f"{row[2]}x{row[3]}" if row[2] and row[3] else "unknown",
                'brightness': row[4] if row[4] else 0
            })
        
        return results
        
    def search_by_color(self, color_brightness_min: float = 0, color_brightness_max: float = 255) -> List[Dict]:
        """Search images by brightness range"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT file_name, file_path, image_type, avg_brightness, dominant_color
            FROM images
            WHERE avg_brightness BETWEEN ? AND ?
            ORDER BY avg_brightness
        ''', (color_brightness_min, color_brightness_max))
        
        results = []
        for row in cursor.fetchall():
            dominant_color = json.loads(row[4]) if row[4] else None
            results.append({
                'file_name': row[0],
                'file_path': row[1],
                'image_type': row[2],
                'brightness': row[3] if row[3] else 0,
                'dominant_color': dominant_color
            })
        
        return results
        
    def get_image_stats(self) -> Dict:
        """Get overall image statistics"""
        cursor = self.conn.cursor()
        
        # Basic counts
        cursor.execute('SELECT COUNT(*) FROM images')
        total_images = cursor.fetchone()[0]
        
        # Type breakdown
        cursor.execute('''
            SELECT image_type, COUNT(*) as count
            FROM images
            GROUP BY image_type
            ORDER BY count DESC
        ''')
        types = dict(cursor.fetchall())
        
        # Text stats
        cursor.execute('SELECT COUNT(*) FROM images WHERE has_text = 1')
        with_text = cursor.fetchone()[0]
        
        # Brightness stats
        cursor.execute('''
            SELECT 
                AVG(avg_brightness) as avg_brightness,
                MIN(avg_brightness) as min_brightness,
                MAX(avg_brightness) as max_brightness
            FROM images
            WHERE avg_brightness > 0
        ''')
        brightness_stats = cursor.fetchone()
        
        return {
            'total_images': total_images,
            'types': types,
            'with_text': with_text,
            'brightness': {
                'average': brightness_stats[0] if brightness_stats[0] else 0,
                'min': brightness_stats[1] if brightness_stats[1] else 0,
                'max': brightness_stats[2] if brightness_stats[2] else 0
            }
        }
        
    def show_sample_images(self, limit: int = 10):
        """Show sample of processed images"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT file_name, image_type, width, height, avg_brightness, extracted_text
            FROM images
            ORDER BY file_name
            LIMIT ?
        ''', (limit,))
        
        print(f"\n📸 Sample Images (first {limit}):")
        print("-" * 80)
        
        for row in cursor.fetchall():
            filename = row[0]
            img_type = row[1]
            dimensions = f"{row[2]}x{row[3]}" if row[2] and row[3] else "unknown"
            brightness = f"{row[4]:.1f}" if row[4] else "unknown"
            text_preview = row[5][:50] + "..." if row[5] and len(row[5]) > 50 else row[5] or "no text"
            
            print(f"{filename:<30} | {img_type:<12} | {dimensions:<10} | Brightness: {brightness:<8} | {text_preview}")

def main():
    """Interactive search demo"""
    print("🔍 IMAGE SEARCH ENGINE")
    print("=" * 60)
    
    search_engine = ImageSearchEngine()
    
    # Show stats
    stats = search_engine.get_image_stats()
    print(f"\n📊 Image Database Stats:")
    print(f"   Total images: {stats['total_images']}")
    print(f"   Images with text: {stats['with_text']}")
    print(f"   Average brightness: {stats['brightness']['average']:.1f}")
    
    print(f"\n🏷️ Image Types:")
    for img_type, count in stats['types'].items():
        print(f"   {img_type}: {count} images")
    
    # Show samples
    search_engine.show_sample_images(15)
    
    # Demo searches
    print(f"\n🔍 Search Examples:")
    
    # Search for logos
    logo_results = search_engine.search_by_type('logo')
    print(f"\n📂 Logos ({len(logo_results)} found):")
    for result in logo_results[:10]:
        print(f"   {result['file_name']} - {result['dimensions']}")
    
    # Search for SeaRobin Tech files
    srt_results = search_engine.search_by_filename('srt')
    print(f"\n🏢 SeaRobin Tech files ({len(srt_results)} found):")
    for result in srt_results:
        print(f"   {result['file_name']} ({result['image_type']}) - {result['dimensions']}")
    
    # Search by brightness (dark images)
    dark_results = search_engine.search_by_color(0, 100)
    print(f"\n🌑 Dark images ({len(dark_results)} found):")
    for result in dark_results[:5]:
        color_info = f"RGB{result['dominant_color']}" if result['dominant_color'] else "unknown"
        print(f"   {result['file_name']} - Brightness: {result['brightness']:.1f}, Color: {color_info}")
    
    print(f"\n✅ Search demo complete!")
    print(f"💡 Use this system to find images by name, type, or visual properties")

if __name__ == "__main__":
    main()