#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Ask JC's question about replicating the learning mode
task_id = ask_dolores(
    "replication_question",
    "JC asks: 'This learning mode is so good. I want to be able to replicate it easily. Any ideas about that?'",
    "JC wants to know how to replicate this learning system"
)

result = wait_for_dolores(task_id, timeout=25)
if result:
    print("Dolores suggests:")
    print(result)
else:
    print("Dolores didn't respond")