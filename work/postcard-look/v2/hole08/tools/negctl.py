"""Negative controls for the hole's own re-expressed gates (hole08_look.look_gates): build the look in-process, then apply one mutation at a time and check that
the named gate FAILS (and that the unmutated scene passes everything). Blender -b --factory-startup --python negctl.py"""
import sys, os, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy, numpy as np
from mathutils import Vector
import postcard_lib as P
import postcard_look_lib as L
import postcard_props_lib as PL
import hole08_build as B
import hole08_look as K
YD = P.YD
OUT = REPO + "/work/postcard-look/v2/hole08/scratch/negctl"
os.makedirs(OUT, exist_ok=True)
D = P.start("hole08_design", out_dir=OUT)
P.build_terrain(D); B.weld_terrain(D); B.fix_overhangs(D); B.split_deep_band(D)
P.build_play_surfaces(D); P.build_water(D); B.tidy_all_flat(D); B.trim_lip_off_green(D); P.build_gameplay(D)
info = K.look_pass(D)


def run():
    return {n: (ok, d) for n, ok, d in K.look_gates(D, info)}


base = run()
print("BASE all pass:", all(v[0] for v in base.values()), [n for n, v in base.items() if not v[0]])
results = []


def check(label, mutate, undo, expect):
    mutate()
    bpy.context.view_layer.update()
    r = run()
    failed = sorted(n for n, v in r.items() if not v[0])
    ok = all(e in failed for e in expect)
    print(f"NEGCTL {label}: expected FAIL {expect} -> failed {failed} => {'OK' if ok else 'NOT CAUGHT'}")
    results.append((label, expect, failed, ok))
    undo()
    bpy.context.view_layer.update()


# 1 a stack moved to 12 yd from the centerline -> NEEDLES
st = info["stacks"][0]
mains = st["objs"]
def mv(objs, dx, dy, dz=0.0):
    for o in objs: o.location += Vector((dx, dy, dz))
cen = P.m(0, 0)
check("needle 10 yd from the centerline", lambda: mv(mains, 25.0, 0.0), lambda: mv(mains, -25.0, 0.0), ["NEEDLES"])
# 2 a needle pushed up to 20 m -> NEEDLES (cap)
check("needle summit above 18 m", lambda: mv(mains, 0, 0, 9.0), lambda: mv(mains, 0, 0, -9.0), ["NEEDLES"])
# 3 old needle position in front of the arch opening (design stack 3 at (-14, 160)) -> ARCH_OPENING_CLEAR
s3 = [s for s in info["stacks"] if s["seed"] == 3][0]
ox, oy = P.m(-14.0, 160.0); dx, dy = ox - s3["xy"][0], oy - s3["xy"][1]
check("needle 3 back at its design position (in front of the arch opening)", lambda: mv(s3["objs"], dx, dy), lambda: mv(s3["objs"], -dx, -dy), ["ARCH_OPENING_CLEAR"])
# 4 a boulder hovering 2 m over a pad rim -> ROCKS_CONTACT_CHAIN + ROCKS_REST
land = [o for o in info["rocks"] if world_max < 0 ] if False else None
lr = [o for o in info["rocks"] if K.world_verts([o])[:, 2].max() >= 5.5][0]
check("a land rock hovering 2 m up", lambda: mv([lr], 0, 0, 2.0), lambda: mv([lr], 0, 0, -2.0), ["ROCKS_CONTACT_CHAIN", "ROCKS_REST"])
# 5 a rock on the fairway of the middle pad -> ROCKS_OFF_PLAY_SURFACES
fx, fy = P.m(19.0, 178.0)
z0 = K.world_verts([lr])
cx0, cy0 = z0[:, 0].mean(), z0[:, 1].mean()
check("a rock stands on the landing fairway", lambda: mv([lr], fx - cx0, fy - cy0, 0.0), lambda: mv([lr], -(fx - cx0), -(fy - cy0), 0.0), ["ROCKS_OFF_PLAY_SURFACES"])
# 6 a big rock stands on the tee camera's line of play -> LINES_OF_PLAY_VISIBLE
tx, ty = P.m(8.0, 60.0)
check("a boulder on the line of play 60 yd from the tee, 6 m tall", lambda: (setattr(lr, 'scale', (2.0, 2.0, 2.0)), mv([lr], tx - cx0, ty - cy0, 1.6)),
      lambda: (setattr(lr, 'scale', (1.0, 1.0, 1.0)), mv([lr], -(tx - cx0), -(ty - cy0), -1.6)), ["LINES_OF_PLAY_VISIBLE"])
