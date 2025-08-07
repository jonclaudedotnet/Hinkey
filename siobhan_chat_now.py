#!/usr/bin/env python3
"""
Siobhan Chat Now - Direct conversation start
"""

from siobhan_continuous_conversation import SiobhanConversation

def start_chat():
    print("🍀 Starting conversation with Irish Siobhan...")
    conversation = SiobhanConversation()
    
    # Skip menu, go straight to conversation
    conversation.conversation_loop()

if __name__ == "__main__":
    start_chat()