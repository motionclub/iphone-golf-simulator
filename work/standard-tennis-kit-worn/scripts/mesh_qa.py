"""Mesh QA on the staged kit blends (+ no-logo evidence).  blender -b --factory-startup --python mesh_qa.py -> proof/mesh_qa.json"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy, bmesh
from kitlib import *

out = {}
for gender in ('male', 'female'):
    blend = f'{WORK}/export/StandardKit_{"Male" if gender == "male" else "Female"}.blend'
    bpy.ops.wm.open_mainfile(filepath=blend)
    rep = dict(objects={}, collections={c.name: [o.name for o in c.objects] for c in bpy.data.collections}, image_textures=[], material_nodes={}, non_mesh_objects=[])
    for m in bpy.data.materials:
        rep['material_nodes'][m.name] = sorted(set(n.bl_idname for n in m.node_tree.nodes)) if m.use_nodes else []
        if m.use_nodes:
            for n in m.node_tree.nodes:
                if n.bl_idname == 'ShaderNodeTexImage':
                    rep['image_textures'].append(m.name)
    rep['blend_images'] = [i.name for i in bpy.data.images if i.name not in ('Render Result', 'Viewer Node')]
    for o in bpy.data.objects:
        if o.type != 'MESH':
            rep['non_mesh_objects'].append((o.name, o.type))
            continue
        if not o.name.startswith('Kit_'):
            continue
        me = o.data
        bm = bmesh.new()
        bm.from_mesh(me)
        deg = sum(1 for f in bm.faces if f.calc_area() < 1e-10)
        loose = sum(1 for v in bm.verts if not v.link_faces)
        nonman = sum(1 for e in bm.edges if len(e.link_faces) > 2)
        bound = sum(1 for e in bm.edges if len(e.link_faces) == 1)
        # connected islands
        seen = set(); islands = 0
        for v in bm.verts:
            if v.index in seen or not v.link_faces:
                continue
            islands += 1
            stack = [v]; seen.add(v.index)
            while stack:
                a = stack.pop()
                for e in a.link_edges:
                    b = e.other_vert(a)
                    if b.index not in seen:
                        seen.add(b.index); stack.append(b)
        uv = me.uv_layers.active
        uvs = np.array([l.uv[:] for l in uv.data]) if uv else np.zeros((0, 2))
        quads = sum(1 for p in me.polygons if len(p.vertices) != 3)
        rep['objects'][o.name] = dict(tris=sum(len(p.vertices) - 2 for p in me.polygons), verts=len(me.vertices), degenerate_faces=deg, loose_verts=loose,
                                      nonmanifold_edges=nonman, boundary_edges=bound, islands=islands, non_tri_polys=quads, uv_layers=len(me.uv_layers),
                                      uv_min=uvs.min(0).round(3).tolist() if len(uvs) else None, uv_max=uvs.max(0).round(3).tolist() if len(uvs) else None,
                                      uv_nan=bool(np.isnan(uvs).any()) if len(uvs) else None, materials=[m.name for m in me.materials],
                                      custom_normals=bool(me.has_custom_normals), modifiers=len(o.modifiers), parent=o.parent.name if o.parent else None,
                                      matrix_identity=bool(np.allclose(np.array(o.matrix_world), np.eye(4))), colorway=o.get('colorway'), category=o.get('kit_category'),
                                      faces_slot0=int(sum(1 for p in me.polygons if p.material_index == 0)), faces_slot1_piping=int(sum(1 for p in me.polygons if p.material_index == 1)),
                                      slot_materials=[m.name for m in me.materials])
        bm.free()
    out[gender] = rep
json.dump(out, open(f'{WORK}/proof/mesh_qa.json', 'w'), indent=1)
for g, rep in out.items():
    print('==', g, 'image textures:', rep['image_textures'], 'blend images:', rep['blend_images'], 'non-mesh:', [n for n, t in rep['non_mesh_objects']])
    for n, o in rep['objects'].items():
        print(f"  {n:30s} tris {o['tris']:6d} deg {o['degenerate_faces']} loose {o['loose_verts']} nonman {o['nonmanifold_edges']} islands {o['islands']:3d} uv {o['uv_layers']} uv[{o['uv_min']},{o['uv_max']}] cN {o['custom_normals']} mods {o['modifiers']} I4 {o['matrix_identity']} {o['colorway']}")
