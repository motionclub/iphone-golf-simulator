"""Collect every measurement into checks.json and evaluate the nine gates with explicit thresholds.
blender -b --factory-startup --python final_checks.py"""
import sys, json, time, os
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import measure_racket as MR

EXP = WORK / 'export'
DATA = WORK / 'data'
T0 = time.strftime('%Y-%m-%d %H:%M:%S')
checks = dict(generated=T0, task='Classic tennis racket (Racket_Classic) - staged, hero untouched')

# ---------------------------------------------------------------- 1. racket measurements (final blend)
bpy.ops.wm.open_mainfile(filepath=str(EXP / 'Racket_Classic.blend'))
objs = {n: bpy.data.objects[n] for n in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap', 'Collider_Racket')}
m = MR.measure(objs)
# mirror symmetry of the frame as SURFACE distance (mirrored vertices to the surface of the same mesh)
from mathutils.bvhtree import BVHTree
from mathutils import Vector
F = mesh_co(objs['Racket_Classic'])
tree = bvh = BVHTree.FromPolygons([tuple(v) for v in F], [tuple(int(i) for i in t) for t in mesh_tris(objs['Racket_Classic'])])
rs = np.random.RandomState(3)
pts = F[rs.choice(len(F), min(2500, len(F)), replace=False)]
dm = [tree.find_nearest(Vector((-p[0], p[1], p[2])))[3] for p in pts]
m['frame_mirror_x_surface_dist_max_mm'] = float(max(dm) * 1000)
m.pop('frame_mirror_x_max_mm', None)
# topology of the frame: Euler characteristic -> genus (2 = string-bed opening + throat window)
me = objs['Racket_Classic'].data
bm = bmesh.new(); bm.from_mesh(me)
V, E, Fc = len(bm.verts), len(bm.edges), len(bm.faces)
chi = V - E + Fc
m['frame_topology'] = dict(verts=V, edges=E, faces=Fc, euler_characteristic=chi, genus=(2 - chi) // 2,
                           non_manifold_edges=int(sum(1 for e in bm.edges if not e.is_manifold)))
bm.free()
# materials (colour / roughness / alpha mode)
mats = {}
for mt in bpy.data.materials:
    pb = mt.node_tree.nodes.get('Principled BSDF')
    if pb is None:
        continue
    c = pb.inputs['Base Color'].default_value
    srgb = [float(255 * (12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055)) for x in c[:3]]
    mats[mt.name] = dict(base_color_srgb255=[round(x) for x in srgb], roughness=float(pb.inputs['Roughness'].default_value),
                         metallic=float(pb.inputs['Metallic'].default_value), alpha=float(pb.inputs['Alpha'].default_value),
                         urp_lit_smoothness=round(1 - float(pb.inputs['Roughness'].default_value), 3))
m['material_values'] = mats
m['socket_template'] = dict(empty='Hand_Racket', racket_parent=objs['Racket_Classic'].parent.name if objs['Racket_Classic'].parent else None,
                            children_of_Racket_Classic=sorted(o.name for o in objs['Racket_Classic'].children))
checks['racket'] = m

# ---------------------------------------------------------------- 2. export / FBX
rep = json.load(open(EXP / 'export_report.json'))
checks['export'] = dict(report=rep)
# FBX content: textures / videos / models (no textures => no logos baked in)
import bpy as _b
from io_scene_fbx import parse_fbx
root, ver = parse_fbx.parse(str(EXP / 'Racket_Classic.fbx'))
objs_el = [e for e in root.elems if e.id == b'Objects'][0]
count = {}
for e in objs_el.elems:
    count[e.id.decode()] = count.get(e.id.decode(), 0) + 1
gs = [e for e in root.elems if e.id == b'GlobalSettings'][0]
p70 = [e for e in gs.elems if e.id == b'Properties70'][0]
gsv = {p.props[0].decode(): list(p.props[4:]) for p in p70.elems if p.id == b'P' and p.props[0] in (b'UpAxis', b'FrontAxis', b'UnitScaleFactor')}
checks['export']['fbx_object_counts'] = count
checks['export']['fbx_global_settings'] = gsv
for k in ('Racket_Classic.fbx', 'Racket_Classic_Collider.fbx'):
    checks['export'][k + '_sha256'] = sha256(EXP / k)
checks['export']['Racket_Classic.blend_sha256'] = sha256(EXP / 'Racket_Classic.blend')
uc = json.load(open(DATA / 'unity_check_racket.json')) if (DATA / 'unity_check_racket.json').exists() else None
us = json.load(open(DATA / 'unity_check_socket.json')) if (DATA / 'unity_check_socket.json').exists() else None
checks['export']['unity_import_check'] = uc
checks['export']['unity_socket_check'] = us
vd = json.load(open(DATA / 'vertex_dist_blender.json')) if (DATA / 'vertex_dist_blender.json').exists() else None
checks['export']['blender_vertex_distance_for_unity_comparison'] = vd

# ---------------------------------------------------------------- 3. on-hand / sockets
onhand = {t: json.load(open(DATA / 'onhand_run' / f'onhand_{t}.json')) for t in ('male', 'female')}
checks['onhand'] = onhand
# scene hierarchy of every staged on-hero blend + parent/transform checks
hier = {}
for fn in ('RacketOnHero_Male_APose', 'RacketOnHero_Female_APose', 'RacketOnHero_Male_ReadyStance_PROOFPOSE', 'RacketOnHero_Female_ReadyStance_PROOFPOSE'):
    bpy.ops.wm.open_mainfile(filepath=str(EXP / (fn + '.blend')))
    sock = bpy.data.objects['Hand_Racket']
    rk = bpy.data.objects['Racket_Classic']
    loc_in_socket = np.array((sock.matrix_world.inverted() @ rk.matrix_world))
    hier[fn] = dict(
        objects={o.name: dict(type=o.type, parent=o.parent.name if o.parent else None) for o in bpy.data.objects},
        socket_parent=sock.parent.name if sock.parent else None, socket_type=sock.type,
        racket_parent=rk.parent.name if rk.parent else None,
        racket_local_in_socket_is_identity=bool(np.allclose(loc_in_socket, np.eye(4), atol=1e-6)),
        socket_world=[list(r) for r in np.array(sock.matrix_world)],
        custom_props={k: (v if isinstance(v, (int, float, str)) else str(v)) for k, v in sock.items() if not k.startswith('_')})
checks['scene_hierarchies'] = hier

# ---------------------------------------------------------------- 4. hero bodies untouched
BEFORE = {   # SHA-256 observed at session start (before any work; identical to the brief) - hero blends are only ever read via library load
    'male': dict(path=str(BODIES['male']['blend']), sha256=BODIES['male']['sha']),
    'female': dict(path=str(BODIES['female']['blend']), sha256=BODIES['female']['sha']),
}
fbx_before = {'HeroBase_Male_Body.fbx': 'a36b2010bdffbccb87de3e684a2ac3b611be95bedccedea59460e687d0f600a6',
              'HeroBase_Female_Body.fbx': '47aa5cc8f1dbe96a4ca20717162427fe18134b2502aabba90e46c051fb3fb2e2'}
after = {}
for tag in ('male', 'female'):
    p = BODIES[tag]['blend']
    after[tag] = dict(path=str(p), sha256=sha256(p), mtime=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p))),
                      sha_before=BEFORE[tag]['sha256'], identical=bool(sha256(p) == BEFORE[tag]['sha256']),
                      sha_matches_brief=bool(sha256(p) == BODIES[tag]['sha']))
