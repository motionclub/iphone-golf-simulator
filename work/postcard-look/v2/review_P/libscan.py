import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np, bmesh
import postcard_props_lib as PL
bpy.ops.wm.read_factory_settings(use_empty=True)
PL.ensure_library()
rows=[]
for ob in bpy.data.objects:
    if ob.type!='MESH' or not ob.name.startswith("ROCK_"): continue
    me=ob.data
    co=np.empty(len(me.vertices)*3); me.vertices.foreach_get("co",co); co=co.reshape(-1,3)
    # my own weld: round to 1mm
    w=len({tuple(np.round(c,3)) for c in co})
    me.calc_loop_triangles()
    # icosahedron-ness: count distinct vertex degrees / radial stddev
    # face normals clustering: number of distinct normals (rounded 5 deg)
    nrm=np.array([p.normal[:] for p in me.polygons]); A=np.array([p.area for p in me.polygons])
    # Detect 12-vertex-component icosahedron: connected components via vertex adjacency
    bm=bmesh.new(); bm.from_mesh(me)
    seen=set(); comps=[]
    for v in bm.verts:
        if v.index in seen: continue
        st=[v]; seen.add(v.index); n=0
        while st:
            a=st.pop(); n+=1
            for e in a.link_edges:
                b=e.other_vert(a)
                if b.index not in seen: seen.add(b.index); st.append(b)
        comps.append(n)
    bm.free()
    rows.append((ob.name,len(me.vertices),w,len(me.polygons),len(comps),min(comps)))
for r in sorted(rows,key=lambda r:r[2]): print("%-26s verts %4d weld1mm %4d faces %4d comps %3d mincomp %3d"%r)
print("min weld",min(r[2] for r in rows),"12-vert comps:",[r[0] for r in rows if r[5]<=12])
