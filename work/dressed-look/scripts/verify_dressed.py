"""Gate evidence for one hero.  Opens each source file and the dressed blend as MAIN files one after the other (read-only: nothing is saved),
so every matrix_world is really evaluated, and compares them.

  blender -b --factory-startup --python verify_dressed.py -- <male|female> [dressed.blend] [out.json]

Evidence written: BODIES (geometry hashes of every source mesh vs the dressed copy), KIT_SEPARATE (names / parents / sockets / own mesh datablocks),
NO_REFIT (geometry hash + bit-identical world vertices + no modifiers/shape keys/vertex groups on all 12 pieces), BOTH_COLORS (collections,
materials), RACKET_IN_HAND (socket chain, racket geometry hashes, hand distance in the evaluated pose)."""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *
from mathutils.bvhtree import BVHTree

a_ = args_after_dashes()
tag = a_[0]
H = HERO[tag]
DRESSED = a_[1] if len(a_) > 1 else f"{EXPORT}/HeroBase_{H['label']}_Dressed.blend"
OUTJSON = a_[2] if len(a_) > 2 else f'{DATA}/verify_{tag}.json'
R = dict(tag=tag, dressed=DRESSED)


def open_ro(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    bpy.context.view_layer.update()


def exact_world(o):
    return hashlib.sha256(np.ascontiguousarray(mesh_co(o, world=True)).tobytes()).hexdigest(), mesh_co(o, world=True)


# --------------------------------------------------------------- sources
src_sha_before = {k: sha256_file(SRC[k]) for k in SHA}
open_ro(SRC[H['body_src']])
src_body = {o.name: dict(geometry=mesh_geometry_hash(o.data), n_verts=len(o.data.vertices), vgroups=len(o.vertex_groups),
                         mods=len(o.modifiers), verts_hash=hashlib.sha256(np.ascontiguousarray(mesh_co(o)).tobytes()).hexdigest())
            for o in bpy.data.objects if o.type == 'MESH'}
open_ro(SRC[H['kit_src']])
kit_src = {}
kit_src_xyz = {}
for color in COLORS:
    for n, sock in piece_names(tag, color):
        o = bpy.data.objects[n]
        h, xyz = exact_world(o)
        kit_src[n] = dict(geometry=mesh_geometry_hash(o.data), world_exact=h, matrix=mat_hash(o.matrix_world), n_verts=len(o.data.vertices),
                          socket_src=o.parent.name, mats=[m.name if m else None for m in o.data.materials])
        kit_src_xyz[n] = xyz
open_ro(SRC['racket'])
rk_src = {}
for o in bpy.data.objects:
    if o.type == 'MESH':
        rk_src[o.name] = dict(geometry=mesh_geometry_hash(o.data), parent=o.parent.name if o.parent else None, loc=[round(x, 6) for x in o.location],
                              rot=[round(x, 6) for x in o.rotation_euler], scale=[round(x, 6) for x in o.scale], n_verts=len(o.data.vertices),
                              mats=[m.name if m else None for m in o.data.materials])
rk_src['Hand_Racket'] = dict(parent=None, empty=True)

# --------------------------------------------------------------- dressed
open_ro(DRESSED)
body = bpy.data.objects[H['body']]
dressed_meshes = {o.name: dict(geometry=mesh_geometry_hash(o.data), n_verts=len(o.data.vertices), vgroups=len(o.vertex_groups),
                               verts_hash=hashlib.sha256(np.ascontiguousarray(mesh_co(o)).tobytes()).hexdigest(),
                               mods=[(m.name, m.type) for m in o.modifiers]) for o in bpy.data.objects if o.type == 'MESH' and o.name in src_body}
bodies = {}
for n, s_ in src_body.items():
    d = dressed_meshes.get(n)
    bodies[n] = dict(source_geometry=s_['geometry'], dressed_geometry=d['geometry'] if d else None, geometry_equal=bool(d and d['geometry'] == s_['geometry']),
                     verts_hash_equal=bool(d and d['verts_hash'] == s_['verts_hash']), n_verts_equal=bool(d and d['n_verts'] == s_['n_verts']),
                     source_vgroups=s_['vgroups'], dressed_vgroups=d['vgroups'] if d else None, dressed_modifiers=d['mods'] if d else None)
R['BODIES'] = dict(per_mesh=bodies, ok=all(b['geometry_equal'] and b['verts_hash_equal'] and b['n_verts_equal'] for b in bodies.values()),
                   note='vertex groups on Body_* added by the right-hand rig: ' + str(bodies[H['body']]['dressed_vgroups'] - bodies[H['body']]['source_vgroups']))

# KIT_SEPARATE / NO_REFIT / BOTH_COLORS
body_mesh_name = body.data.name
kit_rows = {}
all_sep, all_refit = True, True
col_members = {c: sorted(o.name for o in bpy.data.collections[f'Kit_{c}'].objects) if f'Kit_{c}' in bpy.data.collections else None for c in COLORS}
mats_used = set()
for color in COLORS:
    for n, sock in piece_names(tag, color):
        o = bpy.data.objects.get(n)
        if o is None:
            kit_rows[n] = dict(missing=True)
            all_sep = all_refit = False
            continue
        h, xyz = exact_world(o)
        s_ = kit_src[n]
        sep = dict(is_mesh=o.type == 'MESH', parent=o.parent.name if o.parent else None, parent_type=o.parent_type, expected_socket=sock,
                   parent_is_socket=bool(o.parent and o.parent.name == sock and o.parent.type == 'EMPTY' and o.parent_type == 'OBJECT'),
                   own_datablock=o.data is not body.data, datablock_users=o.data.users, in_collection=n in (col_members[color] or []))
        ref = dict(geometry_equal=mesh_geometry_hash(o.data) == s_['geometry'], world_exact_equal=(h == s_['world_exact']),
                   max_abs_world_diff=float(np.abs(xyz - kit_src_xyz[n]).max()) if xyz.shape == kit_src_xyz[n].shape else None,
                   n_verts_equal=len(o.data.vertices) == s_['n_verts'], modifiers=len(o.modifiers), shape_keys=bool(o.data.shape_keys), vgroups=len(o.vertex_groups),
                   matrix_dressed=mat_hash(o.matrix_world), matrix_source=s_['matrix'])
        ref['ok'] = bool(ref['geometry_equal'] and ref['world_exact_equal'] and ref['n_verts_equal'] and ref['modifiers'] == 0 and not ref['shape_keys'] and ref['vgroups'] == 0
                         and ref['matrix_dressed'] == ref['matrix_source'])
        sep['ok'] = bool(sep['is_mesh'] and sep['parent_is_socket'] and sep['own_datablock'] and sep['in_collection'])
        all_sep &= sep['ok']
        all_refit &= ref['ok']
        mats = [m.name if m else None for m in o.data.materials]
        mats_used.update(mats)
        kit_rows[n] = dict(sep=sep, refit=ref, materials=mats, source_materials=s_['mats'])
sockets_ok = {s_: dict(exists=s_ in bpy.data.objects, type=bpy.data.objects[s_].type if s_ in bpy.data.objects else None,
                       parent=bpy.data.objects[s_].parent.name if s_ in bpy.data.objects and bpy.data.objects[s_].parent else None,
                       world=[round(x, 5) for x in bpy.data.objects[s_].matrix_world.translation] if s_ in bpy.data.objects else None) for s_ in SOCKETS}
R['KIT_SEPARATE'] = dict(rows={n: r.get('sep', r) for n, r in kit_rows.items()}, sockets=sockets_ok,
                         ok=bool(all_sep and all(v['exists'] for v in sockets_ok.values()) and len(kit_rows) == 12),
                         body_vertex_count_equal_source=bodies[H['body']]['n_verts_equal'])
R['NO_REFIT'] = dict(rows={n: r.get('refit', r) for n, r in kit_rows.items()}, ok=bool(all_refit and len(kit_rows) == 12))
mat_names = sorted(m for m in mats_used if m)
R['BOTH_COLORS'] = dict(collections={c: col_members[c] for c in COLORS}, materials_on_kit_pieces=mat_names,
                        materials_ok=bool(set(mat_names) <= {'Std_White_Lit', 'Std_Black_Lit'}),
                        six_each=bool(all(col_members[c] and len(col_members[c]) == 6 for c in COLORS)),
                        kit_materials_in_file=sorted(m.name for m in bpy.data.materials if m.name.startswith('Std_')))
R['BOTH_COLORS']['ok'] = bool(R['BOTH_COLORS']['materials_ok'] and R['BOTH_COLORS']['six_each'] and R['BOTH_COLORS']['kit_materials_in_file'] == ['Std_Black_Lit', 'Std_White_Lit'])
R['BOTH_SEXES_part'] = dict(polo=H['polo'], bottom=H['bottom'], present=[n for n in kit_rows if H['polo'] in n or H['bottom'] in n])

# RACKET_IN_HAND
hr = bpy.data.objects.get('Hand_Racket')
rk_rows = {}
for n in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap', 'Collider_Racket'):
    o = bpy.data.objects.get(n)
    s_ = rk_src[n]
    rk_rows[n] = dict(exists=bool(o), geometry_equal=bool(o and mesh_geometry_hash(o.data) == s_['geometry']), parent=o.parent.name if o and o.parent else None,
                      expected_parent=s_['parent'], loc_rot_scale_equal=bool(o and [round(x, 6) for x in o.location] == s_['loc'] and [round(x, 6) for x in o.rotation_euler] == s_['rot']
                                                                           and [round(x, 6) for x in o.scale] == s_['scale']))
rig = bpy.data.objects.get('Rig_Hand_R')
dg = bpy.context.evaluated_depsgraph_get()
hand_tree = None
ev = body.evaluated_get(dg)
Xb = np.empty(len(body.data.vertices) * 3, np.float32)
em = ev.to_mesh()
em.vertices.foreach_get('co', Xb)
Tb = np.empty(len(em.loop_triangles) * 3, np.int64) if False else None
ev.to_mesh_clear()
Xb = Xb.reshape(-1, 3).astype(float)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handlib import edges_of, adjacency, hand_region
co_rest = mesh_co(body).astype(float)
adj = adjacency(len(co_rest), edges_of(body.data))
hand = hand_region(co_rest, adj, tag)
inh = np.zeros(len(co_rest), bool)
inh[hand] = True
tris = mesh_tris(body)
T_hand = tris[np.all(inh[tris], axis=1)]
htree = BVHTree.FromPolygons([tuple(map(float, x)) for x in Xb], [tuple(int(i) for i in t) for t in T_hand], epsilon=0.0)
grip = bpy.data.objects['Grip']
gv = mesh_co(grip, world=True)
d_grip = min(htree.find_nearest(Vector(q))[3] for q in gv[::2])
O = np.array(hr.matrix_world.translation)
d_palm = float(np.linalg.norm(Xb[hand] - O, axis=1).min())
chain_ok = bool(rk_rows['Racket_Classic']['parent'] == 'Hand_Racket' and all(rk_rows[n]['parent'] == rk_rows[n]['expected_parent'] for n in rk_rows))
R['RACKET_IN_HAND'] = dict(rows=rk_rows, hand_racket=dict(exists=bool(hr), type=hr.type if hr else None, parent=hr.parent.name if hr and hr.parent else None,
                                                          parent_type=hr.parent_type if hr else None, parent_bone=hr.parent_bone if hr else None,
                                                          world=[round(x, 5) for x in O]),
                           grip_to_evaluated_hand_min_mm=d_grip * 1000, hand_vertex_nearest_to_grip_origin_mm=d_palm * 1000,
                           action=rig.animation_data.action.name if rig and rig.animation_data and rig.animation_data.action else None,
                           socket_ok=bool(hr and hr.parent and hr.parent.name == 'Rig_Hand_R' and hr.parent_type == 'BONE' and hr.parent_bone == 'Hand_R'),
                           chain_ok=chain_ok, geometry_ok=all(r['geometry_equal'] for r in rk_rows.values()),
                           in_hand_measured=bool(d_grip <= 0.003 and d_palm <= 0.045))
R['RACKET_IN_HAND']['ok'] = bool(R['RACKET_IN_HAND']['socket_ok'] and chain_ok and R['RACKET_IN_HAND']['geometry_ok'])
R['RACKET_IN_HAND']['float_label'] = None if R['RACKET_IN_HAND']['in_hand_measured'] else 'FLOAT'
R['visibility'] = dict(Kit_White_hidden_in_viewport=bpy.context.view_layer.layer_collection.children['Kit_White'].hide_viewport,
                       Kit_Black_hidden_in_viewport=bpy.context.view_layer.layer_collection.children['Kit_Black'].hide_viewport)
R['sources_sha_before_verify'] = {k: v == SHA[k] for k, v in src_sha_before.items()}
json.dump(R, open(OUTJSON, 'w'), indent=1, default=str)
print('VERIFY_DONE', tag, {k: R[k].get('ok') for k in ('BODIES', 'KIT_SEPARATE', 'NO_REFIT', 'BOTH_COLORS', 'RACKET_IN_HAND')})
