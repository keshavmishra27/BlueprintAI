import os
import time
import subprocess
import hashlib
import sys

def get_hash(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def run_watcher():
    last_hash = None
    print("IDE Agent Watcher started...")
    while True:
        if not os.path.exists("ready.txt") and os.path.exists("current_prompt.md"):
            current_hash = get_hash("current_prompt.md")
            if current_hash and current_hash != last_hash:
                print(f"[{time.strftime('%X')}] Detected new prompt. Running IDE Agent...", flush=True)
                
                prompt = (
                    "Read current_prompt.md. Based on its instructions, generate the requested JSON payload "
                    "(either baseline architecture, blueprint start payload, or branch architecture) and write it "
                    "to the correct file (baseline.json, blueprint.json, or branch.json). "
                    "Do not use markdown blocks around the JSON in the file, just valid raw JSON. "
                    "After writing the file, create a file named ready.txt."
                )
                
                subprocess.run(["agy", "--print", prompt, "--dangerously-skip-permissions"], shell=True)
                print(f"[{time.strftime('%X')}] IDE Agent finished processing prompt.", flush=True)
                last_hash = current_hash
        time.sleep(2)

if __name__ == "__main__":
    run_watcher()
