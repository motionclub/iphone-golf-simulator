"""Build one dressed hero blend.

  blender -b --factory-startup --python build_dressed.py -- <male|female> [out.blend]

1. byte-copies the source body blend to export/HeroBase_<Sex>_Dressed.blend (the copy is what gets opened and saved; the source
   file is never opened for writing) and records SHA(copy) == SHA(source) before anything is touched;
2. appends the six kit pieces of BOTH colours from the kit blend (objects + their materials only, no FitRef, no kit sockets),
   creates the four named sockets Chest_Top / Hip_Bottom / Foot_L_Shoe / Foot_R_Shoe (same world transforms as the kit's own
   sockets) and re-parents every piece to its socket keeping its authored parent-inverse (world transform identical by construction);
3. appends the classic racket (+ its Hand_Racket socket);
4. handrig.build_and_pose: right-hand finger rig, grip pose (action), Hand_Racket placed at the palm and parented to the palm bone;
5. saves; writes data/build_<sex>.json with every number the gates need.
Nothing is written outside work/dressed-look/."""
import os
import shutil
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *
import handrig

a_ = args_after_dashes()
tag = a_[0]
H = HERO[tag]
NAME = H['label']
OUT = a_[1] if len(a_) > 1 else f'{EXPORT}/HeroBase_{NAME}_Dressed.blend'
assert OUT.startswith(WORK + '/'), 'output must stay inside work/dressed-look'
os.makedirs(os.path.dirname(OUT), exist_ok=True)
os.makedirs(DATA, exist_ok=True)
report = dict(tag=tag, generated_by='build_dressed.py')

# ------------------------------------------------------------------ 1. duplicate the source body blend
src_path = SRC[H['body_src']]
assert sha256_file(src_path) == SHA[H['body_src']], 'source body SHA differs from the brief - stop'
shutil.copyfile(src_path, OUT)
report['copy_sha256_before_edit'] = sha256_file(OUT)
assert report['copy_sha256_before_edit'] == SHA[H['body_src']]
bpy.ops.wm.open_mainfile(filepath=OUT)
sc = bpy.context.scene
body = bpy.data.objects[H['body']]
src_meshes = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
report['source_mesh_geometry_hash'] = {n: mesh_geometry_hash(o.data) for n, o in src_meshes.items()}
report['source_body_vertex_hash'] = hashlib.sha256(np.ascontiguousarray(mesh_co(body)).tobytes()).hexdigest()
report['source_vgroups'] = [g.name for g in body.vertex_groups]
report['source_nverts'] = {n: len(o.data.vertices) for n, o in src_meshes.items()}
report['unit'] = [sc.unit_settings.system, sc.unit_settings.scale_length]


