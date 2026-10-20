import numpy as np, collections
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
A=np.load('data/artdir_body.npz'); B=np.load('data/base_body.npz'); T=np.load('data/form5_body.npz')
vm=np.load(f'{R}/work/female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz'); b2f=vm['base_to_final']
f5=np.load(f'{R}/work/female-torso-form5/export/torso_form5_delta.npz')
c7=np.load(f'{R}/work/female-parallel-torso/export/torso_delta.npz')
def corner_map(d):
    # dict: (face key tuple sorted verts) -> list of (vertex -> loop index)
    ls,lt,cv=d['loop_start'],d['loop_total'],d['corner_verts']; m={}
    for s,t in zip(ls,lt):
        vs=tuple(int(x) for x in cv[s:s+t]); m[tuple(sorted(vs))]=(vs,s)
    return m
mA=corner_map(A); mB=corner_map(B); mT=corner_map(T)
rawA=A['custom_normal_i16']; rawB=B['custom_normal_i16']; rawT=T['custom_normal_i16']
# ArtDir vs FORM5 candidate: same topology/order -> compare by loop index directly
print('FORM5 cand vs ArtDir raw: same loop structure', np.array_equal(A['corner_verts'],T['corner_verts']))
dif=(rawT!=rawA).any(1); print('  loops with changed raw code:', dif.sum(), ' code1 changed:', (rawT[:,1]!=rawA[:,1]).sum(), ' code0 changed:', (rawT[:,0]!=rawA[:,0]).sum())
# base vs ArtDir through vmap: for each ArtDir face whose verts all map, find the base face with the mapped verts
n=0; same=0; diffs=[]; c7set=set(c7['moved_idx'].tolist())
inc7=lambda v: v in c7set
for key,(vs,s) in mA.items():
    mv=[int(b2f[v]) for v in vs]
    if min(mv)<0: continue
    k2=tuple(sorted(mv))
    if k2 not in mB: continue
    vsb,sb=mB[k2]
    # loop-by-loop: ArtDir loop i has vertex vs[i]; base loop with vertex b2f[vs[i]]
    pos={v:j for j,v in enumerate(vsb)}
    for i,v in enumerate(vs):
        j=pos[int(b2f[v])]
        n+=1
        if (rawA[s+i]==rawB[sb+j]).all(): same+=1
        else: diffs.append((v, any(inc7(x) for x in vs)))
print('ArtDir corners compared with base:', n, ' identical raw:', same, ' different:', len(diffs))
if diffs:
    dv=[d[0] for d in diffs]; print('   different corners whose face touches a chat-7 vert:', sum(d[1] for d in diffs), ' others:', sum(1 for d in diffs if not d[1]))
    print('   z range of vertices at differing corners:', A['V'][dv,2].min(), A['V'][dv,2].max())
