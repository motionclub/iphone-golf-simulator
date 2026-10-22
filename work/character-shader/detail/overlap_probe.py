import sys, os, numpy as np, bpy, math
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..",".."))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(ROOT,"Unity/Assets/Characters/MatchHeroKit/Male_Kit.fbx"))
o=bpy.data.objects["Kit_Top"]; m=o.data; m.calc_loop_triangles()
uvd=np.zeros(len(m.loops)*2); m.uv_layers[0].data.foreach_get("uv",uvd); UV=uvd.reshape(-1,2)
P=np.zeros(len(m.vertices)*3); m.vertices.foreach_get("co",P); P=P.reshape(-1,3)
S=512
cnt=np.zeros((S,S),dtype=np.int32); first_c=np.zeros((S,S,3)); 
tri_idx=np.full((S,S),-1,dtype=np.int64)
spread=np.zeros((S,S))
pos=np.zeros((S,S,3)); have=np.zeros((S,S),dtype=bool)
for t in m.loop_triangles:
    uv=UV[list(t.loops)]*S
    mn=np.floor(uv.min(0)).astype(int); mx=np.ceil(uv.max(0)).astype(int)
    xs,ys=np.meshgrid(np.arange(max(mn[0],0),min(mx[0],S-1)+1)+.5,np.arange(max(mn[1],0),min(mx[1],S-1)+1)+.5)
    (x0,y0),(x1,y1),(x2,y2)=uv; den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
    if abs(den)<1e-12: continue
    w0=((y1-y2)*(xs-x2)+(x2-x1)*(ys-y2))/den; w1=((y2-y0)*(xs-x2)+(x0-x2)*(ys-y2))/den; w2=1-w0-w1
    ins=(w0>=0)&(w1>=0)&(w2>=0)
    if not ins.any(): continue
    p=(w0[...,None]*P[t.vertices[0]]+w1[...,None]*P[t.vertices[1]]+w2[...,None]*P[t.vertices[2]])
    iy=(ys[ins]-.5).astype(int); ix=(xs[ins]-.5).astype(int)
    for a,b,pp in zip(iy,ix,p[ins]):
        if have[a,b]:
            spread[a,b]=max(spread[a,b],np.linalg.norm(pos[a,b]-pp))
        else: pos[a,b]=pp; have[a,b]=True
        cnt[a,b]+=1
print("covered texels",have.sum(),"with >1 tri",(cnt>1).sum(), "with 3D spread>2cm",(spread>0.02).sum(), "max spread",spread.max().round(3))
ys,xs=np.nonzero(spread>0.02)
print("OVERLAP sample (u,v,spread):",[(round(x/S,3),round(y/S,3),round(spread[y,x],3)) for x,y in list(zip(xs,ys))[::max(1,len(xs)//8)]][:8])
