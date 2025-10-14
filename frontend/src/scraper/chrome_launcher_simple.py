#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Chrome Launcher for Django Integration
Launches Chrome with debugging port without hanging the Django process
MOVED TO FRONTEND - Optimized for single dependency management
"""

import subprocess
import time
import sys
import os
from pathlib import Path

# Check if Chrome is already running with debugging
def check_chrome_running():
    """Check if Chrome is already running with debugging"""
    try:
        import requests
        response = requests.get('http://localhost:9222/json/version', timeout=2)
        return response.status_code == 200
    except:
        return False

def find_chrome():
    # Find Chrome executable in common locations
    chrome_paths = [
        # Windows standard paths
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        # Windows server paths
        r'C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe',
        # Current user path
        os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe'),
        # Portable Chrome
        r'.\chrome\chrome.exe',
        r'.\GoogleChromePortable\GoogleChromePortable.exe',
        # If Chrome is in PATH
        'chrome.exe',
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"Found Chrome at: {path}")
            return path
    
    return None

# Kill existing Chrome processes
def kill_existing_chrome():
    """Kill existing Chrome processes"""
    try:
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], 
                     capture_output=True, shell=True)
        time.sleep(2)
    except:
        pass

def start_chrome_nonblocking():
    """Start Chrome with debugging (non-blocking for Django)"""
    try:
        print("Starting Chrome with debugging for Django...")
        
        # Get data directory - UPDATED PATH for frontend integration
        project_root = Path(__file__).parent.parent.parent.parent
        data_dir = project_root / "backend" / "notification_push" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if already running
        if check_chrome_running():
            print("Chrome debugging already available")
            return True
        
        # Find Chrome executable
        chrome_path = find_chrome()
        if not chrome_path:
            print("ERROR: Chrome not found on system!")
            return False
        
        # Kill existing Chrome instances
        kill_existing_chrome()
        
        # Chrome command with debugging
        chrome_cmd = [
            chrome_path,
            "--remote-debugging-port=9222",
            "--no-first-run", 
            "--no-default-browser-check",
            f"--user-data-dir={data_dir}\\chrome_debug",
            "https://www.upwork.com/ab/account-security/login"
        ]
        
        # Launch Chrome (non-blocking)
        process = subprocess.Popen(chrome_cmd, shell=True, 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
        
        print("Chrome started with debugging port 9222")
        print("Chrome should be visible - log in to Upwork manually")
        print("Debugging port available at: http://localhost:9222")
        print(f"User data dir: {data_dir}\\chrome_debug")
        
        # Quick check - wait max 2 seconds to see if debugging becomes available
        for i in range(4):  # 4 × 0.5s = 2 seconds max wait
            time.sleep(0.5)
            if check_chrome_running():
                print("Chrome debugging confirmed working")
                return True
        
        # Don't wait longer - let Chrome start in background
        print("Chrome launched, debugging may take a moment to become available")
        return True
        
    except Exception as e:
        print(f"Error starting Chrome: {e}")
        return False

if __name__ == "__main__":
    success = start_chrome_nonblocking()
    sys.exit(0 if success else 1)