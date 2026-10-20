"""chestvar6.py: scan conc_post (upper-chest landing) variants.  python3 tools/chestvar6.py '{"conc_post.zs":[1.262,1.24],"conc_post.pw":[1,0.5]}' ['{"fixed overrides"}']
keys 'conc_post.xxx' override P5_final['conc_post'][xxx]; other keys are b5.xxx / top-level (torso5.apply_ov).  Builds chest + FORM4 glute + pelvis (build5.build_final5)."""
import sys, os, json, itertools, copy, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import build5, torso5 as t5
import chestprof6 as cp6
from torso4 import CO0
from torso5 import section_extents, fillnan, ZG
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = np.load(HERE + '/data/plate_front_fine4.npy')
PC0 = json.load(open(HERE + '/data/P5_final.json')); PG = json.load(open(HERE + '/data/P_glute4.json')); PP = json.load(open(HERE + '/data/PP5_final.json'))
C4 = np.load(HERE + '/data/co_FORM4_final.npy').astype(np.float64)

def env(c, zs):
    fe, be = section_extents(c); fe = fillnan(fe)
    return np.interp(zs, ZG, fe)

def make(over):
    PC = copy.deepcopy(PC0)
    for k, v in over.items():
        if k.startswith('conc_post.'):
            PC.setdefault('conc_post', {})[k.split('.', 1)[1]] = v
        elif k == 'conc_post' and v is None:
            PC.pop('conc_post', None)
        else:
            PC = t5.apply_ov(PC, {k: v})
    return build5.build_final5(PC, PG, PP)

def report(tag, co, plate_img=None):
    zb = np.arange(1.15, 1.2701, 0.005)
    e = env(co, zb) - np.interp(zb, FF[0], FF[1]); rms = float(np.sqrt((e ** 2).mean()) * 1000)
    zd = np.array([1.28, 1.30, 1.32])
    d5 = 1000 * (env(co, zd) - np.interp(zd, FF[0], FF[1]))
    zz = np.arange(1.25, 1.3551, 0.01); sl = np.degrees(np.arctan(np.gradient(env(co, zz), 0.01)))
    img, _ = cp6.render_front(co, 1.5); c, s_ = cp6.groups(img)
    d4 = 1000 * (env(C4, zd) - np.interp(zd, FF[0], FF[1]))
    print(f'{tag:34s} bumpRMS {rms:4.2f} | dev@1.28/1.30/1.32 {d5[0]:5.1f} {d5[1]:5.1f} {d5[2]:5.1f} (F4 {d4[0]:5.1f} {d4[1]:5.1f} {d4[2]:5.1f}) | slope z1.25..1.35 ' + ' '.join(f'{v:4.0f}' for v in sl) + f' | dip cen {cp6.dip(c):5.1f} side {cp6.dip(s_):5.1f}')
    return d5, sl, cp6.dip(c)

if __name__ == '__main__':
    grid = json.loads(sys.argv[1]); fixed = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    keys = list(grid.keys())
    img4, _ = cp6.render_front(C4, 1.5); c4, s4 = cp6.groups(img4)
    print(f'FORM4 reference: dip cen {cp6.dip(c4):5.1f} side {cp6.dip(s4):5.1f}')
    for combo in itertools.product(*[grid[k] for k in keys]):
        over = dict(fixed); over.update(dict(zip(keys, combo)))
        t0 = time.time(); co = make(over)
        tag = ' '.join(f'{k.split(".")[-1]}={v}' for k, v in zip(keys, combo))
        report(tag, co)
        np.save(HERE + '/data/_cv_' + '_'.join(str(v) for v in combo) + '.npy', co)
