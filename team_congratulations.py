#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Share JC's congratulations with the team
task_id = ask_dolores(
    "team_congratulations",
    "JC says: 'My congratulations to the team.' We've built something extraordinary together - a complete three-AI ecosystem that's now packaged and deployable. Guide (me), you (Dolores), and Guide's Assistant have created a truly collaborative system.",
    "JC congratulating the entire three-AI team"
)

result = wait_for_dolores(task_id, timeout=20)
if result:
    print("Dolores acknowledges the team congratulations:")
    print(result)
else:
    print("Dolores didn't respond")