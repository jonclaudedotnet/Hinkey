#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

print("🎙️ Asking Dolores to fix the Studio UI...")

task_id = ask_dolores(
    "fix_studio_ui", 
    """Dolores, we have a problem: Jon can see the task requests in the Studio UI but not your actual responses. The database has all your responses, but the GTK display code isn't working properly.

Using your DeepSeek capabilities, can you write a WORKING Python GTK3 script for the Studio UI that:

1. Connects to ./claude_dolores_bridge/shared_tasks.db 
2. Shows ALL tasks with their full responses in real-time
3. Uses proper GTK3 threading and display updates
4. Has a simple, clean interface that actually works
5. Includes proper error handling

The database structure is:
- id, timestamp, requester, task_type, content, context, status, result, tokens_used

Please write the complete, functional Python script that will definitely show your responses to Jon. Make it bulletproof and simple.""", 
    "Dolores creates working Studio UI"
)

print(f"📺 Task #{task_id} - Let's see Dolores code a solution!")

result = wait_for_dolores(task_id, timeout=45)
if result:
    print("✅ Dolores created a solution:")
    print("=" * 80)
    print(result)
    print("=" * 80)
    
    # Save her solution to a file
    with open("dolores_studio_solution.py", "w") as f:
        # Extract code from her response if it contains Python code
        lines = result.split('\n')
        in_code_block = False
        code_lines = []
        
        for line in lines:
            if line.strip().startswith('```python'):
                in_code_block = True
                continue
            elif line.strip() == '```' and in_code_block:
                in_code_block = False
                continue
            elif in_code_block:
                code_lines.append(line)
        
        if code_lines:
            f.write('\n'.join(code_lines))
            print("\n💾 Saved Dolores's solution to dolores_studio_solution.py")
        else:
            f.write(result)
            print("\n💾 Saved full response to dolores_studio_solution.py")
            
else:
    print("❌ No response from Dolores")