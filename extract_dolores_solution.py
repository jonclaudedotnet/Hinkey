#!/usr/bin/env python3
import sqlite3
from pathlib import Path

db_path = Path("./claude_dolores_bridge/shared_tasks.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT result FROM tasks WHERE id = 15")
result = cursor.fetchone()

if result:
    solution = result[0]
    print("💡 DOLORES'S STUDIO UI SOLUTION:")
    print("=" * 80)
    print(solution)
    print("=" * 80)
    
    # Extract Python code
    lines = solution.split('\n')
    in_code = False
    code_lines = []
    
    for line in lines:
        if '```python' in line:
            in_code = True
            continue
        elif '```' in line and in_code:
            in_code = False
            break
        elif in_code:
            code_lines.append(line)
    
    if code_lines:
        code = '\n'.join(code_lines)
        with open('dolores_studio_working.py', 'w') as f:
            f.write(code)
        print(f"\n💾 Extracted {len(code_lines)} lines of Python code to dolores_studio_working.py")
    else:
        print("❌ No Python code block found")
else:
    print("❌ No solution found")

conn.close()