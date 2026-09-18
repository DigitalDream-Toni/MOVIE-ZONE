import subprocess
import time
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Starting server...")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

time.sleep(5)

# Check if server started
poll = proc.poll()
if poll is not None:
    stderr = proc.stderr.read().decode()
    print(f"Server failed to start (exit code {poll})")
    print(f"Error: {stderr}")
    sys.exit(1)

print("Server running, starting tests...\n")

try:
    result = subprocess.run(
        [sys.executable, "test_api.py"],
        timeout=60,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except:
        proc.kill()
    print("Server stopped.")
