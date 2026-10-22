import sys, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy, numpy as np, bmesh
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
ob=bpy.data.objects["BUNKER_01_LIP"]; me=ob.data
V=np.array([v.co[:] for v in me.vertices])
print("verts",len(V),"z levels",sorted(set(np.round(V[:,2],3))))
print("poly sizes", sorted({len(p.vertices) for p in me.polygons}), "n tri", sum(1 for p in me.polygons if len(p.vertices)==3), "n quad", sum(1 for p in me.polygons if len(p.vertices)==4))
bm=bmesh.new(); bm.from_mesh(me)
b=[e for e in bm.edges if len(e.link_faces)==1]
print("boundary edges",len(b))
# boundary loops
import collections
adj=collections.defaultdict(list)
for e in b:
    adj[e.verts[0].index].append(e.verts[1].index); adj[e.verts[1].index].append(e.verts[0].index)
seen=set(); loops=[]
for s0 in adj:
    if s0 in seen: continue
    loop=[s0]; seen.add(s0); prev=None; cur=s0
    while True:
        nx=[v for v in adj[cur] if v!=prev and v not in seen]
        if not nx: break
        prev,cur=cur,nx[0]; seen.add(cur); loop.append(cur)
    loops.append(loop)
for l in loops: print("loop len",len(l),"z",np.round(V[l][:,2].mean(),3),"centroid",np.round(V[l][:,:2].mean(0),2))
# valence histogram
val=collections.Counter(len(v.link_faces) for v in bm.verts); print("link_faces hist",dict(val))
