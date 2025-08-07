#!/usr/bin/env python3
"""
Transcript Processor - Watches for new transcripts and feeds them to Dolores's memory
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
from dolores_core import DoloresMemory

class TranscriptProcessor:
    """Processes meeting transcripts for Dolores's knowledge base"""
    
    def __init__(self, watch_directory: str = "./meeting_transcripts"):
        self.watch_dir = Path(watch_directory)
        self.watch_dir.mkdir(exist_ok=True)
        self.processed_dir = self.watch_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        self.memory = DoloresMemory()
        self.processed_files = self._load_processed_list()
        
    def _load_processed_list(self) -> set:
        """Load list of already processed files"""
        manifest_file = self.processed_dir / "manifest.json"
        if manifest_file.exists():
            with open(manifest_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def _save_processed_list(self):
        """Save list of processed files"""
        manifest_file = self.processed_dir / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(list(self.processed_files), f)
    
    def process_transcript(self, filepath: Path):
        """Process a single transcript file"""
        print(f"Processing transcript: {filepath.name}")
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Parse transcript format (expecting timestamp: speaker: text)
            lines = content.strip().split('\n')
            current_speaker = None
            current_text = []
            
            for line in lines:
                # Simple parsing - customize based on actual transcript format
                if ': ' in line:
                    parts = line.split(': ', 2)
                    if len(parts) >= 2:
                        # Extract meaningful segments
                        text = parts[-1].strip()
                        
                        # Look for personal information
                        if any(word in text.lower() for word in ['i', 'my', 'me', 'our']):
                            self.memory.remember(
                                content=text,
                                category="personal",
                                source="podcast",
                                context=f"From transcript: {filepath.name}",
                                importance=7
                            )
                        
                        # Store general conversation
                        self.memory.remember(
                            content=text,
                            category="podcast_conversation",
                            source="podcast",
                            context=f"From transcript: {filepath.name}",
                            importance=5
                        )
            
            # Move to processed folder
            processed_path = self.processed_dir / filepath.name
            filepath.rename(processed_path)
            
            # Update processed list
            self.processed_files.add(filepath.name)
            self._save_processed_list()
            
            stats = self.memory.get_memory_stats()
            print(f"✓ Processed. Dolores now knows {stats['total_memories']} things")
            
        except Exception as e:
            print(f"Error processing {filepath.name}: {e}")
    
    def watch_for_transcripts(self):
        """Continuously watch for new transcript files"""
        print(f"Watching for transcripts in: {self.watch_dir}")
        print("Press Ctrl+C to stop")
        
        while True:
            try:
                # Check for new transcript files
                for filepath in self.watch_dir.glob("*.txt"):
                    if filepath.name not in self.processed_files:
                        # Wait a moment to ensure file is completely written
                        time.sleep(1)
                        self.process_transcript(filepath)
                
                # Check every 5 seconds
                time.sleep(5)
                
            except KeyboardInterrupt:
                print("\nStopping transcript processor")
                break
            except Exception as e:
                print(f"Error in watch loop: {e}")
                time.sleep(5)


def main():
    processor = TranscriptProcessor()
    processor.watch_for_transcripts()

if __name__ == "__main__":
    main()