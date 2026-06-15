#!/usr/bin/env python
import subprocess
import os
import signal
import sys

# Start channel stub on port 8001
channel_process = subprocess.Popen([
    sys.executable, "-m", "uvicorn", 
    "backend.channel_stub:app",
    "--host", "0.0.0.0",
    "--port", "8001"
])

# Start CRM service on dynamic port
port = os.environ.get("PORT", "8000")
crm_process = subprocess.Popen([
    sys.executable, "-m", "uvicorn",
    "backend.crm_service:app",
    "--host", "0.0.0.0",
    "--port", port
])

def signal_handler(sig, frame):
    channel_process.terminate()
    crm_process.terminate()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Keep both processes running
while True:
    if channel_process.poll() is not None or crm_process.poll() is not None:
        break
