#!/usr/bin/env python
import threading
import time
import os
import sys
from uvicorn import run
from backend.crm_service import app as crm_app
from backend.channel_stub import app as channel_app


def run_channel():
    """Run channel stub on port 8001"""
    run(channel_app, host="0.0.0.0", port=8001, log_level="info")


def run_crm():
    """Run CRM on dynamic port"""
    port = int(os.environ.get("PORT", 8000))
    run(crm_app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    # Start channel stub in background thread
    channel_thread = threading.Thread(target=run_channel, daemon=True)
    channel_thread.start()
    
    # Give channel stub a moment to start
    time.sleep(2)
    
    # Run CRM in main thread
    run_crm()
