#!/usr/bin/env python3
"""
Test SMB parsing functionality
"""

from smb_nexus_ingestion import SMBConnection, SMBNexusIngestion
import json

def test_smb_parsing():
    """Test the improved SMB parsing functionality"""
    print("🔍 Testing SMB Parsing Improvements")
    print("=" * 50)
    
    # SMB configuration
    server = "10.0.0.141"
    username = "jonclaude"
    password = "1D3fd4138e!!"
    
    # Test connection first
    smb = SMBConnection(server, username, password)
    
    print("1️⃣ Testing share listing...")
    shares = smb.list_shares()
    print(f"   ✅ Found {len(shares)} shares: {', '.join(shares[:5])}{'...' if len(shares) > 5 else ''}")
    
    if not shares:
        print("❌ No shares found - SMB connection issue!")
        return False
    
    # Test file listing on a known share
    test_share = "SYNSRT"  # Known to exist from previous test
    if test_share in shares:
        print(f"\n2️⃣ Testing file listing in share: {test_share}")
        files = smb.list_files(test_share, "")
        
        print(f"   📊 Parser found {len(files)} items in root:")
        
        # Show some sample files/directories
        for i, file_info in enumerate(files[:10]):
            icon = "📁" if file_info['is_dir'] else "📄"
            print(f"   {i+1:2d}. {icon} {file_info['name']} ({file_info['size']} bytes)")
        
        if len(files) > 10:
            print(f"   ... and {len(files) - 10} more items")
        
        # Test directory scanning if we found directories
        directories = [f for f in files if f['is_dir']][:3]  # Test first 3 dirs
        for dir_info in directories:
            print(f"\n3️⃣ Testing subdirectory: {dir_info['name']}")
            subfiles = smb.list_files(test_share, dir_info['path'])
            print(f"   📊 Found {len(subfiles)} items in {dir_info['name']}")
            
            # Show sample files from subdirectory
            for j, subfile in enumerate(subfiles[:5]):
                icon = "📁" if subfile['is_dir'] else "📄"
                print(f"      {j+1}. {icon} {subfile['name']}")
    
    else:
        print(f"❌ Test share '{test_share}' not found!")
        return False
    
    print(f"\n✅ SMB parsing test completed successfully!")
    return True

def test_ingestion_small():
    """Test ingestion on a small subset"""
    print(f"\n🚀 Testing Small-Scale Ingestion")
    print("=" * 50)
    
    # SMB configuration
    server = "10.0.0.141"
    username = "jonclaude"
    password = "1D3fd4138e!!"
    
    # Initialize ingestion system
    ingestion = SMBNexusIngestion(server, username, password)
    
    print("🎯 Running limited ingestion test...")
    
    # Test just listing shares without full scan
    shares = ingestion.smb.list_shares()
    print(f"📊 Available shares: {', '.join(shares)}")
    
    # Get initial stats
    initial_stats = ingestion.get_stats()
    print(f"📈 Initial stats: {json.dumps(initial_stats, indent=2)}")
    
    return True

if __name__ == "__main__":
    success = test_smb_parsing()
    if success:
        test_ingestion_small()
    else:
        print("❌ SMB parsing test failed!")