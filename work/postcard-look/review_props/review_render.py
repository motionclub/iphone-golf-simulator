"""Reviewer re-render (writes ONLY into work/postcard-look/review_props/). Headless:
    Blender -b --factory-startup --python work/postcard-look/review_props/review_render.py -- --scratch work/postcard-look/review_props/render
1. the owner's 9 library panels, rebuilt from the library code into the reviewer dir (review_sheet_lib.png)
2. BASELINE hole blends with swap_legacy_rocks applied: tee / fairway cameras (+ the untouched baseline for comparison) and the
   phone camera (CameraRig.FrameAddress: 4.5 yd behind, 2.4 yd up, FOV 60 vertical, portrait) -> review_sheet_holes.png,
   review_sheet_phone.png
"""
import sys
import os
import math

sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
OUT = os.path.join(REPO, "work", "postcard-look", "review_props")
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import postcard_props_smoke as SM  # noqa: E402  (module import: main() does not run; SCRATCH = --scratch)
import postcard_props_lib as PL  # noqa: E402
import postcard_lib as P  # noqa: E402

assert os.path.abspath(SM.SCRATCH).startswith(OUT), SM.SCRATCH
RND = SM.SCRATCH
os.makedirs(RND, exist_ok=True)


def eevee(res, samples=24):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    try:
        sc.view_settings.view_transform = 'Standard'
        sc.eevee.taa_render_samples = samples
    except Exception:
        pass


def shoot(cam, fn, res):
    sc = bpy.context.scene
    eevee(res)
    sc.camera = cam
    sc.render.filepath = os.path.join(RND, fn)
    bpy.ops.render.render(write_still=True)
    print("rendered", fn, flush=True)
    return sc.render.filepath


def phone_cam(name, tee, ahead):
    """CameraRig.FrameAddress at the tee: 4.5 yd behind the ball, 2.4 yd up, looking 1.5 yd ahead, FOV 60 vertical."""
    d = Vector((ahead[0] - tee[0], ahead[1] - tee[1], 0)).normalized()
    yd = P.YD
    loc = Vector((tee[0], tee[1], 6.0)) - d * 4.5 * yd + Vector((0, 0, 2.4 * yd))
    tgt = Vector((tee[0], tee[1], 6.0)) + d * 1.5 * yd
    cam = SM.camera(name, loc, tgt, lens=20, clip=2000)
    cam.data.sensor_fit = 'VERTICAL'
    cam.data.angle_y = math.radians(60)
    return cam


def hole_shots(tag, swap, toward):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, "work", "postcard-look", "baseline", "blender", f"hole_{tag}.blend"))
    PL._COUNTERS.clear()
    label = "swap" if swap else "base"
    if swap:
        objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.data is not None and o.data.name.split(".")[0] in PL.LEGACY_MESHES
                and not any(c.name == "ASSET_LIBRARY" for c in o.users_collection)]
        PL.swap_legacy_rocks(None, objs=objs, basalt=(tag == "10"))
    out = []
    for cn in ("CAM_TEE_VIEW", "CAM_FAIRWAY_VIEW"):
        cam = bpy.data.objects.get(cn)
        cam.data.clip_end = 3000
        out.append(shoot(cam, f"hole{tag}_{label}_{cn.lower()}.png", (800, 500)))
    ph = phone_cam(f"CAM_PHONE_{tag}", (0.0, 0.0), toward)
    ph_path = shoot(ph, f"hole{tag}_{label}_phone.png", (450, 800))
    return out, ph_path


def main():
    # 1. library panels (same builder as the owner's sheet, reviewer output dir)
    panels = SM.build_panels()
    paths = SM.render_panels(panels)
    SM.compose_sheet(paths, os.path.join(OUT, "review_sheet_lib.png"), cols=3)
    # 2. baseline holes with the legacy swap
    land, phone = [], []
    aims = {"08": (0.0, 60.0), "09": (0.0, 60.0), "10": (16.0, 73.0)}
    for tag in ("10", "08", "09"):
        for swap in ((False, True) if tag == "10" else (True,)):
            o, p = hole_shots(tag, swap, aims[tag])
            land += o
            phone.append(p)
    SM.compose_sheet(land, os.path.join(OUT, "review_sheet_holes.png"), cols=2)
    SM.compose_sheet(phone, os.path.join(OUT, "review_sheet_phone.png"), cols=4)


main()
sys.stdout.flush()
os._exit(0)
