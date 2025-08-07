#!/usr/bin/env python3
"""
Ingestion Process Frontend with MCP Integration
Real-time monitoring and control interface for SMB ingestion
"""

import asyncio
import aiohttp
import json
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime
from pathlib import Path
from connect_to_lyra import DocmackLyraClient

class IngestionFrontend:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dolores Ingestion Control Panel")
        self.root.geometry("1200x800")
        
        # MCP client for research capabilities
        self.lyra_client = DocmackLyraClient()
        self.mcp_connected = False
        
        # Ingestion status file
        self.status_file = Path("/home/jonclaude/agents/Hinkey/ingestion_status.json")
        
        # Setup UI
        self.setup_ui()
        
        # Start background tasks
        self.running = True
        self.start_background_tasks()
        
    def setup_ui(self):
        """Create the UI components"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🤖 Dolores Ingestion Control Panel", 
                               font=('Arial', 20, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Status Panel
        status_frame = ttk.LabelFrame(main_frame, text="📊 Current Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Progress bars
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, length=800, 
                                           variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, columnspan=2, pady=5)
        
        self.progress_label = ttk.Label(status_frame, text="Progress: 0.00%")
        self.progress_label.grid(row=0, column=2, padx=10)
        
        # Statistics Grid
        stats_frame = ttk.Frame(status_frame)
        stats_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        # Create stat labels
        self.stat_labels = {}
        stats = [
            ("Files Found", "files_found"),
            ("Files Cached", "files_cached"),
            ("Files Vectorized", "files_vectorized"),
            ("Speed (files/sec)", "speed"),
            ("Current Directory", "current_dir"),
            ("Elapsed Time", "elapsed")
        ]
        
        for i, (label, key) in enumerate(stats):
            row = i // 3
            col = (i % 3) * 2
            
            ttk.Label(stats_frame, text=f"{label}:").grid(row=row, column=col, 
                                                          sticky=tk.W, padx=5, pady=2)
            self.stat_labels[key] = ttk.Label(stats_frame, text="0", 
                                             font=('Arial', 10, 'bold'))
            self.stat_labels[key].grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=2)
        
        # Control Panel
        control_frame = ttk.LabelFrame(main_frame, text="🎮 Controls", padding="10")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Buttons
        self.pause_button = ttk.Button(control_frame, text="⏸️ Pause", 
                                      command=self.toggle_pause, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=0, padx=5)
        
        self.research_button = ttk.Button(control_frame, text="🔬 Research Current File", 
                                         command=self.research_current_file)
        self.research_button.grid(row=0, column=1, padx=5)
        
        self.refresh_button = ttk.Button(control_frame, text="🔄 Refresh", 
                                        command=self.refresh_status)
        self.refresh_button.grid(row=0, column=2, padx=5)
        
        # MCP Status
        self.mcp_status_label = ttk.Label(control_frame, text="MCP: Disconnected", 
                                         foreground="red")
        self.mcp_status_label.grid(row=0, column=3, padx=20)
        
        # Research Panel
        research_frame = ttk.LabelFrame(main_frame, text="🔬 MCP Research", padding="10")
        research_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), 
                           pady=5, padx=5)
        
        # Research input
        ttk.Label(research_frame, text="Query:").grid(row=0, column=0, sticky=tk.W)
        self.research_entry = ttk.Entry(research_frame, width=50)
        self.research_entry.grid(row=0, column=1, padx=5)
        
        research_go_button = ttk.Button(research_frame, text="Research", 
                                       command=self.do_research)
        research_go_button.grid(row=0, column=2, padx=5)
        
        # Research output
        self.research_output = scrolledtext.ScrolledText(research_frame, height=8, width=60)
        self.research_output.grid(row=1, column=0, columnspan=3, pady=5)
        
        # Activity Log
        log_frame = ttk.LabelFrame(main_frame, text="📜 Activity Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=120)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure log colors
        self.log_text.tag_config("info", foreground="blue")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("warning", foreground="orange")
        
    def log(self, message, level="info"):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", level)
        self.log_text.see(tk.END)
        
    def start_background_tasks(self):
        """Start background monitoring tasks"""
        # MCP connection thread
        threading.Thread(target=self.connect_mcp_async, daemon=True).start()
        
        # Status update thread
        threading.Thread(target=self.update_loop, daemon=True).start()
        
    def connect_mcp_async(self):
        """Connect to MCP in background"""
        asyncio.run(self.connect_mcp())
        
    async def connect_mcp(self):
        """Connect to MCP server"""
        self.log("Connecting to MCP server on MacMini...")
        
        try:
            connected = await self.lyra_client.test_connection()
            if connected:
                self.mcp_connected = True
                self.mcp_status_label.config(text="MCP: Connected ✅", foreground="green")
                self.log("Successfully connected to MCP server!", "success")
            else:
                self.log("Failed to connect to MCP server", "error")
        except Exception as e:
            self.log(f"MCP connection error: {e}", "error")
            
    def update_loop(self):
        """Background loop to update status"""
        while self.running:
            try:
                self.refresh_status()
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                self.log(f"Update error: {e}", "error")
                time.sleep(5)
                
    def refresh_status(self):
        """Read and display current ingestion status"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    status = json.load(f)
                
                # Update progress
                progress = status.get('processing_progress', 0)
                self.progress_var.set(progress)
                self.progress_label.config(text=f"Progress: {progress:.2f}%")
                
                # Update statistics
                self.stat_labels['files_found'].config(text=f"{status.get('files_found', 0):,}")
                self.stat_labels['files_cached'].config(text=f"{status.get('files_cached', 0):,}")
                self.stat_labels['files_vectorized'].config(text=f"{status.get('files_vectorized', 0):,}")
                self.stat_labels['speed'].config(text=f"{status.get('files_per_second', 0):.2f}")
                
                # Current directory (truncate if too long)
                current_dir = status.get('current_directory', 'Unknown')
                if len(current_dir) > 50:
                    current_dir = "..." + current_dir[-47:]
                self.stat_labels['current_dir'].config(text=current_dir)
                
                # Elapsed time
                elapsed = status.get('elapsed_time', 0)
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                self.stat_labels['elapsed'].config(text=f"{hours}h {minutes}m")
                
                # Log current file being processed
                current_file = status.get('current_file', '')
                if hasattr(self, '_last_file') and self._last_file != current_file:
                    self.log(f"Processing: {current_file}", "info")
                self._last_file = current_file
                
        except Exception as e:
            self.log(f"Failed to read status: {e}", "error")
            
    def toggle_pause(self):
        """Toggle pause state of ingestion"""
        # TODO: Implement pause functionality
        self.log("Pause functionality not yet implemented", "warning")
        
    def research_current_file(self):
        """Research the current file being processed"""
        if not self.mcp_connected:
            self.log("MCP not connected", "error")
            return
            
        try:
            with open(self.status_file, 'r') as f:
                status = json.load(f)
            
            current_file = status.get('current_file', '')
            if current_file:
                query = f"What type of file is {Path(current_file).name} and what might it contain?"
                self.research_entry.delete(0, tk.END)
                self.research_entry.insert(0, query)
                self.do_research()
            else:
                self.log("No current file to research", "warning")
                
        except Exception as e:
            self.log(f"Research error: {e}", "error")
            
    def do_research(self):
        """Perform research query via MCP"""
        query = self.research_entry.get()
        if not query:
            return
            
        if not self.mcp_connected:
            self.log("MCP not connected", "error")
            return
            
        self.log(f"Researching: {query}")
        self.research_output.delete(1.0, tk.END)
        self.research_output.insert(tk.END, "Querying MCP server...")
        
        # Run async research in thread
        threading.Thread(target=self.research_async, args=(query,), daemon=True).start()
        
    def research_async(self, query):
        """Async wrapper for research"""
        asyncio.run(self.perform_research(query))
        
    async def perform_research(self, query):
        """Perform the actual research"""
        try:
            result = await self.lyra_client.query_lyra_research(query)
            
            # Update UI in main thread
            self.root.after(0, self.update_research_output, result)
            self.root.after(0, self.log, f"Research completed: {len(result)} chars", "success")
            
        except Exception as e:
            error_msg = f"Research failed: {e}"
            self.root.after(0, self.update_research_output, error_msg)
            self.root.after(0, self.log, error_msg, "error")
            
    def update_research_output(self, text):
        """Update research output in UI thread"""
        self.research_output.delete(1.0, tk.END)
        self.research_output.insert(tk.END, text)
        
    def run(self):
        """Start the frontend"""
        self.log("Ingestion Frontend started", "success")
        self.log(f"Monitoring: {self.status_file}")
        self.root.mainloop()
        self.running = False

def main():
    """Launch the ingestion frontend"""
    app = IngestionFrontend()
    app.run()

if __name__ == "__main__":
    main()