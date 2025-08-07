#!/usr/bin/env python3
"""
Inspect Excel file structure to understand invoice format
"""

import pandas as pd
from pathlib import Path
import glob

def inspect_excel_file(file_path):
    """Inspect structure of a single Excel file"""
    try:
        print(f"\n📄 File: {Path(file_path).name}")
        print("=" * 50)
        
        # Read Excel file
        df = pd.read_excel(file_path, engine='openpyxl')
        
        print(f"Dimensions: {df.shape[0]} rows x {df.shape[1]} columns")
        print(f"\nColumns: {list(df.columns)}")
        
        # Show first few rows
        print(f"\nFirst 5 rows:")
        print(df.head().to_string())
        
        # Look for numeric data
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            print(f"\nNumeric columns: {list(numeric_cols)}")
            for col in numeric_cols:
                non_zero = df[col][df[col] != 0]
                if len(non_zero) > 0:
                    print(f"  {col}: Max={non_zero.max()}, Mean=${non_zero.mean():.2f}")
        
        # Look for cells containing currency symbols
        print(f"\nCells containing '$':")
        for col in df.columns:
            dollar_cells = df[col].astype(str).str.contains('$', na=False)
            if dollar_cells.any():
                print(f"  Column '{col}': {df[col][dollar_cells].tolist()}")
                
        return True
        
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

def main():
    """Inspect sample Excel files"""
    print("🔍 EXCEL FILE STRUCTURE INSPECTOR")
    print("=" * 60)
    
    # Get sample files
    excel_files = glob.glob("/home/jonclaude/agents/Hinkey/desktop_ingest_job/**/SRT*.xlsx", recursive=True)
    
    # Inspect first 3 files
    for i, file_path in enumerate(excel_files[:3]):
        inspect_excel_file(file_path)
        
        if i < 2:  # Add separator between files
            print("\n" + "="*60)

if __name__ == "__main__":
    main()