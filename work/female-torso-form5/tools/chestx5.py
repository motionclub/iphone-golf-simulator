"""chestx5.py: chest-only variants -> front profile table (envelope + columns) + slope monotonicity report.
python3 tools/chestx5.py NAME '{"wc_s":0.46, "b5.H":0.02}' [--base data/P5_final.json]   (saves data/co5_NAME.npy, data/P5_NAME.json)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torso5 as t5, torso4 as t4
from torso4 import section_extents, fillnan, ZG
from footprint import grid_surface
import seam
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = np.load(HERE + '/data/plate_front_fine4.npy')


def profile_report(co, tag, cols=(0.0, 0.04, 0.06, 0.08), z0=1.20, z1=1.37):
    fe, be = section_extents(co); fe = fillnan(fe)
    zs = np.arange(z0, z1 + 1e-9, 0.01)
    env = np.interp(zs, ZG, fe); pl = np.interp(zs, FF[0], FF[1])
    G = grid_surface(co, 'front', np.array(cols), zs, sig=0.004)
    sl = lambda a: np.degrees(np.arctan(np.gradient(a, 0.01)))
    print(f'[{tag}] z      env   plate  | ' + ' '.join(f'x={c:.2f}' for c in cols) + ' (mm)  | slope deg env, ' + ' '.join(f'x={c:.2f}' for c in cols))
    se = sl(env); sc = [sl(G[:, j]) for j in range(len(cols))]
    for i, z in enumerate(zs):
        print(f'[{tag}] {z:.2f} {1000*env[i]:7.1f} {1000*pl[i]:7.1f} | ' + ' '.join(f'{1000*G[i,j]:7.1f}' for j in range(len(cols))) + ' | ' + f'{se[i]:6.1f} ' + ' '.join(f'{sc[j][i]:6.1f}' for j in range(len(cols))))
    return env


def run(name, ov, base=HERE + '/data/P5_final.json', save=True):
    P0 = {**t4.DEFAULT3, **json.load(open(base))}
    P = t5.apply_ov(P0, ov)
    co, dF, dB = t5.build_chest(P)
    if save:
        np.save(f'{HERE}/data/co5_{name}.npy', co); json.dump(P, open(f'{HERE}/data/P5_{name}.json', 'w'), indent=1)
    return co, P


if __name__ == '__main__':
    name = sys.argv[1]; ov = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    co, P = run(name, ov)
    bs = seam.border_steps(co)[0]
    print(f'seams: legs {bs["legs"]["max_mm"]:.2f} arm {bs["arm"]["max_mm"]:.2f} top {bs["top"]["max_mm"]:.2f}')
    profile_report(co, name)
