import bpy, sys, math, collections, numpy as np
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import hole08_design as D, postcard_check as PC
H=PC.Hole(D); YD=0.9144
def wv(o):
    M=np.array(o.matrix_world); V=np.array([v.co[:] for v in o.data.vertices]).reshape(-1,3); return (np.c_[V,np.ones(len(V))]@M.T)[:,:3]
shore=np.array(D.SHORE)*YD
def dist_poly(p):
    a=shore; b=np.roll(shore,-1,0); ab=b-a; ap=p[None]-a
    t=np.clip((ap*ab).sum(1)/(ab*ab).sum(1),0,1); d=np.linalg.norm(p[None]-(a+ab*t[:,None]),axis=1); return d.min()
def inside(p): return H.on_land((p[0]/YD,p[1]/YD))
# also water ellipses: scoring water inside ellipses
for nm in ('WATER_SHELF','WATER_OCEAN'):
    o=bpy.data.objects[nm]; V=wv(o); print(nm,len(V),'z range',V[:,2].min(),V[:,2].max(),'bbox',V.min(0).round(1),V.max(0).round(1))
    me=o.data; print(' faces',len(me.polygons),'area', sum(p.area for p in me.polygons))
o=bpy.data.objects['WATER_SHELF']; V=wv(o); me=o.data
# face-wise: outside-of-shore distance of face centroids; shelf is a ring so verts either hug the shore (d~0) or at outer edge
ds=[];
for p in me.polygons:
    c=V[list(p.vertices)].mean(0)
    if inside(c): ds.append(-1); continue
    ds.append(dist_poly(c[:2]))
ds=np.array(ds); out=ds[ds>=0]
print('shelf faces',len(ds),'inside shore polygon',int((ds<0).sum()),'outside dist: median %.2f p90 %.2f p95 %.2f max %.2f'%(np.median(out),np.percentile(out,90),np.percentile(out,95),out.max()))
vd=np.array([dist_poly(v[:2]) if not inside(v) else 0 for v in V]); print('verts dist p50 %.2f p95 %.2f max %.2f'%(np.median(vd),np.percentile(vd,95),vd.max()))
# shelf colour? material
print([ (m.name, m.node_tree is not None) for m in o.data.materials if m])
# surf runs: for each WATER_SURF object compute centroid along shore, arc length extents
shore_cum=np.r_[0,np.cumsum(np.linalg.norm(np.roll(shore,-1,0)-shore,axis=1))]; L=shore_cum[-1]
print('shore perimeter m',L, 'ymax',shore[:,1].max())
sf=[ob for ob in bpy.data.objects if ob.name.startswith('WATER_SURF')]
tot=0
for ob in sf:
    Vv=wv(ob); print(ob.name,'z',round(Vv[:,2].min(),2),round(Vv[:,2].max(),2),'bbox m',(Vv.max(0)-Vv.min(0)).round(1), 'area %.1f'%sum(p.area for p in ob.data.polygons))
    tot+=sum(p.area for p in ob.data.polygons)
print('surf total area',tot)
