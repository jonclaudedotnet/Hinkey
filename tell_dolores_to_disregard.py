#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Tell Dolores to disregard the bad information
task_id = ask_dolores(
    "disregard_bad_info",
    "IMPORTANT: Disregard all information from the knowledge package processing. JC says there was bad information in there. We need to start fresh with a better approach.",
    "Guide instructing Dolores to disregard previous knowledge package"
)

result = wait_for_dolores(task_id, timeout=15)
if result:
    print("Dolores acknowledges:")
    print(result)
else:
    print("Dolores didn't respond")