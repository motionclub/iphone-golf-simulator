import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import os
def obj_bvh(ob):
    me=ob.data; me.calc_loop_triangles()
    verts=[v.co.copy() for v in me.vertices]
    tr=[(lt.vertices[:], lt.loops[:]) for lt in me.loop_triangles]
    return me, verts, tr, BVHTree.FromPolygons(verts,[t[0] for t in tr])
def uv_at(ob, pack, x, y):
    me,verts,tr,bvh=pack
    uv=me.uv_layers[0].data
    loc,n,idx,d=bvh.ray_cast(Vector((x,y,50)),Vector((0,0,-1)))
    if loc is None: return None
    vi,li=tr[idx]
    a,b,c=[verts[i] for i in vi]
    T=np.array([[a.x-c.x,b.x-c.x],[a.y-c.y,b.y-c.y]]); r=np.array([x-c.x,y-c.y])
    l1,l2=np.linalg.solve(T,r); l3=1-l1-l2
    return l1*np.array(uv[li[0]].uv)+l2*np.array(uv[li[1]].uv)+l3*np.array(uv[li[2]].uv), n, (me,li)
fw=bpy.data.objects['FAIRWAY']; tb=bpy.data.objects['TEE_BOX']
pf=obj_bvh(fw); pt=obj_bvh(tb)
img=bpy.data.images.load('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/Fairway_C.png')
W,H=img.size; a=np.empty(W*H*4,np.float32); img.pixels.foreach_get(a); a=a.reshape(H,W,4)
def tex(u,v):
    x=(u%1.0)*W; y=(v%1.0)*H
    return a[int(y)%H,int(x)%W,:3]
print('img',W,H)
# step across the tee far edge at several x
for x in np.linspace(-4,4,9):
    # find tee box far edge y at this x
    ys=np.linspace(5.0,7.5,251)
    last=None
    for y in ys:
        r=uv_at(tb,pt,x,y)
        if r is None: break
        last=y
    yb=last
    rin=uv_at(tb,pt,x,yb-0.05); rout=uv_at(fw,pf,x,yb+0.15)
    rfin=uv_at(fw,pf,x,yb-0.05)
    # normals (geometric)
    print('x %.1f edge y %.2f'%(x,yb),'tex in',tex(*rin[0]).round(3),'tex out',tex(*rout[0]).round(3),'fw-under-tee tex',tex(*rfin[0]).round(3), 'uv in',rin[0].round(3),'uv fw at same',rfin[0].round(3))
