#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import sqlite3
import threading
import queue
import time
import os

class TaskViewer:
    def __init__(self):
        self.db_path = './claude_dolores_bridge/shared_tasks.db'
        self.update_interval = 2  # seconds
        self.task_queue = queue.Queue()
        
        # Create main window
        self.window = Gtk.Window(title="Dolores Task Viewer")
        self.window.set_default_size(800, 600)
        self.window.connect("destroy", Gtk.main_quit)
        
        # Create main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window.add(self.main_box)
        
        # Create scrolled window
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.main_box.pack_start(self.scrolled_window, True, True, 0)
        
        # Create tree view
        self.tree_view = Gtk.TreeView()
        self.scrolled_window.add(self.tree_view)
        
        # Create list store model
        self.list_store = Gtk.ListStore(str, str, str, str, str, str, str, str, str)
        self.tree_view.set_model(self.list_store)
        
        # Create columns
        columns = [
            ("ID", 0),
            ("Timestamp", 1),
            ("Requester", 2),
            ("Type", 3),
            ("Content", 4),
            ("Status", 6),
            ("Result", 7),
            ("Tokens", 8)
        ]
        
        for title, col_id in columns:
            renderer = Gtk.CellRendererText()
            renderer.set_property("wrap-mode", 2)  # WORD
            renderer.set_property("wrap-width", 400)
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_resizable(True)
            if title == "Content" or title == "Result":
                renderer.set_property("width-chars", 50)
                renderer.set_property("ellipsize", 3)  # END_ELLIPSIS
            self.tree_view.append_column(column)
        
        # Add refresh button
        self.refresh_btn = Gtk.Button(label="Manual Refresh")
        self.refresh_btn.connect("clicked", self.on_refresh_clicked)
        self.main_box.pack_start(self.refresh_btn, False, False, 0)
        
        # Start database monitoring thread
        self.running = True
        self.thread = threading.Thread(target=self.db_monitor_thread)
        self.thread.daemon = True
        self.thread.start()
        
        # Start GUI update handler
        GLib.timeout_add(500, self.process_queue)
    
    def db_monitor_thread(self):
        while self.running:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tasks ORDER BY timestamp DESC")
                rows = cursor.fetchall()
                conn.close()
                
                # Put the results in the queue for GUI thread
                self.task_queue.put(rows)
                
            except Exception as e:
                print(f"Database error: {e}")
                self.task_queue.put(None)  # Signal error
                
            time.sleep(self.update_interval)
    
    def process_queue(self):
        try:
            while not self.task_queue.empty():
                rows = self.task_queue.get()
                
                if rows is None:
                    self.show_error_dialog("Database Error", "Could not read from database")
                    continue
                
                # Update the list store
                self.list_store.clear()
                for row in rows:
                    self.list_store.append([
                        str(row[0]),  # id
                        row[1],       # timestamp
                        row[2],       # requester
                        row[3],       # task_type
                        row[4],       # content
                        row[5],       # context
                        row[6],       # status
                        row[7],       # result
                        str(row[8])  # tokens_used
                    ])
                
        except Exception as e:
            print(f"GUI update error: {e}")
        
        return True  # Keep timeout active
    
    def on_refresh_clicked(self, widget):
        # Force immediate refresh by putting a dummy item in the queue
        self.task_queue.put([])
    
    def show_error_dialog(self, title, message):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def run(self):
        self.window.show_all()
        Gtk.main()

if __name__ == "__main__":
    # Verify database exists
    if not os.path.exists('./claude_dolores_bridge/shared_tasks.db'):
        print("Error: Database file not found at ./claude_dolores_bridge/shared_tasks.db")
        exit(1)
    
    viewer = TaskViewer()
    viewer.run()