# 7 fallen block lifted off the outcrop -> ARCH_FALLEN_BLOCKS_REST
fb = info["arch"]["fallen"][0]
check("a fallen block hovering 1 m over the outcrop", lambda: mv([fb], 0, 0, 1.0), lambda: mv([fb], 0, 0, -1.0), ["ARCH_FALLEN_BLOCKS_REST"])
# 8 arch shifted 3 m off its outcrop -> ARCH
ar = info["arch"]["arch"]
check("the arch shifted 4 m off the outcrop", lambda: mv([ar], -4.0, 0, 0), lambda: mv([ar], 4.0, 0, 0), ["ARCH"])
# 9 a needle right behind the flag seen from the middle pad camera -> NEEDLES_NOT_BEHIND_TARGETS
pin = P.m(*D.hole.pin)
cam = P.m(19.0, 178.0)
dv = Vector((pin[0] - cam[0], pin[1] - cam[1], 0)).normalized()
s9 = info["stacks"][8]
tgt = Vector((pin[0], pin[1], 0)) + dv * 40.0
dx, dy = tgt.x - s9["xy"][0], tgt.y - s9["xy"][1]
check("a needle straight behind the flag seen from the middle pad", lambda: mv(s9["objs"], dx, dy), lambda: mv(s9["objs"], -dx, -dy), ["NEEDLES_NOT_BEHIND_TARGETS"])
# 10 the tee box back to LK_GREEN -> MOW_PATTERN
tbm = bpy.data.objects["TEE_BOX"].data
fw_mat, gr_mat = tbm.materials[0], bpy.data.materials["LK_GREEN"]
check("the tee box back on LK_GREEN", lambda: tbm.materials.__setitem__(0, gr_mat), lambda: tbm.materials.__setitem__(0, fw_mat), ["MOW_PATTERN"])
# 11 the tee box UV scaled x3 (a 3x denser tile) -> MOW_PATTERN (UV density)
import numpy as _np
_lay = tbm.uv_layers.active.data
_uv0 = _np.array([l.uv[:] for l in _lay])
def _scale(f):
    for l, q in zip(_lay, _uv0): l.uv = (q[0] * f, q[1] * f)
check("the tee box UV scaled x3", lambda: _scale(3.0), lambda: _scale(1.0), ["MOW_PATTERN"])
# 12 the fairway stripe shift removed (U - 0.2 on every FAIRWAY loop) -> MOW_PATTERN (stripe phase)
_fw = bpy.data.objects["FAIRWAY"].data
_flay = _fw.uv_layers.active.data
_fuv0 = _np.array([l.uv[:] for l in _flay])
def _shift_fw(dx):
    for l, q in zip(_flay, _fuv0): l.uv = (q[0] + dx, q[1])
check("the fairway stripe shift removed", lambda: _shift_fw(-K.FAIRWAY_STRIPE_SHIFT), lambda: _shift_fw(0.0), ["MOW_PATTERN"])
# 13 the tee path moved 2.2 m towards the tee ball (round 3: the address balls stay 0.5 m off the stones) -> PATH_CLEAR_OF_BALL
_tp = [o for o in bpy.data.objects if o.name.startswith("DRESS_PATH_01")]
check("the tee path moved 2.2 m onto the tee ball", lambda: mv(_tp, 2.2, 0.0), lambda: mv(_tp, -2.2, 0.0), ["PATH_CLEAR_OF_BALL"])
# 14 the tee box back to the round-4 cross-mown UV (u = arc / 10 + 0.8, v = -lateral / 10: stripes turned 90 degrees at the seam) -> TEE_SEAM_SEEN (round 6: the old plan-view TEE_SEAM_UV is retired)
_tile = L.LOOK["LK_FAIRWAY"][2]
_cl = L.CenterlineParam(D)
_tb = bpy.data.objects["TEE_BOX"]
_tmw = _np.array(_tb.matrix_world)
_Vw = _np.array([_tb.data.vertices[l.vertex_index].co[:] for l in _tb.data.loops]) @ _tmw[:3, :3].T + _tmw[:3, 3]
_lat, _arc = _cl.uv(_Vw[:, 0], _Vw[:, 1])
_uv_seamless = _np.array([l.uv[:] for l in _lay])
def _tee_cross(on):
    uv = _np.stack([_arc / _tile + K.TEE_CROSS_PHASE, -_lat / _tile], 1) if on else _uv_seamless
    _lay.foreach_set("uv", uv.ravel())
