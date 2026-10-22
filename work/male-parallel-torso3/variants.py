"""Run form3 variants in parallel: python3.13 variants.py <spec.json> [--yaw] ; spec = {tag: cfg-override-dict}; prints gate lines.  renders skin (+yaw views with --yaw)."""
import json, subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
PY = '/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13'
env = dict(os.environ, PYTHONPATH='../male-micro1i/pylib')
spec = json.load(open(sys.argv[1])); yaw = '--yaw' in sys.argv; skin = '--noskin' not in sys.argv; nogate = '--nogate' in sys.argv
def run(item):
    tag, cfg = item
    r = subprocess.run([PY, 'form3.py', tag, json.dumps(cfg)], capture_output=True, text=True, env=env); line = [l for l in r.stdout.strip().split('\n') if l.startswith(tag + ' dy')]
    out = (line[0] if line else r.stdout[-300:] + r.stderr[-300:])
    if not nogate: out += '\n' + subprocess.run(['./gate_only.sh', tag], capture_output=True, text=True, env=env).stdout.strip()
    if skin: subprocess.run(['./skin.sh', tag], capture_output=True, env=env)
    if yaw: subprocess.run(['./yaws.sh', tag], capture_output=True, env=env)
    return out
with ThreadPoolExecutor(4) as ex:
    for line in ex.map(run, spec.items()): print(line)
