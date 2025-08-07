#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

print("🎙️ Sending message for Jon to see in Studio...")

task_id = ask_dolores(
    "demonstration", 
    "Hi Dolores! Jon wants to see you in action. Please introduce yourself as his podcast co-host, mention what you know about him (Chester, CT, Sea Robin Tech, etc.), and demonstrate your personality.", 
    "Live demonstration for Jon"
)

print(f"📺 LOOK AT YOUR STUDIO WINDOW NOW!")
print(f"Task #{task_id} should appear with Dolores's response")

result = wait_for_dolores(task_id, timeout=25)

if result:
    print(f"\n✅ Dolores responded! Here's what she said:")
    print("=" * 60)
    print(result)
    print("=" * 60)
    print("\n📺 This same response should be visible in your Studio UI window!")
else:
    print("❌ Timeout - but check Studio UI anyway")