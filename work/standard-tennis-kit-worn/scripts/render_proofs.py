"""Proof renders from the assembled worn-kit blends.
blender -b --factory-startup --python render_proofs.py -- <male|female> <mode>
modes: onbody | waist | hem | exploded | ids | liner_mask | sections | clearance
Raw cells go to proof/raw/ and are composed into sheets by compose_proofs.py (system python + Pillow)."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector
from kitlib import *
import render_setup as rs
from preview_common import material

RAW = f'{WORK}/proof/raw'
os.makedirs(RAW, exist_ok=True)
SKIN = (0.80, 0.60, 0.46)
LIFT = {'male': 0.0285, 'female_authority': 0.0235, 'female_arms_candidate': 0.0245}
BLEND = {'male': f'{WORK}/export/StandardKit_Male.blend', 'female': f'{WORK}/export/StandardKit_Female.blend'}
BODY = {'male': 'FitRef_Body_M', 'female': 'FitRef_Body_F'}
BAND_Z = {'male': (0.925, 0.965), 'female': (0.955, 0.995)}


def load(gender):
    bpy.ops.wm.open_mainfile(filepath=BLEND[gender])
    return bpy.data.objects


def kit_meshes(cw, alt=False):
    cname = f'Kit_{cw}' + ('_FitArmsCand' if alt else '')
    return [o for o in bpy.data.collections[cname].objects if o.type == 'MESH']


def cat(o):
    return o.get('kit_category')


def show_only(objs):
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.name.startswith('Studio_'):
            o.hide_render = o not in objs
            o.hide_viewport = o.hide_render


def skin_body(gender):
    body = bpy.data.objects[BODY[gender]]
    body.data.materials.clear()
    body.data.materials.append(material('Body_skin', SKIN, .55, .3))
    return body


def lift_of(gender, alt=False):
    return LIFT['male'] if gender == 'male' else LIFT['female_arms_candidate' if alt else 'female_authority']


def set_lift(objs, dz):
    for o in objs:
        o.location.z = dz


def render_onbody(gender):
    load(gender)
    skin = skin_body(gender)
    rs.setup(samples=48)
    views = (('front', 0, 3), ('back', 180, 3), ('left', -90, 3), ('right', 90, 3), ('q3', 38, 4))
    variants = [('authority' if gender == 'female' else 'authority', False)]
    if gender == 'female':
        variants.append(('arms_candidate', True))
    for tag, alt in variants:
        body = bpy.data.objects[BODY[gender]]
        if alt:
            body = bpy.data.objects['FitRef_Body_F_ArmsCandidate']
            body.hide_render = False
            body.data.materials.clear()
            body.data.materials.append(material('Body_skin', SKIN, .55, .3))
        for cw in ('White', 'Black'):
            kit = [o for o in kit_meshes(cw) if cat(o) in ('Top', 'Bottom')] + ([o for o in kit_meshes(cw, True)] if alt else [o for o in kit_meshes(cw) if cat(o) in ('Sock', 'Shoe')])
            show_only(kit + [body])
            body.hide_render = False
            lift = lift_of(gender, alt)
            set_lift(kit + [body], lift)
            for nm, az, el in views:
                rs.shot(f'{RAW}/onbody_{gender}_{tag}_{cw}_{nm}.png', (0, -0.05, 0.86 + lift), az, el, dist=6.4, lens=105, res=(560, 800))
            set_lift(kit + [body], 0.0)
    print('onbody done')


def render_waist(gender):
    load(gender)
    skin_body(gender)
    rs.setup(samples=64)
    body = bpy.data.objects[BODY[gender]]
    zc = 0.5 * sum(BAND_Z[gender]) + 0.0
    lift = lift_of(gender)
    for cw in ('White', 'Black'):
        kit = [o for o in kit_meshes(cw) if cat(o) in ('Top', 'Bottom')]
        show_only(kit + [body])
        body.hide_render = False
        set_lift(kit + [body], lift)
        # wide waist view (front, 3/4, side, back) + tight overlap close-ups (front, side, back low, front-low)
        for nm, az, el, dist, lens in (('front', 0, 4, 2.6, 85), ('q3', 38, 6, 2.6, 85), ('side', 90, 4, 2.6, 85), ('back', 180, 4, 2.6, 85),
                                       ('c_front', 0, 3, 1.15, 85), ('c_side', 90, 3, 1.15, 85), ('c_back', 180, 3, 1.15, 85), ('c_q3', 40, 10, 1.15, 85)):
            rs.shot(f'{RAW}/waist_{gender}_{cw}_{nm}.png', (0, -0.04, zc + lift), az, el, dist=dist, lens=lens, res=(560, 560))
        set_lift(kit + [body], 0.0)
    print('waist done')


def render_hem(gender):
    """female: skirt hem close-ups (front, back, side, 3/4, low-angle) - the built-in shorts must not show."""
    load(gender)
    skin_body(gender)
    rs.setup(samples=64)
    body = bpy.data.objects[BODY[gender]]
    lift = lift_of(gender)
    for cw in ('White', 'Black'):
        kit = [o for o in kit_meshes(cw) if cat(o) in ('Top', 'Bottom')]
        show_only(kit + [body])
        body.hide_render = False
        set_lift(kit + [body], lift)
        for nm, az, el in (('front', 0, 3), ('back', 180, 3), ('left', -90, 3), ('right', 90, 3), ('q3f', 35, 4), ('q3b', 215, 4), ('low_front', 20, -2), ('low_back', 200, -2)):
            rs.shot(f'{RAW}/hem_{gender}_{cw}_{nm}.png', (0, 0.0, 0.70 + lift), az, el, dist=2.0, lens=85, res=(560, 640))
        set_lift(kit + [body], 0.0)
    print('hem done')


PIECE_COLORS = {'Top': (0.20, 0.45, 1.0), 'Bottom': (0.12, 0.75, 0.35), 'Sock': (0.98, 0.78, 0.15), 'Shoe': (0.75, 0.30, 0.90)}
EXPLODE_DZ = {'Top': 0.22, 'Bottom': 0.10, 'Sock': -0.02, 'Shoe': -0.20}


def render_exploded(gender):
    load(gender)
    rs.setup(samples=48)
    rs.set_floor_z(-0.42)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith('FitRef'):
            o.hide_render = True
    for cw in ('White', 'Black'):
        kit = kit_meshes(cw)
        show_only(kit)
        for o in kit:
            o.location.z = EXPLODE_DZ[cat(o)]
        for nm, az, el in (('front', 0, 4), ('q3', 38, 8), ('back', 180, 4)):
            rs.shot(f'{RAW}/exploded_{gender}_{cw}_{nm}.png', (0, -0.05, 0.66), az, el, dist=6.4, lens=105, res=(620, 880))
        for o in kit:
            o.location.z = 0.0
    print('exploded done')


def render_ids(gender):
    """flat object-id colours on the body: every piece is its own object; the band (slot 2) and the liner are tinted so the layering reads."""
    load(gender)
    skin = skin_body(gender)
    rs.setup(samples=32)
    body = bpy.data.objects[BODY[gender]]
    lift = lift_of(gender)
    ids = {k: material('ID_' + k, v, .9, .0) for k, v in PIECE_COLORS.items()}
    band_mat = material('ID_Band', (1.0, 0.45, 0.05), .9, .0)
    liner_mat = material('ID_Liner', (1.0, 0.0, 0.8), .9, .0)
    kit = kit_meshes('White')
    for o in kit:
        me = o.data
        idx = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get('material_index', idx)           # read BEFORE clear(): clearing the slots resets every face to slot 0 (the band would be lost)
        me.materials.clear()
        for m in (ids[cat(o)], ids[cat(o)], band_mat, liner_mat):
            me.materials.append(m)
        me.polygons.foreach_set('material_index', idx)
        if cat(o) == 'Bottom':
            tags = json.loads(me['kit_tagnames'])
            tv = np.zeros(len(me.polygons), np.int32)
            me.attributes['kit_tag'].data.foreach_get('value', tv)
            liner_ids = [i for i, t in enumerate(tags) if t.startswith('liner')]
            idx = np.where(np.isin(tv, liner_ids), 3, idx)
            me.polygons.foreach_set('material_index', idx)
    show_only(kit + [body])
    body.hide_render = False
    set_lift(kit + [body], lift)
    for nm, az, el in (('front', 0, 3), ('q3', 38, 4), ('side', 90, 3), ('back', 180, 3)):
        rs.shot(f'{RAW}/ids_{gender}_{nm}.png', (0, -0.05, 0.86 + lift), az, el, dist=6.4, lens=105, res=(560, 800))
    # the same with the body ghosted out: only the garments
    body.hide_render = True
    for nm, az, el in (('front', 0, 3), ('q3', 38, 4)):
        rs.shot(f'{RAW}/ids_nobody_{gender}_{nm}.png', (0, -0.05, 0.86 + lift), az, el, dist=6.4, lens=105, res=(560, 800))
    set_lift(kit + [body], 0.0)
    print('ids done')


def render_liner_mask(gender):
    """SKIRT_COVERS evidence: the liner (inner shorts) is painted pure magenta (emission), everything else is rendered normally.  Counting magenta
    pixels in the final images: 0 = the liner never shows.  Positive control: the same view with the skirt + flap hidden shows the magenta liner."""
    load(gender)
    skin_body(gender)
    rs.setup(samples=32)
    sc = bpy.context.scene
    sc.view_settings.view_transform = 'Standard'
    body = bpy.data.objects[BODY[gender]]
    lift = lift_of(gender)
    mag = bpy.data.materials.new('MASK_Liner')
    mag.use_nodes = True
    nt = mag.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (1.0, 0.0, 1.0, 1.0)
    em.inputs['Strength'].default_value = 1.0
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0], out.inputs[0])
    res = {}
    for cw in ('White', 'Black'):
        kit = kit_meshes(cw)
        bottom = [o for o in kit if cat(o) == 'Bottom'][0]
        top = [o for o in kit if cat(o) == 'Top'][0]
        me = bottom.data
        orig_slots = [m for m in me.materials]
        me.materials.append(mag)
        mi = len(me.materials) - 1
        idx = np.zeros(len(me.polygons), np.int32)
        me.polygons.foreach_get('material_index', idx)
        tv = np.zeros(len(me.polygons), np.int32)
        me.attributes['kit_tag'].data.foreach_get('value', tv)
        tags = json.loads(me['kit_tagnames'])
        liner_ids = [i for i, t in enumerate(tags) if t.startswith('liner')]
        liner_mask = np.isin(tv, liner_ids)
        idx0 = idx.copy()
        me.polygons.foreach_set('material_index', np.where(liner_mask, mi, idx))
        show_only([o for o in kit if cat(o) in ('Top', 'Bottom')] + [body])
        body.hide_render = False
        set_lift([o for o in kit if cat(o) in ('Top', 'Bottom')] + [body], lift)
        views = []
        for az in range(0, 360, 30):
            for el in (-12, 0, 8, 22):
                views.append((f'a{az:03d}_e{el:+03d}', az, el))
        for nm, az, el in views:
            rs.shot(f'{RAW}/mask_{gender}_{cw}_{nm}.png', (0, 0.0, 0.80 + lift), az, el, dist=3.0, lens=85, res=(480, 560))
        # positive control: hide skirt + flap (everything of the bottom except the liner) by moving the non-liner faces to a hidden slot
        clear = bpy.data.materials.new('MASK_Clear')
        clear.use_nodes = True
        for n in list(clear.node_tree.nodes):
            clear.node_tree.nodes.remove(n)
        tr = clear.node_tree.nodes.new('ShaderNodeBsdfTransparent')
        o2 = clear.node_tree.nodes.new('ShaderNodeOutputMaterial')
        clear.node_tree.links.new(tr.outputs[0], o2.inputs[0])
        me.materials.append(clear)
        ci = len(me.materials) - 1
        me.polygons.foreach_set('material_index', np.where(liner_mask, mi, ci))
        sc.render.film_transparent = False
        for nm, az, el in (('ctl_front', 0, 3), ('ctl_q3', 38, 4), ('ctl_back', 180, 3)):
            rs.shot(f'{RAW}/mask_{gender}_{cw}_{nm}.png', (0, 0.0, 0.80 + lift), az, el, dist=3.0, lens=85, res=(480, 560))
        set_lift([o for o in kit if cat(o) in ('Top', 'Bottom')] + [body], 0.0)
        me.polygons.foreach_set('material_index', idx0)
    print('liner mask done')


SEC_Z = {
    'male': [1.30, 1.10, 0.985, 0.955, 0.94, 0.90, 0.70, 0.60],
    'female': [1.28, 1.10, 1.01, 0.985, 0.965, 0.90, 0.80, 0.68],
}


def sections_data(gender):
    load(gender)
    body = bpy.data.objects[BODY[gender]]
    Vb, Fb = mesh_arrays(body)
    data = dict(levels=SEC_Z[gender], layers={})

    def loops_at(V, F, z):
        out = []
        for P in slice_plane(V, F, 2, z):
            if len(P) >= 4:
                seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
                closed = bool(np.linalg.norm(P[0] - P[-1]) < 3.0 * max(np.median(seg), 1e-6))
                out.append(dict(p=P[:, :2].round(5).tolist(), closed=closed))
        return out
    data['layers']['body'] = [loops_at(Vb, Fb, z) for z in SEC_Z[gender]]
    suffix = 'M' if gender == 'male' else 'F'
    names = {'polo': [f'Kit_Top_Polo_{suffix}_White'], 'bottom': [f'Kit_Bottom_{"Shorts_M" if gender == "male" else "Skort_F"}_White']}
    meshes = {}
    for gname, nm_list in names.items():
        meshes[gname] = [mesh_arrays(bpy.data.objects[nm]) for nm in nm_list]
        data['layers'][gname] = [[l for (V, F) in meshes[gname] for l in loops_at(V, F, z)] for z in SEC_Z[gender]]
    # band only (face slot 2) so the contrast ring reads separately from the fabric
    bo = bpy.data.objects[names['bottom'][0]]
    me = bo.data
    idx = np.zeros(len(me.polygons), np.int32)
    me.polygons.foreach_get('material_index', idx)
    Vv, Fv = mesh_arrays(bo)
    Fband = Fv[idx == 2]
    data['layers']['band'] = [loops_at(Vv, Fband, z) for z in SEC_Z[gender]]
    json.dump(data, open(f'{RAW}/sections_{gender}.json', 'w'))
    print('sections data done')


def render_clearance(gender):
    """garments coloured by clearance to the fit-ref body (red <3 mm, orange <6, yellow <9, green >=9; inner faces excluded)."""
    load(gender)
    body = bpy.data.objects[BODY[gender]]
    Vb, Fb = mesh_arrays(body)
    tree = bvh_from(Vb, Fb)
    rs.setup(samples=32)
    skin = material('Body_clr', (0.55, 0.55, 0.58), .8, .1)
    body.data.materials.clear()
    body.data.materials.append(skin)

    def clr(d):
        if d < 0.003: return (0.95, 0.10, 0.10, 1)
        if d < 0.006: return (0.98, 0.55, 0.10, 1)
        if d < 0.009: return (0.98, 0.88, 0.20, 1)
        return (0.25, 0.78, 0.35, 1)
    stats = {}
    show = [body]
    for o in kit_meshes('White'):
        me = o.data
        cols = me.color_attributes.new('clearance', 'FLOAT_COLOR', 'POINT')
        d = np.empty(len(me.vertices))
        for i, v in enumerate(me.vertices):
            loc, n, idx, dist = tree.find_nearest(o.matrix_world @ v.co)
            s = ((o.matrix_world @ v.co) - loc).dot(n)
            d[i] = dist if s >= 0 else -dist
            cols.data[i].color = clr(d[i])
        stats[o.name] = dict(min_mm=float(d.min() * 1000), p5_mm=float(np.percentile(d, 5) * 1000), mean_mm=float(d.mean() * 1000))
        m = bpy.data.materials.new('clr_' + o.name)
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        att = nt.nodes.new('ShaderNodeVertexColor')
        att.layer_name = 'clearance'
        em = nt.nodes.new('ShaderNodeEmission')
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(att.outputs['Color'], em.inputs['Color'])
        nt.links.new(em.outputs[0], out.inputs[0])
        me.materials.clear()
        for _ in range(3):
            me.materials.append(m)
        show.append(o)
    show_only(show)
    lift = lift_of(gender)
    set_lift(show, lift)
    bpy.context.scene.view_settings.view_transform = 'Standard'
    for nm, az, el in (('front', 0, 3), ('back', 180, 3), ('right', 90, 3), ('q3', 38, 4)):
        rs.shot(f'{RAW}/clear_{gender}_{nm}.png', (0, -0.05, 0.86 + lift), az, el, dist=6.4, lens=105, res=(560, 800))
    json.dump(stats, open(f'{RAW}/clear_{gender}.json', 'w'), indent=1)
    print('clearance done', {k: round(v['min_mm'], 2) for k, v in stats.items()})


def main():
    gender, mode = sys.argv[sys.argv.index('--') + 1], sys.argv[sys.argv.index('--') + 2]
    {'onbody': render_onbody, 'waist': render_waist, 'hem': render_hem, 'exploded': render_exploded, 'ids': render_ids, 'liner_mask': render_liner_mask,
     'sections': sections_data, 'clearance': render_clearance}[mode](gender)


main()
