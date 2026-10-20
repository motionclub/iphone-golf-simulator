import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
PY = '/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13'
SHAPES = {'mono': [0.8, 1.0, 0.85, 0.65, 0.45, 0.3, 0.15, 0.0], 'low': [0.8, 1.0, 0.7, 0.4, 0.2, 0.08, 0.0, 0.0], 'tall': [0.8, 1.0, 0.95, 0.85, 0.7, 0.55, 0.35, 0.1]}
jobs = [(sh, A) for sh in ('mono', 'low', 'tall') for A in (4.0, 8.0, 12.0)]
def run(job):
    sh, A = job; tag = f'cl_{sh}{int(A)}'; ak = {f'a{i}': round(A * v, 3) for i, v in enumerate(SHAPES[sh])}
    cfg = {'_base': 'A3', '_only': ['cleft2'], 'cleft2': ak}
    subprocess.run([PY, 'struct3.py', tag, json.dumps(cfg)], capture_output=True, env={'PYTHONPATH': '../male-micro1i/pylib'})
    return subprocess.run(['./gate_only.sh', tag], capture_output=True, text=True).stdout.strip()
with ThreadPoolExecutor(4) as ex:
    for line in ex.map(run, jobs): print(line)