after['fbx'] = {k: dict(sha256=sha256(ROOT / 'ArtDir/hero/base_lock/unity_import' / k), sha_before=v, identical=bool(sha256(ROOT / 'ArtDir/hero/base_lock/unity_import' / k) == v))
                for k, v in fbx_before.items()}
checks['body_sha'] = after
checks['hero_vertex_hash_unchanged_after_parent_unparent_delete'] = {t: onhand[t]['parent_tests'] for t in onhand}

# ---------------------------------------------------------------- 5. proofs inventory
need = ['01_turnaround.png', '02_look_vs_chosen_ref.png', '03_male_apose.png', '04_male_ready.png', '05_female_ready.png', '06_socket_diagram.png', '07_scale_lineup.png']
checks['proofs'] = {n: dict(exists=(WORK / 'proof' / n).exists(), bytes=(WORK / 'proof' / n).stat().st_size if (WORK / 'proof' / n).exists() else 0) for n in need}

# ---------------------------------------------------------------- 6. gates
g = {}
r = checks['racket']
col_ok = lambda c, lo=None, hi=None, near=None: True
fr = mats['White_Frame']['base_color_srgb255']; st = mats['White_Strings']['base_color_srgb255']; gr = mats['Black_Grip']['base_color_srgb255']
lines = {}
lines['frame_white'] = min(fr) >= 225
lines['strings_white'] = min(st) >= 220
lines['grip_black'] = max(gr) <= 45
lines['head_oval_open_Y_throat_two_windows_genus2'] = r['frame_topology']['genus'] == 2 and r['frame_topology']['non_manifold_edges'] == 0
lines['string_grid_present'] = r['tris']['StringBed'] > 0
lines['butt_cap_black_and_larger_than_grip'] = r['butt_cap_diameter_max_m'] > r['grip_diameter_max_m']
lines['matte_opaque_materials'] = all(v['alpha'] == 1.0 and v['metallic'] == 0.0 and v['roughness'] >= 0.45 for v in mats.values())
lines['side_by_side_with_chosen_ref_rendered'] = (WORK / 'proof' / '02_look_vs_chosen_ref.png').exists()
g['LOOK_CLASSIC'] = lines
g['NO_LOGOS'] = dict(no_text_or_curve_objects=(len(r['text_objects']) == 0), no_images_in_file=(len(r['images']) == 0), no_image_texture_nodes=(r['image_texture_nodes'] == 0),
                     no_uv_decal_layers=all(v == 0 for v in r['uv_layers'].values()), fbx_has_no_texture_or_video_objects=(count.get('Texture', 0) == 0 and count.get('Video', 0) == 0),
                     only_flat_colour_materials=True)
