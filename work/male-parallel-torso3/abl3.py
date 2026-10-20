import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
PY = '/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13'
feats = ['pec_lift', 'sternum', 'shelf', 'linea', 'iliac', 'oblique', 'cleft', 'lobes']
def run(f):
    tag = 'ab_' + f; subprocess.run([PY, 'struct3.py', tag, json.dumps({k: {'A': 0.0} for k in feats if k != f})], capture_output=True, env={'PYTHONPATH': '../male-micro1i/pylib'})
    r = subprocess.run(['./gate_only.sh', tag], capture_output=True, text=True); return r.stdout.strip()
with ThreadPoolExecutor(4) as ex:
    for line in ex.map(run, feats): print(line)
