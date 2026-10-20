"""evaluate the gate metric for many tags in parallel: python3.13 gate_many.py tag1 tag2 ... ; prints one line per tag (clay render + 6-region metric)."""
import subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
env = dict(os.environ, PYTHONPATH='../male-micro1i/pylib')
def run(t): return subprocess.run(['./gate_only.sh', t], capture_output=True, text=True, env=env).stdout.strip()
with ThreadPoolExecutor(5) as ex:
    for line in ex.map(run, sys.argv[1:]): print(line)
