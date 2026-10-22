"""H_FRAME_VARIATION: how much ALBEDO variation the phone cameras see on the ground (lighting free, so it does not depend on Blender vs Unity lights).
For each Game camera (CameraRig.FrameAddress: 4.5 yd behind the ball, 2.4 yd up, looks 1.5 yd past the ball, 60 deg vertical FOV, 900x1600) every
pixel of the lower 60 percent of the frame (a grid of GX x GY rays) is cast onto the staged scene; where it lands on ground / path the albedo
luminance (Rec.709 of the sRGB PNG of the face's LK_ material, sampled at the face UV, bilinear) is recorded.  Reports sd, p10..p90, the tone-band
contrast across the frame and the material shares.  Props (plants, rocks) hit by a ray are counted separately.
usage: Blender -b --factory-startup --python frame_variation.py -- STAGED.blend OUT.json [--tag X]"""
import sys, os, json, math, struct, zlib
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

YD = 0.9144
LOOK = REPO + "/Unity/Assets/Resources/Course/Look/"
TEX = {"LK_FAIRWAY": "Fairway_C", "LK_GREEN": "Green_C", "LK_ROUGH": "Rough_C", "LK_PATH": "Path_C", "LK_SAND": "Sand_C"}
GROUND = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "DRESS_PATH")
SHOTS = {"tee": ((0.0, 0.0), (19.0, 178.0)), "approach": ((19.0, 178.0), (-6.0, 340.0))}
GX, GY = 120, 213           # rays across / down the lower 60 % (900 x 960 px at 1/7.5)


def readpng(p):
    d = open(p, 'rb').read()
    i = 8
    idat = b''
    w = h = ct = 0
    while i < len(d):
        n = struct.unpack('>I', d[i:i + 4])[0]
        t = d[i + 4:i + 8]
        c = d[i + 8:i + 8 + n]
        if t == b'IHDR':
            w, h, _bd, ct = struct.unpack('>IIBB', c[:10])
        if t == b'IDAT':
            idat += c
        i += 12 + n
    raw = zlib.decompress(idat)
    ch = {2: 3, 6: 4, 0: 1}[ct]
    stride = w * ch
    out = np.zeros((h, stride), np.uint8)
    prev = np.zeros(stride, np.int32)
    pos = 0
    for y in range(h):
        f = raw[pos]
        pos += 1
        line = np.frombuffer(raw[pos:pos + stride], np.uint8).astype(np.int32)
        pos += stride
        if f == 0:
            cur = line
        elif f == 1:
            cur = line.copy()
            for x in range(ch, stride):
                cur[x] = (cur[x] + cur[x - ch]) & 255
        elif f == 2:
            cur = (line + prev) & 255
        elif f == 3:
            cur = line.copy()
            for x in range(stride):
                l = cur[x - ch] if x >= ch else 0
                cur[x] = (cur[x] + ((l + prev[x]) >> 1)) & 255
        else:
            cur = line.copy()
            for x in range(stride):
                l = cur[x - ch] if x >= ch else 0
                u = prev[x]
                ul = prev[x - ch] if x >= ch else 0
                p = l + u - ul
                pa, pb, pc = abs(p - l), abs(p - u), abs(p - ul)
                pr = l if (pa <= pb and pa <= pc) else (u if pb <= pc else ul)
                cur[x] = (cur[x] + pr) & 255
        out[y] = cur
        prev = cur
    return out.reshape(h, w, ch)[:, :, :3].astype(np.float32)


_lum_cache = {}


def lum_tex(name):
    if name not in _lum_cache:
        im = readpng(LOOK + TEX[name] + ".png")
        _lum_cache[name] = im @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    return _lum_cache[name]


