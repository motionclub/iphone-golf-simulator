import bpy, sys, numpy as np, json
mode=sys.argv[sys.argv.index('--')+1]
out=sys.argv[sys.argv.index('--')+2]
PFX=('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER')
d={}
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith(PFX): continue
    me=o.data; mw=np.array(o.matrix_world)
    v=np.array([tuple(x.co) for x in me.vertices]); v=(mw[:3,:3]@v.T).T+mw[:3,3]
    tris=[]; 
    me.calc_loop_triangles()
    for t in me.loop_triangles:
        tris.append((tuple(t.vertices), tuple(t.normal)))
    d[o.name]=dict(v=v, polys=[list(p.vertices) for p in me.polygons], tris=tris,
       nup=[tuple(p.normal) for p in me.polygons], mats=[p.material_index for p in me.polygons])
np.save(out, d, allow_pickle=True)
