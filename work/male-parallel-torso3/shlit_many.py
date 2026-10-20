import subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
PYB = '/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13'; env = dict(os.environ, PYTHONPATH='../male-micro1i/pylib')
def run(t): return subprocess.run([PYB, 'shlit.py', t], capture_output=True, text=True, env=env).stdout.strip().split('\n')[-1]
with ThreadPoolExecutor(4) as ex:
    for l in ex.map(run, sys.argv[1:]): print(l)
