"""SIL_BALD gate for the head+neck of the assembled female blend vs the bald FRONT and BACK figures of female_body_bald.jpg (plate scale 0.0025954 m/px).
blender -b --factory-startup --python sil_body.py -- <assembled.blend> <out.json> [debug_png_prefix]
Per row (head top .. z=1.43 m, just above the grey collar): plate skin-silhouette extent vs model alpha extent; metric = sum|dL|+|dR| / sum plate width  (== XOR area / plate area for row-convex shapes)."""
import sys, json, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np, bpy
from PIL import Image
from mathutils import Vector
import fl
argv = sys.argv[sys.argv.index('--') + 1:]
blend, out = argv[0], argv[1]; dbg = argv[2] if len(argv) > 2 else None
S = 0.0025954
plate = np.asarray(Image.open(fl.PLATES / 'female_body_bald.jpg').convert('RGB')).astype(float)
R, G, B = plate[..., 0], plate[..., 1], plate[..., 2]
skin = (R - B > 22) & (R > G + 6) & (G > B) & (R > 120)
H_, W_ = skin.shape
res = {}


def extents(mask, r0, r1, c0, c1):
    ex = {}
    for r in range(r0, r1):
        xs = np.where(mask[r, c0:c1])[0]
        if len(xs): ex[r] = (c0 + xs.min(), c0 + xs.max() + 1)     # [left, right) pixel edges
    return ex


bpy.ops.wm.open_mainfile(filepath=blend)
for o in list(bpy.data.objects):
    if o.type != 'MESH' or o.name not in ('Body_F', 'Face_F'): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.film_transparent = True
sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (1, 1, 1)
sc.display.render_aa = 'OFF'; sc.view_settings.view_transform = 'Standard'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_start = 0.01; cd.clip_end = 50
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
zmodel_top = max(v.co.z for o in bpy.data.objects if o.type == 'MESH' for v in o.data.vertices)

for view, (cl, cr) in (('front', (330, 560)), ('back', (740, 960))):
    ex = extents(skin, 15, 150, cl, cr)
    r_top = min(ex)
    # figure centre column from the cranium rows (r_top+14 .. r_top+30), ears excluded
    cen = np.mean([0.5 * (ex[r][0] + ex[r][1]) for r in range(r_top + 14, r_top + 30) if r in ex])
    z_of = lambda r: zmodel_top - (r - r_top) * S
    r_end = min(r for r in range(r_top, 160) if z_of(r) < 1.43)
    # render window: plate cols [cen-110, cen+110), rows [r_top-6, r_end+4)
    c0, c1 = int(cen - 110), int(cen + 110); r0, r1 = r_top - 6, r_end + 4
    up = 4
    cd.ortho_scale = (c1 - c0) * S
    tz = z_of((r0 + r1) / 2.0); tx = ((c0 + c1) / 2.0 - cen) * S
    if view == 'front': cam.location = Vector((tx, -3.0, tz)); az = 0.0
    else: cam.location = Vector((-tx, 3.0, tz)); az = 180.0
    cam.rotation_euler = (math.radians(90), 0, math.radians(az))
    sc.render.resolution_x, sc.render.resolution_y = (c1 - c0) * up, (r1 - r0) * up
    path = f'/private/tmp/claude-501/sil_{view}.png'; sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    im = np.asarray(Image.open(path).convert('RGBA'))[..., 3] > 128
    rows = []; sumd = 0.0; sumw = 0.0; xor = 0.0; area = 0.0; worst = []
    per_row = {}
    for r in range(r_top, r_end):
        if r not in ex: continue
        yy = int(((r + 0.5) - r0) * up)
        xs = np.where(im[yy])[0]
        if len(xs) == 0: continue
        ml, mr = c0 + xs.min() / up, c0 + (xs.max() + 1) / up
        pl, pr = ex[r]
        dl, dr = ml - pl, mr - pr
        sumd += abs(dl) + abs(dr); sumw += (pr - pl)
        # XOR of the two intervals
        a0, a1 = max(ml, pl), min(mr, pr); inter = max(0.0, a1 - a0)
        xor += (mr - ml) + (pr - pl) - 2 * inter; area += (pr - pl)
        per_row[r] = (round(float(dl), 2), round(float(dr), 2))
        worst.append((abs(dl) + abs(dr), r, dl, dr))
    worst.sort(reverse=True)
    pct = 100.0 * xor / area
    res[view] = dict(rows=f'{r_top}..{r_end}', plate_center_col=float(cen), z_top=float(zmodel_top), z_bottom_compared=float(z_of(r_end)), sil_error_pct=float(pct), mean_abs_row_err_px=float(sumd / max(len(per_row), 1) / 2),
                     worst=[(int(r), round(float(a), 1), round(float(b), 1)) for _, r, a, b in worst[:8]], per_row={str(k): v for k, v in per_row.items()})
    print(view, 'rows', r_top, r_end, 'centre col %.1f' % cen, 'SIL error %.2f %%' % pct, 'mean |edge err| %.2f px (1 px = %.2f mm)' % (sumd / max(len(per_row), 1) / 2, S * 1000))
    print('  worst rows (row, dL, dR px):', res[view]['worst'])
    if dbg:
        # overlay: plate crop with model silhouette edge
        pc = Image.fromarray(plate[r0:r1, c0:c1].astype(np.uint8)).resize(((c1 - c0) * up, (r1 - r0) * up), Image.NEAREST)
        a = np.asarray(pc).copy(); edge = im ^ np.roll(im, 1, axis=1); a[edge] = (255, 0, 0)
        pm = np.zeros_like(im); sk = np.zeros_like(im)
        for r in per_row:
            yy0 = (r - r0) * up; pl, pr = ex[r]; sk[yy0:yy0 + up, int((pl - c0) * up):int((pr - c0) * up)] = True
        ed2 = sk ^ np.roll(sk, 1, axis=1); a[ed2] = (0, 90, 255)
        Image.fromarray(a).save(f'{dbg}_{view}.png')
json.dump(res, open(out, 'w'), indent=1)