_uv_hidden = _np.array([l.uv[:] for l in _lay])           # round 6: the tee box UV with the hidden-band shift (the build's)
check("the tee box back on the cross-mown (90 degree) stripes", lambda: _tee_cross(True), lambda: _lay.foreach_set("uv", _uv_hidden.ravel()), ["TEE_SEAM_SEEN"])
# 15 the tee path bent right just before the tee box's front edge (x += 0.6 (y - 1.5) for y > 1.5 m): its edge now leans away from the line of sight there -> PATH_SEAM_JUMP
_p1 = [o for o in bpy.data.objects if o.name.startswith("DRESS_PATH_01")][0]
def _bend(k):
    for v in _p1.data.vertices:
        if v.co.y > 1.5:
            v.co.x += k * (v.co.y - 1.5)
    _p1.data.update()
check("the tee path bent right before the tee box's front edge", lambda: _bend(0.6), lambda: _bend(-0.6), ["PATH_SEAM_JUMP"])
# 16 one capping-ledge face back to dark LK_CLIFF -> LEDGES_ARE_TURF
_sk = None
for _o in [o for o in bpy.data.objects if o.name.startswith("ROCK_SKIN_")]:
    _names = [m.name.split(".")[0] if m else "" for m in _o.data.materials]
    if "LK_ROUGH" in _names and "LK_CLIFF" in _names:
        _sk = _o
        break
_rs, _cs = [i for i, n_ in enumerate([m.name.split(".")[0] if m else "" for m in _sk.data.materials]) if n_ == "LK_ROUGH"][0], [i for i, n_ in enumerate([m.name.split(".")[0] if m else "" for m in _sk.data.materials]) if n_ == "LK_CLIFF"][0]
_fi = next(p_.index for p_ in _sk.data.polygons if p_.material_index == _rs)            # by index: a polygon reference goes stale when the mesh is touched
check("one capping-ledge face back on dark LK_CLIFF", lambda: setattr(_sk.data.polygons[_fi], "material_index", _cs), lambda: setattr(_sk.data.polygons[_fi], "material_index", _rs), ["LEDGES_ARE_TURF"])
# 17 the bunker lip back on LK_GREEN -> BUNKER_LIP_NOT_GREEN
_lm = bpy.data.objects["BUNKER_01_LIP"].data
_rough_m = _lm.materials[0]
check("the bunker lip back on LK_GREEN", lambda: _lm.materials.__setitem__(0, bpy.data.materials["LK_GREEN"]), lambda: _lm.materials.__setitem__(0, _rough_m), ["BUNKER_LIP_NOT_GREEN"])
# 18 the outcrop vines carried 6 m away from the rock -> OUTCROP_VINES
_ov = [o for o in info["outcrop_vines"] if o.name in bpy.data.objects]
check("the outcrop vines 6 m off the rock", lambda: mv(_ov, 6.0, 0.0, 0.0), lambda: mv(_ov, -6.0, 0.0, 0.0), ["OUTCROP_VINES"])
# round 6 controls
# 19 the tee box on the plain FAIRWAY mapping (round 5: no shift for the 0.35 m band the 10 cm step hides) -> TEE_SEAM_SEEN
def _tee_plain(on):
    uv = _np.stack([_lat / _tile + K.FAIRWAY_STRIPE_SHIFT, _arc / _tile], 1) if on else _uv_hidden
    _lay.foreach_set("uv", uv.ravel())
