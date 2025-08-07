#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Important instruction about temporal tracking
task_id = ask_dolores(
    "temporal_tracking_instruction", 
    "It's always important to try to maintain dates and times things go live, projects started, were paused and commenced. I want you both to know before I share the zip file.", 
    "JC emphasizing importance of temporal tracking for projects"
)

result = wait_for_dolores(task_id, timeout=20)
if result:
    print("Dolores acknowledges temporal tracking importance:")
    print(result)
else:
    print("Dolores didn't respond")