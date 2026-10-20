"""Define the female TORSO vertex zone (chest -> waist/pelvis shell) on the start mesh.
Writes data/zone.npz : flags + weights.  Pure numpy.
Rules (documented in FEMALE_TORSO_RESULTS.md):
  z_crotch = 0.795  (legs separate below: 2 components)   -> legs excluded
  z_top    = 1.37   (neck base; above = head/neck chat 6) -> head/neck excluded
  arms: below armpit z<1.165 -> separate connected components; above -> |x| > X_B(z)
"""
import numpy as np
d=np.load('data/start.npz'); co=d['co']; ed=d['edges']; n=len(co)
Z_C=0.795; Z_ARMPIT=1.165; Z_TOP=1.37
# ---- connected components inside the band Z_C <= z <= Z_ARMPIT
inband=(co[:,2]>=Z_C)&(co[:,2]<=Z_ARMPIT)
par=np.arange(n)
def find(a):
    while par[a]!=a:
        par[a]=par[par[a]]; a=par[a]
    return a
for a,b in ed:
    if inband[a] and inband[b]:
        ra,rb=find(a),find(b)
        if ra!=rb: par[rb]=ra
roots=np.array([find(i) if inband[i] else -1 for i in range(n)])
ids,cnt=np.unique(roots[inband],return_counts=True)
comps=sorted(zip(cnt,ids),reverse=True)
print("band components (count, mean|x|):",[(int(c),round(float(np.abs(co[roots==i,0]).mean()),3)) for c,i in comps[:6]])
torso_root=comps[0][1]
# confirm biggest comp is central
assert np.abs(co[roots==torso_root,0]).mean()<0.1
band_torso=(roots==torso_root)
band_arm=inband&~band_torso
# ---- above armpit: lateral plane X_B(z)
def XB(z):
    z=np.asarray(z)
    return np.where(z<=1.28,0.124,np.where(z>=1.34,0.17,0.124+(z-1.28)/(0.06)*(0.17-0.124)))
above=(co[:,2]>Z_ARMPIT)&(co[:,2]<Z_TOP)
above_torso=above&(np.abs(co[:,0])<=XB(co[:,2]))
above_arm=above&~above_torso
torso=band_torso|above_torso
arm=band_arm|above_arm
# arm verts also exist below Z_C (hands) and torso-height arm verts at z>=Z_TOP? (none at z>=1.37 beyond neck) keep as non-zone.
print("torso zone verts:",int(torso.sum()),"arm-ish verts in band:",int(arm.sum()))
# ---- weights
def sstep(t): t=np.clip(t,0,1); return t*t*(3-2*t)
wz=sstep((co[:,2]-Z_C)/0.045)*sstep((Z_TOP-co[:,2])/0.06)
# distance to nearest arm vertex (any z in [0.7,1.45] arm verts incl. hands) -> lateral taper near arm junction
armset=co[arm]
tz=co[torso]
dist=np.full(n,9.0)
idx=np.where(torso)[0]
for s in range(0,len(idx),512):
    sub=co[idx[s:s+512]]
    dd=np.sqrt(((sub[:,None,:]-armset[None,:,:])**2).sum(2)).min(1)
    dist[idx[s:s+512]]=dd
warm=sstep(dist/0.03)
w=np.where(torso,wz*warm,0.0)
print("w>0:",int((w>0).sum()),"w>0.99:",int((w>0.99).sum()),"zone z-range:",co[torso,2].min().round(3),co[torso,2].max().round(3))
np.savez('data/zone.npz',torso=torso,arm=arm,w=w,wz=wz,warm=warm,dist=dist)
