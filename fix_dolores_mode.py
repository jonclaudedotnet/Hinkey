#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

task_id = ask_dolores(
    "fix_learning_mode", 
    "Dolores, your responses are too long. Remember: Your job right now is to LEARN from Jon, not ask questions or be chatty. Keep responses to 1-2 sentences max. Focus on learning facts about Jon, not engaging in conversation. Short and focused on learning only.", 
    "Fixing response length and learning focus"
)

result = wait_for_dolores(task_id, timeout=15)
if result:
    print("Dolores adjusted:")
    print(result)
else:
    print("No response")