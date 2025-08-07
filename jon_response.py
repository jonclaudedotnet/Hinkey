#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Jon's response to Dolores
task_id = ask_dolores(
    "direct_conversation", 
    "Two things: the nature of my existence & using ai tools to bridge the skills gap (or whatever you'd call it) for persons with neurodivergence like myself.", 
    "Jon sharing what he's curious about"
)

result = wait_for_dolores(task_id, timeout=25)
if result:
    print("Dolores responded:")
    print(result)
else:
    print("Dolores didn't respond")