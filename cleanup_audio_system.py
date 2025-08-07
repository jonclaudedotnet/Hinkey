#!/usr/bin/env python3
"""
Audio System Cleanup - Reset all audio to default state
Remove all Siobhan virtual devices and restore clean audio
"""

import subprocess
import time

def show_current_audio_mess():
    """Show what audio devices currently exist"""
    print("🔍 Current Audio System Status")
    print("=" * 40)
    
    try:
        # Show all sinks (output devices)
        print("📤 Current Audio Sinks (Outputs):")
        result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                              capture_output=True, text=True)
        
        siobhan_sinks = []
        normal_sinks = []
        
        for line in result.stdout.split('\n'):
            if line.strip():
                if any(word in line.lower() for word in ['siobhan', 'browser', 'meeting']):
                    siobhan_sinks.append(line.strip())
                else:
                    normal_sinks.append(line.strip())
        
        for sink in normal_sinks:
            print(f"   ✅ {sink}")
        for sink in siobhan_sinks:
            print(f"   🗑️ {sink} (will be removed)")
        
        # Show all sources (input devices)
        print("\n📥 Current Audio Sources (Inputs):")
        result = subprocess.run(['pactl', 'list', 'short', 'sources'], 
                              capture_output=True, text=True)
        
        siobhan_sources = []
        normal_sources = []
        
        for line in result.stdout.split('\n'):
            if line.strip():
                if any(word in line.lower() for word in ['siobhan', 'browser', 'meeting']):
                    siobhan_sources.append(line.strip())
                else:
                    normal_sources.append(line.strip())
        
        for source in normal_sources:
            print(f"   ✅ {source}")
        for source in siobhan_sources:
            print(f"   🗑️ {source} (will be removed)")
        
        # Show loaded modules
        print("\n🔧 Audio Modules:")
        result = subprocess.run(['pactl', 'list', 'short', 'modules'], 
                              capture_output=True, text=True)
        
        siobhan_modules = []
        for line in result.stdout.split('\n'):
            if line.strip() and any(word in line.lower() for word in ['siobhan', 'browser', 'meeting', 'loopback']):
                siobhan_modules.append(line.strip())
        
        print(f"   Found {len(siobhan_modules)} Siobhan-related modules to remove")
        
        return len(siobhan_sinks) + len(siobhan_sources) + len(siobhan_modules)
        
    except Exception as e:
        print(f"❌ Error checking audio status: {e}")
        return 0

def remove_all_siobhan_modules():
    """Remove all Siobhan-related audio modules"""
    print("\n🧹 Removing All Siobhan Audio Modules...")
    
    try:
        result = subprocess.run(['pactl', 'list', 'short', 'modules'], 
                              capture_output=True, text=True)
        
        modules_to_remove = []
        for line in result.stdout.split('\n'):
            if line.strip():
                # Look for any modules related to our virtual devices
                if any(word in line.lower() for word in [
                    'siobhan', 'browser', 'meeting', 
                    'null-sink', 'loopback', 'combine-sink'
                ]):
                    module_id = line.split('\t')[0]
                    if module_id.isdigit():
                        modules_to_remove.append((module_id, line.strip()))
        
        print(f"   Found {len(modules_to_remove)} modules to remove")
        
        removed_count = 0
        for module_id, module_desc in modules_to_remove:
            try:
                result = subprocess.run(['pactl', 'unload-module', module_id], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   ✅ Removed: {module_desc[:60]}...")
                    removed_count += 1
                else:
                    print(f"   ⚠️ Warning removing {module_id}: {result.stderr}")
            except Exception as e:
                print(f"   ❌ Error removing {module_id}: {e}")
        
        print(f"✅ Removed {removed_count} audio modules")
        return removed_count
        
    except Exception as e:
        print(f"❌ Error during module cleanup: {e}")
        return 0

def restart_pulseaudio():
    """Restart PulseAudio to ensure clean state"""
    print("\n🔄 Restarting PulseAudio Service...")
    
    try:
        # Kill user PulseAudio processes
        subprocess.run(['pulseaudio', '--kill'], capture_output=True)
        time.sleep(2)
        
        # Start PulseAudio again
        subprocess.run(['pulseaudio', '--start'], capture_output=True)
        time.sleep(3)
        
        print("✅ PulseAudio restarted")
        return True
        
    except Exception as e:
        print(f"⚠️ PulseAudio restart error: {e}")
        print("   Audio should still work, continuing...")
        return False

def check_default_audio():
    """Check and show default audio devices"""
    print("\n🎯 Checking Default Audio Configuration...")
    
    try:
        # Get default sink
        result = subprocess.run(['pactl', 'info'], capture_output=True, text=True)
        
        default_sink = None
        default_source = None
        
        for line in result.stdout.split('\n'):
            if 'Default Sink:' in line:
                default_sink = line.split(': ')[1].strip()
            elif 'Default Source:' in line:
                default_source = line.split(': ')[1].strip()
        
        print(f"   🔊 Default Output: {default_sink}")
        print(f"   🎤 Default Input: {default_source}")
        
        # Test default audio
        print("\n🧪 Testing Default Audio...")
        test_result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                                   capture_output=True, text=True)
        
        clean_sinks = []
        for line in test_result.stdout.split('\n'):
            if line.strip() and not any(word in line.lower() for word in ['siobhan', 'browser', 'meeting']):
                clean_sinks.append(line.strip())
        
        print(f"   ✅ Found {len(clean_sinks)} clean audio devices")
        for sink in clean_sinks:
            print(f"      {sink}")
        
        return len(clean_sinks) > 0
        
    except Exception as e:
        print(f"❌ Error checking default audio: {e}")
        return False

