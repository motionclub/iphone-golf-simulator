"""Swap the new shoes and socks into a copy of the start kit blend.   blender -b --factory-startup --python assemble_fit.py -- <male|female>
export/StandardKit_<Male|Female>.blend  <-  start/StandardKit_<Male|Female>.blend (SHA verified)
 * replaces ONLY Kit_Shoe_L/R and Kit_Sock_L/R (both colourways): same object names, collections, material slots, props; parent = Foot_L_Shoe / Foot_R_Shoe
 * deletes the ArmsCandFit sock/shoe objects, meshes and collections (female) and the arms-candidate FitRef body
 * FitRef body = a copy of THIS job's body mesh (appended from the SHA-verified body blend, never written back)
 * foot sockets get an identity transform; every kit mesh keeps an identity world transform
Polo / bottom objects are not touched."""
import sys, os, json, math, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from kit_common import mesh_topology

gender = sys.argv[sys.argv.index('--') + 1]
G = {'male': dict(name='Male', body_blend=MALE_BODY_BLEND, body_obj='Body_M', body_sha=MALE_BODY_SHA, fit_old='FitRef_Body_M'),
     'female': dict(name='Female', body_blend=FEMALE_BODY_BLEND, body_obj='Body_F', body_sha=FEMALE_BODY_SHA, fit_old='FitRef_Body_F')}[gender]
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
start = f'{WORK}/start/StandardKit_{G["name"]}.blend'
out_blend = f'{WORK}/export/StandardKit_{G["name"]}.blend'
assert sha(start) == START_KIT_SHA[gender], 'start kit SHA mismatch'
assert sha(G['body_blend']) == G['body_sha'], 'body SHA mismatch'
body_sha_before = sha(G['body_blend'])
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.open_mainfile(filepath=start)
sc = bpy.context.scene
mat_w, mat_b = bpy.data.materials['Std_White_Lit'], bpy.data.materials['Std_Black_Lit']
log = dict(gender=gender, removed_objects=[], removed_meshes=[], removed_collections=[], replaced=[])

# ---- 1. delete the ArmsCandFit extras -----------------------------------------------------------------------------------------------------------------
for o in list(bpy.data.objects):
    if 'armscand' in o.name.lower() or o.get('fit_ref') == 'arms_candidate' or (o.type == 'MESH' and 'armscand' in o.data.name.lower()):
        log['removed_objects'].append(o.name)
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and me.users == 0:
            log['removed_meshes'].append(me.name)
            bpy.data.meshes.remove(me)
for c in list(bpy.data.collections):
    if 'armscand' in c.name.lower():
        log['removed_collections'].append(c.name)
        bpy.data.collections.remove(c)

# ---- 2. FitRef = this job's body --------------------------------------------------------------------------------------------------------------------
fitref = bpy.data.collections['FitRef']
old = bpy.data.objects[G['fit_old']]
for o in list(fitref.objects):
    me = o.data
    log['removed_objects'].append(o.name)
    bpy.data.objects.remove(o, do_unlink=True)
    if me is not None and me.users == 0:
        log['removed_meshes'].append(me.name)
        bpy.data.meshes.remove(me)
with bpy.data.libraries.load(G['body_blend'], link=False) as (src, dst):
    dst.objects = [G['body_obj']]
nb = dst.objects[0]
nb.name = G['fit_old']
fitref.objects.link(nb)
for c in list(nb.users_collection):
    if c is not fitref:
        c.objects.unlink(nb)
nb['fit_ref'] = f'{os.path.basename(G["body_blend"])} sha256 {body_sha_before}'
nb['fit_ref_note'] = 'TENNIS_SHOES_FIT: shoes + socks are fit to THIS body (not to the older ArtDir body the start kit was fit to)'
ref_mat = bpy.data.materials.get('FitRef_Grey')
nb.data.materials.clear()
nb.data.materials.append(ref_mat)
nb.hide_render = True
nb.hide_viewport = False
nb.name = G['fit_old']

# ---- 3. replace shoes + socks -----------------------------------------------------------------------------------------------------------------------
SPECS = [('Kit_Sock_L', 'sockL', 'Foot_L_Shoe', 'Sock'), ('Kit_Sock_R', 'sockR', 'Foot_R_Shoe', 'Sock'),
         ('Kit_Shoe_L', 'shoeL', 'Foot_L_Shoe', 'Shoe'), ('Kit_Shoe_R', 'shoeR', 'Foot_R_Shoe', 'Shoe')]


def tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def piece_mats(cw):
    return [mat_w, mat_w] if cw == 'White' else [mat_b, mat_w]