check("the tee box UV without the hidden-band shift (round 5)", lambda: _tee_plain(True), lambda: _tee_plain(False), ["TEE_SEAM_SEEN"])
# 20 the path's plate part sunk back under the plate along the front edge (round 5: ribbon draped on the lowest ground of its cells) -> PATH_STEP_CONTINUOUS (a grass strip across the stones)
_poly, _zt = K._plate_poly("TEE_BOX")
_pv = _p1.data.vertices
_sunk = [v.index for v in _pv if v.co.z > _zt and -0.40 < K._poly_sd(_poly, [v.co.x], [v.co.y])[0] < 0.0]
def _sink(dz):
    for i in _sunk: _pv[i].co.z += dz
    _p1.data.update()
check("the path's plate part sunk under the plate near the front edge (round 5 draping)", lambda: _sink(-0.10), lambda: _sink(0.10), ["PATH_STEP_CONTINUOUS"])
# 21 the stones beyond the plate edge shifted by 15 cm along the path (the hidden band not compensated, as in round 5) -> PATH_STEP_CONTINUOUS (texture jump)
_play = _p1.data.uv_layers.active.data
_far_loops = [li for li, l in enumerate(_p1.data.loops) if K._poly_sd(_poly, [_pv[l.vertex_index].co.x], [_pv[l.vertex_index].co.y])[0] > 0.0 and _pv[l.vertex_index].co.y > 0.0]
def _slide(dv):
    for li in _far_loops:
        u_, v_ = _play[li].uv
        _play[li].uv = (u_, v_ + dv)
check("the stones beyond the plate edge slid 15 cm (hidden band not compensated)", lambda: _slide(0.03), lambda: _slide(-0.03), ["PATH_STEP_CONTINUOUS"])
# 22 the outcrop's turf bank back on bare LK_ROCK -> ARCH_SLAB_COVERED
_oc = info["arch"]["outcrop"]
_om = _oc.data
_onames = [m.name.split(".")[0] if m else "" for m in _om.materials]
_i_rock, _i_rough = _onames.index("LK_ROCK"), _onames.index("LK_ROUGH")
_omw = _np.array(_oc.matrix_world)
_turf_idx = [p_.index for p_ in _om.polygons if p_.material_index == _i_rough and (_omw @ _np.append(_np.array(p_.center), 1.0))[2] < info["arch"]["centre"][2] - 0.05]
def _bank(to_rock):
    for i in _turf_idx: _om.polygons[i].material_index = _i_rock if to_rock else _i_rough
    _om.update()
check("the outcrop wall back on bare rock (round 5)", lambda: _bank(True), lambda: _bank(False), ["ARCH_SLAB_COVERED", "ARCH_LEFT_STRIP_COVERED"])
# ---------------------------------------------------------------- round 8 controls (grass fringe, arch fold, vine roots, crown tufts)
fr = [o for o in info["fringe_objs"] if o.name in bpy.data.objects]
def _loc(o, v):
    o.location = Vector(v)
# 23 the outcrop's custom normals replaced by flat face normals (the round-7 hard fold) -> ARCH_FOLD_SOFT
_ocm = info["arch"]["outcrop"].data
_ocm.calc_loop_triangles()
_cn0 = _np.empty(len(_ocm.loops) * 3); _ocm.corner_normals.foreach_get("vector", _cn0)
_flat = _np.empty(len(_ocm.loops) * 3)
for _p in _ocm.polygons:
    for _i in range(_p.loop_start, _p.loop_start + _p.loop_total):
        _flat[_i * 3:_i * 3 + 3] = _p.normal[:]
