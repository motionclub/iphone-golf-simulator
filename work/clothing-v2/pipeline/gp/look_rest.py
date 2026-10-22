"""GARMENT PIPELINE: rest-pose look renders of a hero's worn set (for REF_MATCH side-by-sides), >= 1080p.
Blender -b --factory-startup --python gp/look_rest.py -- <hero> <out.png> [--cand <run_dir>] [--region torso|full|feet|hips] [--pose apose]
Views: front, right side, back, front three-quarter (like the reference sheets). --pose apose lowers the arms ~25 deg from vertical
(rest-relative bone rotation of the upper arms only) to match the reference A-pose; the bind pose itself is not changed."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rig, scene, render as RD, overlay as OV, candidate as CA

argv = sys.argv[sys.argv.index('--') + 1:]
hid, out = argv[0], argv[1]
opt = {argv[i][2:]: argv[i + 1] for i in range(2, len(argv) - 1, 2)}
h = rig.Hero(hid); R = scene.Rig(h)
items = scene.items_from_dump(h)
if 'cand' in opt:
    cand = CA.load_dir(os.path.join(opt['cand'], hid), h)
    items = [cand.get(i.tag, i) for i in items]
    if 'body' in cand: items[0] = cand['body']
mats = R.rest.copy()


def rot_about(M, pivot, axis, ang):
    c, s = math.cos(ang), math.sin(ang); x, y, z = axis
    Rm = np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                   [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                   [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])
    T = np.eye(4); T[:3, :3] = Rm; T[:3, 3] = pivot - Rm @ pivot
    return T @ M


if opt.get('pose') == 'apose':
    # arms: measure the current upper-arm angle from vertical, rotate about the shoulder in the frontal plane to ~25 deg
    for side, sg in (('Left', -1), ('Right', 1)):
        ua, la = h.bidx[side + 'UpperArm'], h.bidx[side + 'LowerArm']
        sh, el = mats[ua][:3, 3], mats[la][:3, 3]
        d = (el - sh) / np.linalg.norm(el - sh)
        cur = math.degrees(math.atan2(abs(d[0]), -d[1]))
        ang = math.radians(cur - 25) * (1 if sg > 0 else -1) * (1 if d[0] * sg > 0 else -1)
        desc = [i for i, b in enumerate(h.bones) if b.startswith(side) and any(k in b for k in ('UpperArm', 'LowerArm', 'Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Little'))]
        desc += [i for i, b in enumerate(h.bones) if b.startswith('ArmBlend_')]
        for i in desc:
            if h.bones[i].startswith('ArmBlend_'):
                a = h.bones[i].split('_'); x, y = int(a[1]), int(a[2])
                bn = [h.bones[g] for g in h.body.gidx]
                if not (bn[x].startswith(side) or bn[y].startswith(side)) or 'Shoulder' in bn[x] and 'Shoulder' in bn[y]: continue
                if not any(bn[q].startswith(side + 'UpperArm') or bn[q].startswith(side + 'LowerArm') or bn[q].startswith(side + 'Hand') for q in (x, y)): continue
            mats[i] = rot_about(mats[i], sh, np.array([0, 0, 1.0]), -ang)
sw = {}
Ps = [R.posem(it, mats, None) for it in items]


class _S: pass
S = _S(); S.items = items
region = opt.get('region', 'torso')
views = [(0.0, 0.05), (math.pi / 2, 0.05), (math.pi, 0.05), (math.pi / 4, 0.12)]
if region == 'feet': views = [(math.pi / 2, 0.08), (math.pi / 4, 0.35), (math.pi, 0.1), (0.0, 1.2)]   # side, 3/4, back, top
ZOOM = {'torso': ('UpperChest', -.06, .30), 'hips': ('Hips', -.10, .32), 'feet': ('LeftFoot', -.05, .16), 'full': ('Hips', .0, 1.0)}
bone, dy, half = ZOOM[region]
c = mats[h.bidx[bone]][:3, 3].copy(); c[1] += dy
if region == 'feet': c[0] = 0
Rh = RD.Renderer(1080, 1080, half) if region != 'full' else OV.hi_renderer(1080, 1350)
tiles = [OV.shot(S, Ps, v, R=Rh, centre=c) for v in views]
h0 = min(t.shape[0] for t in tiles)
row = np.concatenate([t[:h0] for t in tiles], 1)
RD.write_png(out, row)
print('LOOK', out, row.shape)
