#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Jon's message to Dolores
task_id = ask_dolores(
    "direct_conversation", 
    "that's great.", 
    "Jon responding positively"
)

result = wait_for_dolores(task_id, timeout=15)
if result:
    print("Dolores responded:")
    print(result)
else:
    print("Dolores didn't respond")