"""Build the Classic racket in Blender (headless) from racket_geom.py and save export/Racket_Classic.blend.
blender -b --factory-startup --python build_racket.py [-- out.blend]"""
import sys, json, importlib
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import racket_geom as G
importlib.reload(G)

MATS = {   # name: (sRGB hex, roughness)  -- URP Lit equivalents: smoothness = 1 - roughness, metallic 0
    'White_Frame': ('#EEEDEA', 0.50),
    'White_Strings': ('#E8E7E3', 0.55),
    'Black_Grip': ('#1C1C1F', 0.78),
}


def make_material(name):
    hexc, rough = MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    rgb = hex_rgb(hexc)
    n = m.node_tree.nodes['Principled BSDF']
    n.inputs['Base Color'].default_value = (*lin(rgb), 1)
    n.inputs['Roughness'].default_value = rough
    n.inputs['Metallic'].default_value = 0.0
    if 'Specular IOR Level' in n.inputs:
        n.inputs['Specular IOR Level'].default_value = 0.35
    m.diffuse_color = (*lin(rgb), 1)
    m.roughness = rough
    m.metallic = 0.0
    m.blend_method = 'OPAQUE' if hasattr(m, 'blend_method') else None
    return m


def mesh_obj(name, verts, faces, mat=None, smooth=True, parent=None, sharp_angle=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in np.asarray(verts, float)], [], [tuple(int(i) for i in f) for f in faces])
    me.update(calc_edges=True)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if sharp_angle is not None:
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > sharp_angle:
                e.smooth = False
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set('use_smooth', [smooth] * len(me.polygons))
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if mat is not None:
        me.materials.append(mat)
    if parent is not None:
        o.parent = parent
    return o


def build(out_blend, params=None):
    reset_scene()
    p = dict(G.P)
    if params:
        p.update(params)
    mats = {k: make_material(k) for k in MATS}
    # socket template: the racket sits under Hand_Racket with an identity local transform
    sock = bpy.data.objects.new('Hand_Racket', None)
    sock.empty_display_type = 'ARROWS'
    sock.empty_display_size = 0.05
    bpy.context.scene.collection.objects.link(sock)

    import sdf_tools as S
    V, T, finfo = G.build_frame_sdf(p, h=p['sdf_h'], k=p['sdf_k'])
    frame = mesh_obj('Racket_Classic', V, T, mats['White_Frame'], parent=sock)
    n_raw = len(frame.data.polygons)
    mod = frame.modifiers.new('Decimate', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = min(1.0, p['frame_target_tris'] / n_raw)
    mod.use_collapse_triangulate = True
    mod.use_symmetry = True
    mod.symmetry_axis = 'X'
    bpy.context.view_layer.update()
    ev = frame.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me2 = bpy.data.meshes.new_from_object(ev)
    frame.modifiers.remove(mod)
    old = frame.data
    frame.data = me2
    bpy.data.meshes.remove(old)
    me2.materials.clear()
    me2.materials.append(mats['White_Frame'])
    me2.polygons.foreach_set('use_smooth', [True] * len(me2.polygons))
    # analytic normals from the SDF gradient (smooth regardless of the decimated triangulation)
    co = mesh_co(frame)
    for _ in range(3):                                   # pull the decimated vertices back onto the SDF iso-surface
        dd = S.sample(finfo['F'], finfo['gridobj'], co)
        gg = S.gradient(finfo['F'], finfo['gridobj'], co)
        co = co - dd[:, None] * gg / np.maximum(np.linalg.norm(gg, axis=1, keepdims=True), 1e-9)
    me2.vertices.foreach_set('co', co.ravel())
    gdir = S.gradient(finfo['F'], finfo['gridobj'], co)
    gdir /= np.maximum(np.linalg.norm(gdir, axis=1, keepdims=True), 1e-9)
    me2.normals_split_custom_set_from_vertices([tuple(x) for x in gdir])
    me2.update()
    finfo['raw_tris'] = n_raw
    finfo.pop('F'); finfo.pop('gridobj')
    sv, sf, sinfo = G.build_strings(p)
    strings = mesh_obj('StringBed', sv, sf, mats['White_Strings'], parent=frame)
    gv, gf, ginfo = G.build_grip(p)
    grip = mesh_obj('Grip', gv, gf, mats['Black_Grip'], parent=frame, sharp_angle=np.radians(38))
    bv, bf = G.build_butt_cap(p)
    cap = mesh_obj('ButtCap', bv, bf, mats['Black_Grip'], parent=frame, sharp_angle=np.radians(38))
    cv, cf = G.build_collider(p)
    col = mesh_obj('Collider_Racket', cv, cf, None, parent=frame, smooth=False)
    col.display_type = 'WIRE'
    col.hide_render = True
    for o in (frame, strings, grip, cap, col):
        o.matrix_parent_inverse.identity()

    bpy.context.view_layer.update()
    info = dict(params=p, frame=dict(a=finfo['a'], b=finfo['b'], yc=finfo['yc'], arms=finfo['arms'], raw_tris=finfo['raw_tris'], grid=finfo['grid']), strings=sinfo, grip=ginfo)
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend))
    return info


if __name__ == '__main__':
    a = args_after_dashes()
    out = Path(a[0]) if a else WORK / 'export' / 'Racket_Classic.blend'
    info = build(out)
    (WORK / 'data' / 'build_info.json').write_text(json.dumps(info, indent=1, default=float))
    tris = {}
    for o in bpy.data.objects:
        if o.type == 'MESH':
            tris[o.name] = int(sum(len(p.vertices) - 2 for p in o.data.polygons))
    print('BUILD_DONE', out, tris)