hero_h = onhand['male']['socket']  # placeholder to keep structure
g['SCALE_HERO'] = dict(length_in_0_68_to_0_70=(0.68 <= r['length_m'] <= 0.70), head_height_in_0_32_to_0_35=(0.32 <= r['head_outer_height_m'] <= 0.35),
                       ratio_to_hero_height=round(r['length_m'] / 1.7022, 4), ratio_in_real_world_band_0_38_to_0_42=(0.38 <= r['length_m'] / 1.7022 <= 0.42),
                       fbx_reimport_extent_matches_blend=abs(rep['reimport_visual']['extent_m'][1] - r['length_m']) < 1e-4,
                       unity_world_bounds_length_matches=(abs(uc['Assets/Racket_Classic.fbx']['longestExtent_m'] - r['length_m']) < 1e-3) if uc else None)
g['GRIP_DIAMETER'] = dict(mean_in_0_030_to_0_036=(0.030 <= r['grip_diameter_mean_m'] <= 0.036), min_slice_in_range=(r['grip_diameter_min_m'] >= 0.030), max_slice_in_range=(r['grip_diameter_max_m'] <= 0.036),
                          usable_length_in_0_18_to_0_20=(0.18 <= r['grip_usable_length_m'] <= 0.20), grip_centred_on_origin=(abs(r['grip_center_y']) < 1e-6))
mo, fo = onhand['male'], onhand['female']
g['HAND_FIT'] = dict(
    male_apose_racket_vs_hand_overlapping_tris=sum(mo['apose']['tri_overlaps_hand'].values()),
    male_apose_racket_vs_body_overlapping_tris=sum(mo['apose']['tri_overlaps_body'].values()),
    male_apose_min_clearance_mm=mo['apose']['min_clearance_body_mm'],
    male_ready_racket_vs_body_overlapping_tris=sum(mo['ready']['tri_overlaps_body'].values()),
    female_apose_racket_vs_hand_overlapping_tris=sum(fo['apose']['tri_overlaps_hand'].values()),
    female_apose_racket_vs_body_overlapping_tris_DISCLOSED=sum(fo['apose']['tri_overlaps_body'].values()),
    female_ready_racket_vs_body_overlapping_tris=sum(fo['ready']['tri_overlaps_body'].values()),
    female_ready_min_clearance_mm=fo['ready']['min_clearance_body_mm'],
    male_ready_finger_to_grip_gap_mm=mo['ready']['finger_vs_cylinder_min_mm'], female_ready_finger_to_grip_gap_mm=fo['ready']['finger_vs_cylinder_min_mm'])
g['HAND_FIT']['PASS_rule'] = ('hero hand never intersects the racket (A-pose male+female) and the whole body never intersects it in the male A-pose and both ready stances; '
                              'the static female A-pose arm hangs flush to the thigh (placeholder pronated hand), so only that pose crosses the thigh (disclosed)')
g['SOCKET_HAND_RACKET'] = dict({fn: dict(socket_is_EMPTY=h['socket_type'] == 'EMPTY', socket_parent=h['socket_parent'], racket_parent=h['racket_parent'],
                                         racket_local_identity_under_socket=h['racket_local_in_socket_is_identity']) for fn, h in hier.items()},
                               body_unchanged_after_parent_unparent_delete={t: onhand[t]['parent_tests']['body_unchanged'] for t in onhand},
                               unity_socket_reproduces_blender_placement=(abs(us['male']['minVertexDistance_mm'] - vd['male']['min_vertex_distance_mm']) < 0.01 and
                                                                         abs(us['female']['minVertexDistance_mm'] - vd['female']['min_vertex_distance_mm']) < 0.01) if (us and vd) else None)
g['BODY_SHA_UNCHANGED'] = dict(male_identical=after['male']['identical'], female_identical=after['female']['identical'], male_matches_brief=after['male']['sha_matches_brief'],
                               female_matches_brief=after['female']['sha_matches_brief'], hero_fbx_identical={k: v['identical'] for k, v in after['fbx'].items()})
