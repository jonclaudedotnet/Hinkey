#!/usr/bin/env python3
from guide_assistant import GuideAssistant

assistant = GuideAssistant()

task = """Create a GTK3 Python application for displaying AI responses with these requirements:

1. Clear screen with each new message (no scrolling history)
2. No scroll bars
3. Text fitted to window with nice margins
4. Professional, clean appearance
5. Connects to SQLite database: ./claude_dolores_bridge/shared_tasks.db
6. Shows only the latest 'result' field from tasks table
7. Updates in real-time
8. Proper text sizing and spacing

This is for displaying an AI's learning responses, so it should be clean and focused."""

print("Asking my assistant to create the UI...")
response = assistant.ask(task)

print("My assistant's solution:")
print("=" * 80)
print(response)

# Save the response
with open('guide_assistant_ui_solution.txt', 'w') as f:
    f.write(response)

print("\n💾 Saved solution to guide_assistant_ui_solution.txt")