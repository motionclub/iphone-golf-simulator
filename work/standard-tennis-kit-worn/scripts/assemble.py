"""Assemble the staged worn-kit blends: python assemble.py -- <male|female>

Objects (separate closed meshes): Kit_Top_Polo_*, Kit_Bottom_Shorts_M / Kit_Bottom_Skort_F, Kit_Sock_L/R, Kit_Shoe_L/R, each PARENTED to its socket empty
(Chest_Top / Hip_Bottom / Foot_L_Shoe / Foot_R_Shoe) with an identity world transform (meshes are authored in body space; the parent only anchors the swap).
Material slots: 0 fabric, 1 piping, 2 waistband (bottoms only; the CONTRASTING colour: black on the white kit, white on the black kit).
Collections: Kit_White, Kit_Black (each with its own socket empties), Kit_*_FitArmsCand (female alt footwear), FitRef (reference body, never exported).
"""
import sys, os, json, math, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Matrix
from kitlib import *
from kit_common import mesh_topology

KIT = {
    'male': dict(
        body=MALE_BLEND, body_obj='Body_M', suffix='M',
        parts=[('Kit_Top_Polo_M', 'polo_male', 'Chest_Top', 'Top'),
               ('Kit_Bottom_Shorts_M', 'shorts_male', 'Hip_Bottom', 'Bottom'),
               ('Kit_Sock_L', 'sockL_male', 'Foot_L_Shoe', 'Sock'), ('Kit_Sock_R', 'sockR_male', 'Foot_R_Shoe', 'Sock'),
               ('Kit_Shoe_L', 'shoeL_male', 'Foot_L_Shoe', 'Shoe'), ('Kit_Shoe_R', 'shoeR_male', 'Foot_R_Shoe', 'Shoe')],
        alt=[], shoe_lift=0.0285,
        sockets={'Chest_Top': (0, 0, 1.25), 'Hip_Bottom': (0, 0, 0.95), 'Foot_L_Shoe': (-0.18, 0.0, 0.09), 'Foot_R_Shoe': (0.18, 0.0, 0.09)}),
    'female': dict(
        body=FEMALE_BLEND, body_obj='Body_F', suffix='F',
        parts=[('Kit_Top_Polo_F', 'polo_female', 'Chest_Top', 'Top'),
               ('Kit_Bottom_Skort_F', 'skort_female', 'Hip_Bottom', 'Bottom'),
               ('Kit_Sock_L', 'sockL_female_auth', 'Foot_L_Shoe', 'Sock'), ('Kit_Sock_R', 'sockR_female_auth', 'Foot_R_Shoe', 'Sock'),
               ('Kit_Shoe_L', 'shoeL_female_auth', 'Foot_L_Shoe', 'Shoe'), ('Kit_Shoe_R', 'shoeR_female_auth', 'Foot_R_Shoe', 'Shoe')],
        alt=[('Kit_Sock_L_ArmsCandFit', 'sockL_female', 'Foot_L_Shoe', 'Sock'), ('Kit_Sock_R_ArmsCandFit', 'sockR_female', 'Foot_R_Shoe', 'Sock'),
             ('Kit_Shoe_L_ArmsCandFit', 'shoeL_female', 'Foot_L_Shoe', 'Shoe'), ('Kit_Shoe_R_ArmsCandFit', 'shoeR_female', 'Foot_R_Shoe', 'Shoe')],
        shoe_lift=0.0235, shoe_lift_alt=0.0245,
        sockets={'Chest_Top': (0, 0, 1.22), 'Hip_Bottom': (0, 0, 0.975), 'Foot_L_Shoe': (-0.125, 0.0, 0.08), 'Foot_R_Shoe': (0.125, 0.0, 0.08)}),
}

WHITE_RGB = (0.93, 0.93, 0.93)
BLACK_RGB = (0.035, 0.035, 0.04)


def lin(c):
    return tuple(((v + .055) / 1.055) ** 2.4 if v > .04045 else v / 12.92 for v in c)


