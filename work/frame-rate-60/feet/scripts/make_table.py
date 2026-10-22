"""clip_table_new.json (what the Unity wiring reads) + foot_vertices_<hero>.json (foot vertex indices of the body mesh for the Play-mode foot-height trace).
python3.13 scripts/make_table.py   (Blender's python: numpy needed for the skin file)"""
import json, os, sys
import numpy as np
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet'
rows = []
gen = {}
for tag, sex in (('male', 'Male'), ('female', 'Female')):
    fb = json.load(open(f'{W}/data/fbx_{tag}.json'))
    for clip, v in fb.items():
        g = json.loads(str(np.load(f'{W}/data/gen_{ {"Serve": "serve", "Walk": "walk", "RunForward": "runf", "RunLeft": "runl", "RunRight": "runr"}[clip] }_{tag}.npz', allow_pickle=True)['meta']))
        gen[(tag, clip)] = g
        rows.append(dict(name=clip, sex=sex, fbxSha256=v['sha256'], length=round((v['frames'] - 1) / 30.0, 6), contact=float(g['contact']) if clip == 'Serve' else 0.0, loop=bool(g.get('loop', False))))
sm = gen[('male', 'Serve')]
serve = {k: float(sm[k]) for k in ('stance', 'release', 'trophy', 'deepest', 'takeoff', 'contact', 'landing')}
table = dict(clips=rows, serve=serve, walkSpeed=float(gen[('male', 'Walk')]['V']), runSpeed=float(gen[('male', 'RunForward')]['V']))
for (tag, clip), g in gen.items():           # the two heroes share the design numbers
    if clip == 'Serve':
        assert all(abs(float(g[k]) - serve[k]) < 1e-9 for k in serve), 'serve times differ between heroes'
    if clip == 'Walk': assert abs(g['V'] - table['walkSpeed']) < 1e-9
    if clip.startswith('Run'): assert abs(g['V'] - table['runSpeed']) < 1e-9
# the forward run read backwards (backing away from the net) must put its stance windows on the stance windows of the sideways runs: time = pivot - phase, the pivot is twice the stance centre
# of each foot (the left stance centre; the right foot's centre taken half a cycle later), averaged; checked on both heroes
piv = []
for tag in ('male', 'female'):
    vb = json.load(open(f'{W}/data/verify_blend_{tag}.json'))['clips']['RunForward']
    n = vb['frames'] - 1
    cs = []
    for side, off in (('L', 0), ('R', n / 2.0)):
        pl = [i for i, x in enumerate(vb['foot_height_mm'][side][:n]) if x <= 10]
        c = float(np.mean(pl)) + (n if side == 'R' and np.mean(pl) < n / 2.0 else 0)
        cs.append((2 * c) % n)
    piv.append(float(np.mean(cs)) / 30.0)
assert abs(piv[0] - piv[1]) < 1e-9, piv
table['runReversePivot'] = round(piv[0], 6)
json.dump(table, open(f'{W}/data/clip_table_new.json', 'w'), indent=1)
for tag in ('male', 'female'):
    sk = np.load(f'{W}/data/skin_{tag}.npz'); names = list(sk['names']); dom = sk['dom']; co = sk['co']
    ix = {n: i for i, n in enumerate(names)}
    L = np.where(np.isin(dom, [ix['LeftFoot'], ix['LeftToes']]))[0]; R = np.where(np.isin(dom, [ix['RightFoot'], ix['RightToes']]))[0]
    rng = np.random.default_rng(1); chk = np.concatenate([L[rng.choice(len(L), 24, replace=False)], R[rng.choice(len(R), 24, replace=False)]])
    json.dump(dict(vertex_count=int(len(co)), L=[int(i) for i in L], R=[int(i) for i in R], check=[float(v) for i in chk for v in ([int(i)] + list(co[i]))]), open(f'{W}/data/foot_vertices_{tag}.json', 'w'))
print('table', json.dumps(table)[:400])