check("the outcrop's rim shading flat again (round 7: one-pixel 60-75 degree normal step)", lambda: _ocm.normals_split_custom_set(_flat.reshape(-1, 3).tolist()), lambda: _ocm.normals_split_custom_set(_cn0.reshape(-1, 3).tolist()), ["ARCH_FOLD_SOFT"])
# 24-27 a fringe tuft on the fairway / in the sea / 1.5 m from the approach ball / a 1.2 m tuft in the corridor
_t0 = fr[0]
_o0 = tuple(_t0.location)
_sc0 = tuple(_t0.scale)
_mx, _my = P.m(19.0, 150.0)
check("a fringe tuft in the middle of the fairway", lambda: _loc(_t0, (_mx, _my, 6.14)), lambda: _loc(_t0, _o0), ["GRASS_NOT_ON_PLAY_SURFACES"])
_sx, _sy = P.m(60.0, 100.0)
check("a fringe tuft in the sea", lambda: _loc(_t0, (_sx, _sy, 0.0)), lambda: _loc(_t0, _o0), ["GRASS_NOT_ON_WATER"])
_bx, _by = P.m(19.0, 178.0)
check("a fringe tuft 1.5 m from the approach ball", lambda: _loc(_t0, (_bx + 1.5, _by, 6.14)), lambda: _loc(_t0, _o0), ["GRASS_BALL_CLEAR"])
_near = min(fr, key=lambda o: abs(o.location.x - _bx) + abs(o.location.y - _by))
_nsc = tuple(_near.scale)
check("a 1.2 m tuft in the ball corridor (scale x 2 on the nearest fringe tuft)", lambda: setattr(_near, "scale", (2.0, 2.0, 2.0)), lambda: setattr(_near, "scale", _nsc), ["GRASS_BALL_CLEAR"])
_px, _py = P.m(*D.hole.pin)
check("a fringe tuft 3 m from the pin", lambda: _loc(_t0, (_px + 3.0, _py, 6.0)), lambda: _loc(_t0, _o0), ["GRASS_BALL_CLEAR"])
# 28 the fringe thinned to 100 tufts -> GRASS_FRINGE_PRESENT
_full = list(info["fringe_objs"])
check("only 100 fringe tufts left", lambda: info.__setitem__("fringe_objs", _full[:100]), lambda: info.__setitem__("fringe_objs", _full), ["GRASS_FRINGE_PRESENT"])
# 29 the triangle cap at 150k -> GRASS_TRI_BUDGET
_cap0 = K.TRI_CAP
check("the triangle cap at 150k", lambda: setattr(K, "TRI_CAP", 150000), lambda: setattr(K, "TRI_CAP", _cap0), ["GRASS_TRI_BUDGET"])
# 30 an island tuft on the outcrop's rim (0 m) -> GRASS_OUTCROP_FRINGE
_of = [o for o in bpy.data.objects if o.type == 'MESH' and "lk_outcrop_fringe" in o.keys()]
_rim = K._outcrop_rim(info["arch"]["outcrop"], info["arch"]["centre"][2])
_ot = _of[0]
_oo = tuple(_ot.location)
check("an island tuft standing on the rim line", lambda: _loc(_ot, (float(_rim[0][0]), float(_rim[0][1]), _oo[2])), lambda: _loc(_ot, _oo), ["GRASS_OUTCROP_FRINGE"])
# 31 a crown tuft 5 m away from its stack -> CROWN_TUFTS
_ct = info["crowns"]["objs"][0]
_co = tuple(_ct.location)
check("a crown tuft 5 m beside its stack", lambda: _loc(_ct, (_co[0] + 5.0, _co[1], _co[2])), lambda: _loc(_ct, _co), ["CROWN_TUFTS"])
# 32 a vine 0.5 m off its wall -> VINE_ROOT_GAP
_vn = info["vines"][3]
_vo = tuple(_vn.location)
check("a cliff vine hanging 0.5 m off the wall", lambda: _loc(_vn, (_vo[0] + 0.5 * math.sin(_vn.rotation_euler.z), _vo[1] - 0.5 * math.cos(_vn.rotation_euler.z), _vo[2])), lambda: _loc(_vn, _vo), ["VINE_ROOT_GAP"])
bad = [r for r in results if not r[3]]
print(f"NEGCTL SUMMARY {len(results) - len(bad)}/{len(results)} mutations caught; base scene passes every gate: {all(v[0] for v in base.values())}")
