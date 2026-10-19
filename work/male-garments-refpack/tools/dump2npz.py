"""dump2npz.py <hero> <outdir> : the game's worn kit (pipeline dump = what Unity draws) as render_npz-compatible npz (+ copies of the maps)."""
import sys, os, json, shutil, numpy as np
H, OUT = sys.argv[1:3]; D = f'../clothing-v2/pipeline/dump/{H}'; O = f'../clothing-v2/out/{H}/unity'; os.makedirs(OUT, exist_ok=True)
meta = json.load(open(D + '/hero.json'))
ROLE = {'Kit_Top': 'Kit_Shirt', 'Kit_Bottom': 'Kit_Shorts', 'Kit_Belt': 'Kit_Belt', 'Kit_Sock_L': 'Kit_Sock', 'Kit_Sock_R': 'Kit_Sock'}
for p in meta['parts'][1:]:
    t = p['name']
    if not os.path.exists(f'{D}/{t}_pos.f32'): continue
    P = np.fromfile(f'{D}/{t}_pos.f32', np.float32).reshape(-1, 3); T = np.fromfile(f'{D}/{t}_tri.i32', np.int32).reshape(-1, 3)
    uv = np.fromfile(f'{D}/{t}_uv.f32', np.float32).reshape(-1, 2) if os.path.exists(f'{D}/{t}_uv.f32') else np.zeros((len(P), 2), np.float32)
    subs = p.get('submeshes') or []
    mat = np.zeros(len(T), np.int32); roles = [ROLE.get(t, 'Kit_Shirt')]
    if subs and isinstance(subs[0], dict) and 'role' in subs[0]:
        roles = [s['role'] for s in subs]
        for i, s in enumerate(subs): mat[s['start'] // 3:(s['start'] + s['count']) // 3] = i
    np.savez(f'{OUT}/{t}_final.npz', pos=P, tri=T, uv=uv, mat=mat, roles=np.array(roles))
    tag = t[4:].replace('_', '')
    for k in 'NM':
        f = f'{O}/{tag}_{k}.png'
        if os.path.exists(f): shutil.copy(f, f'{OUT}/{tag}_{k}.png')
    print(t, len(P), len(T), roles)
