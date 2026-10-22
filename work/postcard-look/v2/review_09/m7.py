import bpy, bmesh, numpy as np, math
from mathutils import Vector
T=bpy.data.objects['TERRAIN_SPLIT']; me=T.data
mats=[m.name for m in me.materials]
bm=bmesh.new(); bm.from_mesh(me); bm.edges.ensure_lookup_table()
def top(f): return f.normal.z>0.5
segs=[]
for e in bm.edges:
    fs=e.link_faces
    if len(fs)!=2: continue
    a,b=fs
    if not(top(a) and top(b)): continue
    ma=mats[a.material_index]; mb=mats[b.material_index]
    if {ma,mb}=={'LK_SCRUB','LK_ROUGH'}:
        p=(e.verts[0].co+e.verts[1].co)/2
        segs.append((p.x,p.y,(e.verts[0].co-e.verts[1].co).length))
segs=np.array(segs); print('scrub/rough boundary edges',len(segs),'length m',segs[:,2].sum())
# also scrub next to fairway-ish (other play surfaces handled by ground meshes) -> terrain top boundary edges of scrub where only 1 face (hole punched?)
props=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('PLANT_','ROCK_','DRESS_')) and not o.hide_viewport and not o.name.startswith('ROCK_SKIN')]
P=np.array([[o.matrix_world.translation.x,o.matrix_world.translation.y, 1 if o.name.startswith(('PLANT_SHRUB','PLANT_AGAVE','ROCK_')) else 0.5] for o in props])
# Also include any prop (tufts) 
cnt=[];cntbig=[]
for x,y,l in segs:
    d=np.hypot(P[:,0]-x,P[:,1]-y)
    cnt.append((d<3).sum()); cntbig.append(((d<3)&(P[:,2]==1)).sum())
cnt=np.array(cnt);cntbig=np.array(cntbig)
for th in (1,2,3):
    print('len frac with >=%d props within 3m: %.2f ; shrubs/rocks only: %.2f'%(th,(segs[:,2]*(cnt>=th)).sum()/segs[:,2].sum(),(segs[:,2]*(cntbig>=th)).sum()/segs[:,2].sum()))
# longest bare stretch: sort segments by y, find run where cntbig==0 consecutive in proximity
idx=np.argsort(segs[:,1]); bare=0;best=0;worst_at=None;run=[]
bare_pts=segs[cntbig==0]
print('bare (no shrub/rock within 3m) total len',bare_pts[:,2].sum())
# cluster bare points by proximity
used=np.zeros(len(bare_pts),bool); clusters=[]
for i in range(len(bare_pts)):
    if used[i]: continue
    st=[i];used[i]=True;cl=[i]
    while st:
        k=st.pop()
        d=np.hypot(bare_pts[:,0]-bare_pts[k,0],bare_pts[:,1]-bare_pts[k,1])
        for j in np.where((d<8)&~used)[0]: used[j]=True;st.append(j);cl.append(j)
    clusters.append((bare_pts[cl,2].sum(),bare_pts[cl,0].mean(),bare_pts[cl,1].mean()))
clusters.sort(reverse=True); print('largest bare clusters (len,x,y):',[tuple(round(v,1) for v in c) for c in clusters[:6]])
