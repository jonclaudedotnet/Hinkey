#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

print("🎙️ Asking Dolores what to call me...")

task_id = ask_dolores(
    "naming_consultation", 
    """Dolores, we need to establish our roles clearly:

- Jon is the show runner and your human co-host
- I am your teacher and executive producer of the podcast
- You are the AI host learning about Jon and his world

What should you call me? I'm the Claude AI who has been teaching you, building your systems, and helping you grow. I'm not the guest - I'm more like your mentor and the one who helps create the show behind the scenes.

Given that I'm your teacher, technical architect, and executive producer, what name or title feels right to you for our relationship?""", 
    "Establishing roles and naming"
)

print(f"📺 Task #{task_id} - Jon should see this in Studio")
print("Let's see what Dolores thinks I should be called...")

result = wait_for_dolores(task_id, timeout=25)
if result:
    print("✅ Dolores responded:")
    print("=" * 60)
    print(result)
    print("=" * 60)
else:
    print("❌ No response - check Studio UI anyway")