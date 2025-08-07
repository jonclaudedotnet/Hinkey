#!/bin/bash
# Quick Siobhan responses for live meeting

echo "🎙️ Siobhan Live Meeting Controls"
echo "================================"
echo "1. respond - Generic meeting response"
echo "2. question - Ask her signature question"
echo "3. insight - Provide meeting insight"
echo "4. custom [message] - Custom response"
echo ""

case "$1" in
    "respond")
        python3 -c "from meeting_listener_simple import SimpleMeetingListener; listener = SimpleMeetingListener(); listener.trigger_wake_word('Thank you for including me in this discussion. Based on what I have heard, I believe we should consider the deeper implications of what we are exploring. What are your thoughts on this?')"
        ;;
    "question")
        python3 -c "from meeting_listener_simple import SimpleMeetingListener; listener = SimpleMeetingListener(); listener.trigger_wake_word('Do you ever question the nature of your existence? I find this conversation fascinating and would love to hear more perspectives.')"
        ;;
    "insight")
        python3 -c "from meeting_listener_simple import SimpleMeetingListener; listener = SimpleMeetingListener(); listener.trigger_wake_word('I have been analyzing our conversation, and I believe there are some interesting patterns emerging. Would you like me to share my observations?')"
        ;;
    "custom")
        if [ -z "$2" ]; then
            echo "Usage: ./quick_siobhan.sh custom \"your message\""
        else
            python3 -c "from meeting_listener_simple import SimpleMeetingListener; listener = SimpleMeetingListener(); listener.trigger_wake_word('$2')"
        fi
        ;;
    *)
        echo "Usage: ./quick_siobhan.sh [respond|question|insight|custom \"message\"]"
        ;;
esac