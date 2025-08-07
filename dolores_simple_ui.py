import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

class ResponseWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Learning Responses")
        self.set_default_size(600, 400)
        
        # Create main container
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(self.box)
        
        # Create scrolled window
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Create text view for responses
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_buffer = self.text_view.get_buffer()
        
        # Add text view to scrolled window
        self.scrolled_window.add(self.text_view)
        self.box.pack_start(self.scrolled_window, True, True, 0)
        
        # Show all widgets
        self.show_all()
    
    def add_response(self, text):
        end_iter = self.text_buffer.get_end_iter()
        self.text_buffer.insert(end_iter, text + "\n\n")
        # Auto-scroll to bottom
        adj = self.scrolled_window.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

# Create and run the window
win = ResponseWindow()
win.connect("destroy", Gtk.main_quit)
Gtk.main()