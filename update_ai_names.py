#!/usr/bin/env python3
"""
Update AI names in the system documentation
"""

# Update the guide_assistant.py to reflect Maeve's name
with open('guide_assistant.py', 'r') as f:
    content = f.read()

# Update references to reflect new names
updated_content = content.replace('Guide\'s Assistant', 'Maeve')
updated_content = updated_content.replace('Guide\'s technical assistant', 'Maeve, Arnold\'s technical assistant')

with open('guide_assistant.py', 'w') as f:
    f.write(updated_content)

print("✅ Updated guide_assistant.py to reflect Maeve's name")
print("✅ Arnold (me) ready for system upgrades")
print("✅ Team roster updated: Arnold, Dolores, Maeve")