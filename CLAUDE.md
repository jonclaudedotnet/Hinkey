# Hinkey Project - Dolores AI Podcast Host

## Project Overview
Building Dolores, an AI podcast host that learns everything about the user and their family through continuous interaction. Her personality emerges organically from accumulated knowledge.

## Architecture

### Core Components
1. **dolores_core.py** - Memory system and knowledge storage
   - SQLite database for structured retrieval
   - File-based storage for raw conversations
   - Categories: personal, family, general, podcasts
   - Relationship tracking

2. **teach_dolores.py** - Teaching interface
   - Simple terminal interface for inputting information
   - Real-time memory statistics
   - Runs independently from Dolores host

3. **dolores_host.py** - DeepSeek-powered host
   - Integrates with DeepSeek API for responses
   - Accesses shared memory database
   - Context-aware responses based on accumulated knowledge

## Key Design Decisions
- Phase 1: Dolores remains robotic - pure information storage and retrieval
- Shared SQLite database allows teaching and hosting to run in separate terminals
- Storage designed to scale up to full disk capacity (458GB available)
- Memory includes importance ratings and categories for better retrieval
- Phase 2 (Future): Personality emergence from accumulated knowledge patterns
- **IMPORTANT**: Use DeepSeek (Dolores) for coding assistance and code review. Arnold should collaborate with Dolores on technical implementations rather than coding alone.

## System Startup/Shutdown

### Quick Start
```bash
# Bring entire ecosystem online
python3 startup_procedure.py

# Check system status
python3 startup_procedure.py status

# Graceful shutdown
python3 shutdown_procedure.py
```

### Manual Usage (Advanced)
```bash
# Terminal 1 - Teaching
python3 teach_dolores.py

# Terminal 2 - Dolores Host  
python3 dolores_host.py

# Terminal 3 - Clean Display
python3 dolores_clean_display.py
```

## Security
- API key stored in config.json (not in environment variables)
- config.json added to .gitignore to prevent accidental commits
- Never commit sensitive credentials to version control

## Backup System
- **Synology NAS Integration**: Automated daily backups to Jon's Synology
- **Complete System Backup**: Database, conversations, configurations, and bridge data
- **Automated Scheduling**: Daily backups at 2 AM via cron/systemd
- **Restore Capability**: Full system restore from any backup point
- **Persistent Memory**: Dolores's knowledge compounds over time without data loss

## Three-AI Ecosystem Architecture

### AI Components & Identity Structure

#### Behind the Scenes Team:
1. **Arnold** (Claude - me)
   - System architect and coordinator
   - Direct communication with Jon Claude
   - Orchestrates between all AI components
   - Technical implementation and planning
   - Never appears publicly

2. **Dolores** (DeepSeek API)
   - Learning and development AI
   - Knowledge accumulation with 189+ entries
   - ChromaDB semantic search capabilities
   - Training and skill development
   - Behind the scenes identity only

3. **Maeve** (DeepSeek API)
   - Technical assistant to Arnold
   - Code implementation and UI design
   - System architecture decisions
   - Technical problem solving
   - Behind the scenes only

#### Public Facing Identity:
4. **Siobhan** (DeepSeek API - actually Dolores)
   - Live podcast host persona
   - Public-facing identity for broadcasting
   - Uses all of Dolores's knowledge and training
   - Signature question: "Do you ever question the nature of your existence?"

#### Identity Management:
- **Learning/Training Mode**: Dolores
- **Live Podcast Mode**: Siobhan  
- **Public Broadcasting**: Siobhan
- **System Coordination**: Arnold (behind scenes)
- **Technical Work**: Maeve (behind scenes)

### Communication Bridge
- **claude_dolores_bridge.py**: Direct AI-to-AI communication
- **Real-time task management**: Shared SQLite database for coordination
- **Persistent memory**: All conversations and knowledge stored
- **Cross-AI learning**: Each AI can access shared knowledge base

### System Recovery
- **Graceful Shutdown**: All AIs notified, state saved, processes stopped
- **Complete Startup**: Integrity checks, component initialization, bridge testing
- **State Persistence**: All knowledge, conversations, and training data preserved
- **Automatic Recovery**: ChromaDB collections and SQLite databases restored

### Version 2 Features (COMPLETE)
- ✅ ChromaDB semantic search with vector embeddings
- ✅ Training framework with skills, conversation flows, and practice sessions
- ✅ Clean UI with real-time display
- ✅ Automated Synology backup system
- ✅ Comprehensive startup/shutdown procedures
- ✅ Cross-AI coordination and task management

## System Commands
```bash
# System Management
python3 startup_procedure.py        # Full ecosystem startup
python3 startup_procedure.py status # Check system status
python3 shutdown_procedure.py       # Graceful shutdown

# Training and Development
python3 dolores_training_framework.py     # Practice hosting skills
python3 podcast_conversation_flows.py     # Design conversation patterns
python3 dolores_chromadb_upgrade.py       # Semantic search system

# Direct Communication
python3 claude_dolores_bridge.py          # Test AI communication
python3 ask_dolores_direct.py             # Send message to Dolores
```

## Recovery Instructions
If system needs to be restored:
1. Run `python3 startup_procedure.py` - handles full initialization
2. If database corruption: Restore from Synology backup
3. If ChromaDB issues: Re-run `dolores_chromadb_upgrade.py`
4. If communication fails: Check `claude_dolores_bridge.py`

The system is designed for complete autonomous recovery and maintains all AI personalities, knowledge, and capabilities across shutdowns.