import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))

from benchmark_suite.level6.control_plane.watcher import HardenedWatcher

def main():
    run_id = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BLUEPRINT_RUN_ID", "v3.1_pilot_03")
    print(f"================================================================================")
    print(f"           HARDENED IDE AGENT WATCHER (Run ID: {run_id})                        ")
    print(f"================================================================================")
    print("Features: PromptPacket validation, Bounded Process Execution, 5-D Identity Handshake.")
    print("--------------------------------------------------------------------------------")
    
    watcher = HardenedWatcher(
        active_run_id=run_id,
        workspace_dir=root_dir,
    )
    watcher.run_loop(poll_interval=1.0)

if __name__ == "__main__":
    main()
