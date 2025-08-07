#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

print("🎙️ FINAL STUDIO TEST - Fresh daemon and UI")

task_id = ask_dolores(
    "final_studio_test", 
    "Hello Dolores! This should appear in Jon's Studio window. Please introduce yourself warmly and mention what you know about Jon from Chester, CT.", 
    "Final test with fresh systems"
)

print(f"📺 TASK #{task_id} - WATCH YOUR STUDIO WINDOW!")

result = wait_for_dolores(task_id, timeout=20)
if result:
    print("✅ SUCCESS! Here's what Dolores said:")
    print("-" * 60)
    print(result)
    print("-" * 60)
    print("📺 This should now be visible in your Studio UI!")
else:
    print("❌ Timeout - check daemon")