def sample(L, u, v):
    h, w = L.shape
    x = (u % 1.0) * w - 0.5
    y = ((1.0 - v) % 1.0) * h - 0.5
    x0, y0 = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - x0, y - y0
    a = L[y0 % h, x0 % w]
    b = L[y0 % h, (x0 + 1) % w]
    c = L[(y0 + 1) % h, x0 % w]
    d = L[(y0 + 1) % h, (x0 + 1) % w]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def run(blend, tag=""):
    bpy.ops.wm.open_mainfile(filepath=blend)
    bpy.context.view_layer.update()
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    hide = ("BALL_START", "HOLE_CUP", "MARKER_TEE", "MARKER_PIN", "MARKER_UP")
    res = {}
    for shot, (ball, aim) in SHOTS.items():
        bx, by = ball[0] * YD, ball[1] * YD
        ax, ay = aim[0] * YD, aim[1] * YD
        # ground under the ball (round 5: the old ray stopped on the BALL_START placeholder sphere, 0.6 m too high; and exactly through a mesh vertex it can slip between triangles):
        # ray 1 cm off the ball, placeholders skipped, ball centre = ground + 0.055 m (CameraRig.FrameAddress works from the resting ball)
        o_ = Vector((bx + 0.011, by + 0.007, 40.0))
        bz = None
        for _ in range(8):
            ok, loc, nrm, idx, ob, mw = sc.ray_cast(dg, o_, Vector((0, 0, -1)), distance=80.0)
            if not ok:
                break
            if ob.name in hide:
                o_ = loc + Vector((0, 0, -1e-3))
                continue
            bz = loc.z + 0.055
            break
        if bz is None:
            bz = 6.3
        dv = Vector((ax - bx, ay - by, 0.0)).normalized()
        cam = Vector((bx, by, bz)) - dv * 4.5 * YD + Vector((0, 0, 2.4 * YD))
        look = (Vector((bx, by, bz)) + dv * 1.5 * YD - cam).normalized()
        right = look.cross(Vector((0, 0, 1))).normalized()
        up = right.cross(look).normalized()
        tv = math.tan(math.radians(30.0))
        th = tv * 900 / 1600
        lums, mats, props, xs, bymat, bymesh = [], {}, 0, [], {}, {}
        for gy in range(GY):
            ndc_y = -(0.4 + 0.6 * (gy + 0.5) / GY) * 2 + 1.0          # lower 60 %: y from 40 % to 100 % of the image height (top = 0)
            for gx in range(GX):
                ndc_x = ((gx + 0.5) / GX) * 2 - 1.0
                d = (look + right * (ndc_x * th) + up * (ndc_y * tv)).normalized()
                o = cam.copy()
                hit_name = None
                for _ in range(8):
                    ok, loc, nrm, pidx, hob, _m = sc.ray_cast(dg, o, d, distance=900.0)
                    if not ok:
                        break
                    if hob.name in hide:
                        o = loc + d * 1e-3
                        continue
                    hit_name = hob.name
                    break
                if hit_name is None:
                    continue
                if not hit_name.startswith(GROUND):
                    props += 1
                    continue
                me = hob.data
                poly = me.polygons[pidx]
                mname = me.materials[poly.material_index].name.split(".")[0] if me.materials and me.materials[poly.material_index] else ""
                if mname not in TEX:
                    continue
                # barycentric UV at the hit point on the polygon (triangulated fan around its first vertex: pick the triangle containing the point)
                lp = hob.matrix_world.inverted() @ loc
                uvl = me.uv_layers.active.data
                vs = [me.vertices[me.loops[li].vertex_index].co for li in range(poly.loop_start, poly.loop_start + poly.loop_total)]
                uvs = [uvl[li].uv for li in range(poly.loop_start, poly.loop_start + poly.loop_total)]
                best = None
                for k in range(1, len(vs) - 1):
                    a, b, c = vs[0], vs[k], vs[k + 1]
                    from mathutils import geometry as G
                    w_ = G.barycentric_transform(lp, a, b, c, Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0, 1, 0)))
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
                lums.append(float(sample(lum_tex(mname), u, v)))
                bymat.setdefault(mname, []).append(lums[-1])
                bymesh.setdefault(hit_name.split(".")[0], []).append(lums[-1])
                mats[mname] = mats.get(mname, 0) + 1
                xs.append(ndc_x)
        L_ = np.array(lums)
        xs = np.array(xs)
        n_all = GX * GY
        r = dict(rays=n_all, ground_hits=int(len(L_)), prop_hits=props, materials=mats,
                 lum_sd=float(L_.std()), lum_p10=float(np.percentile(L_, 10)), lum_p90=float(np.percentile(L_, 90)), lum_mean=float(L_.mean()))
        # tone-band contrast: mean luminance of the left third vs the right third of the frame (grass pixels only)
        if len(L_):
            lt, rt = L_[xs < -0.33], L_[xs > 0.33]
            r["left_third_mean"] = float(lt.mean()) if len(lt) else None
            r["right_third_mean"] = float(rt.mean()) if len(rt) else None
            r["band_contrast"] = float(abs(lt.mean() - rt.mean())) if len(lt) and len(rt) else None
        grass = np.array([x for k_, v_ in bymat.items() if k_ != "LK_PATH" for x in v_])
        r["path_share"] = float(len(bymat.get("LK_PATH", [])) / max(len(L_), 1))
        r["grass_only_sd"] = float(grass.std()) if len(grass) else None
        r["grass_only_p10_p90"] = [float(np.percentile(grass, 10)), float(np.percentile(grass, 90))] if len(grass) else None
        r["mesh_mean_lum"] = {k_: [round(float(np.mean(v_)), 2), len(v_)] for k_, v_ in sorted(bymesh.items())}
        res[shot] = r
        print(f"FRAMEVAR {tag} {shot}: ground {r['ground_hits']}/{n_all} props {props} sd {r['lum_sd']:.2f} p10..p90 {r['lum_p10']:.1f}..{r['lum_p90']:.1f} "
              f"path share {r['path_share']:.1%} grass-only sd {r['grass_only_sd']:.2f} mesh means {r['mesh_mean_lum']} band L/R {r.get('left_third_mean')}/{r.get('right_third_mean')} mats {mats}", flush=True)
    return res


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    out = run(args[0], tag=args[args.index("--tag") + 1] if "--tag" in args else "")
    json.dump(out, open(args[1], "w"), indent=1)
