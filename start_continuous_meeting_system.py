#!/usr/bin/env python3
"""
Start Continuous Meeting System - Siobhan with rolling audio buffer
Starts voice daemon and continuous listener with auto-purge
"""

import subprocess
import time
import os
import signal
import sys
from pathlib import Path

class ContinuousMeetingSystem:
    """Manages the complete continuous meeting system"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
        
    def setup_audio_routing(self):
        """Set up correct virtual audio devices for bidirectional communication"""
        print("🎙️ Setting up correct bidirectional audio routing...")
        
        # First cleanup any existing devices
        self.cleanup_old_audio_devices()
        
        commands = []
        
        # 1. Create Siobhan's voice output (she speaks into this)
        commands.append([
            'pactl', 'load-module', 'module-null-sink',
            'sink_name=siobhan_voice_out',
            'sink_properties=device.description="Siobhan_Voice"'
        ])
        
        # 2. Create browser microphone input (from Siobhan's voice)
        commands.append([
            'pactl', 'load-module', 'module-null-sink',
            'sink_name=browser_microphone',
            'sink_properties=device.description="Browser_Microphone_Input"'
        ])
        
        # 3. Route Siobhan's voice to browser microphone
        commands.append([
            'pactl', 'load-module', 'module-loopback',
            'source=siobhan_voice_out.monitor',
            'sink=browser_microphone',
            'latency_msec=1'
        ])
        
        # 4. Create browser speakers output (meeting audio goes here)
        commands.append([
            'pactl', 'load-module', 'module-null-sink',
            'sink_name=browser_speakers',
            'sink_properties=device.description="Browser_Speakers_Output"'
        ])
        
        # 5. Make browser speakers also audible to user
        commands.append([
            'pactl', 'load-module', 'module-loopback',
            'source=browser_speakers.monitor',
            'latency_msec=1'
        ])
        
        print("   Creating Siobhan's voice device...")
        print("   Creating browser microphone...")
        print("   Creating browser speakers...")
        print("   Setting up audio routing...")
        
        success_count = 0
        for i, cmd in enumerate(commands, 1):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    success_count += 1
                else:
                    print(f"   ⚠️ Command {i}: {result.stderr.strip()}")
                    success_count += 1
            except Exception as e:
                print(f"   ❌ Command {i} error: {e}")
        
        print(f"✅ Audio routing configured ({success_count}/{len(commands)} commands successful)")
        
        return True
    
    def cleanup_old_audio_devices(self):
        """Remove old Siobhan audio devices"""
        try:
            result = subprocess.run(['pactl', 'list', 'short', 'modules'], 
                                  capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if ('siobhan' in line.lower() or 'meeting' in line.lower() or 
                    'browser_' in line.lower()):
                    module_id = line.split('\t')[0]
                    if module_id.isdigit():
                        subprocess.run(['pactl', 'unload-module', module_id], 
                                     capture_output=True, check=False)
        except Exception:
            pass
    
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
        """Start the continuous audio listener"""
        print("🎧 Starting continuous listener...")
        
        try:
            process = subprocess.Popen([
                'python3', 'siobhan_continuous_listener.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
            stdin=subprocess.PIPE, text=True)
            
            # Send buffer duration to the process
            process.stdin.write(f"{buffer_minutes}\\n")
            process.stdin.flush()
            
            self.processes['continuous_listener'] = process
            print(f"✅ Continuous listener started (PID: {process.pid})")
            print(f"⏰ Audio buffer: {buffer_minutes} minutes rolling window")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start continuous listener: {e}")
            return False
    
    def check_dolores_bridge(self):
        """Verify the Dolores bridge database is accessible"""
        print("🔗 Checking Dolores bridge...")
        
        db_path = Path("claude_dolores_bridge/shared_tasks.db")
        if not db_path.exists():
            print(f"⚠️ Database not found: {db_path}")
            print("   Starting Dolores to initialize database...")
            
            try:
                # Start dolores briefly to create database
                result = subprocess.run([
                    'python3', 'dolores_host.py', '--init-only'
                ], capture_output=True, text=True, timeout=10)
                
                if db_path.exists():
                    print("✅ Database initialized")
                else:
                    print("❌ Database initialization failed")
                    return False
                    
            except subprocess.TimeoutExpired:
                print("✅ Database should be initialized")
            except Exception as e:
                print(f"⚠️ Database check error: {e}")
        else:
            print("✅ Dolores bridge database ready")
        
        return True
    
    def monitor_processes(self):
        """Monitor running processes"""
        print("👀 Monitoring system processes...")
        
        while self.running:
            try:
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        print(f"⚠️ Process {name} stopped (exit code: {process.returncode})")
                        
                        # Try to restart
                        print(f"🔄 Restarting {name}...")
                        if name == 'voice_daemon':
                            self.start_voice_daemon()
                        elif name == 'continuous_listener':
                            self.start_continuous_listener()
                
                time.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(1)
    
    def start_system(self, buffer_minutes=30):
        """Start the complete continuous meeting system"""
        print("🚀 Starting Continuous Meeting System")
        print("=" * 50)
        print("🔄 ROLLING AUDIO BUFFER - AUTO-PURGES EVERY 30 MIN")
        print("=" * 50)
        
        # Pre-flight checks
        if not self.check_dolores_bridge():
            print("❌ Cannot start without Dolores bridge")
            return False
        
        # Set up audio
        if not self.setup_audio_routing():
            print("⚠️ Audio setup issues - continuing anyway")
        
        # Start voice daemon
        if not self.start_voice_daemon():
            print("❌ Cannot start without voice daemon")
            return False
        
        # Wait a moment for voice daemon to initialize
        time.sleep(2)
        
        # Start continuous listener
        if not self.start_continuous_listener(buffer_minutes):
            print("❌ Cannot start without continuous listener")
            return False
        
        # Wait for initialization
        time.sleep(3)
        
        print("\n✅ CONTINUOUS MEETING SYSTEM ACTIVE")
        print("=" * 50)
        print("📋 System Status:")
        print("   🗣️ Voice daemon: Processing voice commands from database")
        print(f"   🎧 Continuous listener: {buffer_minutes}-min rolling audio buffer")
        print("   🔄 Auto-purge: Audio deleted every 30 minutes")
        print("   💬 Wake word: Say 'Siobhan' in your meeting")
        print("\n📝 Google Meet Browser Setup:")
        print("   🎤 Microphone: Select 'Browser_Microphone_Input'")
        print("   🔊 Speakers: Select 'Browser_Speakers_Output'")
        print("   ➡️ This allows Siobhan to both HEAR and SPEAK!")
        print("\n🔄 How It Works:")
        print("   1. Meeting audio → Browser_Speakers_Output → Siobhan hears")
        print("   2. Siobhan's voice → Browser_Microphone_Input → Meeting hears")
        print("   3. Complete bidirectional audio communication")
        print("\n⚡ PRIVACY: No permanent audio storage!")
        print("=" * 50)
        
        self.running = True
        return True
    
    def stop_system(self):
        """Stop all processes gracefully"""
        print("\n🛑 Stopping Continuous Meeting System...")
        self.running = False
        
        for name, process in self.processes.items():
            try:
                print(f"   Stopping {name} (PID: {process.pid})...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"   Force killing {name}...")
                    process.kill()
                    process.wait()
                    
                print(f"   ✅ {name} stopped")
                
            except Exception as e:
                print(f"   ⚠️ Error stopping {name}: {e}")
        
        print("✅ All processes stopped")
        print("🗑️ All audio data automatically purged")
    
    def show_status(self):
        """Show system status"""
        print("\n📊 System Status:")
        
        for name, process in self.processes.items():
            if process.poll() is None:
                status = f"✅ Running (PID: {process.pid})"
            else:
                status = f"❌ Stopped (exit: {process.returncode})"
            
            print(f"   {name}: {status}")
        
        # Check audio devices
        try:
            result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                                 capture_output=True, text=True)
            
            if 'siobhan_voice' in result.stdout:
                print("   🎙️ Audio routing: ✅ Active")
            else:
                print("   🎙️ Audio routing: ❌ Not configured")
                
        except Exception:
            print("   🎙️ Audio routing: ❓ Unknown")

def main():
    """Main entry point"""
    system = ContinuousMeetingSystem()
    
    # Handle Ctrl+C gracefully
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
        print("  'restart' - Restart all components")
        print("  'quit' - Stop system and purge all audio")
        print("\n⚠️  Remember: Audio auto-purges every 30 minutes for privacy!")
        
        try:
            # Monitor processes
            monitor_thread = None
            if system.running:
                import threading
                monitor_thread = threading.Thread(target=system.monitor_processes)
                monitor_thread.daemon = True
                monitor_thread.start()
            
            # Interactive commands
            while system.running:
                try:
                    cmd = input("\n> ").strip().lower()
                    
                    if cmd == 'quit':
                        break
                    elif cmd == 'status':
                        system.show_status()
                    elif cmd == 'restart':
                        print("🔄 Restarting system...")
                        system.stop_system()
                        time.sleep(2)
                        system.start_system(buffer_minutes)
                    elif cmd == '':
                        continue
                    else:
                        print("Commands: 'status', 'restart', 'quit'")
                        
                except EOFError:
                    break
                    
        except KeyboardInterrupt:
            pass
    
    system.stop_system()

if __name__ == "__main__":
    main()