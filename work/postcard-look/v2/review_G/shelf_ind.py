# independent shelf measurement: top-down first-hit categorisation on a grid, no use of the builder's helpers.
import bpy, sys, numpy as np, math, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
args = sys.argv[sys.argv.index("--")+1:]
BL = args[0]; CELL = float(args[1]) if len(args)>1 else 0.25
bpy.ops.wm.open_mainfile(filepath=BL)
dg = bpy.context.evaluated_depsgraph_get()
V=[];F=[];CAT=[];names=[]
def cat_of(n):
    if n.startswith('WATER_SHELF'): return 1
    if n.startswith('WATER_SURF'): return 2
    if n.startswith('WATER_OCEAN'): return 3
    if n.startswith('WATER_'): return 4
    return 0  # land / anything solid
for o in bpy.data.objects:
    if o.type!='MESH': continue
    if o.name.startswith(('BALL','HOLE_CUP')) : pass
    me=o.data; M=o.matrix_world
    base=len(V)
    V += [tuple(M@v.co) for v in me.vertices]
    for p in me.polygons:
        # fan triangulate
        vs=[base+i for i in p.vertices]
        for k in range(1,len(vs)-1):
            F.append((vs[0],vs[k],vs[k+1])); CAT.append(cat_of(o.name))
CAT=np.array(CAT)
bvh=BVHTree.FromPolygons(V,F)
Varr=np.array(V)
ter=[o for o in bpy.data.objects if o.name.startswith('TERRAIN')][0]
tv=np.array([tuple(ter.matrix_world@v.co) for v in ter.data.vertices])
x0,y0=tv[:,:2].min(0)-50; x1,y1=tv[:,:2].max(0)+50
xs=np.arange(x0,x1,CELL); ys=np.arange(y0,y1,CELL)
print("grid",len(xs),len(ys),len(xs)*len(ys))
G=np.full((len(ys),len(xs)),-1,np.int8)
Zt=np.zeros((len(ys),len(xs)),np.float32)
down=Vector((0,0,-1))
rc=bvh.ray_cast
import time; t=time.time()
for j,y in enumerate(ys):
    for i,x in enumerate(xs):
        h=rc(Vector((x,y,60.0)),down)
        if h[0] is not None:
            G[j,i]=CAT[h[2]]; Zt[j,i]=h[0].z
print("cast s",time.time()-t)
np.savez_compressed(BL.replace('.blend','_grid.npz'),G=G,Z=Zt,x0=x0,y0=y0,cell=CELL)
