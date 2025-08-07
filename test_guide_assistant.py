#!/usr/bin/env python3
from guide_assistant import GuideAssistant

# Test my assistant connection
assistant = GuideAssistant()
response = assistant.ask("Quick test - can you confirm you're connected and working? Just say hello.")
print("My assistant responds:")
print(response)