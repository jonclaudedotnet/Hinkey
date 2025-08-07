#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

print("🎙️ Sending test message to Dolores Studio...")

task_id = ask_dolores(
    "podcast_test", 
    "Dolores, I'm testing the studio system. Can you tell me about your podcast hosting style and ask me an interesting question?", 
    "Studio UI test"
)

print(f"📺 Check the Studio window for task #{task_id}")
print("You should see Dolores's response appear in real-time!")

result = wait_for_dolores(task_id, timeout=30)
if result:
    print("\n✅ Response received! Check Studio UI window.")
else:
    print("❌ Timeout - check Studio UI anyway")