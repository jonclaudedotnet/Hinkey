#!/usr/bin/env python3
"""
Start Simple Meeting System - No browser configuration needed!
Uses simple default monitor approach (Approach 6)
"""

import subprocess
import time
import signal
import sys
from pathlib import Path

class SimpleMeetingSystem:
    """Simple meeting system with default audio monitoring"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
    
    def setup_simple_audio(self):
        """Set up simple audio monitoring (already done by implement_simple_monitor.py)"""
        print("🎧 Verifying simple audio setup...")
        
        try:
            # Check if devices exist
            result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                                  capture_output=True, text=True)
            
            has_siobhan = 'siobhan_voice' in result.stdout
            has_browser_mic = 'browser_microphone' in result.stdout
            
            if has_siobhan and has_browser_mic:
                print("✅ Audio devices ready")
                return True
            else:
                print("⚠️ Audio devices missing, creating them...")
                # Run the setup script
                subprocess.run(['python3', 'implement_simple_monitor.py'], 
                             capture_output=True)
                return True
                
        except Exception as e:
            print(f"❌ Audio setup error: {e}")
            return False
    
    def start_voice_daemon(self):
        """Start the voice system daemon"""
        print("🗣️ Starting voice daemon...")
        
        try:
            process = subprocess.Popen([
                'python3', 'siobhan_voice_system.py', '--daemon'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['voice_daemon'] = process
            print(f"✅ Voice daemon started (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start voice daemon: {e}")
            return False
    
    def start_continuous_listener(self, buffer_minutes=30):
        """Start the simple continuous listener"""
        print("🎧 Starting simple continuous listener...")
        
        try:
            process = subprocess.Popen([
                'python3', 'siobhan_continuous_listener.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
            stdin=subprocess.PIPE, text=True)
            
            # Send buffer duration
            process.stdin.write(f"{buffer_minutes}\\n")
            process.stdin.flush()
            
            self.processes['continuous_listener'] = process
            print(f"✅ Continuous listener started (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start continuous listener: {e}")
            return False
    
    def start_system(self, buffer_minutes=30):
        """Start the simple meeting system"""
        print("🚀 Starting Simple Meeting System")
        print("=" * 50)
        print("🎯 APPROACH 6: DEFAULT AUDIO MONITORING")
        print("=" * 50)
        
        # Setup audio
        if not self.setup_simple_audio():
            print("❌ Audio setup failed")
            return False
        
        # Start voice daemon
        if not self.start_voice_daemon():
            print("❌ Voice daemon failed to start")
            return False
        
        time.sleep(2)
        
        # Start continuous listener
        if not self.start_continuous_listener(buffer_minutes):
            print("❌ Continuous listener failed to start")
            return False
        
        time.sleep(3)
        
        print("\n✅ SIMPLE MEETING SYSTEM ACTIVE")
        print("=" * 50)
        print("📋 System Status:")
        print("   🗣️ Voice daemon: Ready to speak Siobhan's responses")
        print(f"   🎧 Audio monitor: Listening to ALL system audio")
        print("   💬 Wake word: Say 'Siobhan' in your meeting")
        print("   🔄 Auto-purge: Audio deleted every 30 minutes")
        print("\n📝 DEAD SIMPLE Google Meet Setup:")
        print("   🎤 Microphone: Select 'Browser_Microphone'")
        print("   🔊 Speakers: Keep on DEFAULT (your normal speakers)")
        print("   ↳ That's it! No special browser configuration!")
        print("\n🔄 How It Works:")
        print("   1. Meeting plays through your normal speakers")
        print("   2. Siobhan monitors ALL system audio (hears meeting)")
        print("   3. Say 'Siobhan' → She responds through Browser_Microphone")
        print("   4. Meeting participants hear her as if she's real!")
        print("\n⚠️ Keep other audio quiet during meetings")
        print("=" * 50)
        
        self.running = True
        return True
    
    def stop_system(self):
        """Stop all processes"""
        print("\n🛑 Stopping Simple Meeting System...")
        self.running = False
        
        for name, process in self.processes.items():
            try:
                print(f"   Stopping {name}...")
                process.terminate()
                
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    
                print(f"   ✅ {name} stopped")
                
            except Exception as e:
                print(f"   ⚠️ Error stopping {name}: {e}")
        
        print("✅ All processes stopped")
    
    def show_status(self):
        """Show system status"""
        print("\n📊 System Status:")
        
        for name, process in self.processes.items():
            if process.poll() is None:
                status = f"✅ Running (PID: {process.pid})"
            else:
                status = f"❌ Stopped (exit: {process.returncode})"
            
            print(f"   {name}: {status}")

def main():
    """Main entry point"""
    system = SimpleMeetingSystem()
    
    # Handle Ctrl+C
    def signal_handler(sig, frame):
        system.stop_system()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get buffer duration
    try:
        buffer_input = input("🕐 Audio buffer duration in minutes (default 30): ").strip()
        buffer_minutes = int(buffer_input) if buffer_input else 30
    except ValueError:
        buffer_minutes = 30
    
    # Start system
    if system.start_system(buffer_minutes):
        print("\n📋 Commands:")
        print("  'status' - Show system status")
        print("  'test' - Send test voice command")
        print("  'quit' - Stop system")
        
        try:
            while system.running:
                cmd = input("\n> ").strip().lower()
                
                if cmd == 'quit':
                    break
                elif cmd == 'status':
                    system.show_status()
                elif cmd == 'test':
                    # Add test voice command
                    import sqlite3
                    from datetime import datetime
                    
                    db_path = 'claude_dolores_bridge/shared_tasks.db'
                    test_message = 'Testing simple audio system. This should work with no browser configuration!'
                    
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO tasks (timestamp, requester, task_type, content, context, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        datetime.now().isoformat(),
                        'simple_test',
                        'voice_command',
                        test_message,
                        'Simple system test',
                        'pending'
                    ))
                    
                    task_id = cursor.lastrowid
                    conn.commit()
                    conn.close()
                    
                    print(f"🎤 Added test command (task #{task_id})")
                    print("🔊 Siobhan should speak this now!")
                    
                elif cmd == '':
                    continue
                else:
                    print("Commands: 'status', 'test', 'quit'")
                    
        except KeyboardInterrupt:
            pass
    
    system.stop_system()

if __name__ == "__main__":
    main()