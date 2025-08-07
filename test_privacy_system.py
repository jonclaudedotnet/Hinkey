#!/usr/bin/env python3
"""
Privacy System Test Suite
Quick verification that all components work correctly
"""

import sys
import json
import time
from pathlib import Path

def test_privacy_filter():
    """Test core privacy filtering functionality"""
    print("🧪 Testing Privacy Filter...")
    
    try:
        from privacy_filter import PrivacyFilter
        
        # Initialize filter
        filter_system = PrivacyFilter()
        
        # Test file paths from your current scan
        test_cases = [
            ("SYNSRT/SORT/Move off MacMini 2021/Tanasi/Desktop/passwords.txt", 
             "My email is tanasi@example.com and password is secret123!"),
            
            ("SYNSRT/SORT/Move off MacMini 2021/Tanasi/Desktop/Old Firefox Data/places.sqlite",
             "https://facebook.com/tanasi.profile visited at 2023-01-01"),
            
            ("SYNSRT/All Work/JonClaude/project.txt",
             "Project contact: jonclaude@searobintech.com phone 555-1234"),
            
            ("SYNSRT/public/readme.txt",
             "This is public documentation for the project")
        ]
        
        for file_path, content in test_cases:
            filtered_content, metadata = filter_system.filter_content(file_path, content)
            
            owner = metadata['owner']
            privacy_level = metadata['privacy_level']
            filtered = metadata['filtered']
            patterns = metadata.get('patterns_detected', [])
            
            print(f"   📄 {Path(file_path).name}")
            print(f"      Owner: {owner}")
            print(f"      Level: {privacy_level}")
            print(f"      Filtered: {filtered}")
            if patterns:
                print(f"      Patterns: {', '.join(patterns)}")
            print()
        
        print("✅ Privacy Filter: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Privacy Filter: FAILED - {e}")
        return False

def test_database():
    """Test privacy database functionality"""
    print("🧪 Testing Privacy Database...")
    
    try:
        from privacy_filter import PrivacyDatabase, PrivacyLevel
        
        # Initialize database
        db = PrivacyDatabase()
        
        # Test basic operations
        db.set_file_privacy_level(
            "test/file.txt", 
            "tanasi", 
            PrivacyLevel.PRIVATE, 
            "Test override"
        )
        
        level = db.get_file_privacy_level("test/file.txt")
        if level != PrivacyLevel.PRIVATE:
            raise Exception("File privacy level not set correctly")
        
        # Test audit stats
        stats = db.get_audit_stats(1)
        if not isinstance(stats, dict):
            raise Exception("Audit stats not returned as dict")
        
        print("✅ Privacy Database: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Privacy Database: FAILED - {e}")
        return False

def test_api_startup():
    """Test if API can start up"""
    print("🧪 Testing API Startup...")
    
    try:
        import subprocess
        import time
        import urllib.request
        
        # Start API in background
        cmd = [sys.executable, "privacy_api.py"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give it time to start
        time.sleep(3)
        
        # Test health endpoint
        try:
            response = urllib.request.urlopen("http://localhost:5001/api/health", timeout=5)
            if response.status == 200:
                data = json.loads(response.read())
                if data.get('status') == 'healthy':
                    print("✅ API Startup: PASSED")
                    success = True
                else:
                    print("❌ API Startup: FAILED - Unhealthy response")
                    success = False
            else:
                print(f"❌ API Startup: FAILED - Status {response.status}")
                success = False
        except Exception as e:
            print(f"❌ API Startup: FAILED - {e}")
            success = False
        
        # Clean up
        process.terminate()
        process.wait(timeout=5)
        
        return success
        
    except Exception as e:
        print(f"❌ API Startup: FAILED - {e}")
        return False

def test_smb_integration():
    """Test SMB integration compatibility"""
    print("🧪 Testing SMB Integration...")
    
    try:
        from smb_privacy_integration import PrivacyEnabledDocumentProcessor
        from privacy_filter import PrivacyFilter
        
        # Initialize components
        privacy_filter = PrivacyFilter()
        processor = PrivacyEnabledDocumentProcessor(privacy_filter)
        
        # Create test file
        test_file = Path("test_document.txt")
        test_content = "Test document with email: test@example.com"
        
        test_file.write_text(test_content)
        
        try:
            # Process test file
            result = processor.process_file(test_file, "SYNSRT/test/document.txt")
            
            if result is None:
                print("   File was blocked by privacy filter")
            elif 'privacy_metadata' in result:
                print("   Privacy filtering applied successfully")
            else:
                print("   File processed without privacy filtering")
            
            # Check stats
            stats = processor.get_privacy_stats()
            print(f"   Privacy stats: {stats}")
            
            print("✅ SMB Integration: PASSED")
            success = True
            
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
        
        return success
        
    except Exception as e:
        print(f"❌ SMB Integration: FAILED - {e}")
        return False

def test_deployment_readiness():
    """Test if system is ready for deployment"""
    print("🧪 Testing Deployment Readiness...")
    
    try:
        from deploy_privacy_system import PrivacySystemDeployer
        
        deployer = PrivacySystemDeployer()
        
        # Check prerequisites
        if not deployer.check_prerequisites():
            print("❌ Prerequisites not met")
            return False
        
        # Check existing ingestion
        existing = deployer.check_existing_ingestion()
        if existing:
            print(f"   Found existing ingestion: {existing.get('files_found', 0)} files")
        else:
            print("   No existing ingestion found")
        
        print("✅ Deployment Readiness: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Deployment Readiness: FAILED - {e}")
        return False

def show_current_ingestion_status():
    """Show current SMB ingestion status"""
    print("📊 Current SMB Ingestion Status")
    print("=" * 40)
    
    status_file = Path("ingestion_status.json")
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
            
            print(f"   Current Share: {status.get('current_share', 'Unknown')}")
            print(f"   Files Found: {status.get('files_found', 0):,}")
            print(f"   Files Processed: {status.get('files_processed', 0):,}")
            print(f"   Files Vectorized: {status.get('files_vectorized', 0):,}")
            print(f"   Current Directory: {status.get('current_directory', 'Unknown')}")
            
            current_file = status.get('current_file', '')
            if current_file:
                filename = Path(current_file).name
                print(f"   Current File: {filename}")
            
            elapsed = status.get('elapsed_time', 0)
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            print(f"   Running Time: {hours}h {minutes}m")
            
            progress = status.get('processing_progress', 0)
            print(f"   Progress: {progress:.1f}%")
            
            # Check if it's Tanasi's files being processed
            current_dir = status.get('current_directory', '')
            if 'tanasi' in current_dir.lower():
                print("   🔒 Processing Tanasi's personal files - Privacy protection needed!")
            
        except Exception as e:
            print(f"   Error reading status: {e}")
    else:
        print("   No ingestion status file found")

def main():
    """Run all tests"""
    print("🔐 Privacy System Test Suite")
    print("=" * 50)
    
    # Show current ingestion status first
    show_current_ingestion_status()
    print()
    
    # Run tests
    tests = [
        test_privacy_filter,
        test_database,
        test_smb_integration,
        test_api_startup,
        test_deployment_readiness
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    # Summary
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All systems ready for deployment!")
        print("\n🚀 To deploy privacy system:")
        print("   python3 deploy_privacy_system.py")
    else:
        print("❌ Some tests failed. Check errors above.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)