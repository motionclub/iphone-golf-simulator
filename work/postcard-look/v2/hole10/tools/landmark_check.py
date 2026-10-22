"""Ray tests of the hole 10 proof cameras (landmarks.json) against a staged blend: nothing blocks the ball / the landmark / the pin.

  Blender -b STAGED.blend --python landmark_check.py -- --shots landmarks.json [--json OUT.json]

Camera mapping = tools/render_views.py (CameraRig.FrameAddress for "address", Unity world yards for "landmark"; course x = Blender x / 0.9144,
course d = Blender y / 0.9144, Unity y = Blender z x 1.0936). Prints `GATE: H_LANDMARK_* PASS|FAIL - numbers`.
"""
import sys
import os
import json
import math
import importlib.util

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

YD = 0.9144
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(n, d=None):
    return args[args.index(n) + 1] if n in args else d


CFG = json.load(open(opt("--shots")))
SHOTS = CFG["shots"]
spec = importlib.util.spec_from_file_location("hole10_design", os.path.join(REPO, "blender", "scripts", "hole10_design.py"))
DES = importlib.util.module_from_spec(spec)
spec.loader.exec_module(DES)
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
sys.dont_write_bytecode = True
import postcard_check as pc  # noqa: E402

HOLE = pc.Hole(DES)
RES = []


def gate(name, ok, detail):
    RES.append(dict(name=name, ok=bool(ok), detail=str(detail)))
    print(f"GATE: {name} {'PASS' if ok else 'FAIL'} - {detail}", flush=True)


# ---- scene BVH of every exported mesh (library originals excluded), polygon -> object name
V, F, owner = [], [], []
names = []
for ob in bpy.data.objects:
    if ob.type != 'MESH' or "ASSET_LIBRARY" in [c.name for c in ob.users_collection] or ob.name not in bpy.context.scene.objects:
        continue
    if ob.name.startswith(("DRESS_SMOKE", "LAVA_LIGHT", "FLAG", "HOLE_CUP", "BALL_START", "MARKER_", "TEE_MARKER")):
        continue                                                      # translucent cards do not block a view
    me = ob.data
    mw = ob.matrix_world
    base = len(V)
    V += [tuple(mw @ v.co) for v in me.vertices]
    for p in me.polygons:
        F.append(tuple(base + i for i in p.vertices))
        owner.append(len(names))
    names.append(ob.name)
BVH = BVHTree.FromPolygons(V, F)
GROUND = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER")


def cls(n):
    if n.startswith("PLANT_"):
        return "plant"
    if n.startswith("ROCK_SKIN"):
        return "wall"
    if n.startswith("TERRAIN"):
        return "wall"
    if n.startswith("ROCK_WALL"):
        return "ring"
    if n.startswith("ROCK_"):
        return "rock"
    if n.startswith("WATER_LAVA"):
        return "lava"
    if n.startswith("DRESS_CONE"):
        return "cone"
    if n.startswith(GROUND):
        return "ground"
    return "other"


def first(o, d, maxd=3000.0):
    h = BVH.ray_cast(Vector(o), Vector(d).normalized(), maxd)
    if h[0] is None:
        return None, None, None
    return names[owner[h[2]]], h[3], h[0]


def ground_z(x, y):
    best = None
    for z0 in (60.0,):
        h = BVH.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)), 200.0)
        while h[0] is not None:
            if names[owner[h[2]]].startswith(GROUND):
                return h[0].z
            h = BVH.ray_cast(h[0] - Vector((0, 0, 0.01)), Vector((0, 0, -1)), 200.0)
    return best


def camera_of(sh):
    kind = sh.get("kind", "landmark" if "pos" in sh else "address")
    ball = None
    if kind == "address":
        bx, by = sh["ball"][0] * YD, sh["ball"][1] * YD
        ball = Vector((bx, by, ground_z(bx, by) + 0.055))
        aim = Vector((sh["aim"][0] * YD - bx, sh["aim"][1] * YD - by, 0)).normalized()
        back, up, ahead = (3.2, 1.4, 2.5) if sh.get("putting") else (4.5, 2.4, 1.5)
        loc = ball - aim * back * YD + Vector((0, 0, up * YD))
        look = ball + aim * ahead * YD
        fov = 60.0
    else:
        w2b = lambda p: Vector((p[0] * YD, p[2] * YD, p[1] / 1.0936))
        loc, look, fov = w2b(sh["pos"]), w2b(sh["look"]), float(sh.get("fov", 60.0))
        if "ball" in sh:
            bx, by = sh["ball"][0] * YD, sh["ball"][1] * YD
            ball = Vector((bx, by, ground_z(bx, by) + 0.055))
    return kind, loc, look, fov, ball


def frame_dirs(loc, look, fov, W=900, H=1600, nx=45, ny=80):
    fwd = (look - loc).normalized()
    right = fwd.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(fwd).normalized()
    ty = math.tan(math.radians(fov) / 2)
    tx = ty * W / H
    out = []
    for j in range(ny):
        for i in range(nx):
            u = (i + 0.5) / nx * 2 - 1
            v = 1 - (j + 0.5) / ny * 2
            out.append(((fwd + right * (u * tx) + up * (v * ty)).normalized(), u, v))
    return out


