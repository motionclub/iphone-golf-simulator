"""Read-only upper bound on water visible through frozen scoring geometry.

Run with Blender --factory-startup --python. All scenery is removed analytically:
every down-facing camera ray may reach an infinite water plane at z=0 unless a
frozen scoring mesh blocks it. This is an optimistic bound, never a PASS proof.
It uses the actual proof address configuration and CameraRig.FrameAddress mirror.
No asset is modified. Pixel-centre rays match the 900x1600 Game-view resolution.
"""
import importlib.util
import json
import math
import os
import time

import bpy

AUDIT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.realpath(os.path.join(AUDIT, "../../../.."))
vp = os.path.join(REPO, "blender/scripts/postcard_look_verify.py")
sp = importlib.util.spec_from_file_location("water_ceiling_verify", vp)
V = importlib.util.module_from_spec(sp)
sp.loader.exec_module(V)
W, H = 900, 1600
WATER_Z = float(os.environ.get("POSTCARD_CEILING_WATER_Z", "0.0"))
SUFFIX = "" if WATER_Z == 0.0 else "_raised599"

with open(os.path.join(REPO, "work/postcard-look/v2/proof/stills_cfg_9.json")) as fh:
    cfg = json.load(fh)

report = dict(resolution=[W, H], water_z_m=WATER_Z, method="infinite water plane; all removable scenery absent; frozen collision bodies opaque with backface culling; pixel-centre rays", camera_source="CameraRig.FrameAddress + v2/proof/stills_cfg_9.json", shots=[])
for hole in (8, 9, 10):
    baseline = os.path.join(REPO, f"work/postcard-look/baseline/blender/hole_{hole:02d}.blend")
    bpy.ops.wm.open_mainfile(filepath=baseline, load_ui=False)
    design, dpath = V.load_design(hole)
    C = V.Ctx(hole, design, dpath, {})
    S = V.Snap("blend", C)
    protected = V.coll_objects(S)
    bvh = V.bvh_of(S, protected)
    shots = [s for s in cfg["shots"] if s["hole"] == hole and s.get("kind") == "address"]
    for name, pos, fwd, up, right, fov in V.smoke_shot_cameras(S, C, shots):
        start = time.time()
        th = math.tan(math.radians(fov) / 2.0)
        aspect = W / H
        free = blocked = above = backfaces_skipped = 0
        for j in range(H):
            yv = (1.0 - (j + 0.5) / H * 2.0) * th
            row = fwd + up * yv
            for i in range(W):
                xv = ((i + 0.5) / W * 2.0 - 1.0) * th * aspect
                d = (row + right * xv).normalized()
                if d.z >= 0.0:
                    above += 1
                    continue
                water_dist = (WATER_Z - pos.z) / d.z
                origin = pos.copy()
                travelled = 0.0
                front_hit = False
                for _ in range(64):
                    hit, normal, _index, hit_dist = bvh.ray_cast(origin, d, water_dist - travelled)
                    if hit is None:
                        break
                    if normal.dot(d) < 0.0:
                        front_hit = True
                        break
                    backfaces_skipped += 1
                    travelled += hit_dist + 1e-4
                    if travelled >= water_dist:
                        break
                    origin = hit + d * 1e-4
                if not front_hit:
                    free += 1
                else:
                    blocked += 1
        share = free / (W * H)
        shot = dict(name=name, hole=hole, camera_position_m=list(pos), camera_forward=list(fwd), fov_deg=fov, frozen_meshes=[o.name for o in protected], pixels_total=W*H, water_possible_pixels=free, frozen_occluded_pixels=blocked, rays_above_water_horizon=above, backfaces_skipped=backfaces_skipped, upper_bound_water_share=share, threshold=0.15, feasible_at_15_percent=share >= 0.15, elapsed_s=round(time.time()-start, 2))
        report["shots"].append(shot)
        print(f"CEILING: {name} {free}/{W*H} = {share:.6%} possible water; threshold >=15%; {'FEASIBLE_BOUND' if share>=.15 else 'IMPOSSIBLE_AT_FROZEN_CAMERA'}", flush=True)

with open(os.path.join(AUDIT, "frozen_water_ceiling" + SUFFIX + ".json"), "w") as fh:
    json.dump(report, fh, indent=2)
with open(os.path.join(AUDIT, "frozen_water_ceiling" + SUFFIX + ".txt"), "w") as fh:
    fh.write(report["method"] + "\n")
    for s in report["shots"]:
        fh.write(f"{s['name']}: upper bound {s['upper_bound_water_share']:.6%} ({s['water_possible_pixels']}/{s['pixels_total']} pixels), need >=15%; {'bound permits 15%' if s['feasible_at_15_percent'] else '15% impossible with frozen camera/scoring geometry'}\n")
