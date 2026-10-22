import sys, numpy as np, bpy, pickle, hashlib
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-legs')
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
cur=sys.argv[sys.argv.index('--')+1]
V0=np.load(R+'/work/male-parallel-legs/data/V_start.npy')
bpy.ops.wm.open_mainfile(filepath=cur)
print('objects',[ (o.name,o.type) for o in bpy.data.objects])
b=bpy.data.objects['Body_M']; me=b.data; n=len(me.vertices)
V=np.empty(n*3); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
print('verts',n,'start verts',len(V0),'polys',len(me.polygons))
m=min(n,len(V0))
d=np.linalg.norm(V[:m]-V0[:m],axis=1)
mv=d>0
print('moved among first %d verts: %d'%(m,mv.sum()))
z=V0[:,2]; x=V0[:,0]
zone=(z<0.765)&(np.abs(x)<0.27)
print('moved in my zone:',(mv[:m]&zone[:m]).sum())
for name,sel in (('head z>1.43',z>1.43),('torso 0.765..1.43 |x|<0.27',(z>=0.765)&(z<=1.43)&(np.abs(x)<0.27)),('arms |x|>=0.27',np.abs(x)>=0.27)):
    print(name,'moved:',(mv[:m]&sel[:m]).sum(),'max mm %.2f'%(d[sel[:m]].max()*1000 if (mv[:m]&sel[:m]).sum() else 0))
if mv.sum():
    idx=np.nonzero(mv)[0]; print('moved z range %.3f..%.3f  x range %.3f..%.3f'%(V0[idx,2].min(),V0[idx,2].max(),V0[idx,0].min(),V0[idx,0].max()))
# faces identical?
F0=pickle.load(open(R+'/work/male-parallel-legs/data/F.pkl','rb'))
F1=[list(p.vertices) for p in me.polygons]
print('first %d faces identical:'%len(F0), F1[:len(F0)]==F0, ' total faces now',len(F1))
