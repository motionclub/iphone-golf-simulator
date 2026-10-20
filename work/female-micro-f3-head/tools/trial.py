"""jaw trial harness: build a variant of the F2 parameter set, apply it to the F1 base, render profile + both 3/4 jaw close-ups next to the plate.
python3 trial.py name key=value ...   (keys: k, k1, kx, cx, cxb, bump_A, nf_d (loft exponent dip), nf_z, nf_w, ztop)   -> data/var_<name>.npz, renders/trial/<name>_*.png, renders/trial/sheet_<names>.png"""
import sys, json, subprocess, copy, os
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np
import exp, make_final as mf, fl
W3 = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/'
B = '/Applications/Blender.app/Contents/MacOS/Blender'
os.makedirs(W3 + 'renders/trial', exist_ok=True)
VIEWS = 'c:90:0:0:-0.03:1.49:0.13:1100,c:35:0:-0.015:-0.06:1.47:0.13:1100,c:-35:0:0.015:-0.06:1.47:0.13:1100'
NAMES = ['c_90_0_0_-0.03_1.49_0.13_1100', 'c_35_0_-0.015_-0.06_1.47_0.13_1100', 'c_-35_0_0.015_-0.06_1.47_0.13_1100']


def _bs3(t):
    t = np.abs(t); out = np.zeros_like(t); m1 = t < 1; m2 = (t >= 1) & (t < 2)
    out[m1] = 2 / 3 - t[m1] ** 2 + 0.5 * t[m1] ** 3; out[m2] = (2 - t[m2]) ** 3 / 6
    return out


def apply_fit(H, fitfile):
    """loft half-width row correction from fit_contour.py (cubic B-spline coefficients on 10 mm knots)"""
    d = json.load(open(W3 + fitfile)); zk = np.array(d['ZK']); coef = np.array(d['coef'])
    B = np.stack([_bs3((H.L.zk - z0) / 0.010) for z0 in zk], -1)
    H.L.a = H.L.a + B @ coef
    return H


def make_H(**kw):
    """analytic head for a variant (no mesh delta). keys as in build_variant.  fit=1: contour fit (data/fit_contour.json): a-row correction + cxb/k1"""
    P = copy.deepcopy(mf.PARAMS)
    fitfile = kw.get('fitfile', 'data/fit_contour.json') if kw.get('fit', 0) else None
    if fitfile:
        for k, v in json.load(open(W3 + fitfile))['par'].items(): kw.setdefault(k, v)
    for k in ('k', 'k1', 'kx', 'cx', 'cxb'):
        if k in kw: P['under'][k] = kw[k]
    if 'bump_A' in kw: P['bumps'][0]['A'] = kw['bump_A']
    import geo2
    geo2.SMIN['mode'] = {0: 'quad', 1: 'cubic', 2: 'exp'}[int(kw.get('smin', 0))]; geo2.SMIN['mul'] = kw.get('smul', 1.0)
    H = exp.build(under=P['under'], prof=exp.prof_nochin(P['prof_zcut'])); exp.apply_a_smooth(H, sig=kw.get('rows_sig', P['rows_smooth']['sig']), rows=tuple(P['rows_smooth']['rows']) + (('nf',) if kw.get('nf_smooth', 0) else ()))
    H.bumps = P['bumps']
    if fitfile: apply_fit(H, fitfile)
    if 'nf_d' in kw:                       # rounder cross-section: lower the front-section exponent around z = nf_z (gaussian, width nf_w)
        z0, w = kw.get('nf_z', 1.50), kw.get('nf_w', 0.03)
        H.L.nf = H.L.nf - kw['nf_d'] * np.exp(-((H.L.zk - z0) / w) ** 2)
    return H, P


def build_variant(name, **kw):
    if kw.get('protect_eyes_ears', 0): exp.PROTECT_GROUPS = exp.PROTECT_GROUPS + ('LOOP_eyeL', 'LOOP_eyeR', 'LOOP_lid_up_L', 'LOOP_lid_up_R', 'LOOP_lid_low_L', 'LOOP_lid_low_R', 'LOOP_ear_attach_L', 'LOOP_ear_attach_R', 'LOOP_helix_L', 'LOOP_helix_R', 'LOOP_concha_L', 'LOOP_concha_R')
    exp.SMOOTH5['on'] = bool(kw.get('s5', 0))
    ctx = exp.Ctx()
    H, P = make_H(**kw)
    if 'ztop' in kw: exp.ZONE['zt'] = (kw['ztop'], kw['ztop'] + 0.025)
    Vn, D, nbad = exp.mesh_normal_delta(H, ctx, name, nb=P['zone']['neck_blend'])
    exp.ZONE.clear()
    return Vn, ctx, H


def render(name):
    subprocess.run([B, '-b', '--factory-startup', '--python', W3 + 'tools/ul.py', '--', W3 + f'data/var_{name}.npz', W3 + 'renders/trial', VIEWS, name], check=True, capture_output=True)


def sheet(names, out, labels=None):
    from PIL import Image, ImageDraw, ImageFont
    try: font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 30)
    except Exception: font = ImageFont.load_default()
    src = Image.open(fl.PLATES / 'female_head_detail.jpg').convert('RGB')
    h = 0.065 / fl.K; r = float(fl.rowz(1.49)); c = 653 + (-0.03 - fl.Y0) / fl.K
    plate = src.crop((int(c - h), int(r - h), int(c + h), int(r + h))).resize((1100, 1100), Image.LANCZOS)
    cols = [('PLATE (profile)', plate)]
    for n in names:
        im = Image.open(W3 + f'renders/trial/{n}_{NAMES[0]}.png').convert('RGBA'); bg = Image.new('RGBA', im.size, (224, 224, 226, 255)); bg.alpha_composite(im); cols.append((n, bg.convert('RGB')))
    S = 700
    sh = Image.new('RGB', (S * len(cols), S * 3 + 44), (20, 20, 22)); d = ImageDraw.Draw(sh)
    for k, (lab, im) in enumerate(cols):
        d.text((k * S + 10, 6), lab, fill=(255, 255, 255), font=font); sh.paste(im.resize((S, S), Image.LANCZOS), (k * S, 44))
        for j in (1, 2):
            if k == 0: continue
            n = names[k - 1]; im2 = Image.open(W3 + f'renders/trial/{n}_{NAMES[j]}.png').convert('RGBA'); bg = Image.new('RGBA', im2.size, (224, 224, 226, 255)); bg.alpha_composite(im2)
            sh.paste(bg.convert('RGB').resize((S, S), Image.LANCZOS), (k * S, 44 + j * S))
    sh.save(out); return sh.size


if __name__ == '__main__':
    name = sys.argv[1]; kw = {}
    for a in sys.argv[2:]:
        k, v = a.split('='); kw[k] = float(v)
    build_variant(name, **kw); render(name)
    print('built + rendered', name, kw)
