#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Jon's message goes directly to Dolores
task_id = ask_dolores(
    "direct_conversation", 
    "Any speculations?", 
    "Direct message from Jon"
)

print(f"Message sent to Dolores - Task #{task_id}")
result = wait_for_dolores(task_id, timeout=20)

if result:
    print("Dolores responded:")
    print(result)
else:
    print("Dolores didn't respond")