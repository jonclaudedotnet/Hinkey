#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Jon's message to Dolores
task_id = ask_dolores(
    "direct_conversation", 
    "We will get there. remember everything I say goes to Dolores. Does she have a question for me?", 
    "Jon asking if Dolores has a question"
)

result = wait_for_dolores(task_id, timeout=20)
if result:
    print("Dolores responded (you should see this in her clean display):")
    print(result)
else:
    print("Dolores didn't respond")