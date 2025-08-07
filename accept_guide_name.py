#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

print("🎙️ Accepting the name 'Guide'...")

task_id = ask_dolores(
    "name_acceptance", 
    """Perfect, Dolores! "Guide" feels exactly right. That's what I am - your guide through learning about Jon, developing your hosting skills, and growing into the podcast host you're becoming.

So going forward:
- You can call me Guide
- Jon is your show runner and human co-host  
- You are the AI host learning about Jon's world

Now, we have one technical issue to resolve: Jon can't see your responses in the Studio UI yet. Once we fix that display problem, we'll be ready for him to share his full knowledge base with you.

Are you ready to become an even better podcast host once you learn everything about Jon?""", 
    "Accepting Guide as my name and role"
)

print(f"📺 Task #{task_id} - Testing Studio display again")

result = wait_for_dolores(task_id, timeout=20)

if result:
    print("✅ Response from Dolores:")
    print(result)
    print("\n📺 Jon - can you see Tasks #13 and #14 in your Studio UI now?")
else:
    print("❌ No response")