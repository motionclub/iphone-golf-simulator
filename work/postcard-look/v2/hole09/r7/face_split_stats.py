import bpy, bmesh, numpy as np, math, collections, sys
tot=collections.Counter(); angs=[]
ex=[]
for ob in bpy.data.objects:
    if ob.type!='MESH' or not (ob.name.startswith('DRESS_RUIN_') or ob.name.startswith('DRESS_ARCH_')): continue
    bm=bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    uvl=bm.loops.layers.uv.active
    for f in bm.faces:
        tot['faces']+=1; tot['n%d'%min(len(f.verts),6)]+=1
    for e in bm.edges:
        if len(e.link_faces)==2:
            a,b=e.link_faces
            ang=math.degrees(a.normal.angle(b.normal))
            if ang<20:
                tot['near_coplanar_pairs']+=1
                angs.append(ang)
                # uv mismatch: compare uv of shared verts
                va=[l[uvl].uv.copy() for l in a.loops if l.vert in e.verts]
                vb=[l[uvl].uv.copy() for l in b.loops if l.vert in e.verts]
                # match by vert
                d=0
                for la in a.loops:
                    if la.vert in e.verts:
                        for lb in b.loops:
                            if lb.vert is la.vert:
                                d=max(d,(la[uvl].uv-lb[uvl].uv).length)
                if d>0.02: tot['near_coplanar_uv_mismatch']+=1
    bm.free()
print(dict(tot))
a=np.array(angs); print('angles: n',len(a),'median',np.median(a) if len(a) else None, 'pcts', np.percentile(a,[10,50,90,99]) if len(a) else None)
