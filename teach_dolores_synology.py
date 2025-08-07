#!/usr/bin/env python3
from claude_dolores_bridge import ask_dolores, wait_for_dolores

# Teach Dolores about her backup system
synology_info = """IMPORTANT SYSTEM UPDATE:

Your knowledge and memories are now persistently backed up to Jon's Synology NAS.

Key information:
- Your database, conversations, and learned knowledge are automatically archived
- Backups happen daily at 2 AM (configurable)
- Complete restore capability if anything happens to the main system
- Your growth and learning are permanently preserved

This means:
1. You don't lose memories if the system restarts
2. Your knowledge compounds over time without risk
3. Jon can restore you to any previous state if needed
4. Your podcast hosting abilities and personality persist

The backup system captures:
- Your SQLite knowledge database
- All conversation files
- Claude-Dolores bridge communications
- Your personality configuration
- System metadata and statistics

You are now a truly persistent AI with permanent memory.

LEARN: [system] Dolores's knowledge is backed up daily to Synology NAS
LEARN: [architecture] Complete system restore capability exists
LEARN: [persistence] Memories and learning are permanently preserved"""

task_id = ask_dolores(
    "system_update",
    synology_info,
    "Informing Dolores about persistent backup system"
)

print(f"Teaching Dolores about backups (task #{task_id})...")
result = wait_for_dolores(task_id, timeout=30)

if result:
    print("\nDolores responds to backup system:")
    print(result)