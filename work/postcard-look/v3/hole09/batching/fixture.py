"""Whole-stone batching preservation proof; all output remains in v3."""
import os, sys, json, hashlib
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, ROOT+'/blender/scripts')
import bpy, numpy as np
import postcard_lib as P
import postcard_look_lib as L
import hole09_masonry as HM
import postcard_look_verify as V
import types
OUT=os.path.dirname(__file__)
SOURCE=ROOT+'/work/postcard-look/v3/lib/masonry/after/fixture.blend'

def snapshot(objects):
    faces={}; edges=[]; verts=0; polys=0; tris=0
    for ob in objects:
        me=ob.data; mw=np.asarray(ob.matrix_world, float)
        co=np.asarray([tuple(v.co) for v in me.vertices], float)
        world=co@mw[:3,:3].T+mw[:3,3]
        nm=np.linalg.inv(mw[:3,:3]).T
        ns=np.asarray([tuple(n.vector) for n in me.corner_normals],float)@nm.T
        ns/=np.maximum(np.linalg.norm(ns,axis=1)[:,None],1e-12)
        for p in me.polygons:
            loops=list(p.loop_indices)
            uv=tuple((l.name,tuple(tuple(l.data[i].uv) for i in loops)) for l in me.uv_layers)
            key=(tuple(tuple(world[i]) for i in p.vertices), uv, me.materials[p.material_index].name,p.use_smooth)
            if key in faces: raise RuntimeError('duplicate polygon signature in fixture')
            faces[key]=ns[loops]
        for e in me.edges:
            edges.append((tuple(sorted(tuple(world[i]) for i in e.vertices)),e.use_edge_sharp,e.use_seam))
        me.calc_loop_triangles()
        verts+=len(me.vertices); polys+=len(me.polygons); tris+=len(me.loop_triangles)
    return dict(faces=faces,edges=sorted(edges),vertices=verts,polygons=polys,triangles=tris)

results=[]
for cap in (490,3000):
    out=OUT+f'/faces{cap}'; os.makedirs(out,exist_ok=True)
    D=P.start('hole09_design',out_dir=out)
    bpy.ops.wm.open_mainfile(filepath=SOURCE,load_ui=False)
    original=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('DRESS_RUIN','DRESS_ARCH'))]
    D.objects={o.name:o for o in bpy.data.objects if o.type=='MESH'}
    D.look_objects=[o.name for o in original]
    before=snapshot(original)
    S=V.Snap('blend',types.SimpleNamespace(tag='09'))
    block_before=V.masonry_blocks(S,{o.name:o for o in original})
    groups=[]
    category_sources={k:[o for o in original if o.name.startswith(k)] for k in ('DRESS_RUIN','DRESS_ARCH')}
    for category in ('DRESS_RUIN','DRESS_ARCH'):
        ob=category_sources[category]
        groups.append(HM.merge_static_masonry(D,ob,max_faces=cap,max_span_m=12.0))
    merged=[o for r in groups for o in r['objects']]
    after=snapshot(merged)
    keys_ok=before['faces'].keys()==after['faces'].keys()
    normal_delta=max((float(np.abs(before['faces'][k]-after['faces'][k]).max()) for k in before['faces'] if k in after['faces']),default=0.)
    S2=V.Snap('blend',types.SimpleNamespace(tag='09'))
    block_after=V.masonry_blocks(S2,{o.name:o for o in merged})
    material_ok,material_detail=V.g_prop_mats(S2,None)
    budget_ok,budget_detail=V.g_prop_budget(S2,None)
    # Export neutral support ground as part of this isolated positive fixture.
    ground=bpy.data.objects.get('TERRAIN_fixture')
    if ground:
        mw=ground.matrix_world.copy(); ground.parent=merged[0].parent; ground.matrix_world=mw
        P.link_to(ground,'COURSE')
    blend=out+'/fixture.blend'
    bpy.ops.wm.save_as_mainfile(filepath=blend,relative_remap=False)
    L.export_look_fbx(D)
    row=dict(max_faces=cap,source=SOURCE,
             before_objects=len(original),after_objects=len(merged),
             vertices=[before['vertices'],after['vertices']],polygons=[before['polygons'],after['polygons']],
             triangles=[before['triangles'],after['triangles']],
             polygon_coordinates_uv_material_smooth_exact=keys_ok,
             edge_sharp_seam_exact=before['edges']==after['edges'],normal_max_abs_delta=normal_delta,
             masonry_blocks=[block_before,block_after],material_gate=dict(ok=material_ok,detail=material_detail),
             prop_budget=dict(ok=budget_ok,detail=budget_detail),groups=[r['stats'] for r in groups],
             pieces=[p for r in groups for p in r['pieces']])
    row['pass']=bool(keys_ok and before['edges']==after['edges'] and normal_delta<=1e-6
                      and all(before[k]==after[k] for k in ('vertices','polygons','triangles'))
                      and block_before==block_after and material_ok and budget_ok)
    results.append(row)
    with open(out+'/preservation.json','w') as f:json.dump(row,f,indent=2)
    print(f"GATE: MASONRY_BATCH_PRESERVATION {'PASS' if row['pass'] else 'FAIL'} faces{cap}: "
          f"{len(original)} -> {len(merged)} renderers; coords/UV/material {keys_ok}, normaldelta {normal_delta:g}",flush=True)
with open(OUT+'/results.json','w') as f:json.dump(results,f,indent=2)
sys.exit(0 if all(r['pass'] for r in results) else 1)
