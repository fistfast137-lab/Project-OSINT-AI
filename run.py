import subprocess, sys, os, signal, time

processes = []

def cleanup(signum=None, frame=None):
    print("Shutting down both bots...")
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass
    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

print("Starting SHUVO BOT (main.py)...")
p1 = subprocess.Popen([sys.executable, "main.py"])

time.sleep(2)

print("Starting SHUVO BOT Controller (controller.py)...")
p2 = subprocess.Popen([sys.executable, "controller.py"])

processes = [p1, p2]
print("Both bots running!")

while True:
    if p1.poll() is not None:
        print(f"main.py exited (code {p1.returncode}), restarting...")
        p1 = subprocess.Popen([sys.executable, "main.py"])
        processes[0] = p1
    if p2.poll() is not None:
        print(f"controller.py exited (code {p2.returncode}), restarting...")
        p2 = subprocess.Popen([sys.executable, "controller.py"])
        processes[1] = p2
    time.sleep(5)
