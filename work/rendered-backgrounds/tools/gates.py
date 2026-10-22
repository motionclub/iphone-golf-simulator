#!/usr/bin/env python3
"""Binary gates for one venue from a before capture dir and an after capture dir (RenderedBackgroundsCapture).
   tools/gates.py <venue> <before_dir> <after_dir> [out.json]
Gates: NO_PAINT, SUN_MATCH, PARALLAX, LONG_LENS, PERF, CHAR_SAME (QUALITY is Adnan's review, listed separately)."""
import sys, os, re, json, math
import numpy as np
from PIL import Image

PAINTED = ['ArchipelagoSky', 'SummerSky', 'SkyCoastalSmall', 'SkyVolcanic', 'SkyRooftop', 'CloudTops', 'clouds', 'ash_cloud']
venue, before, after = sys.argv[1], sys.argv[2], sys.argv[3]
out = sys.argv[4] if len(sys.argv) > 4 else None
log = open(os.path.join(after, f'{venue}_capture.txt')).read()
R = {}

def img(d, shot):
    return np.asarray(Image.open(os.path.join(d, f'{venue}_{shot}.png')).convert('RGB')).astype(np.float64) / 255

# NO_PAINT ----------------------------------------------------------------------------------------
def texname(l):
    return l.split()[1] if l.startswith('tex ') else l.split('=', 1)[1].strip() if l.startswith('global ') else ''
hits = [l for l in log.splitlines() if texname(l) in PAINTED]
R['NO_PAINT'] = dict(pass_=not hits, detail=hits[:8] or 'no painted panorama bound on any enabled renderer, the skybox or a global')

# SUN_MATCH ---------------------------------------------------------------------------------------
def vec(tag):
    m = re.search(tag + r'.*?\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)', log)
    return np.array([float(v) for v in m.groups()]) if m else None
light, disc, scat = vec('^sun dir_to_light='.replace('^', '')), vec('rendered_sky_disc dir='), vec('rendered_sky_scatter dir=')
if light is not None and disc is not None:
    ang = math.degrees(math.acos(np.clip(np.dot(light, disc) / np.linalg.norm(light) / np.linalg.norm(disc), -1, 1)))
    az = lambda v: math.degrees(math.atan2(v[0], v[2]))
    daz = abs((az(scat) - az(light) + 180) % 360 - 180)
    R['SUN_MATCH'] = dict(pass_=ang <= 3 and daz <= 3, detail=f'disc vs light {ang:.3f} deg; scattering-glow azimuth vs light {daz:.3f} deg; light az {az(light):.1f} el {math.degrees(math.asin(light[1])):.1f}')
else:
    R['SUN_MATCH'] = dict(pass_=False, detail='no rendered sky in the after capture')

# PARALLAX ----------------------------------------------------------------------------------------
lum = lambda a: a @ np.array([.2126, .7152, .0722])
golf = venue.startswith('hole'); hub = venue == 'hub'
pairs = {'crane': ('06_crane0', '06_crane60')} if hub else {'crane': ('05_crane0', '05_crane60')} if golf else {'dolly': ('02_dolly0', '02_dolly2'), 'crane': ('02_crane0', '02_crane60'), 'craneB': ('02_craneB0', '02_craneB60')}
imgs = {}
rows = []
for l in log.splitlines():
    m = re.match(r'landmark (\S+) (\S+) dist_m=(\d+) radius_m=(\d+) a_px=\(([-\d.]+),([-\d.]+)\) b_px=\(([-\d.]+),([-\d.]+)\) predicted_dx=([-\d.]+)', l)
    if not m: continue
    tag, name, dist, rad = m.group(1), m.group(2), float(m.group(3)), float(m.group(4)); x0, y0, x2, y2, pdx = map(float, m.groups()[4:])
    if tag not in imgs: imgs[tag] = tuple(lum(img(after, s)) for s in pairs[tag])
    L0, L2 = imgs[tag]
    hw, hh = 40, 24; cx, cy = int(round(x0)), int(round(y0)); dy = int(round(y2 - y0)); pc = int(round(pdx))
    R_ = int(max(6, .6 * abs(pdx) + 6))
    if cy - hh < 0 or cy + hh >= L0.shape[0] or cy + dy + hh >= L0.shape[0] or cx - hw - R_ + pc < 0 or cx + hw + R_ + pc >= L0.shape[1] or cx - hw < 0: continue
    p = L0[cy - hh:cy + hh, cx - hw:cx + hw]; p = p - p.mean()
    if p.std() < .01: continue
    scores = []
    for dx in range(pc - R_, pc + R_ + 1):
        q = L2[cy - hh + dy:cy + hh + dy, cx - hw + dx:cx + hw + dx]; q = q - q.mean()
        scores.append((p * q).sum() / (np.sqrt((p * p).sum() * (q * q).sum()) + 1e-9))
    k = int(np.argmax(scores)); dx = k + pc - R_
    if k == 0 or k == len(scores) - 1: continue   # best match on the search edge = ambiguous (flat patch or occluder)
    if 0 < k < len(scores) - 1:
        a_, b_, c_ = scores[k - 1], scores[k], scores[k + 1]; dx += .5 * (a_ - c_) / (a_ - 2 * b_ + c_ + 1e-12)
    # the patch covers the island's near face to its far side: its true depth spans dist +- radius
    lo_, hi_ = sorted((pdx * dist / max(dist - rad, 1), pdx * dist / (dist + rad)))
    err = max(0.0, lo_ - dx, dx - hi_)
    rows.append(dict(move=tag, landmark=name, dist_m=dist, radius_m=rad, predicted_dx=round(pdx, 2), predicted_range=(round(lo_, 2), round(hi_, 2)), measured_dx=round(float(dx), 2), err_px=round(float(err), 2), ncc=round(float(max(scores)), 3)))
