import hashlib
import os

files = [
    'benchmark_suite/level6/control_plane/watcher.py',
    'benchmark_suite/level6/control_plane/invoker.py',
    'benchmark_suite/level6/control_plane/handshake.py',
    'benchmark_suite/level6/agent_driver.py'
]

with open('benchmark_suite/level6/results/control_plane_manifest_v2.txt', 'w') as out:
    for f in files:
        h = hashlib.sha256(open(f, 'rb').read()).hexdigest()
        out.write(f'{f}: {h}\n')
        print(f'{f}: {h}')
