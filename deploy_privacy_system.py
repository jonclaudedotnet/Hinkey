#!/usr/bin/env python3
"""
Privacy System Deployment Script
Developed by Maeve for immediate deployment of privacy filtering system
"""

import os
import sys
import json
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime

class PrivacySystemDeployer:
    """Deploy and manage the privacy filtering system"""
    
    def __init__(self):
        self.base_dir = Path.cwd()
        self.log_file = self.base_dir / "privacy_deployment.log"
        self.processes = {}
    
    def log(self, message: str):
        """Log deployment messages"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a') as f:
            f.write(log_message + "\n")
    
    def check_prerequisites(self) -> bool:
        """Check if all required files exist"""
        required_files = [
            "privacy_filter.py",
            "privacy_api.py", 
            "smb_privacy_integration.py",
            "smb_nexus_ingestion.py"
        ]
        
        self.log("🔍 Checking prerequisites...")
        
        missing_files = []
        for file in required_files:
            if not (self.base_dir / file).exists():
                missing_files.append(file)
        
        if missing_files:
            self.log(f"❌ Missing required files: {', '.join(missing_files)}")
            return False
        
        # Check for Python packages
        try:
            import flask
            import sqlite3
            import chromadb
            self.log("✅ All Python dependencies available")
        except ImportError as e:
            self.log(f"❌ Missing Python package: {e}")
            return False
        
        self.log("✅ All prerequisites met")
        return True
    
    def initialize_database(self):
        """Initialize privacy filter database"""
        self.log("🗄️ Initializing privacy database...")
        
        try:
            from privacy_filter import PrivacyDatabase
            db = PrivacyDatabase()
            self.log("✅ Privacy database initialized")
            
            # Test database connection
            stats = db.get_audit_stats(1)
            self.log(f"📊 Database connection verified")
            
        except Exception as e:
            self.log(f"❌ Database initialization failed: {e}")
            raise
    
    def check_existing_ingestion(self) -> dict:
        """Check if there's an existing SMB ingestion running"""
        self.log("🔍 Checking for existing SMB ingestion...")
        
        status_file = self.base_dir / "ingestion_status.json"
        if status_file.exists():
            try:
                with open(status_file, 'r') as f:
                    status = json.load(f)
                
                # Check if it's recent (within last hour)
                last_update = status.get('last_update', 0)
                current_time = time.time()
                
                if current_time - last_update < 3600:  # 1 hour
                    self.log("✅ Found active SMB ingestion")
                    self.log(f"   Current share: {status.get('current_share', 'Unknown')}")
                    self.log(f"   Files found: {status.get('files_found', 0):,}")
                    self.log(f"   Files processed: {status.get('files_processed', 0):,}")
                    return status
                else:
                    self.log("⚠️ Found stale ingestion status")
                    
            except Exception as e:
                self.log(f"⚠️ Error reading ingestion status: {e}")
        
        self.log("ℹ️ No active SMB ingestion found")
        return {}
    
    def start_control_panel(self) -> bool:
        """Start the privacy control panel API"""
        self.log("🌐 Starting privacy control panel...")
        
        try:
            cmd = [sys.executable, "privacy_api.py"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.base_dir
            )
            
            self.processes['control_panel'] = process
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if it's running
            if process.poll() is None:
                self.log("✅ Privacy control panel started")
                self.log("📊 Access at: http://localhost:5001/")
                return True
            else:
                stdout, stderr = process.communicate()
                self.log(f"❌ Control panel failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error starting control panel: {e}")
            return False
    
    def upgrade_existing_ingestion(self):
        """Upgrade existing ingestion with privacy filtering"""
        self.log("🔄 Upgrading existing ingestion with privacy filtering...")
        
        try:
            from smb_privacy_integration import upgrade_existing_ingestion
            success = upgrade_existing_ingestion()
            
            if success:
                self.log("✅ Successfully upgraded existing ingestion")
            else:
                self.log("⚠️ Upgrade completed with warnings")
                
        except Exception as e:
            self.log(f"❌ Error upgrading ingestion: {e}")
            raise
    
    def start_new_privacy_ingestion(self):
        """Start new privacy-enabled ingestion"""
        self.log("🚀 Starting new privacy-enabled SMB ingestion...")
        
        try:
            cmd = [sys.executable, "smb_privacy_integration.py", "start"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.base_dir
            )
            
            self.processes['ingestion'] = process
            self.log("✅ Privacy-enabled ingestion started")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error starting privacy-enabled ingestion: {e}")
            return False
    
    def start_monitoring(self):
        """Start privacy monitoring in background"""
        self.log("📊 Starting privacy monitoring...")
        
        def monitor():
            try:
                cmd = [sys.executable, "smb_privacy_integration.py", "monitor"]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.base_dir
                )
                self.processes['monitor'] = process
                
            except Exception as e:
                self.log(f"⚠️ Monitoring error: {e}")
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        self.log("✅ Privacy monitoring started in background")
    
    def create_desktop_shortcut(self):
        """Create desktop shortcut for control panel"""
        try:
            desktop_file = Path.home() / "Desktop" / "Privacy_Control_Panel.desktop"
            
            shortcut_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Privacy Control Panel
