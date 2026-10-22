import sys, numpy as np, bpy, bmesh
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
for nm in ("DRESS_PATH_01","DRESS_PATH_02"):
    ob=bpy.data.objects[nm]; me=ob.data
    bm=bmesh.new(); bm.from_mesh(me)
    co=np.array([v.co[:] for v in me.vertices])
    areas=np.array([f.calc_area() for f in bm.faces])
    nm_edges=sum(1 for e in bm.edges if len(e.link_faces)>2)
    bnd=sum(1 for e in bm.edges if len(e.link_faces)==1)
    # vertical faces
    vert=[f for f in bm.faces if abs(f.normal.z)<0.2]
    uv=bm.loops.layers.uv.active
    uvs=np.array([l[uv].uv[:] for f in bm.faces for l in f.loops])
    # uv orientation sign of top faces (nz>0.5): signed area in uv vs plan
    flips=0
    for f in bm.faces:
        if f.normal.z>0.5:
            a=sum(l[uv].uv.x*l.link_loop_next[uv].uv.y-l.link_loop_next[uv].uv.x*l[uv].uv.y for l in f.loops)
            if a<0: flips+=1
    print(nm,"verts",len(co),"faces",len(bm.faces),"nan",bool(np.isnan(co).any()),"min area",float(areas.min()),"n<1e-8",int((areas<1e-8).sum()),"nonmanifold edges",nm_edges,"boundary edges",bnd,"vertical faces",len(vert),"uv flips (top faces)",flips,"uv range",uvs.min(0).round(3).tolist(),uvs.max(0).round(3).tolist())
    for f in vert[:6]:
        print("  riser",[tuple(round(c,3) for c in v.co) for v in f.verts])
