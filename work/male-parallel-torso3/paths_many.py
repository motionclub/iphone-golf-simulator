"""run several joint LM paths in parallel and keep the last iterate: python3.13 paths_many.py <spec.json>  (spec={tag: rbf overrides}) -> data/V_<tag>.npy, data/c_<tag>.npz"""
import json, subprocess, sys, os, shutil
from concurrent.futures import ThreadPoolExecutor
PY = '/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13'; env = dict(os.environ, PYTHONPATH='../male-micro1i/pylib')
spec = json.load(open(sys.argv[1]))
def run(item):
    tag, R = item; R = dict(R.get('rbf', R)); n = R.get('iters', 14)
    r = subprocess.run([PY, 'path3.py', 'both', 'PP_' + tag, json.dumps(R)], capture_output=True, text=True, env=env)
    k = n - 1
    while k >= 0 and not os.path.exists(f'data/V_PP_{tag}_i{k}.npy'): k -= 1
    shutil.copy(f'data/V_PP_{tag}_i{k}.npy', f'data/V_{tag}.npy'); shutil.copy(f'data/c_PP_{tag}_i{k}.npz', f'data/c_{tag}.npz')
    return f'{tag}: last iterate {k}'
with ThreadPoolExecutor(4) as ex:
    for l in ex.map(run, spec.items()): print(l)