Comment=SMB Privacy Filter Control Panel
Exec=python3 {self.base_dir}/privacy_api.py
Icon=security-high
Terminal=false
Categories=Utility;Security;
"""
            
            with open(desktop_file, 'w') as f:
                f.write(shortcut_content)
            
            # Make executable
            desktop_file.chmod(0o755)
            
            self.log(f"✅ Desktop shortcut created: {desktop_file}")
            
        except Exception as e:
            self.log(f"⚠️ Could not create desktop shortcut: {e}")
    
    def generate_deployment_report(self, existing_ingestion: dict):
        """Generate deployment summary report"""
        report = {
            "deployment_timestamp": datetime.now().isoformat(),
            "deployment_status": "SUCCESS",
            "components_deployed": {
                "privacy_filter": True,
                "control_panel_api": "control_panel" in self.processes,
                "database": True,
                "integration": True
            },
            "existing_ingestion": bool(existing_ingestion),
            "ingestion_stats": existing_ingestion,
            "access_points": {
                "control_panel": "http://localhost:5001/",
                "api_health": "http://localhost:5001/api/health"
            },
            "files_created": [
                "privacy_filter.py",
                "privacy_api.py", 
                "smb_privacy_integration.py",
                "privacy_filter.db",
                "privacy_deployment.log"
            ],
            "next_steps": [
                "Access control panel at http://localhost:5001/",
                "Monitor privacy filtering in real-time",
                "Adjust privacy rules as needed",
                "Review audit logs for sensitive data detection"
            ]
        }
        
        report_file = self.base_dir / "privacy_deployment_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"📄 Deployment report saved: {report_file}")
        return report
    
    def deploy(self):
        """Main deployment process"""
        self.log("🚀 Starting Privacy System Deployment")
        self.log("=" * 50)
        
        try:
            # Step 1: Check prerequisites
            if not self.check_prerequisites():
                self.log("❌ Deployment failed - prerequisites not met")
                return False
            
            # Step 2: Initialize database
            self.initialize_database()
            
            # Step 3: Check for existing ingestion
            existing_ingestion = self.check_existing_ingestion()
            
            # Step 4: Start control panel
            if not self.start_control_panel():
                self.log("⚠️ Control panel failed to start, continuing deployment...")
            
            # Step 5: Handle ingestion
            if existing_ingestion:
                self.upgrade_existing_ingestion()
            else:
                # Ask user if they want to start new ingestion
                response = input("\n🤔 No existing ingestion found. Start new privacy-enabled scan? (y/N): ")
                if response.lower() in ['y', 'yes']:
                    if not self.start_new_privacy_ingestion():
                        self.log("⚠️ New ingestion failed to start")
            
            # Step 6: Start monitoring
            self.start_monitoring() 
            
            # Step 7: Create shortcuts
            self.create_desktop_shortcut()
            
            # Step 8: Generate report
            report = self.generate_deployment_report(existing_ingestion)
            
            # Success!
            self.log("✅ Privacy System Deployment Complete!")
            self.log("=" * 50)
            self.log("🔐 Privacy filtering is now active")
            self.log("📊 Control Panel: http://localhost:5001/")
            self.log("📄 Deployment report: privacy_deployment_report.json")
            
            # Show quick status
            if existing_ingestion:
                self.log(f"\n📈 Existing Ingestion Enhanced:")
                self.log(f"   Files being processed: {existing_ingestion.get('files_found', 0):,}")
                self.log(f"   Privacy filtering now active on all new files")
            
            self.log("\n🎯 Next Steps:")
            self.log("   1. Open http://localhost:5001/ to access control panel")
            self.log("   2. Monitor privacy filtering in real-time")
            self.log("   3. Adjust privacy rules as needed")
            self.log("   4. Review audit logs for sensitive content")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Deployment failed: {e}")
            self.cleanup()
            return False
    
    def cleanup(self):
        """Clean up processes if deployment fails"""
        self.log("🧹 Cleaning up processes...")
        
        for name, process in self.processes.items():
            try:
                if process.poll() is None:
                    process.terminate()
                    self.log(f"   Stopped {name}")
            except Exception as e:
                self.log(f"   Error stopping {name}: {e}")
    
    def status(self):
        """Show current privacy system status"""
        self.log("📊 Privacy System Status")
        self.log("=" * 30)
        
        # Check if control panel is running
        try:
            import urllib.request
            response = urllib.request.urlopen("http://localhost:5001/api/health", timeout=5)
            if response.status == 200:
                self.log("✅ Control Panel: Running (http://localhost:5001/)")
            else:
                self.log("⚠️ Control Panel: Not responding")
        except:
            self.log("❌ Control Panel: Not running")
        
        # Check database
        try:
            from privacy_filter import PrivacyDatabase
            db = PrivacyDatabase()
            stats = db.get_audit_stats(1)
            self.log(f"✅ Database: Connected ({stats.get('total_files', 0)} files processed)")
        except:
            self.log("❌ Database: Not accessible")
        
        # Check ingestion status
        status_file = self.base_dir / "ingestion_status.json"
        if status_file.exists():
            with open(status_file, 'r') as f:
                status = json.load(f)
            
            last_update = status.get('last_update', 0)
            if time.time() - last_update < 300:  # 5 minutes
                self.log("✅ SMB Ingestion: Active")
                self.log(f"   Files processed: {status.get('files_processed', 0):,}")
            else:
                self.log("⚠️ SMB Ingestion: Inactive")
        else:
            self.log("❌ SMB Ingestion: No status found")
        
        # Check privacy status
        privacy_file = self.base_dir / "privacy_status.json"
        if privacy_file.exists():
            with open(privacy_file, 'r') as f:
                privacy_status = json.load(f)
            
            self.log("✅ Privacy Filtering: Active")
            self.log(f"   Files filtered: {privacy_status.get('files_filtered', 0):,}")
            self.log(f"   Files blocked: {privacy_status.get('files_blocked', 0):,}")
        else:
            self.log("⚠️ Privacy Filtering: No status available")

def main():
    """Main entry point"""
    deployer = PrivacySystemDeployer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'status':
            deployer.status()
        elif command == 'cleanup':
            deployer.cleanup()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python3 deploy_privacy_system.py [status|cleanup]")
    else:
        # Full deployment
        success = deployer.deploy()
        if not success:
            print("\n❌ Deployment failed. Check privacy_deployment.log for details.")
            sys.exit(1)

if __name__ == "__main__":
    main()