"""render skin (front/back) and yaw views for many tags in parallel: python3.13 render_many.py [--noyaw] tag..."""
import subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
env = dict(os.environ, PYTHONPATH='../male-micro1i/pylib'); noyaw = '--noyaw' in sys.argv; tags = [a for a in sys.argv[1:] if not a.startswith('--')]
def run(t):
    subprocess.run(['./skin.sh', t], capture_output=True, env=env)
    if not noyaw: subprocess.run(['./yaws.sh', t], capture_output=True, env=env)
    return t
with ThreadPoolExecutor(5) as ex: list(ex.map(run, tags))
print('rendered', tags)
