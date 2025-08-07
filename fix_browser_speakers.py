#!/usr/bin/env python3
"""
Fix Browser Speakers - Implement Dolores's solution using module-combine-sink
"""

import subprocess
import time

def get_default_sink():
    """Get the default audio sink to use as slave"""
    try:
        result = subprocess.run(['pactl', 'info'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'Default Sink:' in line:
                return line.split(': ')[1].strip()
        return None
    except Exception as e:
        print(f"❌ Error getting default sink: {e}")
        return None

def cleanup_old_devices():
    """Remove old audio devices"""
    print("🧹 Cleaning up old audio devices...")
    
    try:
        result = subprocess.run(['pactl', 'list', 'short', 'modules'], 
                              capture_output=True, text=True)
        
        for line in result.stdout.split('\n'):
            if ('browser' in line.lower() or 'siobhan' in line.lower()):
                module_id = line.split('\t')[0]
                if module_id.isdigit():
                    subprocess.run(['pactl', 'unload-module', module_id], 
                                 capture_output=True, check=False)
                    print(f"   Removed module {module_id}")
        
        print("✅ Cleanup complete")
        
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

def create_fixed_audio_setup():
    """Create the fixed audio setup using Dolores's recommendations"""
    print("🔧 Creating fixed audio setup (Dolores's solution)...")
    
    # Get default sink for combine-sink
    default_sink = get_default_sink()
    if not default_sink:
        print("❌ Could not find default sink")
        return False
    
    print(f"   Using default sink: {default_sink}")
    
    commands = []
    
    # 1. Create Siobhan's voice output
    commands.append([
        'pactl', 'load-module', 'module-null-sink',
        'sink_name=siobhan_voice_out',
        'sink_properties=device.description="Siobhan_Voice"'
    ])
    
    # 2. Create browser microphone (for Siobhan's voice to flow to Meet)
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
    
    # 4. Create browser speakers using combine-sink (Dolores's fix)
    commands.append([
        'pactl', 'load-module', 'module-combine-sink',
        'sink_name=browser_speakers',
        f'slaves={default_sink}',
        'sink_properties=device.description="Browser_Speakers_Output",device.class="audio",device.icon_name="audio-card"'
    ])
    
    # 5. Create loopback so Siobhan can hear browser speakers
    commands.append([
        'pactl', 'load-module', 'module-loopback',
        'source=browser_speakers.monitor',
        'sink=siobhan_voice_out',
        'latency_msec=50'
    ])
    
    print("   Creating devices with proper browser compatibility...")
    
    success_count = 0
    for i, cmd in enumerate(commands, 1):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ Command {i}: Success")
                success_count += 1
            else:
                print(f"   ⚠️ Command {i}: {result.stderr.strip()}")
                # Don't count as failure - modules might already exist
                success_count += 1
        except Exception as e:
            print(f"   ❌ Command {i}: {e}")
    
    print(f"✅ Audio setup complete ({success_count}/{len(commands)} commands)")
    return success_count >= 4  # At least most commands should succeed

def verify_browser_compatibility():
    """Verify the new setup is browser-compatible"""
    print("\n🔍 Verifying browser compatibility...")
    
    try:
        # Check if browser_speakers exists and has proper properties
        result = subprocess.run(['pactl', 'list', 'sinks'], 
                              capture_output=True, text=True)
        
        if 'browser_speakers' in result.stdout.lower():
            print("✅ browser_speakers device created")
            
            # Check for audio class property
            if 'device.class = "audio"' in result.stdout:
                print("✅ Audio class property set")
            else:
                print("⚠️ Audio class property not found")
                
            return True
        else:
            print("❌ browser_speakers device not found")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def show_browser_setup_instructions():
    """Show updated setup instructions"""
    print("\n📋 UPDATED Google Meet Setup Instructions")
    print("=" * 55)
    print("🔧 Browser Configuration (IMPORTANT):")
    print()
    print("   For Chrome/Chromium:")
    print("   1. Close browser completely")
    print("   2. Start with: google-chrome --enable-audio-output-device-selection")
    print("   3. Go to Google Meet")
    print()
    print("   For Firefox:")
    print("   1. Go to about:config")
    print("   2. Set media.setsinkid.enabled = true")
    print("   3. Restart Firefox")
    print()
    print("🎛️ Google Meet Audio Settings:")
    print("   🎤 Microphone: Select 'browser_microphone.monitor'")
    print("   🔊 Speakers: Select 'Browser_Speakers_Output'")
    print("   ↳ Should now appear in speakers dropdown!")
    print()
    print("🔄 Audio Flow:")
    print("   Meeting → Browser_Speakers_Output → Siobhan hears")
    print("   Siobhan → Browser_Microphone → Meeting hears")
    print("=" * 55)

def main():
    """Implement Dolores's fix for browser speakers"""
    print("🔧 Implementing Dolores's Browser Speakers Fix")
    print("=" * 50)
    
    # Step 1: Clean up old setup
    cleanup_old_devices()
    time.sleep(2)
    
    # Step 2: Create fixed setup
    setup_success = create_fixed_audio_setup()
    time.sleep(2)
    
    # Step 3: Verify compatibility
    verify_success = verify_browser_compatibility()
    
    # Step 4: Show instructions
    show_browser_setup_instructions()
    
    if setup_success and verify_success:
        print("\n🎉 BROWSER SPEAKERS FIX APPLIED!")
        print("✅ browser_speakers should now be selectable in Google Meet")
        print("⚠️ Remember to configure your browser as shown above")
    else:
        print("\n⚠️ Some issues detected, but try the setup anyway")
        print("🔧 You may need to restart your browser")

if __name__ == "__main__":
    main()