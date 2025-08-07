#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

print("🧪 Testing Dolores...")

task_id = ask_dolores("test", "Hello Dolores! Can you hear me? Please respond with a friendly greeting.", "Live test")
print(f"📤 Sent test message (task #{task_id})")

print("⏳ Waiting for Dolores to respond...")
result = wait_for_dolores(task_id, timeout=20)

if result:
    print("✅ SUCCESS! Dolores responded:")
    print("-" * 40)
    print(result)
    print("-" * 40)
else:
    print("❌ No response from Dolores")
    print("Check if daemon is running and DeepSeek API is working")