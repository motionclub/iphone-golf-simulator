"""Trade-off scan: torso FORM3 gate regions (their metric) + cleft depth + sharp edges for parameter variants of P_F4.
blender-python: tradeoff.py name:key=val,key=val ...   keys: cleft.scale cleft.s0 cleft.s1 shift.A smile fold.A dsmooth gap.k"""
import sys, json, copy, os, subprocess, numpy as np
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '.'); sys.path.insert(0, '../male-parallel-torso3')
import np_model6 as M
import relcorr as RC
from PIL import Image
from common import *
import roughness as RG
base = json.load(open('P_F4.json'))
REG = {'chest': (1.15, 1.32), 'abdomen': (0.90, 1.15), 'pelvis': (0.80, 0.90)}
def setp(P, key, v):
    ks = key.split('.')
    if key == 'smile': P['rear']['smile'] = v
    elif key == 'dsmooth': P['dsmooth']['iters'] = int(v)
    elif key == 'gap.k': P['gap']['k'] = v
    elif key == 'fold.A': P['rear']['fold']['A'] = v
    elif ks[0] == 'cleft': P['rear']['cleft'][ks[1]] = v
    elif ks[0] == 'shift': P['rear']['shift'][ks[1]] = v
    elif key.startswith('sz'): P['rear']['shift']['z'][int(key[2])] = v
    elif key == 'su': P['rear']['shift']['su'] = v
    elif ks[0] == 'nape': pass
    else: raise SystemExit('key ' + key)
def run(spec):
    name, _, kv = spec.partition(':'); P = copy.deepcopy(base)
    for item in filter(None, kv.split(',')): k, v = item.split('='); setp(P, k, float(v))
    V, _ = M.build(P); np.save(f'data/V_{name}.npy', V)
    env = dict(os.environ)
    subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '--python', 'rig.py', '--', f'data/V_{name}.npy', f'r/{name}_m', 'front,back', 'clay'], env=env, capture_output=True)
    row = {}
    for v in ('front', 'back'):
        mesh = Image.open(f'r/{name}_m/{v}.png').convert('L'); a, b = RC.dog(RC.PL, 1.2, 5.0), RC.dog(mesh, 1.2, 5.0)
        for rn, (z0, z1) in REG.items(): m = RC.torso_mask(v, z0, z1, 0.12); row[f'{v[0]}_{rn[:3]}'] = float(np.corrcoef(a[m], b[m])[0, 1])
    row['mean'] = float(np.mean(list(row.values())))
    d0 = RG.dihedral(V0); d1 = RG.dihedral(V)
    mz = RG.zones['crotch z.735-.83 |x|<.1']; row['new_sharp'] = int(((d1 > 40) & (d0 < 25) & mz).sum())
    c = rear_curve(V, 1e-5, np.array([0.84]))[0] * 1000; pk = max(rear_curve(V, u + 1e-5, np.array([0.84]))[0] * 1000 for u in (0.03, 0.04, 0.05, 0.06, 0.07, 0.08))
    row['cleft84'] = float(pk - c); return name, row
if __name__ == '__main__':
    specs = sys.argv[1:]
    with ThreadPoolExecutor(6) as ex: res = list(ex.map(run, specs))
    print('name        f_che f_abd f_pel b_che b_abd b_pel | mean  cleft84  sharp')
    for n, r in res: print(f'{n:10s} {r["f_che"]:+.3f} {r["f_abd"]:+.3f} {r["f_pel"]:+.3f} {r["b_che"]:+.3f} {r["b_abd"]:+.3f} {r["b_pel"]:+.3f} | {r["mean"]:+.3f} {r["cleft84"]:6.1f} {r["new_sharp"]:3d}')
