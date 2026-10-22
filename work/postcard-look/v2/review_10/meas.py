import bpy, bmesh, sys, math, collections, json
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import numpy as np
out={}
base=sys.argv[sys.argv.index('--')+1]
cur={o.name:o for o in bpy.data.objects}
# load baseline
with bpy.data.libraries.load(base) as (df,dt):
    dt.objects=df.objects
bobj={}
for o in dt.objects:
    if o: bobj[o.name[:-4] if o.name.endswith('.001') else o.name]=o
PL=('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER')
def names(d): return sorted(n for n in d if n.startswith(PL) )
print("PLAY names base",names(bobj)); print("cur",names({n:o for n,o in cur.items() if o.name in cur}))
def ws(o):
    mw=o.matrix_world
    return np.array([ (mw@v.co)[:] for v in o.data.vertices])
def upfaces(o):
    mw=o.matrix_world; s=set()
    me=o.data
    for p in me.polygons:
        n=(mw.to_3x3()@p.normal)
        if n.z>0.5:
            vs=tuple(sorted(tuple(np.round((mw@me.vertices[i].co)[:],4)) for i in p.vertices))
            s.add(vs)
    return s
maxd=0;bad=[]
for n in names(bobj):
    b=bobj[n]; c=cur.get(n)
    if c is None: bad.append(('missing',n)); continue
    vb=ws(b); vc=ws(c)
    if len(vb)!=len(vc): bad.append(('vcount',n,len(vb),len(vc))); continue
    d=np.abs(vb-vc).max(); maxd=max(maxd,d)
    fb=upfaces(b); fc=upfaces(c)
    if fb!=fc: bad.append(('upfaces',n,len(fb),len(fc)))
    if len(b.data.polygons)!=len(c.data.polygons): bad.append(('polys',n))
print("PLAY maxdelta",maxd,"bad",bad)
extra=[n for n in cur if n.startswith(PL) and n not in bobj]
print("extra collision-prefixed",extra)
# also marker placeholders
for n in ('MARKER_PIN','MARKER_TEE','BALL_START','HOLE_CUP','FLAG','FLAG_POLE'):
    if n in bobj and n in cur:
        print(n,(bobj[n].matrix_world.translation-cur[n].matrix_world.translation).length)
