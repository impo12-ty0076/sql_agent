#!/usr/bin/env python3
"""
Startup script for the SQL Agent backend server.
This script ensures the server runs with the correct Python path and module resolution.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    
    # Add the current directory to Python path
    os.environ['PYTHONPATH'] = str(script_dir)
    
    # Change to the current directory
    os.chdir(script_dir)
    
    # Run uvicorn with the correct module path
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "sql_agent.backend.main:app", 
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]
    
    print(f"Starting server from: {script_dir}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())