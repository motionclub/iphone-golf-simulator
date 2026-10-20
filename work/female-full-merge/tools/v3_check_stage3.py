import numpy as np, json, collections
A=np.load('data/artdir_body.npz'); B=np.load('data/base_body.npz'); T=np.load('data/form5_body.npz'); S=np.load('data/stage3_body.npz')
vm=np.load('data/vmap_artdir_to_base.npz')['base_to_final']
dz=np.load('start/torso_form5_delta.npz'); c7=np.load('start/chat7_torso_delta.npz')
zone=dz['zone_mask'].astype(bool); border=dz['border_mask'].astype(bool); idx=dz['moved_idx']
rep={}
# topology identical to base
for k in ('corner_verts','loop_start','loop_total','material_index'): assert np.array_equal(S[k],B[k]), k
assert np.array_equal(S['uv'],B['uv'])
VS=S['V']; VB=B['V']
# 1) positions: FORM5 candidate zone == stage3 zone, bit-identical
zi=np.nonzero(zone)[0]; t=vm[zi]
rep['zone_verts']=int(len(zi)); rep['zone_pos_identical_to_FORM5_candidate']=int((VS[t]==T['V'][zi]).all(1).sum())
rep['zone_border_verts']=int(border.sum()); rep['border_at_ArtDir_original']=int((VS[vm[np.nonzero(border)[0]]]==A['V'][np.nonzero(border)[0]]).all(1).sum())
# 2) everything outside the zone unchanged vs base
mask_zone_base=np.zeros(len(VS),bool); mask_zone_base[t]=True
chg=(VS!=VB).any(1)
rep['verts_changed_vs_base']=int(chg.sum()); rep['changed_outside_zone']=int((chg&~mask_zone_base).sum())
rep['changed_verts_that_are_hand_22419_23246']=int(chg[22419:].sum())
rep['changed_z_range']=[float(VS[chg,2].min()),float(VS[chg,2].max())]
# legs: below the FORM5 floor ring z .62?
rep['changed_verts_below_z0.62(strict)']=int((chg&(VB[:,2]<0.62-1e-4)).sum())
# 3) raw custom normals vs FORM5 candidate, corner by corner via vertex identity
rawS=S['custom_normal_i16']; rawT=T['custom_normal_i16']; rawA=A['custom_normal_i16']; rawB=B['custom_normal_i16']
def cmap(d):
    ls,lt,cv=d['loop_start'],d['loop_total'],d['corner_verts']; m={}
    for s,tt in zip(ls,lt):
        vs=tuple(int(x) for x in cv[s:s+tt]); m[tuple(sorted(vs))]=(vs,s)
    return m
mT=cmap(T); mS=cmap(S)
n=0; eq=0; bad=[]
inv=-np.ones(len(VS),np.int64); inv[vm[vm>=0]]=np.nonzero(vm>=0)[0]    # base idx -> ArtDir idx
zone_corner_total=0
for key,(vs,s) in mS.items():
    art=[int(inv[v]) for v in vs]
    if min(art)<0: continue
    if not any(zone[a] for a in art): continue
    k2=tuple(sorted(art))
    if k2 not in mT: continue
    vst,st=mT[k2]; pos={v:j for j,v in enumerate(vst)}
    for i,v in enumerate(vs):
        j=pos[inv[v]]; n+=1
        if (rawS[s+i]==rawT[st+j]).all(): eq+=1
        else: bad.append(int(v))
rep['corners_of_faces_touching_zone_compared']=n; rep['raw_cn_identical_to_FORM5_candidate']=eq; rep['raw_cn_different']=len(bad)
# 4) raw changed vs base overall
dif=(rawS!=rawB).any(1); rep['raw_cn_loops_changed_vs_base']=int(dif.sum()); rep['raw_changes_code1']=int((rawS[:,1]!=rawB[:,1]).sum())
print(json.dumps(rep,indent=1)); json.dump(rep,open('data/stage3_check.json','w'),indent=1)
