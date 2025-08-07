#!/usr/bin/env python3
"""
Fix Audio Routing - Proper bidirectional setup for Siobhan
"""

import subprocess
import time

def cleanup_old_devices():
    """Remove old Siobhan audio devices"""
    print("🧹 Cleaning up old audio devices...")
    
    try:
        # Get list of loaded modules
        result = subprocess.run(['pactl', 'list', 'short', 'modules'], 
                              capture_output=True, text=True)
        
        # Find and unload Siobhan-related modules
        for line in result.stdout.split('\n'):
            if 'siobhan' in line.lower() or 'meeting' in line.lower():
                module_id = line.split('\t')[0]
                if module_id.isdigit():
                    subprocess.run(['pactl', 'unload-module', module_id], 
                                 capture_output=True)
                    print(f"   Removed module {module_id}")
        
        print("✅ Cleanup complete")
        
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

def setup_correct_audio_routing():
    """Set up proper audio routing for bidirectional communication"""
    print("🎙️ Setting up CORRECT audio routing...")
    
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
    
    # 4. Create a virtual speaker device for browser output
    commands.append([
        'pactl', 'load-module', 'module-null-sink',
        'sink_name=browser_speakers',
        'sink_properties=device.description="Browser_Speakers_Output"'
    ])
    
    # 5. Make browser speakers also go to real speakers (so you can hear too)
    commands.append([
        'pactl', 'load-module', 'module-loopback',
        'source=browser_speakers.monitor',
        'latency_msec=1'
    ])
    
    print("   Creating audio devices...")
    
    for i, cmd in enumerate(commands, 1):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ Command {i}: Success")
            else:
                print(f"   ⚠️ Command {i}: {result.stderr.strip()}")
        except Exception as e:
            print(f"   ❌ Command {i}: {e}")
    
    print("✅ Audio routing configured!")
    
    return True

def show_audio_setup_instructions():
    """Show the correct setup instructions"""
    print("\n📋 CORRECT Google Meet Browser Setup:")
    print("=" * 50)
    print("🎤 MICROPHONE:")
    print("   Select: 'Browser_Microphone_Input' (monitor)")
    print("   ↳ This carries Siobhan's voice to the meeting")
    print()
    print("🔊 SPEAKERS:")
    print("   Select: 'Browser_Speakers_Output'")
    print("   ↳ This sends meeting audio where Siobhan can hear it")
    print()
    print("🔄 Audio Flow:")
    print("   Meeting → Browser_Speakers_Output → Siobhan hears")
    print("   Siobhan → Browser_Microphone_Input → Meeting hears")
    print("=" * 50)

def test_new_setup():
    """Test the new audio setup"""
    print("\n🧪 Testing new audio setup...")
    
    try:
        # List sinks (should show up as speakers/outputs)
        result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                              capture_output=True, text=True)
        
        browser_sinks = []
        for line in result.stdout.split('\n'):
            if 'browser_speakers' in line.lower():
                browser_sinks.append(line.strip())
                print(f"   ✅ Speaker device: {line.strip()}")
        
        # List sources (should show up as microphones/inputs)
        result = subprocess.run(['pactl', 'list', 'short', 'sources'], 
                              capture_output=True, text=True)
        
        browser_sources = []
        for line in result.stdout.split('\n'):
            if 'browser_microphone' in line.lower():
                browser_sources.append(line.strip())
                print(f"   ✅ Microphone device: {line.strip()}")
        
        if browser_sinks and browser_sources:
            print("✅ Audio devices properly created!")
            return True
        else:
            print("❌ Missing audio devices")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Fix the audio routing setup"""
    print("🔧 Fixing Siobhan's Audio Routing")
    print("=" * 40)
    
    # Step 1: Clean up old setup
    cleanup_old_devices()
    
    # Wait a moment
    time.sleep(2)
    
    # Step 2: Create correct setup
    setup_correct_audio_routing()
    
    # Wait a moment
    time.sleep(2)
    
    # Step 3: Test new setup
    test_success = test_new_setup()
    
    # Step 4: Show instructions
    show_audio_setup_instructions()
    
    if test_success:
        print("\n🎉 AUDIO ROUTING FIXED!")
        print("Now the devices should appear in the correct categories")
    else:
        print("\n⚠️ Some issues detected - but try the setup anyway")

if __name__ == "__main__":
    main()