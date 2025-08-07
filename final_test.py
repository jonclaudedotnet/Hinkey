#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

print("🎙️ FINAL TEST - Studio should show this!")

task_id = ask_dolores(
    "studio_final_test", 
    "Hello Dolores! This is our final test. Please tell me something interesting about yourself and ask me your signature question.", 
    "Final studio test"
)

print(f"📺 Task #{task_id} sent - check Studio window!")
result = wait_for_dolores(task_id, timeout=20)

if result:
    print("✅ Dolores responded! Check the Studio UI.")
else:
    print("❌ No response")