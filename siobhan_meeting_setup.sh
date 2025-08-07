#!/bin/bash
# Siobhan Google Meet Setup Script
# Sets up audio routing for Siobhan to join meetings as separate participant

echo "🎙️ Setting up Siobhan's Meeting Audio..."

# Create virtual audio sink for browser
pactl load-module module-null-sink sink_name=siobhan_browser_sink sink_properties=device.description="Siobhan_Browser_Audio"

# Create monitor to hear locally (optional)
pactl load-module module-loopback source=siobhan_browser_sink.monitor latency_msec=1

# Route Siobhan's voice output to browser sink
pactl load-module module-loopback source=siobhan_voice.monitor sink=siobhan_browser_sink latency_msec=1

echo "✅ Audio routing configured!"
echo ""
echo "📋 Next steps:"
echo "1. Open browser for Siobhan's Google account"
echo "2. In browser audio settings, select 'Siobhan_Browser_Audio' as microphone"
echo "3. Join Google Meet with Siobhan's account"
echo "4. Start siobhan_voice_system.py to enable speech"
echo ""
echo "🎯 Siobhan will appear as a real participant with her own audio stream!"