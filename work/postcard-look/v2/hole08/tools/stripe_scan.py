"""Scan the mow-stripe phase of LK_FAIRWAY (fairway / first cut / apron) and of a cross-mown TEE_BOX against the albedo variation the two phone cameras see.
Casts the lower 60 % of each frame once (frame_variation.py geometry), keeps (mesh, material, UV as built, lateral / arc) per hit and re-evaluates the luminance of
the real Fairway_C / Green_C PNGs for every candidate shift.  usage: Blender -b --factory-startup --python stripe_scan.py -- STAGED.blend OUT.json"""
import sys, os, json, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.path.insert(0, REPO + "/work/postcard-look/v2/hole08/tools")
sys.dont_write_bytecode = True
import bpy
import numpy as np
from mathutils import Vector, geometry as G
import frame_variation as FV
import postcard_lib as P
import postcard_look_lib as L
import postcard_check as PC
import hole08_design as DES

YD = P.YD


class DD:
    hole = PC.Hole(DES)


def gather(blend):
    bpy.ops.wm.open_mainfile(filepath=blend)
    bpy.context.view_layer.update()
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    cl = L.CenterlineParam(DD)
    hide = ("BALL_START", "HOLE_CUP", "MARKER_TEE", "MARKER_PIN", "MARKER_UP")
    out = {}
    for shot, (ball, aim) in FV.SHOTS.items():
        bx, by = ball[0] * YD, ball[1] * YD
        ax, ay = aim[0] * YD, aim[1] * YD
        ok, loc, nrm, idx, ob, mw = sc.ray_cast(dg, Vector((bx, by, 40.0)), Vector((0, 0, -1)), distance=80.0)
        bz = loc.z
        dv = Vector((ax - bx, ay - by, 0.0)).normalized()
        cam = Vector((bx, by, bz)) - dv * 4.5 * YD + Vector((0, 0, 2.4 * YD))
        look = (Vector((bx, by, bz)) + dv * 1.5 * YD - cam).normalized()
        right = look.cross(Vector((0, 0, 1))).normalized()
        up = right.cross(look).normalized()
        tv = math.tan(math.radians(30.0))
        th = tv * 900 / 1600
        rec = []
        for gy in range(FV.GY):
            ndc_y = -(0.4 + 0.6 * (gy + 0.5) / FV.GY) * 2 + 1.0
            for gx in range(FV.GX):
                ndc_x = ((gx + 0.5) / FV.GX) * 2 - 1.0
                d = (look + right * (ndc_x * th) + up * (ndc_y * tv)).normalized()
                o = cam.copy()
                hit = None
                for _ in range(8):
                    ok, loc, nrm, pidx, hob, _m = sc.ray_cast(dg, o, d, distance=900.0)
                    if not ok:
                        break
                    if hob.name in hide:
                        o = loc + d * 1e-3
                        continue
                    hit = (loc, pidx, hob)
                    break
                if hit is None:
                    continue
                loc, pidx, hob = hit
                if not hob.name.startswith(FV.GROUND):
                    rec.append((ndc_x, gy, "prop", "", 0.0, 0.0, 0.0, 0.0, hob.name))
                    continue
                me = hob.data
                poly = me.polygons[pidx]
                mname = me.materials[poly.material_index].name.split(".")[0] if me.materials and me.materials[poly.material_index] else ""
                lp = hob.matrix_world.inverted() @ loc
                uvl = me.uv_layers.active.data
                vs = [me.vertices[me.loops[li].vertex_index].co for li in range(poly.loop_start, poly.loop_start + poly.loop_total)]
                uvs = [uvl[li].uv for li in range(poly.loop_start, poly.loop_start + poly.loop_total)]
                best = None
                for k in range(1, len(vs) - 1):
                    w_ = G.barycentric_transform(lp, vs[0], vs[k], vs[k + 1], Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0, 1, 0)))
                    l1, l2 = w_.x, w_.y
                    l0 = 1 - l1 - l2
                    mn = min(l0, l1, l2)
                    if best is None or mn > best[0]:
                        best = (mn, l0, l1, l2, k)
                    if mn >= -1e-6:
                        break
                _mn, l0, l1, l2, k = best
                u = l0 * uvs[0][0] + l1 * uvs[k][0] + l2 * uvs[k + 1][0]
                v = l0 * uvs[0][1] + l1 * uvs[k][1] + l2 * uvs[k + 1][1]
                lat, arc = cl.uv([loc.x], [loc.y])
                rec.append((ndc_x, gy, hob.name, mname, u, v, float(lat[0]), float(arc[0]), ""))
        out[shot] = rec
    return out


TEXL = {}


def lum_of(mname, u, v):
    if mname not in TEXL:
        TEXL[mname] = FV.lum_tex(mname)
    Lm = TEXL[mname]
    h, w = Lm.shape
    x = (u % 1.0) * w - 0.5
    y = ((1.0 - v) % 1.0) * h - 0.5
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    a = Lm[y0 % h, x0 % w]
    b = Lm[y0 % h, (x0 + 1) % w]
    c = Lm[(y0 + 1) % h, x0 % w]
    d = Lm[(y0 + 1) % h, (x0 + 1) % w]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def evaluate(rec, fshift, tee_mode, tee_phase, tile=10.0):
    """luminance array of the ground hits: LK_FAIRWAY faces (not the tee box) get U + fshift; the tee box is LK_GREEN as built (tee_mode 'green') or
    cross-mown LK_FAIRWAY (tee_mode 'cross': U = arc/10 + tee_phase, V = -lat/10)."""
    groups = {}
    for (nx, gy, name, mname, u, v, lat, arc, _p) in rec:
        if name == "prop" or mname not in FV.TEX:
            continue
        if name == "TEE_BOX" and tee_mode == "cross":
            groups.setdefault("LK_FAIRWAY", []).append((nx, arc / tile + tee_phase, -lat / tile))
        elif name == "TEE_BOX" and tee_mode == "fairway":
            groups.setdefault("LK_FAIRWAY", []).append((nx, lat / tile + fshift, arc / tile))
        elif mname == "LK_FAIRWAY":
            groups.setdefault("LK_FAIRWAY", []).append((nx, u + fshift, v))
        else:
            groups.setdefault(mname, []).append((nx, u, v))
    lums, xs = [], []
    for mname, arr in groups.items():
        a = np.array(arr)
        lums.append(lum_of(mname, a[:, 1], a[:, 2]))
        xs.append(a[:, 0])
    return np.concatenate(lums), np.concatenate(xs)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    rec = gather(args[0])
    res = {"fshift_scan": [], "tee_cross_scan": []}
    print("SCAN fairway stripe shift (U += s) -> albedo luminance sd in the lower 60 % of the frame; tee box as LK_GREEN (as built)")
    for s in np.arange(0.0, 1.0, 0.05):
        row = {"shift": round(float(s), 2)}
        for shot in rec:
            Lm, xs = evaluate(rec[shot], float(s), "green", 0.0)
            row[shot] = round(float(Lm.std()), 2)
        res["fshift_scan"].append(row)
        print("SCAN", row)
    print("SCAN tee box cross-mown LK_FAIRWAY (U = arc/10 + p, V = -lat/10), fairway shift 0.15")
    for p in np.arange(0.0, 1.0, 0.05):
        row = {"phase": round(float(p), 2)}
        for shot in rec:
            Lm, xs = evaluate(rec[shot], 0.15, "cross", float(p))
            row[shot] = round(float(Lm.std()), 2)
        res["tee_cross_scan"].append(row)
        print("SCAN", row)
    with open(args[1], "w") as fh:
        json.dump(res, fh, indent=1)


main()
