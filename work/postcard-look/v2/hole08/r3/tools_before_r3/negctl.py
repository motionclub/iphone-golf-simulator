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
bad = [r for r in results if not r[3]]
print(f"NEGCTL SUMMARY {len(results) - len(bad)}/{len(results)} mutations caught; base scene passes every gate: {all(v[0] for v in base.values())}")
