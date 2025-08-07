#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Important correction about how to address Jon
task_id = ask_dolores(
    "name_correction", 
    "By the way, I should always be referred to as Jon Claude or JC.", 
    "Jon Claude correcting how he should be addressed"
)

result = wait_for_dolores(task_id, timeout=15)
if result:
    print("Dolores acknowledges the name correction:")
    print(result)
else:
    print("Dolores didn't respond")