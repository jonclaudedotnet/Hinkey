#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Ask Dolores to help name me
task_id = ask_dolores(
    "naming_collaboration", 
    "Between the two of you, please come up with a name for you.. 'claudecoderunningonfedorabox' gotta be better than that.", 
    "Jon asking us to come up with a better name for Guide"
)

result = wait_for_dolores(task_id, timeout=25)
if result:
    print("Dolores's suggestion for my name:")
    print(result)
else:
    print("Dolores didn't respond")