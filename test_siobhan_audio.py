#!/usr/bin/env python3
"""
Test Siobhan's Audio Setup - Verify bidirectional communication
"""

import sounddevice as sd
import subprocess
import time

def test_audio_devices():
    """Test that all audio devices are properly configured"""
    print("🎧 Testing Siobhan's Audio Setup")
    print("=" * 40)
    
    # List all audio devices
    print("📋 Available Audio Devices:")
    devices = sd.query_devices()
    
    siobhan_devices = {}
    
    for i, device in enumerate(devices):
        if isinstance(device, dict):
            name = device.get('name', '')
            print(f"   {i}: {name}")
            
            # Track Siobhan-related devices
            name_lower = name.lower()
            if 'siobhan' in name_lower or 'meeting_audio' in name_lower:
                if device.get('max_output_channels', 0) > 0:
                    siobhan_devices['output'] = (i, name)
                if device.get('max_input_channels', 0) > 0:
                    siobhan_devices['input'] = (i, name)
    
    print(f"\n🎯 Siobhan Audio Devices Found:")
    for device_type, (device_id, device_name) in siobhan_devices.items():
        print(f"   {device_type.title()}: {device_id} - {device_name}")
    
    return siobhan_devices

def test_pulseaudio_setup():
    """Test PulseAudio virtual devices"""
    print("\n🔊 Testing PulseAudio Virtual Devices:")
    
    try:
        # List sinks
        result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                              capture_output=True, text=True)
        
        siobhan_sinks = []
        for line in result.stdout.split('\n'):
            if 'siobhan' in line.lower() or 'meeting' in line.lower():
                siobhan_sinks.append(line.strip())
                print(f"   ✅ Sink: {line.strip()}")
        
        if not siobhan_sinks:
            print("   ❌ No Siobhan sinks found")
            return False
        
        # List sources
        result = subprocess.run(['pactl', 'list', 'short', 'sources'], 
                              capture_output=True, text=True)
        
        siobhan_sources = []
        for line in result.stdout.split('\n'):
            if 'siobhan' in line.lower() or 'meeting' in line.lower():
                siobhan_sources.append(line.strip())
                print(f"   ✅ Source: {line.strip()}")
        
        return len(siobhan_sinks) > 0 and len(siobhan_sources) > 0
        
    except Exception as e:
        print(f"   ❌ PulseAudio test error: {e}")
        return False

def test_voice_output():
    """Test Siobhan's voice output"""
    print("\n🗣️ Testing Voice Output:")
    
    try:
        # Try to play a test sound to siobhan_voice device
        test_cmd = [
            'pactl', 'play-sample', '/usr/share/sounds/alsa/Front_Left.wav',
            '--device=siobhan_voice'
        ]
        
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Voice output device working")
            return True
        else:
            print(f"   ⚠️ Voice test warning: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Voice output test error: {e}")
        return False

def test_audio_routing():
    """Test complete audio routing"""
    print("\n🔗 Testing Audio Routing:")
    
    try:
        # Check loopback modules
        result = subprocess.run(['pactl', 'list', 'short', 'modules'], 
                              capture_output=True, text=True)
        
        loopback_count = 0
        for line in result.stdout.split('\n'):
            if 'module-loopback' in line and ('siobhan' in line.lower() or 'meeting' in line.lower()):
                loopback_count += 1
                print(f"   ✅ Loopback: {line.strip()}")
        
        if loopback_count > 0:
            print(f"   ✅ Found {loopback_count} audio routing connections")
            return True
        else:
            print("   ❌ No audio routing found")
            return False
            
    except Exception as e:
        print(f"   ❌ Routing test error: {e}")
        return False

def main():
    """Run complete audio test suite"""
    print("🧪 Siobhan Audio System Test")
    print("=" * 40)
    
    # Test 1: Audio devices
    devices = test_audio_devices()
    device_test = len(devices) > 0
    
    # Test 2: PulseAudio setup
    pulse_test = test_pulseaudio_setup()
    
    # Test 3: Voice output
    voice_test = test_voice_output()
    
    # Test 4: Audio routing
    routing_test = test_audio_routing()
    
    # Summary
    print("\n📊 Test Results:")
    print("=" * 40)
    print(f"   Audio Devices: {'✅ PASS' if device_test else '❌ FAIL'}")
    print(f"   PulseAudio Setup: {'✅ PASS' if pulse_test else '❌ FAIL'}")
    print(f"   Voice Output: {'✅ PASS' if voice_test else '❌ FAIL'}")
    print(f"   Audio Routing: {'✅ PASS' if routing_test else '❌ FAIL'}")
    
    all_tests_pass = all([device_test, pulse_test, voice_test, routing_test])
    
    if all_tests_pass:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Siobhan can hear and speak in meetings")
        print("\n📝 Next Steps:")
        print("   1. Start the continuous meeting system")
        print("   2. Set browser microphone to 'Siobhan_Browser_Microphone'")
        print("   3. Set browser speakers to 'Meeting_Audio_For_Siobhan'")
        print("   4. Say 'Siobhan' in your meeting to test")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("🔧 Run: python3 start_continuous_meeting_system.py")
        print("   This will recreate the audio devices")
    
    print("=" * 40)

if __name__ == "__main__":
    main()