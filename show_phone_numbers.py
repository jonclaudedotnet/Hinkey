#!/usr/bin/env python3
"""
Display phone numbers extracted from PDFs
"""

import sqlite3
from collections import Counter

def show_phone_numbers():
    # Connect to database
    conn = sqlite3.connect('pdf_data.db')
    cursor = conn.cursor()
    
    # Get all phone numbers
    cursor.execute("""
        SELECT entity_value, pdf_id 
        FROM pdf_entities 
        WHERE entity_type = 'phone'
    """)
    
    phone_data = cursor.fetchall()
    
    # Count occurrences
    phone_counter = Counter([phone for phone, _ in phone_data])
    
    print("📞 PHONE NUMBERS FOUND IN PDFS")
    print("=" * 60)
    print(f"\nTotal unique phone numbers: {len(phone_counter)}")
    print(f"Total occurrences: {len(phone_data)}")
    
    print("\n📱 Most Frequent Phone Numbers:")
    print("-" * 40)
    
    for phone, count in phone_counter.most_common(20):
        print(f"{phone:<20} - appears {count} times")
    
    # Get some context - which files contain which numbers
    print("\n📄 Sample Files Containing Top Numbers:")
    print("-" * 40)
    
    top_phones = [phone for phone, _ in phone_counter.most_common(5)]
    
    for phone in top_phones:
        cursor.execute("""
            SELECT DISTINCT p.file_name 
            FROM pdf_entities e
            JOIN pdfs p ON e.pdf_id = p.id
            WHERE e.entity_type = 'phone' AND e.entity_value = ?
            LIMIT 3
        """, (phone,))
        
        files = cursor.fetchall()
        print(f"\n{phone}:")
        for (filename,) in files:
            print(f"  - {filename}")
    
    conn.close()

if __name__ == "__main__":
    show_phone_numbers()