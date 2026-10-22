"""foldx5.py: fast underbutt-fold experiments.  python3 tools/foldx5.py NAME '{json overrides of PP5_final}' [--base co_FORM5_mix.npy] [--view]
Builds pelvis5.build_pelvis on the mix coords with PP5_final + overrides, prints fold-onset heights (plate-lit luminance, plate grid), back-envelope deviation,
dip depth/width at several columns, saves data/co5p_NAME.npy and (with --view) scratch/fx_NAME.png (plate | model back view, plate-fit light)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageEnhance, ImageDraw
import pelvis5 as pv
import benv5
import photo3 as ph
from fplate import BALD, BACK_CX, SOLE, S

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FB = np.load(HERE + '/data/plate_back_fine4.npy')
ZR = np.arange(0.74, 0.90, 0.002)
BOX = ph.roi_box('back', -0.20, 0.20, 0.72, 0.92)
FX = (0.03, 0.06, 0.09, 0.12)


def render(co, gain=2.0, box=BOX):
    L = np.array(ph.LIGHT, dtype=float).copy(); L[1:] *= gain
    N = ph.vertex_normals(co, ph.TRI); sh = ph.shade_vertices(co, N, 'back', L)
    img, mask = ph.raster_shaded(co, sh, 'back', box)
    return img, mask


def profile_model(img, x, box=BOX):
    c0, r0, c1, r1 = box
    col = int(round(BACK_CX - x / S)) - c0
    return np.array([img[int(round(SOLE - z / S)) - r0 - 1:int(round(SOLE - z / S)) - r0 + 2, col - 1:col + 2].mean() for z in ZR])


def profile_plate(x):
    col = int(round(BACK_CX - x / S))
    return np.array([BALD[int(round(SOLE - z / S)) - 1:int(round(SOLE - z / S)) + 2, col - 1:col + 2].mean() for z in ZR])


def fold_stats(v):
    r = v - v[:10].mean(); j = int(np.argmin(r)); half = 0.5 * r[j]
    i = j
    while i > 0 and r[i] < half: i -= 1
    k = j
    while k < len(r) - 1 and r[k] < half: k += 1
    return dict(onset=float(ZR[i]), zmin=float(ZR[j]), depth=float(-r[j]), fwhm=float(ZR[k] - ZR[i]))


def band_stats(v):
    """robust dark-band descriptors of a luminance profile (relative to the mean of z .74-.76): lower/upper half-depth edges, argmin and the CENTROID z of the deficit beyond half depth"""
    r = v - v[:10].mean(); j = int(np.argmin(r)); half = 0.5 * r[j]
    i = j
    while i > 0 and r[i] < half: i -= 1
    k = j
    while k < len(r) - 1 and r[k] < half: k += 1
    w = np.clip(half - r, 0, None); c = float((w * ZR).sum() / max(w.sum(), 1e-9))
    return dict(lower=float(ZR[i]), upper=float(ZR[k]), zmin=float(ZR[j]), centroid=c, depth=float(-r[j]))


def lum_err(img, xs=(0.03, 0.06, 0.09, 0.12), z0=0.77, z1=0.90):
    """rms (grey levels) of the plate-relative luminance profile difference (baseline = mean over z .74-.76 of each profile), per column + overall"""
    out = []
    m = (ZR >= z0) & (ZR <= z1)
    for x in xs:
        pp = profile_plate(x); pm = profile_model(img, x)
        d = (pm - pm[:10].mean()) - (pp - pp[:10].mean())
        out.append(float(np.sqrt((d[m] ** 2).mean())))
    return out


def report(tag, co, cmp_to=None):
    img, _ = render(co)
    le = lum_err(img)
    print(f'[{tag}] lum rms err per column (.03 .06 .09 .12): ' + ' '.join(f'{v:.1f}' for v in le) + f'   mean {np.mean(le):.1f}')
    pl = [fold_stats(profile_plate(x)) for x in FX]
    md = [fold_stats(profile_model(img, x)) for x in FX]
    zu = np.arange(0.70, 0.881, 0.02)
    dev = 1000 * (benv5.env(co, zu) - np.interp(zu, FB[0], FB[1]))
    print(f'[{tag}] onset  model ' + ' '.join(f"{m['onset']:.3f}" for m in md) + '   plate ' + ' '.join(f"{p['onset']:.3f}" for p in pl) +
          f"   rise(.06->.12) model {100*(md[3]['onset']-md[1]['onset']):+.1f} cm plate {100*(pl[3]['onset']-pl[1]['onset']):+.1f} cm")
    print(f'[{tag}] zmin   model ' + ' '.join(f"{m['zmin']:.3f}" for m in md) + '   plate ' + ' '.join(f"{p['zmin']:.3f}" for p in pl))
    print(f'[{tag}] depth  model ' + ' '.join(f"{m['depth']:.0f}" for m in md) + '   plate ' + ' '.join(f"{p['depth']:.0f}" for p in pl) + '   (grey levels)')
    print(f'[{tag}] fwhm   model ' + ' '.join(f"{100*m['fwhm']:.1f}" for m in md) + '   plate ' + ' '.join(f"{100*p['fwhm']:.1f}" for p in pl) + '   (cm)')
    print(f'[{tag}] back envelope dev mm (z .70..88): ' + ' '.join(f'{v:+.1f}' for v in dev) + f'  max|.| {np.abs(dev).max():.1f}')
    return img


def view(name, items, gain=2.0, sc=3, zr=(0.66, 0.98), xr=0.20, ref=((0.05, 0.10), (0.70, 0.76)), cont=1.6):
    """plate | model panels, back view; every model panel is offset so its thigh reference patch (x,z ref) has the plate's mean grey (same exposure), background filled with the plate's"""
    box = ph.roi_box('back', -xr, xr, zr[0], zr[1])
    c0, r0, c1, r1 = box
    plate = np.asarray(BALD[r0:r1, c0:c1]).astype(float)
    def patch(img):
        (xa, xb), (za, zb) = ref
        ca, cb = sorted((int(round(BACK_CX - xa / S)) - c0, int(round(BACK_CX - xb / S)) - c0)); ra, rb = sorted((int(round(SOLE - za / S)) - r0, int(round(SOLE - zb / S)) - r0))
        return img[ra:rb, ca:cb].mean()
    pm = patch(plate)
    ims = [Image.fromarray(np.clip(plate, 0, 255).astype(np.uint8)).convert('L')]; labs = ['PLATE']
    for tag, co in items:
        img, mask = render(co, gain, box)
        img = np.asarray(img, dtype=float); img = img + (pm - patch(img)); img[np.asarray(mask) == 0] = plate[0, 0]
        ims.append(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('L')); labs.append(tag)
    W = sum(i.width for i in ims) * sc
    out = Image.new('RGB', (W, ims[0].height * sc), (255, 255, 255)); x = 0
    for im, lab in zip(ims, labs):
        e = ImageEnhance.Contrast(im).enhance(cont).resize((im.width * sc, im.height * sc), Image.LANCZOS).convert('RGB')
        ImageDraw.Draw(e).text((6, 6), lab, fill=(255, 0, 0)); out.paste(e, (x, 0)); x += e.width
    out.save(f'{HERE}/scratch/fx_{name}.png'); print('saved', f'scratch/fx_{name}.png', out.size)


def build(over, base='co_FORM5_mix.npy'):
    PP = json.load(open(HERE + '/data/PP5_final.json')); PP.update(over)
    co_mix = np.load(HERE + '/data/' + base).astype(np.float64)
    return pv.build_pelvis(co_mix, PP), PP


if __name__ == '__main__':
    name = sys.argv[1]; over = json.loads(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else {}
    base = 'co_FORM5_mix.npy'
    if '--base' in sys.argv: base = sys.argv[sys.argv.index('--base') + 1]
    co, PP = build(over, base)
    np.save(f'{HERE}/data/co5p_{name}.npy', co)
    json.dump(PP, open(f'{HERE}/data/PP5_{name}.json', 'w'), indent=1)
    report(name, co)
    if '--view' in sys.argv:
        c4 = np.load(HERE + '/data/co_FORM4_final.npy').astype(np.float64)
        cf = np.load(HERE + '/data/co_FORM5_final.npy').astype(np.float64)
        view(name, [('F4', c4), ('F5 final', cf), (name, co)])
