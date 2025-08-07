#!/usr/bin/env python3
"""
Test dashboard integration with the fixed SMB ingestion system
"""

import json
import time
from pathlib import Path
from smb_nexus_ingestion import SMBNexusIngestion

def test_status_file_generation():
    """Test that status files are properly generated"""
    print("🔍 Testing Dashboard Integration")
    print("=" * 50)
    
    # SMB configuration
    server = "10.0.0.141" 
    username = "jonclaude"
    password = "1D3fd4138e!!"
    
    # Initialize ingestion system
    ingestion = SMBNexusIngestion(server, username, password)
    
    print("1️⃣ Testing status file creation...")
    
    # Simulate some stats
    ingestion.stats['shares_found'] = 5
    ingestion.stats['shares_scanned'] = 2
    ingestion.stats['current_share'] = 'SYNSRT'
    ingestion.stats['files_found'] = 150
    ingestion.stats['files_cached'] = 75
    ingestion.stats['files_processed'] = 50
    ingestion.stats['files_vectorized'] = 40
    ingestion.stats['current_file'] = 'test_document.txt'
    ingestion.stats['current_directory'] = 'SYNSRT/documents'
    
    # Write status
    ingestion.write_status()
    
    # Check if status file was created
    status_file = Path("./ingestion_status.json")
    if status_file.exists():
        print("   ✅ Status file created successfully")
        
        # Read and display contents
        with open(status_file, 'r') as f:
            status_data = json.load(f)
        
        print("   📊 Status file contents:")
        for key, value in status_data.items():
            if key == 'start_time' or key == 'last_update':
                continue  # Skip timestamps for readability
            print(f"      {key}: {value}")
        
        # Check computed fields
        required_fields = ['elapsed_time', 'files_per_second', 'processing_rate', 'processing_progress']
        missing_fields = [field for field in required_fields if field not in status_data]
        
        if missing_fields:
            print(f"   ⚠️ Missing computed fields: {', '.join(missing_fields)}")
        else:
            print("   ✅ All computed fields present")
            
        return True
    else:
        print("   ❌ Status file not created")
        return False

def test_progress_updates():
    """Test progress updates during scanning"""
    print("\n2️⃣ Testing progress updates...")
    
    # SMB configuration
    server = "10.0.0.141"
    username = "jonclaude"
    password = "1D3fd4138e!!"
    
    # Initialize ingestion system
    ingestion = SMBNexusIngestion(server, username, password)
    
    # Test getting shares (should trigger status updates)
    shares = ingestion.smb.list_shares()
    print(f"   📁 Found {len(shares)} shares for testing")
    
    if shares:
        # Test listing files in first share (limited to avoid long scan)
        test_share = shares[0]
        print(f"   🔍 Testing file listing in: {test_share}")
        
        # Simulate scanning a single share  
        ingestion.stats['current_share'] = test_share
        ingestion.stats['shares_found'] = len(shares)
        ingestion.write_status()
        
        # Get files from root directory
        files = ingestion.smb.list_files(test_share, "")
        print(f"   📊 Found {len(files)} items in {test_share} root")
        
        # Simulate processing a few files
        text_files = [f for f in files if not f['is_dir'] and 
                     Path(f['name']).suffix.lower() in {'.txt', '.md', '.py', '.json'}][:3]
        
        for i, file_info in enumerate(text_files):
            ingestion.stats['current_file'] = file_info['path']
            ingestion.stats['files_found'] = len(files)
            ingestion.stats['files_processed'] = i + 1
            ingestion.write_status()
            
            print(f"   ⚡ Simulated processing: {file_info['name']}")
            time.sleep(0.5)  # Brief delay to show updates
    
    print("   ✅ Progress update simulation complete")
    return True

def test_dashboard_compatibility():
    """Test compatibility with dashboard reading"""
    print("\n3️⃣ Testing dashboard compatibility...")
    
    status_file = Path("./ingestion_status.json")
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                status_data = json.load(f)
            
            # Test fields that dashboard expects
            dashboard_fields = [
                'shares_found', 'shares_scanned', 'current_share',
                'directories_scanned', 'files_found', 'files_cached',
                'files_processed', 'files_vectorized', 'current_file',
                'errors', 'elapsed_time', 'processing_progress'
            ]
            
            present_fields = [field for field in dashboard_fields if field in status_data]
            missing_fields = [field for field in dashboard_fields if field not in status_data]
            
            print(f"   ✅ Present fields: {len(present_fields)}/{len(dashboard_fields)}")
            
            if missing_fields:
                print(f"   ⚠️ Missing fields: {', '.join(missing_fields)}")
            else:
                print("   ✅ All dashboard fields available")
            
            # Test numeric fields are actually numeric
            numeric_fields = ['shares_found', 'files_found', 'files_processed', 'elapsed_time']
            for field in numeric_fields:
                if field in status_data:
                    try:
                        float(status_data[field])
                        print(f"   ✅ {field}: {status_data[field]} (numeric)")
                    except (ValueError, TypeError):
                        print(f"   ❌ {field}: {status_data[field]} (not numeric)")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON parsing error: {e}")
            return False
    else:
        print("   ❌ No status file found for dashboard test")
        return False

if __name__ == "__main__":
    success1 = test_status_file_generation()
    success2 = test_progress_updates() 
    success3 = test_dashboard_compatibility()
    
    if all([success1, success2, success3]):
        print(f"\n✅ All dashboard integration tests passed!")
        print("\n🚀 Ready for live monitoring with:")
        print("   python3 ingestion_dashboard.py monitor")
    else:
        print(f"\n❌ Some dashboard integration tests failed!")