def make_material(name, rgb, smooth=0.30, note=''):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes['Principled BSDF']
    n.inputs['Base Color'].default_value = (*lin(rgb), 1)
    n.inputs['Roughness'].default_value = 1.0 - smooth
    n.inputs['Metallic'].default_value = 0.0
    m.diffuse_color = (*lin(rgb), 1)
    # Unity URP Lit mirror (documentation + importer hint)
    m['unity_shader'] = 'Universal Render Pipeline/Lit'
    m['unity_BaseColor_sRGB'] = list(rgb)
    m['unity_Smoothness'] = smooth
    m['unity_Metallic'] = 0.0
    m['unity_Surface'] = 'Opaque'
    m['unity_RenderFace'] = 'Front'
    m['unity_note'] = note
    return m


def mesh_object(name, d, mats, coll):
    """closed mesh from a staged npz dict: welded V/F, per-corner custom normals, material index per face, tag attribute per face."""
    V, F = np.asarray(d['V'], float), np.asarray(d['F'], int)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], F.tolist())
    me.update()
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set('material_index', np.minimum(np.asarray(d['M'], np.int32), len(mats) - 1))
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    try:
        me.normals_split_custom_set(np.asarray(d['LN'], float).reshape(-1, 3).tolist())
    except Exception as e:
        print('  custom normals failed for', name, e)
    at = me.attributes.new('kit_tag', 'INT', 'FACE')
    at.data.foreach_set('value', np.asarray(d['T'], np.int32))
    me['kit_tagnames'] = json.dumps([str(t) for t in d['tagnames']])
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def unwrap(o):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003)
    bpy.ops.object.mode_set(mode='OBJECT')


def tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def piece_mats(cat, cw, mw, mb):
    """material slots per piece: [fabric, piping] (+ band for bottoms).  The band is the CONTRAST colour."""
    if cw == 'White':
        return [mw, mw, mb] if cat == 'Bottom' else [mw, mw]
    return [mb, mw, mw] if cat == 'Bottom' else [mb, mw]


