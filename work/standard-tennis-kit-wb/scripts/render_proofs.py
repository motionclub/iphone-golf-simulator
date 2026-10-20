"""Proof renders from the assembled kit blends.
blender -b --factory-startup --python render_proofs.py -- <male|female> <onbody|pieces|closeups|clearance|sections>
Outputs go to proof/raw/ (cells) and are composed into sheets by compose_proofs.py."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector, Euler
from kitlib import *
import render_setup as rs
from preview_common import material

RAW = f'{WORK}/proof/raw'
os.makedirs(RAW, exist_ok=True)
SKIN = (0.80, 0.60, 0.46)
LIFT = {'male': 0.0285, 'male_authority': 0.0285, 'female_authority': 0.0235, 'female_arms_candidate': 0.0245}
BLEND = {'male': f'{WORK}/export/StandardKit_Male.blend', 'female': f'{WORK}/export/StandardKit_Female.blend'}


def kit_objs(cw, alt=False, which=None):
    cname = f'Kit_{cw}' + ('_FitArmsCand' if alt else '')
    return list(bpy.data.collections[cname].objects)


def set_visible(objs_show, objs_all):
    for o in objs_all:
        vis = o in objs_show
        o.hide_render = not vis
        o.hide_viewport = not vis


def lift_all(objs, dz):
    for o in objs:
        o.location.z += dz


def all_kit_objects():
    out = []
    for c in bpy.data.collections:
        if c.name.startswith('Kit_'):
            out += list(c.objects)
    return out


def setup_scene(samples=48):
    cam = rs.setup(samples=samples)
    return cam


def body_material():
    return material('Body_skin', SKIN, .55, .3)


def load(gender):
    bpy.ops.wm.open_mainfile(filepath=BLEND[gender])
    return bpy.data.objects


def face_obj(gender):
    return None


def render_onbody(gender):
    ob = load(gender)
    bodies = {'male': [('male_authority', 'FitRef_Body_M', 'main', False)],
              'female': [('female_authority', 'FitRef_Body_F', 'main', False), ('female_arms_candidate', 'FitRef_Body_F_ArmsCandidate', 'alt', True)]}[gender]
    kit_all = all_kit_objects()
    skin = body_material()
    setup_scene(48)
    views = (('front', 0, 3), ('back', 180, 3), ('left', -90, 3), ('right', 90, 3), ('q3', 38, 4))
    for tag, bname, kind, alt in bodies:
        body = bpy.data.objects[bname]
        for cw in ('White', 'Black'):
            show = [body]
            top_bottom = [o for o in kit_objs(cw) if o['kit_category'] in ('Top', 'Bottom')]
            foot = kit_objs(cw, alt=True) if alt else [o for o in kit_objs(cw) if o['kit_category'] in ('Sock', 'Shoe')]
            show += top_bottom + foot
            for o in bpy.data.objects:
                if o.type == 'MESH' and not o.name.startswith('Studio_'):
                    o.hide_render = o not in show
                    o.hide_viewport = o.hide_render
            body.hide_render = False
            body.hide_viewport = False
            body.data.materials.clear()
            body.data.materials.append(skin)
            body.location.z = 0.0
            for o in show:
                o.location.z = 0.0
            lift = LIFT[tag]
            for o in show:
                o.location.z = lift
            for nm, az, el in views:
                p = f'{RAW}/onbody_{tag}_{cw}_{nm}.png'
                rs.shot(p, (0, -0.05, 0.86 + lift), az, el, dist=6.4, lens=105, res=(560, 800))
            for o in show:
                o.location.z = 0.0
    print('onbody done')


PIECE_ROWS = {
    'male': [('Polo', ['Kit_Top_Polo_M']), ('Shorts', ['Kit_Bottom_Shorts_M']), ('Socks', ['Kit_Sock_L', 'Kit_Sock_R']), ('Shoes', ['Kit_Shoe_L', 'Kit_Shoe_R'])],
    'female': [('Polo', ['Kit_Top_Polo_F']), ('Skort', ['Kit_Bottom_Skort_F']), ('Socks', ['Kit_Sock_L', 'Kit_Sock_R']), ('Shoes', ['Kit_Shoe_L', 'Kit_Shoe_R']),
               ('Socks_ArmsCand', ['Kit_Sock_L_ArmsCandFit', 'Kit_Sock_R_ArmsCandFit']), ('Shoes_ArmsCand', ['Kit_Shoe_L_ArmsCandFit', 'Kit_Shoe_R_ArmsCandFit'])],
}
PIECE_VIEWS = (('front', 0, 0, 'ortho'), ('back', 180, 0, 'ortho'), ('left', -90, 0, 'ortho'), ('right', 90, 0, 'ortho'),
               ('top', 0, 89.9, 'ortho'), ('bottom', 0, -89.9, 'ortho'), ('q3f', 35, 14, 'ortho'), ('q3b', 215, 14, 'ortho'))


def piece_setup_world():
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.eevee.taa_render_samples = 48
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.view_settings.view_transform = 'AgX'
    w = bpy.data.worlds.new('PieceWorld')
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.80, 0.81, 0.83, 1)
    bg.inputs[1].default_value = 1.0
    # 3 soft area lights
    for name, loc, power, size in (('K', (-2.5, -3.2, 3.0), 220, 3.0), ('F', (3.0, -2.0, 1.5), 120, 3.0), ('R', (0.5, 3.0, 2.8), 160, 2.5), ('T', (0, -0.5, 4.0), 90, 3.0)):
        d = bpy.data.lights.new(name, 'AREA')
        d.energy = power
        d.size = size
        o = bpy.data.objects.new(name, d)
        bpy.context.scene.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 0.3)) - o.location).to_track_quat('-Z', 'Y').to_euler()
    cd = bpy.data.cameras.new('PieceCam')
    cam = bpy.data.objects.new('PieceCam', cd)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def render_pieces(gender):
    load(gender)
    cam = piece_setup_world()
    sc = bpy.context.scene
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = True
    bgnode = bpy.context.scene.world.node_tree.nodes['Background']
    for cw in ('White', 'Black'):
        g_ = 0.40 if cw == 'White' else 0.80                       # mid-grey behind white pieces, light grey behind black pieces
        bgnode.inputs[0].default_value = (g_, g_ + 0.005, g_ + 0.012, 1)
        for row, names in PIECE_ROWS[gender]:
            objs = []
            for nm in names:
                key = nm + '_' + cw
                objs.append(bpy.data.objects[key])
            for o in objs:
                o.hide_render = False
            pts = np.concatenate([np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices]) for o in objs])
            c = 0.5 * (pts.min(0) + pts.max(0))
            ext = pts.max(0) - pts.min(0)
            RW, RH = 360, 440
            for vname, az, el, kind in PIECE_VIEWS:
                a_, e_ = math.radians(az), math.radians(el)
                dvec = Vector((math.sin(a_) * math.cos(e_), -math.cos(a_) * math.cos(e_), math.sin(e_)))
                if abs(el) > 80:
                    dvec = Vector((0, -1e-4 if el > 0 else 1e-4, 1 if el > 0 else -1)).normalized()
                fwd = -dvec
                up_hint = Vector((0, 0, 1)) if abs(el) < 80 else (Vector((0, 1, 0)) if el > 0 else Vector((0, -1, 0)))
                right = fwd.cross(up_hint).normalized()
                upv = right.cross(fwd).normalized()
                cpt = Vector(c)
                rel = pts - np.array(cpt)
                px = rel @ np.array(right)
                py = rel @ np.array(upv)
                mx, my = 0.5 * (px.max() + px.min()), 0.5 * (py.max() + py.min())
                cc = cpt + right * float(mx) + upv * float(my)
                cam.location = cc + dvec * 4.0
                # camera looking along fwd with the chosen up vector
                q = fwd.to_track_quat('-Z', 'Y')
                cam.rotation_euler = q.to_euler()
                # enforce the up vector: roll the camera so that its Y axis matches upv
                M3 = cam.matrix_world.to_3x3() if False else None
                cam.rotation_mode = 'QUATERNION'
                zaxis = -fwd
                xaxis = up_hint.cross(zaxis).normalized()
                yaxis = zaxis.cross(xaxis).normalized()
                from mathutils import Matrix
                cam.rotation_quaternion = Matrix((xaxis, yaxis, zaxis)).transposed().to_quaternion()
                cam.data.type = 'ORTHO'
                wid, hei = float(px.max() - px.min()), float(py.max() - py.min())
                cam.data.ortho_scale = float(max(hei, wid * RH / RW) * 1.12 + 0.01)
                sc.render.resolution_x, sc.render.resolution_y = RW, RH
                sc.render.filepath = f'{RAW}/piece_{gender}_{cw}_{row}_{vname}.png'
                bpy.ops.render.render(write_still=True)
            for o in objs:
                o.hide_render = True
    print('pieces done')


CLOSE = {
    'male': [('collar', (0.0, -0.10, 1.38), 0, 8, 0.55), ('placket', (0.0, -0.17, 1.30), 0, 4, 0.55), ('cuff', (0.36, -0.04, 1.17), 50, 8, 0.50),
             ('hem_waist', (0.0, -0.18, 0.96), 0, 6, 0.75), ('shorts_hem', (0.0, -0.15, 0.60), 25, 5, 0.85), ('shoe_side', (0.0, -0.05, 0.05), 90, 6, 0.80),
             ('shoe_front', (0.22, -0.10, 0.07), 20, 18, 0.65), ('sock_cuff', (0.2, 0.0, 0.29), 40, 4, 0.60)],
    'female': [('collar', (0.0, -0.08, 1.35), 0, 8, 0.55), ('placket', (0.0, -0.13, 1.28), 0, 4, 0.55), ('cuff', (0.20, -0.02, 1.15), 55, 8, 0.50),
               ('hem_waist', (0.0, -0.12, 0.99), 0, 6, 0.75), ('skort_hem', (0.0, -0.13, 0.70), 25, 5, 0.85), ('shoe_side', (0.0, 0.0, 0.05), 90, 6, 0.70),
               ('shoe_front', (0.17, -0.08, 0.07), 20, 18, 0.60), ('sock_cuff', (0.13, 0.04, 0.27), 40, 4, 0.55)],
}


def render_closeups(gender):
    load(gender)
    skin = body_material()
    setup_scene(64)
    body = bpy.data.objects['FitRef_Body_' + ('M' if gender == 'male' else 'F')]
    body.data.materials.clear()
    body.data.materials.append(skin)
    tag = 'male' if gender == 'male' else 'female_authority'
    lift = LIFT[tag]
    for cw in ('White', 'Black'):
        show = [body] + kit_objs(cw)
        for o in bpy.data.objects:
            if o.type == 'MESH' and not o.name.startswith('Studio_'):
                o.hide_render = o not in show
        for o in show:
            o.location.z = lift
        for nm, tgt, az, el, dist in CLOSE[gender]:
            p = f'{RAW}/close_{gender}_{cw}_{nm}.png'
            rs.shot(p, (tgt[0], tgt[1], tgt[2] + lift), az, el, dist=dist * 2.2, lens=85, res=(480, 480))
        for o in show:
            o.location.z = 0.0
    print('closeups done')


def render_clearance(gender):
    """garments coloured by clearance to the fit-ref body (red <1.5mm, orange <3, yellow <6, green >=6)."""
    load(gender)
    from kitlib import bvh_from, mesh_arrays
    tag = 'male' if gender == 'male' else 'female_authority'
    body = bpy.data.objects['FitRef_Body_' + ('M' if gender == 'male' else 'F')]
    Vb, Fb = mesh_arrays(body)
    tree = bvh_from(Vb, Fb)
    cand_tree = None
    if gender == 'female':
        cb = bpy.data.objects['FitRef_Body_F_ArmsCandidate']
        Vc, Fc = mesh_arrays(cb)
        cand_tree = bvh_from(Vc, Fc)
    setup_scene(32)
    skin = material('Body_clr', (0.55, 0.55, 0.58), .8, .1)
    body.data.materials.clear()
    body.data.materials.append(skin)
    def clr(d):
        if d < 0.0015: return (0.95, 0.10, 0.10, 1)
        if d < 0.003: return (0.98, 0.55, 0.10, 1)
        if d < 0.006: return (0.98, 0.88, 0.20, 1)
        return (0.25, 0.78, 0.35, 1)
    stats = {}
    show = [body]
    for o in kit_objs('White'):
        if gender == 'female' and o['kit_category'] in ('Sock', 'Shoe'):
            pass
        tr = tree
        dd = []
        me = o.data
        # colour per vertex by clearance to the fit-ref body (authority; arms-candidate footwear is not shown here)
        cols = me.color_attributes.new('clearance', 'FLOAT_COLOR', 'POINT')
        d = np.empty(len(me.vertices))
        for i, v in enumerate(me.vertices):
            loc, n, idx, dist = tr.find_nearest(o.matrix_world @ v.co)
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
        me.materials.append(m)
        me.materials.append(m)
        show.append(o)
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.name.startswith('Studio_'):
            o.hide_render = o not in show
    for o in show:
        o.location.z = LIFT[tag]
    bpy.context.scene.view_settings.view_transform = 'Standard'
    for nm, az, el in (('front', 0, 3), ('back', 180, 3), ('right', 90, 3), ('q3', 38, 4)):
        rs.shot(f'{RAW}/clear_{gender}_{nm}.png', (0, -0.05, 0.86 + LIFT[tag]), az, el, dist=6.4, lens=105, res=(560, 800))
    json.dump(stats, open(f'{RAW}/clear_{gender}.json', 'w'), indent=1)
    print('clearance done', {k: round(v['min_mm'], 2) for k, v in stats.items()})


SEC_Z = {
    'male': [1.30, 1.15, 0.97, 0.88, 0.70, 0.60, 0.25, 0.06],
    'female': [1.28, 1.12, 0.98, 0.88, 0.76, 0.66, 0.22, 0.06],
}


def sections_data(gender):
    load(gender)
    from kitlib import slice_plane, mesh_arrays
    tag = 'male' if gender == 'male' else 'female_authority'
    body = bpy.data.objects['FitRef_Body_' + ('M' if gender == 'male' else 'F')]
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
    groups = {'polo': ['Kit_Top_Polo_' + ('M' if gender == 'male' else 'F') + '_White'],
              'bottom': ['Kit_Bottom_' + ('Shorts_M' if gender == 'male' else 'Skort_F') + '_White'],
              'sock': ['Kit_Sock_L_White', 'Kit_Sock_R_White'], 'shoe': ['Kit_Shoe_L_White', 'Kit_Shoe_R_White']}
    lift = LIFT[tag]
    for gname, names in groups.items():
        layer = []
        for z in SEC_Z[gender]:
            loops = []
            for nm in names:
                o = bpy.data.objects[nm]
                V, F = mesh_arrays(o)
                loops += loops_at(V, F, z)
            layer.append(loops)
        data['layers'][gname] = layer
    json.dump(data, open(f'{RAW}/sections_{gender}.json', 'w'))
    print('sections data done')


def main():
    gender, mode = sys.argv[sys.argv.index('--') + 1], sys.argv[sys.argv.index('--') + 2]
    {'onbody': render_onbody, 'pieces': render_pieces, 'closeups': render_closeups, 'clearance': render_clearance, 'sections': sections_data}[mode](gender)


main()
