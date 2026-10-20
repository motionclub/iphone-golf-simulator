import bpy, numpy as np, sys
a=sys.argv[sys.argv.index('--')+1:]
def coords(p):
    bpy.ops.wm.open_mainfile(filepath=p); me=bpy.data.objects['Body_M'].data
    V=np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co',V); return V.reshape(-1,3).astype(np.float32)
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-arms/'
V0=np.load(W+'data/mesh_start.npz')['V'].astype(np.float32)
Vt=coords(a[0]); Vm=np.load(W+'data/final_cur.npy')
mt=(Vt!=V0).any(1); mm=(Vm!=V0).any(1)
print('theirs moved',mt.sum(),'mine moved',mm.sum(),'overlap',(mt&mm).sum())
zone=np.load(W+'data/zone.npy')
print('theirs in my zone',(mt&zone).sum())
idx=np.nonzero(mt&zone)[0]
if len(idx):
    from numpy import array
    print('their moved verts inside my zone: x range',V0[idx,0].min(),V0[idx,0].max(),'z',V0[idx,2].min(),V0[idx,2].max())
    import sys
    sys.path.insert(0,W)
    import quality
    t=np.where(V0[idx,0]>0,quality.arm_t(V0[idx].astype(float),+1),quality.arm_t(V0[idx].astype(float),-1)); print('arm t range',t.min(),t.max())
