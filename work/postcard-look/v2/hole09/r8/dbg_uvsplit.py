import bpy, bmesh, math, sys
A = sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath=A[0])
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith(("DRESS_RUIN", "DRESS_ARCH")): continue
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    uv = bm.loops.layers.uv.active
    for e in bm.edges:
        if len(e.link_faces) != 2: continue
        a, b = e.link_faces
        ang = math.degrees(a.normal.angle(b.normal))
        if ang >= 12.0: continue
        d = 0.0
        for la in a.loops:
            if la.vert in e.verts:
                for lb in b.loops:
                    if lb.vert is la.vert:
                        d = max(d, (la[uv].uv - lb[uv].uv).length)
        if d > 0.000125:
            ma = me.materials[a.material_index].name; mb = me.materials[b.material_index].name
            print("MISMATCH", o.name, "ang %.2f" % ang, ma, mb, "nA", tuple(round(x,3) for x in a.normal), "nB", tuple(round(x,3) for x in b.normal), "nverts", len(a.verts), len(b.verts), "d", d, "pos", tuple(round(x,2) for x in (o.matrix_world @ e.verts[0].co)))
