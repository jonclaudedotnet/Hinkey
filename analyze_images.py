#!/usr/bin/env python3
"""
Analyze specific images and tell stories about them
"""

import sqlite3
import json
from pathlib import Path

def analyze_images():
    conn = sqlite3.connect('quick_image_data.db')
    cursor = conn.cursor()
    
    print("🖼️ INTERESTING IMAGES IN YOUR COLLECTION")
    print("=" * 60)
    
    # SeaRobin Tech brand evolution
    print("\n🏢 SEAROBIN TECH BRAND EVOLUTION:")
    cursor.execute('''
        SELECT file_name, width, height, avg_brightness, dominant_color
        FROM images
        WHERE file_name LIKE '%SRT%' OR file_name LIKE '%SeaRobin%'
        ORDER BY file_name
    ''')
    
    for row in cursor.fetchall():
        filename, width, height, brightness, color_json = row
        color = json.loads(color_json) if color_json else None
        color_desc = f"RGB{color}" if color else "unknown"
        
        print(f"   📄 {filename}")
        print(f"      Dimensions: {width}x{height}")
        print(f"      Brightness: {brightness:.1f}/255")
        print(f"      Dominant color: {color_desc}")
        
        # Tell the story
        if "Logo2017" in filename:
            print(f"      📖 Story: This is your 2017 company logo design")
            if "forexcel" in filename:
                print(f"          Optimized version for Excel spreadsheets")
            elif "forfacebook" in filename:
                print(f"          Social media optimized square format")
            elif "sm" in filename:
                print(f"          Small/thumbnail version")
        elif "Logo_2021" in filename:
            print(f"      📖 Story: Your updated 2021 logo design - latest brand identity")
        elif "SRTbackground" in filename:
            print(f"      📖 Story: Large background graphic (3300x3300) - very dark theme")
        elif "001_SRT" in filename:
            print(f"      📖 Story: High-res photo (iPad quality) - possibly documentation")
        print()
    
    # Personal/Professional photos
    print("\n👤 PERSONAL & PROFESSIONAL IMAGES:")
    cursor.execute('''
        SELECT file_name, width, height, avg_brightness
        FROM images
        WHERE file_name LIKE '%jc%' OR file_name LIKE '%sig%' OR file_name LIKE '%current%' OR file_name LIKE '%id_%' OR file_name LIKE '%license%'
        ORDER BY file_name
    ''')
    
    for row in cursor.fetchall():
        filename, width, height, brightness = row
        print(f"   📷 {filename} ({width}x{height})")
        
        # Tell the story
        if "sig" in filename.lower():
            print(f"      📖 Story: Digital signature file - for document signing")
            if "_w" in filename:
                print(f"          White background version")
        elif "current" in filename:
            print(f"      📖 Story: Current profile/ID photo")
        elif "id_" in filename:
            print(f"      📖 Story: ID documentation photo")
        elif "license" in filename:
            print(f"      📖 Story: Driver's license documentation")
        elif "nerd.png" == filename:
            print(f"      📖 Story: Avatar/profile image with person and tie detected by AI")
        print()
    
    # Client logos discovered
    print("\n🏷️ CLIENT & PARTNER LOGOS:")
    cursor.execute('''
        SELECT file_name, width, height, avg_brightness
        FROM images
        WHERE image_type = 'logo' AND file_name NOT LIKE '%SRT%' AND file_name NOT LIKE '%SeaRobin%'
        ORDER BY file_name
    ''')
    
    for row in cursor.fetchall():
        filename, width, height, brightness = row
        print(f"   🏢 {filename} ({width}x{height})")
        
        # Interpret client names
        if "CHS" in filename:
            print(f"      📖 Client: Chester Historical Society")
        elif "lindhfoster" in filename:
            print(f"      📖 Client: Lindh Foster (appears in invoice data)")
        elif "nitroslawncare" in filename:
            print(f"      📖 Client: Nitros Lawn Care")
        elif "hinding" in filename:
            print(f"      📖 Client: Hinding company")
        elif "mapletree" in filename:
            print(f"      📖 Client: Maple Tree business")
        elif "jl" in filename:
            print(f"      📖 Client: Jewish Ledger (matches invoice client!)")
        elif "chd_logo" in filename:
            print(f"      📖 Client: CHD company")
        print()
    
    # Historical/Archive images
    print("\n📅 HISTORICAL BUSINESS IMAGES:")
    cursor.execute('''
        SELECT file_name, width, height, avg_brightness
        FROM images
        WHERE file_name LIKE '%2005%' OR file_name LIKE '%2010%' OR file_name LIKE '%2017%'
        ORDER BY file_name
    ''')
    
    for row in cursor.fetchall():
        filename, width, height, brightness = row
        print(f"   📸 {filename} ({width}x{height})")
        
        if "lobsterfest2005" in filename:
            print(f"      📖 Story: Lobster festival event from 2005 - early business work")
        elif "IPHA2010" in filename:
            print(f"      📖 Story: IPHA event from 2010 - business documentation")
        elif "2017" in filename:
            print(f"      📖 Story: 2017 business materials")
        print()
    
    # Show some statistics
    print("\n📊 COLLECTION INSIGHTS:")
    
    # Brightness analysis
    cursor.execute('''
        SELECT 
            CASE 
                WHEN avg_brightness < 85 THEN 'Very Dark'
                WHEN avg_brightness < 170 THEN 'Dark'
                WHEN avg_brightness < 200 THEN 'Medium'
                WHEN avg_brightness < 230 THEN 'Bright'
                ELSE 'Very Bright'
            END as brightness_category,
            COUNT(*) as count
        FROM images
        WHERE avg_brightness > 0
        GROUP BY brightness_category
        ORDER BY avg_brightness
    ''')
    
    print("   🌈 Brightness Distribution:")
    for category, count in cursor.fetchall():
        print(f"      {category}: {count} images")
    
    # Size analysis  
    cursor.execute('''
        SELECT 
            CASE 
                WHEN width * height > 5000000 THEN 'Very High Res'
                WHEN width * height > 1000000 THEN 'High Res'
                WHEN width * height > 100000 THEN 'Medium Res'
                ELSE 'Low Res'
            END as resolution_category,
            COUNT(*) as count
        FROM images
        WHERE width > 0 AND height > 0
        GROUP BY resolution_category
    ''')
    
    print("\n   📐 Resolution Distribution:")
    for category, count in cursor.fetchall():
        print(f"      {category}: {count} images")
    
    conn.close()

if __name__ == "__main__":
    analyze_images()