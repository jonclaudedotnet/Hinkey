#!/usr/bin/env python3
"""
Excel Invoice Data Processor
Connects all Excel invoice data into a unified SQLite database
"""

import os
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import re
from typing import Dict, List, Optional
import json

class InvoiceProcessor:
    """Process Excel invoice files and extract structured data"""
    
    def __init__(self, db_path: str = "invoice_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.init_database()
        self.stats = {
            'files_processed': 0,
            'invoices_found': 0,
            'clients_found': set(),
            'total_amount': 0.0,
            'errors': []
        }
        
    def init_database(self):
        """Initialize invoice database schema"""
        cursor = self.conn.cursor()
        
        # Main invoices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE,
                client_name TEXT,
                invoice_date TEXT,
                due_date TEXT,
                total_amount REAL,
                status TEXT,
                file_path TEXT,
                extracted_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Invoice line items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                description TEXT,
                quantity REAL,
                rate REAL,
                amount REAL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        ''')
        
        # Clients summary
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT UNIQUE,
                total_invoices INTEGER DEFAULT 0,
                total_revenue REAL DEFAULT 0,
                first_invoice_date TEXT,
                last_invoice_date TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoice_number ON invoices(invoice_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_name ON invoices(client_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoice_date ON invoices(invoice_date)')
        
        self.conn.commit()
        
    def extract_invoice_number(self, filename: str, df: pd.DataFrame) -> Optional[str]:
        """Extract invoice number from filename or content"""
        # First try filename (e.g., SRT123-ClientName.xlsx)
        match = re.match(r'(SRT\d+)', filename)
        if match:
            return match.group(1)
            
        # Try to find in spreadsheet content
        for col in df.columns:
            for val in df[col].astype(str):
                if 'SRT' in val and re.search(r'SRT\d+', val):
                    match = re.search(r'(SRT\d+)', val)
                    if match:
                        return match.group(1)
        
        return None
        
    def extract_client_name(self, filename: str, df: pd.DataFrame) -> Optional[str]:
        """Extract client name from filename or content"""
        # From filename (e.g., SRT123-ClientName.xlsx)
        match = re.match(r'SRT\d+-(.+?)\.xlsx?$', filename)
        if match:
            return match.group(1).replace('_', ' ')
            
        # Look for common patterns in content
        for col in df.columns:
            col_lower = str(col).lower()
            if 'client' in col_lower or 'customer' in col_lower or 'bill to' in col_lower:
                for val in df[col].dropna():
                    if isinstance(val, str) and len(val) > 2:
                        return val
                        
        return None
        
    def extract_amounts(self, df: pd.DataFrame) -> Dict:
        """Extract financial amounts from spreadsheet"""
        amounts = {
            'total': 0.0,
            'items': []
        }
        
        # Convert all data to string for searching
        df_str = df.astype(str)
        
        # Look for "Invoice Total:" pattern
        for row_idx in df_str.index:
            for col in df_str.columns:
                cell_value = str(df_str.loc[row_idx, col]).lower()
                
                if 'invoice total' in cell_value or 'total:' in cell_value or 'proposal total' in cell_value:
                    # Look for amount in adjacent cells (same row, next columns)
                    for next_col_idx, next_col in enumerate(df.columns[list(df.columns).index(col):]):
                        if next_col_idx > 4:  # Don't look too far
                            break
                        try:
                            value = df.loc[row_idx, next_col]
                            if pd.notna(value):
                                numeric_val = pd.to_numeric(value, errors='coerce')
                                if pd.notna(numeric_val) and numeric_val > 0:
                                    amounts['total'] = float(numeric_val)
                                    break
                        except:
                            continue
                            
                    # Also look in the next row
                    if row_idx + 1 in df.index:
                        for next_col in df.columns:
                            try:
                                value = df.loc[row_idx + 1, next_col]
                                if pd.notna(value):
                                    numeric_val = pd.to_numeric(value, errors='coerce')
                                    if pd.notna(numeric_val) and numeric_val > amounts['total']:
                                        amounts['total'] = float(numeric_val)
                                        break
                            except:
                                continue
                                
        # If no "Invoice Total" found, look for largest numeric value
        if amounts['total'] == 0.0:
            all_numeric = []
            for col in df.columns:
                numeric_vals = pd.to_numeric(df[col], errors='coerce').dropna()
                all_numeric.extend(numeric_vals.tolist())
                
            if all_numeric:
                # Filter out very small amounts (likely rates/hours) and very large (likely years)
                filtered = [x for x in all_numeric if 10 <= x <= 100000]
                if filtered:
                    amounts['total'] = float(max(filtered))
                elif all_numeric:
                    amounts['total'] = float(max(all_numeric))
        
        # Extract line items (hours * rate = total patterns)
        for row_idx in df.index:
            row_data = df.loc[row_idx].tolist()
            numeric_row = [pd.to_numeric(x, errors='coerce') for x in row_data]
            numeric_row = [x for x in numeric_row if pd.notna(x)]
            
            # Look for hour/rate/total patterns
            if len(numeric_row) >= 3:
                # Check if we have hours * rate = total
                for i in range(len(numeric_row) - 2):
                    hours = numeric_row[i]
                    rate = numeric_row[i + 1] 
                    total = numeric_row[i + 2]
                    
                    if 0.1 <= hours <= 100 and 20 <= rate <= 500:  # Reasonable hours and rates
                        calculated = hours * rate
                        if abs(calculated - total) < 1:  # Allow small rounding differences
                            # Find description in same row
                            desc = "Work performed"
                            for cell in df.loc[row_idx]:
                                if isinstance(cell, str) and len(cell) > 10:
                                    desc = cell
                                    break
                                    
                            amounts['items'].append({
                                'description': desc,
                                'hours': hours,
                                'rate': rate,
                                'amount': total
                            })
                            
        return amounts
        
    def process_excel_file(self, file_path: Path) -> bool:
        """Process a single Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path, engine='openpyxl')
            
            if df.empty:
                return False
                
            filename = file_path.name
            
            # Extract key information
            invoice_number = self.extract_invoice_number(filename, df)
            if not invoice_number:
                # Generate one if not found
                invoice_number = f"UNK_{self.stats['files_processed']:04d}"
                
            client_name = self.extract_client_name(filename, df)
            if not client_name:
                client_name = "Unknown Client"
                
            amounts = self.extract_amounts(df)
            
            # Extract dates if possible
            invoice_date = None
            # Look for dates in data
            for row_idx in df.index:
                for col in df.columns:
                    cell_value = df.loc[row_idx, col]
                    
                    # Try to parse as datetime
                    if pd.notna(cell_value):
                        try:
                            if isinstance(cell_value, str):
                                # Look for date patterns in strings
                                import re
                                date_pattern = r'\d{1,2}/\d{1,2}/\d{2,4}'
                                if re.search(date_pattern, cell_value):
                                    parsed_date = pd.to_datetime(cell_value, errors='coerce')
                                    if pd.notna(parsed_date):
                                        invoice_date = parsed_date.strftime('%Y-%m-%d')
                                        break
                            else:
                                # Direct datetime conversion
                                parsed_date = pd.to_datetime(cell_value, errors='coerce')
                                if pd.notna(parsed_date) and parsed_date.year >= 2010:  # Reasonable year range
                                    invoice_date = parsed_date.strftime('%Y-%m-%d')
                                    break
                        except:
                            continue
                            
                if invoice_date:
                    break
                        
            # Store in database
            cursor = self.conn.cursor()
            
            # Insert invoice
            cursor.execute('''
                INSERT OR REPLACE INTO invoices 
                (invoice_number, client_name, invoice_date, total_amount, file_path, extracted_data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                invoice_number,
                client_name,
                invoice_date,
                amounts['total'],
                str(file_path),
                json.dumps({
                    'filename': filename,
                    'rows': len(df),
                    'columns': list(df.columns),
                    'items': amounts['items']
                })
            ))
            
            invoice_id = cursor.lastrowid
            
            # Insert line items
            for item in amounts['items']:
                cursor.execute('''
                    INSERT INTO invoice_items (invoice_id, description, quantity, rate, amount)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    invoice_id, 
                    item['description'], 
                    item.get('hours', None),
                    item.get('rate', None),
                    item['amount']
                ))
                
            self.conn.commit()
            
            # Update stats
            self.stats['files_processed'] += 1
            self.stats['invoices_found'] += 1
            self.stats['clients_found'].add(client_name)
            self.stats['total_amount'] += amounts['total']
            
            return True
            
        except Exception as e:
            self.stats['errors'].append({
                'file': str(file_path),
                'error': str(e)
            })
            return False
            
    def update_client_summaries(self):
        """Update client summary statistics"""
        cursor = self.conn.cursor()
        
        # Get unique clients
        cursor.execute('SELECT DISTINCT client_name FROM invoices')
        clients = cursor.fetchall()
        
        for (client_name,) in clients:
            # Calculate stats for each client
            cursor.execute('''
                SELECT 
                    COUNT(*) as invoice_count,
                    SUM(total_amount) as total_revenue,
                    MIN(invoice_date) as first_date,
                    MAX(invoice_date) as last_date
                FROM invoices 
                WHERE client_name = ?
            ''', (client_name,))
            
            stats = cursor.fetchone()
            
            cursor.execute('''
                INSERT OR REPLACE INTO clients 
                (client_name, total_invoices, total_revenue, first_invoice_date, last_invoice_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (client_name, stats[0], stats[1] or 0, stats[2], stats[3]))
            
        self.conn.commit()
        
    def generate_summary_report(self):
        """Generate summary report of all invoice data"""
        cursor = self.conn.cursor()
        
        print("\n📊 INVOICE DATA ANALYSIS REPORT")
        print("=" * 60)
        
        # Overall stats
        print(f"\n📈 Overall Statistics:")
        print(f"   Total files processed: {self.stats['files_processed']}")
        print(f"   Total invoices found: {self.stats['invoices_found']}")
        print(f"   Unique clients: {len(self.stats['clients_found'])}")
        print(f"   Total revenue: ${self.stats['total_amount']:,.2f}")
        
        # Top clients by revenue
        print(f"\n💰 Top 10 Clients by Revenue:")
        cursor.execute('''
            SELECT client_name, total_invoices, total_revenue
            FROM clients
            ORDER BY total_revenue DESC
            LIMIT 10
        ''')
        
        for i, (client, invoices, revenue) in enumerate(cursor.fetchall(), 1):
            print(f"   {i}. {client}: ${revenue:,.2f} ({invoices} invoices)")
            
        # Most frequent clients
        print(f"\n📝 Most Frequent Clients (by invoice count):")
        cursor.execute('''
            SELECT client_name, total_invoices, total_revenue
            FROM clients
            ORDER BY total_invoices DESC
            LIMIT 10
        ''')
        
        for i, (client, invoices, revenue) in enumerate(cursor.fetchall(), 1):
            print(f"   {i}. {client}: {invoices} invoices (${revenue:,.2f})")
            
        # Date range
        cursor.execute('SELECT MIN(invoice_date), MAX(invoice_date) FROM invoices WHERE invoice_date IS NOT NULL')
        date_range = cursor.fetchone()
        if date_range[0]:
            print(f"\n📅 Date Range: {date_range[0]} to {date_range[1]}")
            
        # Revenue by year
        print(f"\n📊 Revenue by Year:")
        cursor.execute('''
            SELECT 
                SUBSTR(invoice_date, 1, 4) as year,
                COUNT(*) as invoice_count,
                SUM(total_amount) as yearly_revenue
            FROM invoices
            WHERE invoice_date IS NOT NULL
            GROUP BY SUBSTR(invoice_date, 1, 4)
            ORDER BY year
        ''')
        
        for year, count, revenue in cursor.fetchall():
            if year:
                print(f"   {year}: ${revenue:,.2f} ({count} invoices)")
                
        # Errors
        if self.stats['errors']:
            print(f"\n⚠️ Processing Errors ({len(self.stats['errors'])} files):")
            for err in self.stats['errors'][:5]:  # Show first 5
                print(f"   - {Path(err['file']).name}: {err['error']}")
                
    def process_all_files(self, directory: str):
        """Process all Excel files in directory"""
        excel_files = []
        
        print(f"🔍 Scanning for Excel files in {directory}...")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.xlsx', '.xls')) and not file.startswith('~'):
                    excel_files.append(Path(root) / file)
                    
        print(f"✅ Found {len(excel_files)} Excel files to process")
        
        # Process each file
        for i, file_path in enumerate(excel_files, 1):
            if i % 10 == 0:
                print(f"   Processing: {i}/{len(excel_files)} files...")
                
            self.process_excel_file(file_path)
            
        # Update client summaries
        print("\n📊 Updating client summaries...")
        self.update_client_summaries()
        
        # Generate report
        self.generate_summary_report()
        
        # Save detailed results
        self.save_detailed_results()
        
    def save_detailed_results(self):
        """Save detailed results to CSV files"""
        output_dir = Path("invoice_analysis_results")
        output_dir.mkdir(exist_ok=True)
        
        # Export invoices
        invoices_df = pd.read_sql_query("SELECT * FROM invoices", self.conn)
        invoices_df.to_csv(output_dir / "all_invoices.csv", index=False)
        
        # Export clients
        clients_df = pd.read_sql_query("SELECT * FROM clients ORDER BY total_revenue DESC", self.conn)
        clients_df.to_csv(output_dir / "client_summary.csv", index=False)
        
        print(f"\n💾 Detailed results saved to {output_dir}/")
        print(f"   - all_invoices.csv")
        print(f"   - client_summary.csv")
        print(f"   - Database: {self.db_path}")

def main():
    """Main entry point"""
    print("💼 EXCEL INVOICE DATA PROCESSOR")
    print("=" * 60)
    
    # Process all Excel files
    processor = InvoiceProcessor(db_path="invoice_data.db")
    processor.process_all_files("/home/jonclaude/agents/Hinkey/desktop_ingest_job")
    
    print("\n✅ Invoice data processing complete!")

if __name__ == "__main__":
    main()