good = [r for r in rows if r['ncc'] > .8]   # confident matches only (occluders, flat patches drop out)
crane = sorted([r for r in good if r['move'].startswith('crane')], key=lambda r: -r['ncc'])[:6]
dolly = sorted([r for r in good if r['move'] == 'dolly'], key=lambda r: -r['ncc'])[:5]
# painted backdrop would give ~0 px for every landmark: the crane move separates real depth from infinity
ok = lambda r: r['err_px'] <= max(1.0, .1 * abs(r['predicted_dx']))
crane_all = sorted([r for r in good if r['move'].startswith('crane')], key=lambda r: -r['ncc'])
dolly_all = sorted([r for r in good if r['move'] == 'dolly'], key=lambda r: -r['ncc'])
crane, dolly = crane_all[:8], dolly_all[:8]
# the brief's test: the layers move as their depth predicts, measured on 3 landmarks (2 m dolly, where at least 3 are
# visible from the low gameplay camera, and the 60 m crane). Every confident match is listed, passing or not.
R['PARALLAX'] = dict(pass_=sum(map(ok, crane)) >= 3 and sum(map(ok, dolly)) >= min(3, len(dolly)),
                     detail=dict(crane_60m=crane, dolly_2m=dolly, note='tolerance max(1 px, 10%); needs 3 crane landmarks + min(3, visible) dolly landmarks within it'))

# LONG_LENS ---------------------------------------------------------------------------------------
def sharp(a):
    g = lum(a)[: int(a.shape[0] * .45)]     # upper 45% = what lies behind the heroes at the 27 deg stare-downs
    lap = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    return float(np.percentile(np.abs(lap), 99))
ll = {}
for shot in (('01_spawn', '03_play_door') if hub else ('04_longlens',) if golf else ('04_stare_rival', '06_stare_player')):
    try:
        ll[shot] = dict(before=round(sharp(img(before, shot)), 4), after=round(sharp(img(after, shot)), 4))
    except FileNotFoundError:
        pass
R['LONG_LENS'] = dict(pass_=bool(ll) and all(v['after'] >= v['before'] * .9 for v in ll.values()),
                      detail=dict(edge_p99_upper_half=ll, note='after must keep >=90% of the before edge energy at the longest lenses (27 deg stare, 14 deg test); crops in proof/'))

# PERF --------------------------------------------------------------------------------------------
perf = re.findall(r'perfAB (\S+) (\S+) .*?delta_median_ms=([-\d.]+)', log)
R['PERF'] = dict(pass_=bool(perf) and all(float(d) <= 1.0 for _, _, d in perf),
                 detail=[f'{c} {res}: +{float(d):.3f} ms (rendered - painted, interleaved median, Editor proxy)' for c, res, d in perf] + ['device: NOT RUN'])

# CHAR_SAME ---------------------------------------------------------------------------------------
def lab(rgb):
    c = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    M = np.array([[.4124, .3576, .1805], [.2126, .7152, .0722], [.0193, .1192, .9505]])
    xyz = c @ M.T / np.array([.95047, 1, 1.08883])
    f = np.where(xyz > .008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)
try:
    mask = img(after, '10_char_mask').max(-1) > .02
    # shrink the mask by 2 px so antialiased silhouette edges (which mix in the background) are excluded
    from scipy.ndimage import binary_erosion  # noqa
    mask = binary_erosion(mask, iterations=2)
except ImportError:
    m = mask.copy()
    for _ in range(2):
        m[1:-1, 1:-1] &= m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:]
    mask = m
except FileNotFoundError:
    mask = None
if mask is not None and mask.sum() > 500:
    dE = np.linalg.norm(lab(img(after, '10_char_A')) - lab(img(after, '10_char_B')), axis=-1)[mask]
    R['CHAR_SAME'] = dict(pass_=float(dE.mean()) <= 2, detail=f'mean dE76 {dE.mean():.3f}, p95 {np.percentile(dE, 95):.3f} over {int(mask.sum())} hero pixels')
else:
    R['CHAR_SAME'] = dict(pass_=False, detail='no character mask')

for k, v in R.items():
    print(f"GATE: {k} {'PASS' if v['pass_'] else 'FAIL'} — {v['detail']}")
if out:
    json.dump(R, open(out, 'w'), indent=1, default=str)
