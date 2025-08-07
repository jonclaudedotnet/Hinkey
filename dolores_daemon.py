#!/usr/bin/env python3
"""
Dolores Daemon - Runs Dolores in background to process Claude's requests
"""

import time
import signal
import sys
from dolores_assistant import DoloresAssistant, process_claude_tasks

class DoloresDaemon:
    def __init__(self):
        self.running = True
        self.assistant = DoloresAssistant()
        
        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.running = False
    
    def run(self):
        print("Dolores daemon started - processing Claude's requests")
        print("Press Ctrl+C to stop")
        
        while self.running:
            try:
                process_claude_tasks(self.assistant)
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                print(f"Error processing tasks: {e}")
                time.sleep(5)
        
        print("Dolores daemon stopped")

if __name__ == "__main__":
    daemon = DoloresDaemon()
    daemon.run()