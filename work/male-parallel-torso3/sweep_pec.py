import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
PY = '/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13'
base = sys.argv[1]
jobs = [(pl, st) for pl in (0.0, 3.0, 6.0, 9.0) for st in (0.0, 2.0, 4.0)]
def run(job):
    pl, st = job; tag = f'pc_{base}_{int(pl)}_{int(st)}'
    cfg = {'_base': base, '_only': ['pec_lift', 'sternum'], 'pec_lift': {'A': pl}, 'sternum': {'A': st}}
    subprocess.run([PY, 'struct3.py', tag, json.dumps(cfg)], capture_output=True, env={'PYTHONPATH': '../male-micro1i/pylib'})
    return subprocess.run(['./gate_only.sh', tag], capture_output=True, text=True).stdout.strip()
with ThreadPoolExecutor(4) as ex:
    for line in ex.map(run, jobs): print(line)
