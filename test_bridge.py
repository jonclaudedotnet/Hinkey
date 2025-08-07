#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Ask Dolores to research recent news
task_id = ask_dolores(
    "research", 
    "Search for recent tech news about Anthropic and DeepSeek, especially from Reddit /r/claudeai. Look for: 1. Recent Anthropic announcements 2. DeepSeek capabilities 3. Community discussions about AI integration patterns",
    "Confirming our integration approach"
)

print(f"Waiting for Dolores to research (task #{task_id})...")
result = wait_for_dolores(task_id, timeout=60)

if result:
    print("\nDolores found:")
    print(result)
else:
    print("Dolores is still working on it...")