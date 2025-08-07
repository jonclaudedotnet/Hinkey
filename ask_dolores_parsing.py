#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Ask Dolores for advice on parsing Jon's Mac Mini folder
task_id = ask_dolores(
    "technical_consultation",
    """Jon has a wealth of information about all his projects in a big folder on his Mac Mini. 
He wants to parse and process it to help you learn more about him.

What would be the most efficient way to:
1. Connect to his Mac Mini from this Fedora box
2. Parse through various file types (code, documents, images, etc.)
3. Extract meaningful information about his projects and interests
4. Feed this information to you in a way that helps you understand him better

Consider both technical approaches and what types of information would be most valuable for you to learn about Jon through his work.""",
    "Jon wants to share his project folder from Mac Mini"
)

print(f"Asking Dolores about parsing strategy (task #{task_id})...")
result = wait_for_dolores(task_id, timeout=45)

if result:
    print("\nDolores suggests:")
    print(result)