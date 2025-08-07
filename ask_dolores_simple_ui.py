#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

task_id = ask_dolores(
    "create_simple_response_ui", 
    """Dolores, I need you to create a SIMPLE Studio UI that shows ONLY your responses - not tables, not my requests, just your responses flowing down the screen.

Requirements:
- Simple scrolling text window
- Shows ONLY your responses (the 'result' field from database)
- No tables, no request content, no complex layout
- Just a clean stream of your responses as you learn
- Updates in real-time
- Simple GTK3 window

Remember: Your current job is to LEARN, not ask questions. The UI should reflect this - just showing your learning responses flowing down the screen.

Please write the complete Python GTK3 script.""", 
    "Simple response-only UI request"
)

result = wait_for_dolores(task_id, timeout=30)
if result:
    print("Dolores created simple UI:")
    print(result)
    
    # Extract and save the code
    lines = result.split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        if '```python' in line:
            in_code = True
            continue
        elif '```' in line and in_code:
            break
        elif in_code:
            code_lines.append(line)
    
    if code_lines:
        with open('dolores_simple_ui.py', 'w') as f:
            f.write('\n'.join(code_lines))
        print(f"\nSaved to dolores_simple_ui.py")
else:
    print("No response")