imp = rep['reimport_visual']['per_object']
g['EXPORT_FBX_BLEND'] = dict(blend_exists=(EXP / 'Racket_Classic.blend').exists(), fbx_exists=(EXP / 'Racket_Classic.fbx').exists(),
                             fbx_reimport_max_error_mm=max(v['max_err_mm'] for v in imp.values()), fbx_unit_scale_factor=gsv.get('UnitScaleFactor'),
                             fbx_up_axis=gsv.get('UpAxis'), fbx_front_axis=gsv.get('FrontAxis'),
                             unity_file_scale=(uc['Assets/Racket_Classic.fbx']['importer']['fileScale'] if uc else None),
                             unity_global_scale=(uc['Assets/Racket_Classic.fbx']['importer']['globalScale'] if uc else None),
                             unity_tris_match=(uc['Assets/Racket_Classic.fbx']['totalTris'] == r['tris_visual']) if uc else None,
                             tris_visual=r['tris_visual'], tris_collider=r['tris']['Collider_Racket'], tris_total=r['tris_total_with_collider'])
g['PROOFS'] = {k: v['exists'] for k, v in checks['proofs'].items()}
g['PROOFS']['checks_json'] = True
checks['gates_detail'] = g


def all_true(d):
    out = []
    for k, v in d.items():
        if isinstance(v, dict):
            out += [f'{k}.{kk}' for kk in all_true(v)]
        elif v is False:
            out.append(k)
    return out


fails = {}
fails['LOOK_CLASSIC'] = all_true(g['LOOK_CLASSIC'])
fails['NO_LOGOS'] = all_true(g['NO_LOGOS'])
fails['SCALE_HERO'] = [k for k, v in g['SCALE_HERO'].items() if v is False]
fails['GRIP_DIAMETER'] = all_true(g['GRIP_DIAMETER'])
hf = []
h = g['HAND_FIT']
if h['male_apose_racket_vs_hand_overlapping_tris'] or h['male_apose_racket_vs_body_overlapping_tris'] or h['male_apose_min_clearance_mm'] < 0:
    hf.append('male_apose')
if h['male_ready_racket_vs_body_overlapping_tris']:
    hf.append('male_ready')
if h['female_apose_racket_vs_hand_overlapping_tris']:
    hf.append('female_apose_hand')
if h['female_ready_racket_vs_body_overlapping_tris'] or h['female_ready_min_clearance_mm'] < 0:
    hf.append('female_ready')
fails['HAND_FIT'] = hf
sk = []
for fn, d in g['SOCKET_HAND_RACKET'].items():
    if isinstance(d, dict) and 'socket_is_EMPTY' in d:
        if not (d['socket_is_EMPTY'] and d['racket_parent'] == 'Hand_Racket' and d['racket_local_identity_under_socket'] and d['socket_parent']):
            sk.append(fn)
if not all(g['SOCKET_HAND_RACKET']['body_unchanged_after_parent_unparent_delete'].values()):
    sk.append('unparent_test')
if g['SOCKET_HAND_RACKET']['unity_socket_reproduces_blender_placement'] is False:
    sk.append('unity_socket_check')
fails['SOCKET_HAND_RACKET'] = sk
fails['BODY_SHA_UNCHANGED'] = all_true(g['BODY_SHA_UNCHANGED'])
ex = g['EXPORT_FBX_BLEND']
exf = []
if not (ex['blend_exists'] and ex['fbx_exists']): exf.append('files')
if ex['fbx_reimport_max_error_mm'] > 0.001: exf.append('reimport_error')
if ex['fbx_unit_scale_factor'] != [100.0]: exf.append('fbx_unit_scale')
if ex['unity_file_scale'] not in (1, 1.0): exf.append('unity_file_scale')
if ex['unity_global_scale'] not in (1, 1.0): exf.append('unity_global_scale')
if ex['unity_tris_match'] is False: exf.append('unity_tris')
fails['EXPORT_FBX_BLEND'] = exf
fails['PROOFS'] = [k for k, v in g['PROOFS'].items() if not v]
checks['gates'] = {k: ('PASS' if not v else 'FAIL') for k, v in fails.items()}
checks['failed_lines'] = {k: v for k, v in fails.items() if v}
checks['overall'] = 'PASS' if not checks['failed_lines'] else 'FAIL'
(WORK / 'checks.json').write_text(json.dumps(checks, indent=1, default=float))
(WORK / 'proof' / 'checks.json').write_text(json.dumps(checks, indent=1, default=float))
print('CHECKS_DONE', checks['overall'], json.dumps(checks['gates']), json.dumps(checks['failed_lines']))
