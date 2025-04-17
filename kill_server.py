import os
import subprocess
import sys

def kill_process_on_port(port=5000):
    print(f"Attempting to kill processes on port {port}...")
    
    if sys.platform.startswith('win'):
        # Windows
        cmd = f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{port}\') do taskkill /F /PID %a'
        result = os.system(cmd)
        if result == 0:
            print(f"Successfully terminated process on port {port}")
        else:
            print(f"No process found running on port {port} or could not terminate")
    else:
        # Linux/Unix
        cmd = f"lsof -i :{port} | grep LISTEN | awk '{{print $2}}' | xargs -r kill -9"
        result = os.system(cmd)
        if result == 0:
            print(f"Successfully terminated process on port {port}")
        else:
            print(f"No process found running on port {port} or could not terminate")

if __name__ == "__main__":
    kill_process_on_port(5000)
    print("Server processes terminated. You can now restart the server.") 