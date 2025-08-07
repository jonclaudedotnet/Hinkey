#!/usr/bin/env python3
"""Restart Studio UI with fixed update mechanism"""

import subprocess
import os
import signal
import time

# Kill existing studio UI
print("Stopping existing Studio UI...")
try:
    # Find and kill studio process
    result = subprocess.run(['pgrep', '-f', 'dolores_studio_ui.py'], capture_output=True, text=True)
    if result.stdout:
        pid = result.stdout.strip()
        os.kill(int(pid), signal.SIGTERM)
        time.sleep(2)
        print(f"Stopped process {pid}")
except Exception as e:
    print(f"Error stopping: {e}")

# Kill daemon processes
print("Stopping daemons...")
try:
    subprocess.run(['pkill', '-f', 'dolores_daemon.py'])
    time.sleep(1)
except:
    pass

# Restart daemon
print("Starting fresh daemon...")
subprocess.Popen(['python3', 'dolores_daemon.py'], 
                 stdout=subprocess.DEVNULL, 
                 stderr=subprocess.DEVNULL)

time.sleep(2)

# Restart studio UI
print("Starting Studio UI...")
subprocess.Popen(['python3', 'dolores_studio_ui.py'])

print("Studio restarted! Check the window now.")