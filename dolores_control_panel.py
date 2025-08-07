#!/usr/bin/env python3
"""
Dolores Control Panel - Comprehensive local engine with GUI dashboard
Run this application to control the entire Dolores system from your desktop
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import time
import queue
import psutil
import sqlite3
from pathlib import Path
from datetime import datetime
from dolores_core import DoloresMemory, DoloresHost
import urllib.request
import urllib.error

class DoloresControlPanel:
    """Unified Dolores Control Panel - Desktop Application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dolores Control Panel - AI Podcast Host")
        self.root.geometry("1200x800")
        
        # System state
        self.system_running = False
        self.memory = None
        self.host = None
        self.api_key = None
        self.message_queue = queue.Queue()
        
        # Load configuration
        self.load_config()
        
        # Initialize UI
        self.setup_ui()
        
        # Start monitoring thread
        self.start_monitoring()
        
    def load_config(self):
        """Load API configuration"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.api_key = config.get('deepseek_api_key')
        except FileNotFoundError:
            messagebox.showerror("Config Error", "config.json not found")
        except json.JSONDecodeError:
            messagebox.showerror("Config Error", "Invalid config.json format")
    
    def setup_ui(self):
        """Create the control panel interface"""
        
        # Main toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        self.start_btn = ttk.Button(toolbar, text="▶️ Start System", command=self.start_system)
        self.start_btn.pack(side='left', padx=2)
        
        self.stop_btn = ttk.Button(toolbar, text="⏹️ Stop System", command=self.stop_system, state='disabled')
        self.stop_btn.pack(side='left', padx=2)
        
        self.restart_btn = ttk.Button(toolbar, text="🔄 Restart", command=self.restart_system, state='disabled')
        self.restart_btn.pack(side='left', padx=2)
        
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=10)
        
        ttk.Button(toolbar, text="⚙️ Settings", command=self.show_settings).pack(side='left', padx=2)
        ttk.Button(toolbar, text="📊 Export Data", command=self.export_data).pack(side='left', padx=2)
        
        # Status bar
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill='x', padx=5, pady=2)
        
        self.status_label = ttk.Label(status_frame, text="● Offline", foreground='red')
        self.status_label.pack(side='left')
        
        self.memory_label = ttk.Label(status_frame, text="Memories: 0")
        self.memory_label.pack(side='left', padx=20)
        
        self.cpu_label = ttk.Label(status_frame, text="CPU: 0%")
        self.cpu_label.pack(side='left', padx=10)
        
        self.api_label = ttk.Label(status_frame, text="API: ✗ Disconnected", foreground='red')
        self.api_label.pack(side='left', padx=10)
        
        # Main content area
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left panel - Conversation
        left_frame = ttk.LabelFrame(main_frame, text="💬 Conversation with Dolores")
        left_frame.pack(side='left', fill='both', expand=True, padx=2)
        
        self.conversation_text = scrolledtext.ScrolledText(left_frame, height=20, state='disabled')
        self.conversation_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        input_frame = ttk.Frame(left_frame)
        input_frame.pack(fill='x', padx=5, pady=5)
        
        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.pack(side='left', fill='x', expand=True, padx=2)
        self.input_entry.bind('<Return>', self.send_message)
        
        self.send_btn = ttk.Button(input_frame, text="Send", command=self.send_message, state='disabled')
        self.send_btn.pack(side='right', padx=2)
        
        # Right panel - Knowledge & Controls  
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='y', padx=2)
        
        # Knowledge base stats
        knowledge_frame = ttk.LabelFrame(right_frame, text="🧠 Knowledge Base")
        knowledge_frame.pack(fill='x', pady=2)
        
        self.knowledge_tree = ttk.Treeview(knowledge_frame, height=8)
        self.knowledge_tree.pack(fill='x', padx=5, pady=5)
        
        # Voice controls
        voice_frame = ttk.LabelFrame(right_frame, text="🎤 Voice System")
        voice_frame.pack(fill='x', pady=2)
        
        self.voice_btn = ttk.Button(voice_frame, text="🎤 Start Listening", state='disabled')
        self.voice_btn.pack(fill='x', padx=5, pady=2)
        
        # Recording controls
        record_frame = ttk.LabelFrame(right_frame, text="⏺️ Recording")  
        record_frame.pack(fill='x', pady=2)
        
        self.record_btn = ttk.Button(record_frame, text="⏺️ Start Recording", state='disabled')
        self.record_btn.pack(fill='x', padx=5, pady=2)
        
        # System logs
        log_frame = ttk.LabelFrame(right_frame, text="📋 System Log")
        log_frame.pack(fill='both', expand=True, pady=2)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state='disabled')
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def log_message(self, message):
        """Add message to system log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def start_system(self):
        """Start the Dolores system"""
        if not self.api_key:
            messagebox.showerror("Error", "No API key configured")
            return
            
        def start_thread():
            try:
                self.log_message("🚀 Starting Dolores system...")
                
                # Initialize memory system
                self.memory = DoloresMemory()
                self.host = DoloresHost(self.memory)
                
                # Test API connection
                self.test_api_connection()
                
                self.system_running = True
                
                # Update UI
                self.root.after(0, self.update_ui_for_running)
                self.log_message("✅ Dolores system online")
                
            except Exception as e:
                self.log_message(f"❌ Failed to start: {str(e)}")
                messagebox.showerror("Startup Error", str(e))
        
        threading.Thread(target=start_thread, daemon=True).start()
    
    def stop_system(self):
        """Stop the Dolores system"""
        self.system_running = False
        self.memory = None
        self.host = None
        
        self.update_ui_for_stopped()
        self.log_message("⏹️ Dolores system stopped")
    
    def restart_system(self):
        """Restart the system"""
        self.log_message("🔄 Restarting system...")
        self.stop_system()
        time.sleep(1)
        self.start_system()
    
    def update_ui_for_running(self):
        """Update UI when system is running"""
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.restart_btn.config(state='normal')
        self.send_btn.config(state='normal')
        self.voice_btn.config(state='normal')
        self.record_btn.config(state='normal')
        
        self.status_label.config(text="● Online", foreground='green')
        self.api_label.config(text="API: ✓ Connected", foreground='green')
        
        # Update knowledge stats
        self.update_knowledge_display()
    
    def update_ui_for_stopped(self):
        """Update UI when system is stopped"""
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.restart_btn.config(state='disabled')
        self.send_btn.config(state='disabled')
        self.voice_btn.config(state='disabled')
        self.record_btn.config(state='disabled')
        
        self.status_label.config(text="● Offline", foreground='red')
        self.api_label.config(text="API: ✗ Disconnected", foreground='red')
    
    def test_api_connection(self):
        """Test DeepSeek API connection"""
        try:
            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            req = urllib.request.Request(
                "https://api.deepseek.com/v1/chat/completions",
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read())
                return True
                
        except Exception as e:
            raise Exception(f"API connection failed: {str(e)}")
    
    def send_message(self, event=None):
        """Send message to Dolores"""
        if not self.system_running:
            return
            
        message = self.input_entry.get().strip()
        if not message:
            return
            
        self.input_entry.delete(0, tk.END)
        
        # Add to conversation display
        self.conversation_text.config(state='normal')
        self.conversation_text.insert(tk.END, f"You: {message}\n", 'user')
        self.conversation_text.config(state='disabled')
        
        def process_message():
            try:
                # Process through Dolores
                self.host.process_input(message, source="control_panel")
                
                # Get response from DeepSeek
                response = self.call_deepseek(message)
                
                # Update UI
                self.root.after(0, lambda: self.add_dolores_response(response))
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.root.after(0, lambda: self.add_dolores_response(error_msg))
        
        threading.Thread(target=process_message, daemon=True).start()
    
    def call_deepseek(self, user_input):
        """Call DeepSeek API for response"""
        try:
            # Get relevant context from memory
            memories = self.memory.recall(user_input, limit=10)
            context = "\n".join([f"[{m['category']}] {m['content']}" for m in memories])
            
            prompt = f"""You are Dolores, an AI podcast host learning about the user. 
Based on your memories: {context}

Respond warmly and conversationally to: {user_input}"""
            
            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            req = urllib.request.Request(
                "https://api.deepseek.com/v1/chat/completions",
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read())
                return result['choices'][0]['message']['content']
                
        except Exception as e:
            return f"I'm having trouble connecting to my thoughts right now. ({str(e)})"
    
    def add_dolores_response(self, response):
        """Add Dolores response to conversation"""
        self.conversation_text.config(state='normal')
        self.conversation_text.insert(tk.END, f"Dolores: {response}\n\n", 'dolores')
        self.conversation_text.see(tk.END)
        self.conversation_text.config(state='disabled')
        
        # Update knowledge display
        self.update_knowledge_display()
    
    def update_knowledge_display(self):
        """Update knowledge base display"""
        if not self.memory:
            return
            
        try:
            stats = self.memory.get_memory_stats()
            self.memory_label.config(text=f"Memories: {stats['total_memories']}")
            
            # Update knowledge tree
            for item in self.knowledge_tree.get_children():
                self.knowledge_tree.delete(item)
            
            # Get category breakdown
            conn = sqlite3.connect(self.memory.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT category, COUNT(*) FROM knowledge GROUP BY category ORDER BY COUNT(*) DESC LIMIT 10")
            
            for category, count in cursor.fetchall():
                self.knowledge_tree.insert('', 'end', values=(f"{category}: {count}",))
            
            conn.close()
            
        except Exception as e:
            self.log_message(f"Error updating knowledge display: {str(e)}")
    
    def start_monitoring(self):
        """Start system monitoring thread"""
        def monitor():
            while True:
                try:
                    # Update CPU usage
                    cpu_percent = psutil.cpu_percent()
                    self.root.after(0, lambda: self.cpu_label.config(text=f"CPU: {cpu_percent}%"))
                    
                    time.sleep(2)
                except:
                    break
        
        threading.Thread(target=monitor, daemon=True).start()
    
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        
        ttk.Label(settings_window, text="DeepSeek API Key:").pack(pady=5)
        api_entry = ttk.Entry(settings_window, width=50, show="*")
        api_entry.pack(pady=5)
        if self.api_key:
            api_entry.insert(0, self.api_key)
        
        def save_settings():
            new_key = api_entry.get()
            if new_key:
                self.api_key = new_key
                config = {"deepseek_api_key": new_key}
                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                messagebox.showinfo("Settings", "Settings saved successfully")
                settings_window.destroy()
        
        ttk.Button(settings_window, text="Save", command=save_settings).pack(pady=10)
    
    def export_data(self):
        """Export conversation and knowledge data"""
        if not self.memory:
            messagebox.showwarning("Export", "System must be running to export data")
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = f"dolores_export_{timestamp}.json"
            
            # Get all knowledge
            conn = sqlite3.connect(self.memory.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge")
            
            export_data = {
                "export_timestamp": timestamp,
                "total_memories": cursor.rowcount,
                "knowledge": [dict(zip([col[0] for col in cursor.description], row)) 
                            for row in cursor.fetchall()]
            }
            
            conn.close()
            
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            messagebox.showinfo("Export", f"Data exported to {export_file}")
            
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
    
    def run(self):
        """Run the control panel application"""
        self.log_message("Dolores Control Panel initialized")
        self.log_message("Click 'Start System' to bring Dolores online")
        self.root.mainloop()

if __name__ == "__main__":
    app = DoloresControlPanel()
    app.run()