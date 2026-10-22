import sys, os, math, collections
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
import postcard_props_lib as PL
hole=os.environ["HOLE"]
bpy.ops.wm.open_mainfile(filepath=R + f"/work/postcard-look/baseline/blender/hole_{hole}.blend")
leg={}
for o in PL.legacy_rocks():
    co=np.array([list(o.matrix_world@v.co) for v in o.data.vertices]); leg[o.name]=(co.min(0),co.max(0))
out=PL.swap_legacy_rocks(None,basalt=(hole=="10"),seed=2)
bpy.context.view_layer.update()
g=collections.defaultdict(list)
for o in out: g[o["lk_swap"]].append(o)
rows=[]
for k,v in g.items():
    pts=np.concatenate([np.array([list(o.matrix_world@vv.co) for vv in o.data.vertices]) for o in v])
    a,b=leg[k]; 
    rows.append((k,v[0].data.name,a[2],b[2],pts[:,2].min(),pts[:,2].max()))
d_bot=np.array([r[4]-r[2] for r in rows]); d_top=np.array([r[5]-r[3] for r in rows])
print("HOLE",hole,"n",len(rows),"bottom delta: min %.2f p10 %.2f med %.2f p90 %.2f max %.2f"%(d_bot.min(),np.percentile(d_bot,10),np.median(d_bot),np.percentile(d_bot,90),d_bot.max()))
print("      top delta: min %.2f p10 %.2f med %.2f p90 %.2f max %.2f"%(d_top.min(),np.percentile(d_top,10),np.median(d_top),np.percentile(d_top,90),d_top.max()))
w=[r for r in rows if r[5]-r[3]<-2.5 or r[5]-r[3]>2.5]
print(" tops differing >2.5m:",len(w),[(r[0],r[1],round(r[3],1),round(r[5],1)) for r in w[:5]])
