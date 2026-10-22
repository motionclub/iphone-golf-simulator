import sys, os, runpy, bpy, numpy as np
REPO=os.getcwd() if os.path.isdir('blender') else "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
REPO="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0,REPO+"/blender/scripts")
import postcard_lib as P
H=sys.argv[sys.argv.index("--")+1]; BL=sys.argv[sys.argv.index("--")+2]
OUT=REPO+"/work/postcard-look/v2/review_G/_scr_"+H; os.makedirs(OUT,exist_ok=True)
_o=P.start; P.start=lambda name,out_dir=None:_o(name,out_dir=OUT)
sys.argv=[REPO+"/work/postcard-look/baseline/scripts/hole%s_build.py"%H]
try: runpy.run_path(sys.argv[0],run_name="__main__")
except SystemExit: pass
D=P._ST["D"]
ells=[]
for kind,hx,hd,w,l,tag in D.hole.hazards:
    print(kind,hx,hd,w,l,tag)
    if kind=="water":
        cx,cy=P.m(hx,hd); ells.append((cx,cy,w/2*P.YD,l/2*P.YD))
print("ELLS",ells, "play_z",D.play_z)
bpy.ops.wm.open_mainfile(filepath=BL)
from mathutils import Vector
from mathutils.bvhtree import BVHTree
Vv=[];F=[]
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith('ROCK_SKIN'): continue
    M=o.matrix_world;b=len(Vv);Vv+=[tuple(M@v.co) for v in o.data.vertices]
    for p in o.data.polygons:
        vs=[b+i for i in p.vertices]
        for k in range(1,len(vs)-1): F.append((vs[0],vs[k],vs[k+1]))
bv=BVHTree.FromPolygons(Vv,F)
tot=0;up=0;maxz=-9
for cx,cy,a,b in ells:
    for x in np.arange(cx-a,cx+a,0.25):
        for y in np.arange(cy-b,cy+b,0.25):
            e=((x-cx)/a)**2+((y-cy)/b)**2
            if e>=1: continue
            # depth proxy: inside by >0.15 m (approx via scaling)
            dd=(1-np.sqrt(e))*min(a,b)
            if dd<0.15: continue
            tot+=1
            h=bv.ray_cast(Vector((x,y,40)),Vector((0,0,-1)))
            if h[0] is not None and h[1].z>0.1: up+=1; maxz=max(maxz,h[0].z)
print("ellipse cells",tot,"covered by up-facing skin",up,"max z",maxz)
