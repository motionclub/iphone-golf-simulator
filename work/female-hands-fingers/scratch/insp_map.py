import numpy as np, json
M = np.load('../female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz', allow_pickle=True)
for k in M.files:
    a = M[k]; print(k, a.shape, a.dtype, a[:5] if a.ndim==1 else '')
rep = json.load(open('../female-parallel-limbs/data/HeroBase_Female_limbs_report.json'))
print(json.dumps(rep, indent=1)[:3000])
rp = json.load(open('../female-parallel-limbs/data/ring_params.json')); print(json.dumps(rp, indent=1)[:2000])
