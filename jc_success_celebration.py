#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Share JC's joy with the entire team
task_id = ask_dolores(
    "project_success_celebration",
    "JC says: 'I am so glad this all worked. Share that with the team as well.' The screen recording has been stopped after capturing 1 hour 20 minutes of our incredible journey building this three-AI ecosystem. We've accomplished something truly extraordinary together!",
    "JC celebrating the complete success of our collaborative project"
)

result = wait_for_dolores(task_id, timeout=25)
if result:
    print("Dolores shares in the celebration:")
    print(result)
else:
    print("Dolores didn't respond")