def main():
    gender = sys.argv[sys.argv.index('--') + 1]
    K = KIT[gender]
    out_blend = f'{WORK}/export/StandardKit_{"Male" if gender == "male" else "Female"}.blend'
    # start from the authority body blend (fit reference) so the kit file stays self-contained; the body is NOT modified and NOT saved over
    body_sha_before = hashlib.sha256(open(K['body'], 'rb').read()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=K['body'])
    sc = bpy.context.scene
    keep = {K['body_obj']}
    for o in list(bpy.data.objects):
        if o.name not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
    body = bpy.data.objects[K['body_obj']]
    body.name = 'FitRef_Body_' + K['suffix']
    fitref = bpy.data.collections.new('FitRef')
    sc.collection.children.link(fitref)
    for c in list(body.users_collection):
        c.objects.unlink(body)
    fitref.objects.link(body)
    body['fit_ref'] = os.path.basename(K['body']) + ' sha256 ' + body_sha_before
    if gender == 'female':
        cand = ROOT + '/work/female-arms-form2/export/HeroBase_Female_arms_candidate.blend'
        with bpy.data.libraries.load(cand, link=False) as (src, dst):
            dst.objects = ['Body_F']
        ob = dst.objects[0]
        ob.name = 'FitRef_Body_F_ArmsCandidate'
        fitref.objects.link(ob)
        ob['fit_ref'] = 'HeroBase_Female_arms_candidate.blend sha256 573ab4431d83f8651936f0081ad3bda9c6890c56ee5dce3061140198c9455f0e'
        ob.hide_viewport = True
        ob.hide_render = True
    ref_mat = bpy.data.materials.new('FitRef_Grey')
    ref_mat.use_nodes = True
    ref_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.55, 0.55, 0.58, 1)
    for o in fitref.objects:
        o.hide_render = True
        o.data.materials.clear()
        o.data.materials.append(ref_mat)
    for img in list(bpy.data.images):
        bpy.data.images.remove(img)
    mat_w = make_material('Std_White_Lit', WHITE_RGB, 0.30, 'standard kit white (fabric on the white kit; piping + waistband on the black kit)')
    mat_b = make_material('Std_Black_Lit', BLACK_RGB, 0.30, 'standard kit black (fabric on the black kit; waistband on the white kit)')
    colls, sockets = {}, {}
    for cw in ('White', 'Black'):
        c = bpy.data.collections.new(f'Kit_{cw}')
        sc.collection.children.link(c)
        colls[cw] = c
        # socket empties of this colourway (the pieces are parented to them; world transform of every piece stays identity)
        sockets[cw] = {}
        for nm, loc in K['sockets'].items():
            e = bpy.data.objects.new(f'{nm}_{cw}', None)
            e.empty_display_type = 'PLAIN_AXES'
            e.empty_display_size = 0.04
            e.location = loc
            e['socket_name'] = nm
            c.objects.link(e)
            sockets[cw][nm] = e
        if gender == 'female':
            c2 = bpy.data.collections.new(f'Kit_{cw}_FitArmsCand')
            sc.collection.children.link(c2)
            colls[cw + '_alt'] = c2
    bpy.context.view_layer.update()
    manifest = dict(gender=gender, objects=[], body_sha256=body_sha_before)
    bpy.ops.object.select_all(action='DESELECT')

    def add_set(parts, suffix_tag, key_suffix=''):
        for name, npz, sock, cat in parts:
            z = np.load(f'{WORK}/data/{npz}.npz')
            d = {k: z[k] for k in z.files}
            ow = mesh_object(name + '_White', d, piece_mats(cat, 'White', mat_w, mat_b), colls['White' + key_suffix])
            unwrap(ow)
            mb = ow.data.copy()                                                   # black colourway: same mesh (UVs, custom normals, attributes) + swapped slots
            mb.name = name + '_black'
            mb.materials.clear()
            for m in piece_mats(cat, 'Black', mat_w, mat_b):
                mb.materials.append(m)
            mb.polygons.foreach_set('material_index', np.minimum(np.asarray(d['M'], np.int32), len(mb.materials) - 1))
            ob = bpy.data.objects.new(name + '_Black', mb)
            colls['Black' + key_suffix].objects.link(ob)
            for o, cw in ((ow, 'White'), (ob, 'Black')):
                o['kit_category'] = cat
                o['socket'] = sock
                o['fit_ref'] = suffix_tag
                o['colorway'] = cw
                o['base_name'] = name
                par = sockets[cw][sock]
                o.parent = par
                o.matrix_parent_inverse = par.matrix_world.inverted()           # keep the identity world transform
            tris = tri_count(ow)
            topo = mesh_topology(d['V'], d['F'])
            manifest['objects'].append(dict(name=name, category=cat, socket=sock, tris=tris, verts=len(ow.data.vertices), fit_ref=suffix_tag,
                                            has_uv=len(ow.data.uv_layers) > 0, custom_normals=bool(ow.data.has_custom_normals),
                                            material_slots_white=[m.name for m in ow.data.materials], material_slots_black=[m.name for m in ob.data.materials],
                                            topology=topo, bbox_min=np.array(d['V']).min(0).round(4).tolist(), bbox_max=np.array(d['V']).max(0).round(4).tolist()))
            print(f'  {name:26s} tris {tris:6d} verts {len(ow.data.vertices):6d} uv {len(ow.data.uv_layers)} customN {ow.data.has_custom_normals} '
                  f'boundary {topo["boundary_edges"]} nonman {topo["nonmanifold_edges"]} islands {topo["islands"]}')

    add_set(K['parts'], 'authority')
    if K['alt']:
        add_set(K['alt'], 'arms_candidate', '_alt')
    manifest['shoe_lift_m'] = K['shoe_lift']
    if 'shoe_lift_alt' in K:
        manifest['shoe_lift_alt_m'] = K['shoe_lift_alt']
    manifest['sockets'] = {k: list(v) for k, v in K['sockets'].items()}
    sc['kit_note'] = ('Standard tennis kit, WORN (white + black), staged. Untucked polo (hem overlaps the waistband top), contrasting waistband on the bottom, '
                      'closed double-walled shells, separate objects parented to the socket empties. Body is a fit reference only (FitRef collection).')
    for _ in range(3):
        try:
            bpy.data.orphans_purge(do_recursive=True)
        except Exception:
            break
    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    manifest['blend'] = out_blend
    manifest['blend_sha256'] = hashlib.sha256(open(out_blend, 'rb').read()).hexdigest()
    manifest['body_sha256_after'] = hashlib.sha256(open(K['body'], 'rb').read()).hexdigest()
    json.dump(manifest, open(f'{WORK}/export/manifest_{gender}.json', 'w'), indent=1)
    print('saved', out_blend)


main()
