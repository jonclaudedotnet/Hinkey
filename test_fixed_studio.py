#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

print("🎙️ Testing FIXED studio - you should see this appear!")

task_id = ask_dolores(
    "studio_test_fixed", 
    "Dolores, this is a test of the FIXED studio UI. Please give a warm greeting and show your personality!", 
    "Testing fixed UI"
)

print(f"📺 WATCH YOUR STUDIO WINDOW - Task #{task_id} should appear!")

result = wait_for_dolores(task_id, timeout=15)
if result:
    print("✅ Response received - check Studio window!")
    print(f"Preview: {result[:100]}...")
else:
    print("❌ Timeout")