def new_collection(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    p = parent or sc.collection
    if c.name not in [x.name for x in p.children]:
        p.children.link(c)
    return c


def move_to(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def load_objs(path, names):
    with bpy.data.libraries.load(path, link=False) as (s, d):
        missing = [n for n in names if n not in s.objects]
        assert not missing, missing
        d.objects = list(names)
    return {o.name: o for o in d.objects}


def parent_keep(child, parent):
    """parent so the child's WORLD transform is unchanged, without touching its basis (loc/rot/scale):
    inverse = parent_world^-1 (what Ctrl+P > Object does).  Only valid when the child's basis is its current world matrix."""
    bpy.context.view_layer.update()
    child.parent = parent
    child.parent_type = 'OBJECT'
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    bpy.context.view_layer.update()


# ------------------------------------------------------------------ 2. kit pieces + sockets
kit_path = SRC[H['kit_src']]
# NOTE: objects appended from a library are not evaluated yet (matrix_world is identity) - always use the stored loc/rot/scale (the basis)
kit_sockets = {}
with bpy.data.libraries.load(kit_path, link=False) as (s, d):
    d.objects = [f'{s_}_White' for s_ in SOCKETS]
for o in d.objects:
    assert o.parent is None
    kit_sockets[o.name.replace('_White', '')] = dict(loc=tuple(o.location), rot=tuple(o.rotation_euler), scale=tuple(o.scale), mode=o.rotation_mode)
    bpy.data.objects.remove(o, do_unlink=True)
col_sockets = new_collection('Sockets')
sockets = {}
for nm in SOCKETS:
    e = bpy.data.objects.new(nm, None)
    e.empty_display_type = 'PLAIN_AXES'
    e.empty_display_size = 0.04
    k = kit_sockets[nm]
    e.rotation_mode = k['mode']
    e.location, e.rotation_euler, e.scale = k['loc'], k['rot'], k['scale']
    col_sockets.objects.link(e)
    sockets[nm] = e
bpy.context.view_layer.update()
report['socket_basis'] = {nm: kit_sockets[nm] for nm in SOCKETS}
col_color = {c: new_collection(f'Kit_{c}') for c in COLORS}
pieces = {}
for color in COLORS:
    pn = piece_names(tag, color)
    objs = load_objs(kit_path, [n for n, _ in pn] + [f'{s_}_{color}' for s_ in SOCKETS])
    for n, sock in pn:
        o = objs[n]
        # the kit's pieces are children of per-colour sockets whose world matrices equal the shared socket's: keep the piece's own
        # parent-inverse and basis untouched, only swap the parent pointer -> world transform identical by construction
        old_par = o.parent
        ks = kit_sockets[sock]
        assert old_par is not None and old_par.parent is None, n
        assert (tuple(old_par.location), tuple(old_par.rotation_euler), tuple(old_par.scale)) == (ks['loc'], ks['rot'], ks['scale']), (n, 'this colour socket differs from the shared socket')
        old_inv = o.matrix_parent_inverse.copy()
        o.parent = sockets[sock]
        o.parent_type = 'OBJECT'
        o.matrix_parent_inverse = old_inv
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col_color[color].objects.link(o)
        pieces[n] = o
    for s_ in SOCKETS:                                 # drop the kit's per-colour socket empties
        bpy.data.objects.remove(objs[f'{s_}_{color}'], do_unlink=True)
bpy.context.view_layer.update()
mat_remap = {}
for o in pieces.values():            # the two library loads (white pieces, black pieces) each appended their own copy of the same two kit materials
    for i, m in enumerate(o.data.materials):
        if m is not None and m.name.rsplit('.', 1)[-1].isdigit() and m.name.rsplit('.', 1)[0] in ('Std_White_Lit', 'Std_Black_Lit'):
            base = bpy.data.materials[m.name.rsplit('.', 1)[0]]
            o.data.materials[i] = base
            mat_remap[m.name] = base.name
for m in list(bpy.data.materials):
    if m.users == 0 and m.name.rsplit('.', 1)[0] in ('Std_White_Lit', 'Std_Black_Lit'):
        bpy.data.materials.remove(m)
report['kit_material_remap'] = mat_remap
for nm, e in sockets.items():
    parent_keep(e, body)
report['kit_pieces'] = {n: dict(socket=o.parent.name, geometry_hash=mesh_geometry_hash(o.data), world_exact_dressed=world_exact_hash(o),
                                mat_dressed=mat_hash(o.matrix_world), n_verts=len(o.data.vertices)) for n, o in pieces.items()}

# ------------------------------------------------------------------ 3. racket
rk_names = ['Racket_Classic', 'StringBed', 'Grip', 'ButtCap', 'Collider_Racket', 'Hand_Racket']
rk = load_objs(SRC['racket'], rk_names)
col_rk = new_collection('Racket')
for n, o in rk.items():
    move_to(o, col_sockets if n == 'Hand_Racket' else col_rk)
report['racket_geometry_hash'] = {n: mesh_geometry_hash(o.data) for n, o in rk.items() if o.type == 'MESH'}

# ------------------------------------------------------------------ 4. hand rig + grip pose
col_rig = new_collection('Rig')
sj_all = json.load(open(SRC['socket_json']))['bodies']
report['rig'] = handrig.build_and_pose(tag, body, rk, sockets, dict(rig=col_rig), sj_all['male'],
                                       kit_objs=[pieces[n] for n, _ in piece_names(tag, 'White')], log=print)

# ------------------------------------------------------------------ 5. visibility defaults, save
lc = {c.name: c for c in bpy.context.view_layer.layer_collection.children}
lc['Kit_Black'].hide_viewport = True
col_color['Black'].hide_render = True
rk['Collider_Racket'].hide_render = True
sc['dressed_look'] = 'HeroBase %s + standard tennis kit (white/black) + classic racket; see work/dressed-look/GATE_RESULTS.md' % NAME
bpy.context.preferences.filepaths.save_version = 0           # no .blend1 backups (the backup of the first save would be the untouched source copy)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
report['saved'] = OUT
report['saved_sha256'] = sha256_file(OUT)
report['dressed_mesh_geometry_hash'] = {n: mesh_geometry_hash(o.data) for n, o in src_meshes.items()}
report['dressed_body_vertex_hash'] = hashlib.sha256(np.ascontiguousarray(mesh_co(body)).tobytes()).hexdigest()
report['dressed_vgroups'] = [g.name for g in body.vertex_groups]
report['dressed_nverts'] = {n: len(o.data.vertices) for n, o in src_meshes.items()}
json.dump(report, open(f'{DATA}/build_{tag}.json' if OUT.startswith(EXPORT) else OUT + '.json', 'w'), indent=1)
print('BUILD_DONE', tag, OUT)
