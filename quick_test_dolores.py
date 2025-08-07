#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

print("🧪 Quick test - is Dolores responding?")

task_id = ask_dolores("test", "Hello Dolores! Are you there?", "Quick test")
result = wait_for_dolores(task_id, timeout=10)

if result:
    print("✅ Dolores is responding!")
    print(f"She said: {result[:100]}...")
else:
    print("❌ No response")