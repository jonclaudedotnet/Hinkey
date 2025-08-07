#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

task_id = ask_dolores(
    "testonlinemode", 
    "Dolores, we're testing online mode. Please keep responses VERY short - just 1-2 sentences. Also, can you clear your display window and start fresh? This is test mode.", 
    "Testing online mode with short responses"
)

print(f"Testing online mode - Task #{task_id}")
result = wait_for_dolores(task_id, timeout=15)

if result:
    print("Dolores responded:")
    print(result)
else:
    print("No response")