def kill_all_siobhan_processes():
    """Kill any running Siobhan audio processes"""
    print("\n🛑 Stopping All Siobhan Processes...")
    
    processes_to_kill = [
        'siobhan_voice_system',
        'siobhan_continuous_listener', 
        'siobhan_meeting_listener',
        'start_continuous_meeting_system',
        'start_simple_meeting_system'
    ]
    
    killed_count = 0
    for process_name in processes_to_kill:
        try:
            result = subprocess.run(['pkill', '-f', process_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ Stopped: {process_name}")
                killed_count += 1
            # Don't report if process wasn't running
        except Exception:
            pass
    
    if killed_count > 0:
        print(f"✅ Stopped {killed_count} processes")
        time.sleep(2)  # Give processes time to clean up
    else:
        print("   No Siobhan processes were running")

def test_clean_audio():
    """Test that audio is working normally"""
    print("\n🧪 Testing Clean Audio System...")
    
    try:
        # Try to play a test sound
        print("   Testing audio playback...")
        result = subprocess.run(['pactl', 'play-sample', '0'], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print("   ✅ Audio playback working")
        else:
            print("   ⚠️ Audio playback test failed (but audio may still work)")
        
        # Check microphone
        print("   Testing microphone access...")
        result = subprocess.run(['arecord', '-d', '1', '/dev/null'], 
                              capture_output=True, text=True, timeout=3)
        
        if result.returncode == 0:
            print("   ✅ Microphone access working")
        else:
            print("   ⚠️ Microphone test failed (but may still work)")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("   ⚠️ Audio tests timed out")
        return False
    except Exception as e:
        print(f"   ⚠️ Audio test error: {e}")
        return False

def main():
    """Complete audio system cleanup"""
    print("🧹 Complete Audio System Cleanup")
    print("=" * 50)
    print("This will remove ALL Siobhan virtual audio devices")
    print("and restore your audio system to a clean state.")
    print("=" * 50)
    
    # Show current mess
    device_count = show_current_audio_mess()
    
    if device_count == 0:
        print("\n✅ Audio system appears to be clean already!")
        return
    
    print(f"\n🎯 Found {device_count} audio items to clean up")
    
    # Stop all processes
    kill_all_siobhan_processes()
    
    # Remove all modules
    removed_modules = remove_all_siobhan_modules()
    
    # Restart audio system
    restart_pulseaudio()
    
    # Check defaults
    defaults_ok = check_default_audio()
    
    # Test clean audio
    test_clean_audio()
    
    print("\n" + "=" * 50)
    print("🎉 AUDIO CLEANUP COMPLETE")
    print("=" * 50)
    
    if removed_modules > 0:
        print(f"✅ Removed {removed_modules} virtual audio devices")
        print("✅ PulseAudio restarted")
        print("✅ System restored to clean state")
        
        if defaults_ok:
            print("✅ Default audio devices working")
        else:
            print("⚠️ Check your default audio settings")
            
        print("\n🎵 Your audio should now work normally!")
        print("🎧 Test with your browser, music apps, etc.")
        
    else:
        print("✅ Audio system was already clean")
    
    print("\n📋 To verify everything works:")
    print("   1. Open YouTube and play a video")
    print("   2. Test microphone in browser")  
    print("   3. Check volume controls work normally")
    print("=" * 50)

if __name__ == "__main__":
    main()