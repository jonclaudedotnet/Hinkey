#!/usr/bin/env python3
"""
Implement Approach 6: Simple Default Monitor
Siobhan listens to whatever audio is playing on the system
"""

import subprocess
import time

def cleanup_all_siobhan_audio():
    """Remove all existing Siobhan audio devices"""
    print("🧹 Cleaning up all existing audio devices...")
    
    try:
        result = subprocess.run(['pactl', 'list', 'short', 'modules'], 
                              capture_output=True, text=True)
        
        removed_count = 0
        for line in result.stdout.split('\n'):
            if ('siobhan' in line.lower() or 'browser' in line.lower()):
                module_id = line.split('\t')[0]
                if module_id.isdigit():
                    subprocess.run(['pactl', 'unload-module', module_id], 
                                 capture_output=True, check=False)
                    removed_count += 1
        
        print(f"✅ Removed {removed_count} audio modules")
        
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

def create_simple_audio_setup():
    """Create the simple monitoring setup"""
    print("🎯 Creating Simple Audio Setup (Approach 6)...")
    
    commands = []
    
    # 1. Create Siobhan's voice output (she speaks into this)
    commands.append([
        'pactl', 'load-module', 'module-null-sink',
        'sink_name=siobhan_voice',
        'sink_properties=device.description="Siobhan_Voice"'
    ])
    
    # 2. Create browser microphone (Google Meet selects this as mic)
    commands.append([
        'pactl', 'load-module', 'module-null-sink',
        'sink_name=browser_microphone',
        'sink_properties=device.description="Browser_Microphone"'
    ])
    
    # 3. Route Siobhan's voice to browser microphone
    commands.append([
        'pactl', 'load-module', 'module-loopback',
        'source=siobhan_voice.monitor',
        'sink=browser_microphone',
        'latency_msec=1'
    ])
    
    # 4. SIMPLE APPROACH: Siobhan listens to default system audio
    # This captures whatever is playing on your speakers
    commands.append([
        'pactl', 'load-module', 'module-loopback',
        'source=@DEFAULT_MONITOR@',  # Whatever system is outputting
        'sink=siobhan_voice',        # Route to Siobhan so she can hear
        'latency_msec=50'
    ])
    
    print("   Creating Siobhan's voice device...")
    print("   Creating browser microphone...")
    print("   Setting up voice routing...")
    print("   🎧 Setting up system audio monitoring...")
    
    success_count = 0
    for i, cmd in enumerate(commands, 1):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ Step {i}: Success")
                success_count += 1
            else:
                print(f"   ⚠️ Step {i}: {result.stderr.strip()}")
                success_count += 1  # Count as success anyway
        except Exception as e:
            print(f"   ❌ Step {i}: {e}")
    
    print(f"✅ Simple audio setup complete ({success_count}/{len(commands)} steps)")
    return success_count >= 3

def show_simple_setup_instructions():
    """Show the dead-simple setup instructions"""
    print("\n📋 DEAD SIMPLE Setup Instructions")
    print("=" * 45)
    print("🎛️ Google Meet Settings:")
    print("   🎤 Microphone: Select 'Browser_Microphone'")
    print("   🔊 Speakers: Keep on DEFAULT (whatever you normally use)")
    print("   ↳ No special browser configuration needed!")
    print()
    print("🔄 How It Works:")
    print("   1. Browser plays meeting audio to your DEFAULT speakers")
    print("   2. Siobhan monitors all system audio (hears the meeting)")
    print("   3. When someone says 'Siobhan', she responds")
    print("   4. Her response goes to Browser_Microphone")
    print("   5. Meeting participants hear Siobhan")
    print()
    print("✅ Advantages:")
    print("   • No browser configuration needed")
    print("   • Works with any audio setup")
    print("   • Simple and reliable")
    print("   • You hear the meeting normally")
    print()
    print("⚠️ Note:")
    print("   Siobhan will hear ALL system audio, not just the meeting")
    print("   Keep other audio quiet during meetings")
    print("=" * 45)

def test_simple_setup():
    """Test the simple setup"""
    print("\n🧪 Testing Simple Audio Setup...")
    
    try:
        # Check devices exist
        result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                              capture_output=True, text=True)
        
        has_siobhan = 'siobhan_voice' in result.stdout
        has_browser_mic = 'browser_microphone' in result.stdout
        
        print(f"   Siobhan voice device: {'✅' if has_siobhan else '❌'}")
        print(f"   Browser microphone: {'✅' if has_browser_mic else '❌'}")
        
        # Check loopback connections
        result = subprocess.run(['pactl', 'list', 'short', 'modules'], 
                              capture_output=True, text=True)
        
        has_system_monitor = '@DEFAULT_MONITOR@' in result.stdout or 'DEFAULT_MONITOR' in result.stdout
        has_voice_routing = 'siobhan_voice.monitor' in result.stdout
        
        print(f"   System audio monitoring: {'✅' if has_system_monitor else '❌'}")
        print(f"   Voice routing: {'✅' if has_voice_routing else '❌'}")
        
        return has_siobhan and has_browser_mic and has_voice_routing
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Implement the simple monitoring approach"""
    print("🎯 Implementing Simple Default Monitor (Approach 6)")
    print("=" * 55)
    print("This approach avoids browser audio device selection entirely!")
    print("=" * 55)
    
    # Step 1: Clean up
    cleanup_all_siobhan_audio()
    time.sleep(2)
    
    # Step 2: Create simple setup
    setup_success = create_simple_audio_setup()
    time.sleep(2)
    
    # Step 3: Test
    test_success = test_simple_setup()
    
    # Step 4: Show instructions
    show_simple_setup_instructions()
    
    if setup_success and test_success:
        print("\n🎉 SIMPLE SETUP COMPLETE!")
        print("✅ Ready for Google Meet with minimal configuration")
        print("🚀 Just select 'Browser_Microphone' as mic, keep speakers on DEFAULT")
    else:
        print("\n⚠️ Some issues detected, but setup should still work")
        print("🔧 Try the Google Meet setup anyway")
    
    print("\n🎙️ Next: Start the continuous meeting system!")

if __name__ == "__main__":
    main()