def make_mesh(name, d, mats):
    V, F = np.asarray(d['V'], float), np.asarray(d['F'], int)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], F.tolist())
    me.update()
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set('material_index', np.minimum(np.asarray(d['M'], np.int32), len(mats) - 1))
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    me.normals_split_custom_set(np.asarray(d['LN'], float).reshape(-1, 3).tolist())
    at = me.attributes.new('kit_tag', 'INT', 'FACE')
    at.data.foreach_set('value', np.asarray(d['T'], np.int32))
    me['kit_tagnames'] = json.dumps([str(t) for t in d['tagnames']])
    return me


def unwrap(o):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003)
    bpy.ops.object.mode_set(mode='OBJECT')


# identity foot sockets (the pieces are authored in body space; the sockets only anchor the swap)
for cw in ('White', 'Black'):
    for sn in ('Foot_L_Shoe', 'Foot_R_Shoe'):
        e = bpy.data.objects[f'{sn}_{cw}']
        log.setdefault('sockets_before', {})[e.name] = [round(x, 4) for x in e.location]
        e.location = (0.0, 0.0, 0.0)
        e.rotation_euler = (0.0, 0.0, 0.0)
        e.scale = (1.0, 1.0, 1.0)
bpy.context.view_layer.update()

manifest = dict(gender=gender, objects=[])
fit_tag = f'{os.path.basename(G["body_blend"])} sha256 {body_sha_before[:16]}'
for name, npz, sock, cat in SPECS:
    z = np.load(f'{WORK}/data/{npz}_{gender}.npz')
    d = {k: z[k] for k in z.files}
    for cw in ('White', 'Black'):
        oname = f'{name}_{cw}'
        old_o = bpy.data.objects[oname]
        coll = old_o.users_collection[0]
        par = old_o.parent
        old_mesh = old_o.data
        old_mesh_name = old_mesh.name
        bpy.data.objects.remove(old_o, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
        mesh_name = f'{name}_White' if cw == 'White' else f'{name}_black'
        if cw == 'White':
            me = make_mesh(mesh_name, d, piece_mats('White'))
            o = bpy.data.objects.new(oname, me)
            coll.objects.link(o)
            unwrap(o)
            white_mesh = me
        else:
            me = white_mesh.copy()                                   # the black colourway shares geometry / UVs / normals / tags, only the slots change
            me.name = mesh_name
            me.materials.clear()                                        # NB clear() resets every face to slot 0: the per-face slots are written again below
            for m in piece_mats('Black'):
                me.materials.append(m)
            me.polygons.foreach_set('material_index', np.minimum(np.asarray(d['M'], np.int32), len(me.materials) - 1))
            o = bpy.data.objects.new(oname, me)
            coll.objects.link(o)
        o['kit_category'] = cat
        o['socket'] = sock
        o['fit_ref'] = fit_tag
        o['colorway'] = cw
        o['base_name'] = name
        o.parent = par
        o.matrix_parent_inverse = par.matrix_world.inverted()     # identity (the socket is at the origin now)
        o.hide_render = False
        log['replaced'].append(oname)
        if cw == 'White':
            manifest['objects'].append(dict(name=name, category=cat, socket=sock, tris=tri_count(o), verts=len(me.vertices), has_uv=len(me.uv_layers) > 0,
                                            custom_normals=bool(me.has_custom_normals), topology=mesh_topology(d['V'], d['F']),
                                            bbox_min=np.array(d['V']).min(0).round(4).tolist(), bbox_max=np.array(d['V']).max(0).round(4).tolist()))
bpy.context.view_layer.update()
sc['shoes_fit_note'] = (f'TENNIS_SHOES_FIT: Kit_Shoe_L/R and Kit_Sock_L/R rebuilt on {os.path.basename(G["body_blend"])} (sha256 {body_sha_before}); '
                        'polo and bottom untouched; ArmsCandFit extras removed; foot sockets at identity.')
for _ in range(3):
    try:
        bpy.data.orphans_purge(do_recursive=True)
    except Exception:
        break
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
manifest['blend'] = out_blend
manifest['blend_sha256'] = sha(out_blend)
manifest['body_sha256_before'] = body_sha_before
manifest['body_sha256_after'] = sha(G['body_blend'])
manifest['log'] = log
json.dump(manifest, open(f'{WORK}/export/manifest_{gender}.json', 'w'), indent=1)
print('saved', out_blend, 'sha', manifest['blend_sha256'][:12], 'removed', len(log['removed_objects']), 'replaced', len(log['replaced']))
for o in manifest['objects']:
    print('  ', o['name'], 'tris', o['tris'], 'verts', o['verts'], 'uv', o['has_uv'], 'normals', o['custom_normals'], 'islands', o['topology']['islands'], 'boundary', o['topology']['boundary_edges'])
