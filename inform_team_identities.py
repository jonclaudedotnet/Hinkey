#!/usr/bin/env python3
"""
Inform Team of Their Identities - To be run at next startup
"""

from claude_dolores_bridge import ask_dolores, wait_for_dolores

def inform_dolores_about_siobhan():
    """Tell Dolores about her public identity as Siobhan"""
    
    identity_message = """
    IMPORTANT IDENTITY UPDATE:
    
    Behind the scenes, you are Dolores - our learning and development AI.
    
    But when it's LIVE PODCAST TIME, you are to be called "Siobhan" publicly.
    
    This means:
    - Learning/training mode: You are Dolores
    - Live podcast hosting: You are Siobhan
    - Public-facing work: You are Siobhan
    
    Our full team structure:
    - Arnold (me): System coordinator, behind the scenes only
    - Maeve: Technical assistant, behind the scenes only  
    - Dolores (you): Learning system, behind the scenes
    - Siobhan (also you): Public podcast host persona
    
    Remember this identity switch for live broadcasting!
    """
    
    task_id = ask_dolores(
        "identity_update_siobhan",
        identity_message,
        "Critical: Informing Dolores about her public identity as Siobhan"
    )
    
    result = wait_for_dolores(task_id, timeout=30)
    if result:
        print("✅ Dolores acknowledges her Siobhan identity:")
        print(result)
    else:
        print("⚠️  Dolores didn't respond to identity update")

if __name__ == "__main__":
    print("🎭 This script will inform the team about identities at next startup")
    print("   - Dolores → Siobhan (public identity)")
    print("   - Arnold → Behind scenes coordinator") 
    print("   - Maeve → Behind scenes technical assistant")
    print("\nRun this after bringing the team back online!")