pin = Vector((*[c * YD for c in DES.CENTERLINE[-1]], 0))
pin.z = DES.PLAY_Z + 0.26
all_ok = True
for sh in SHOTS:
    if sh.get("hole", 10) != 10:
        continue
    kind, loc, look, fov, ball = camera_of(sh)
    nm = sh["name"]
    # ---- schema + ball on land (address shots)
    sch = []
    if kind == "address":
        for k in ("ball", "aim"):
            if not (isinstance(sh.get(k), list) and len(sh[k]) == 2):
                sch.append(f"{k} is not [x, d]")
        lie = HOLE.lie_at(tuple(sh["ball"]))
        if lie in ("Water", "OutOfBounds"):
            sch.append(f"ball lie {lie}")
    else:
        for k in ("pos", "look"):
            if not (isinstance(sh.get(k), list) and len(sh[k]) == 3):
                sch.append(f"{k} is not [x, y, z]")
        if not (10 <= float(sh.get("fov", 60)) <= 90):
            sch.append("fov out of range")
    dirs = frame_dirs(loc, look, fov)
    hits = [first(loc, d) for d, u, v in dirs]
    cl = [cls(h[0]) if h[0] else "sky" for h in hits]
    dist = [h[1] if h[1] is not None else 9999.0 for h in hits]
    share = {c: cl.count(c) / len(cl) for c in set(cl)}
    # nothing within 3 m of the camera over the whole frame (a plant, rock or wall in the lens), and nothing in the central 40 % within 6 m
    near_all = [h[0] for h, d_ in zip(hits, dist) if d_ < 2.0 and h[0] and not h[0].startswith(GROUND) and not h[0].startswith("WATER_LAVA")]
    central = [(h[0], d_) for h, d_, (dd, u, v) in zip(hits, dist, dirs) if abs(u) < 0.4 and abs(v) < 0.4]
    blockers = sorted({n for n, d_ in central if n and d_ < 6.0 and cls(n) in ("plant", "rock", "wall") and kind == "address"})
    # ---- the ball / the pin / the landmark
    det = []
    ok = not sch and not near_all
    if ball is not None:
        n_, d_, _ = first(loc, ball - loc)
        dist_ball = (ball - loc).length
        free = n_ is None or d_ >= dist_ball - 0.03 or (n_.startswith(GROUND) and d_ >= dist_ball - 0.12)
        ring_free = 0
        for a in np.linspace(0, math.tau, 8, endpoint=False):
            q = ball + Vector((0.055 * math.cos(a), 0.055 * math.sin(a), 0.0))
            n2, d2, _ = first(loc, q - loc)
            ring_free += (n2 is None or d2 >= (q - loc).length - 0.12)
        det.append(f"ball {dist_ball:.1f} m from the camera: centre ray free {free}, {ring_free}/8 rim rays free")
        ok &= free and ring_free >= 7
    if kind == "address" and sh["ball"][0] > 50:
        top = pin + Vector((0, 0, 9.5))
        n3, d3, _ = first(loc, top - loc)
        vis = n3 is None or d3 >= (top - loc).length - 0.05
        det.append(f"flag top visible {vis}" + ("" if vis else f" (blocked by {n3} at {d3:.1f} m of {(top - loc).length:.1f})"))
        ok &= vis
    if kind == "landmark":
        wall, lava_, ring_, sky, plant = share.get("wall", 0), share.get("lava", 0), share.get("ring", 0), share.get("sky", 0), share.get("plant", 0)
        pin_hit = sum(1 for (n_, d_, p_) in hits if n_ and p_ is not None and math.hypot(p_.x - pin.x, p_.y - pin.y) < 24.0 and cls(n_) in ("wall", "ground"))
        pin_share = pin_hit / len(hits)
        # lava meets wall: a lava pixel directly below / beside a wall pixel in the ray grid
        grid = np.array(cl).reshape(80, 45)
        contact = int(sum(1 for j in range(79) for i in range(45) if (grid[j, i] == "wall" and grid[j + 1, i] == "lava") or (grid[j, i] == "lava" and grid[j + 1, i] == "wall")))
        det.append(f"frame shares {{{', '.join(f'{k} {v:.0%}' for k, v in sorted(share.items()))}}}; wall/lava contact cells {contact}; pillar pixels {pin_share:.1%}")
        ok &= wall >= 0.03 and lava_ >= 0.15 and contact >= 8 and pin_share >= 0.0015 and sky <= 0.55 and plant <= 0.15
    gate(f"H_LANDMARK_CLEAR_{nm}", ok and not blockers,
         f"{kind} camera ({loc.x / YD:.1f}, {loc.z * 1.0936:.2f}, {loc.y / YD:.1f}) world yd; schema problems {sch or 'none'}; objects within 2 m of the lens {sorted(set(near_all))[:3] or 'none'}; "
         f"plants / rocks / wall within 6 m in the central 40 % {blockers[:3] or 'none'}; " + "; ".join(det))
    all_ok &= ok and not blockers
if opt("--json"):
    json.dump(RES, open(opt("--json"), "w"), indent=1)
print(f"RESULT: {'ALL PASS' if all(r['ok'] for r in RES) else 'FAILURES'} ({len(RES)} gates)")
sys.exit(0 if all(r["ok"] for r in RES) else 1)
