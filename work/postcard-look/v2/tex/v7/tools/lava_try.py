"""lava_try.py <outdir> [key=value ...] [--iters N] [--no-fit] [--aa=a,b,s;a,b,s;..] : v7 lava experiments (Blender's python3.13).
Overrides LAVA_P keys, optional LAVA_AA levels, runs stage 1 + tone-curve fit (lava_v5.fit logic) + encode, writes Lava_C/E/N.png into <outdir>,
prints the hairline metrics (gradient percentiles of the shader-model luminance and of Lava_E) and the generator's lava gates, writes sheet.png."""
import sys, os, time, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
sys.path.insert(0, os.path.join(ROOT, 'work/postcard-look/v2/tools'))
import lab
D_RHO = [0.0, 0.12, 0.25, 0.50, 0.75, 0.90, 0.97, 1.0]
D_HEAT = [0.0, 0.157, 0.28, 0.44, 0.68, 0.90, 0.98, 1.0]

def fit(F0, alpha, iters, lut=None, d_rho=D_RHO, d_heat=D_HEAT):
    sp = g.lava_spec()
    hh, crust, seam = [g.ssdown(a_, 2) for a_ in g.lava_design(F0)]
    mol = (crust < 0.03) & (seam < 0.03)
    X = np.array(g.LAVA_LUT_X); lut = list(X if lut is None else lut)
    for it in range(iters):
        r = g.lava_encode(F0, alpha, lut)
        C, E, N = g.enc(r['C']), g.enc(r['E']), g.enc_normal(r['N'])
        H = g.lava_shader_model(C, E, N, sp)[0]
        Hs = np.sort(H.ravel()); newlut = list(lut)
        for k, x in enumerate(X):
            sel = mol & (np.abs(hh - x) < 0.02)
            if sel.sum() < 300: continue
            hk = float(np.median(H[sel])); rho = float(np.searchsorted(Hs, hk) / Hs.size)
            tk = float(np.interp(rho, d_rho, d_heat))
            newlut[k] = lut[k] + (tk - hk) / 2.2 * 0.8
        newlut[0] = 0.0
        for k in range(1, len(newlut)):
            newlut[k] = float(np.clip(max(newlut[k], newlut[k - 1] + 0.004), 0, 1.0))
        lut = newlut
    return lut

def hair(C, E, N, sp):
    h, rgb = g.lava_shader_model(C, E, N, sp)
    L = g.lum(rgb.astype(np.float32) / 255) * 255
    gx = np.abs(np.roll(L, -1, 1) - L); gy = np.abs(np.roll(L, -1, 0) - L)
    gg = np.maximum(gx, gy)
    Le = g.lum(E.astype(np.float32) / 255) * 255
    ge = np.maximum(np.abs(np.roll(Le, -1, 1) - Le), np.abs(np.roll(Le, -1, 0) - Le))
    def mx(a, k):
        hk = k // 2; b = a
        for ax in (0, 1):
            m = b
            for d in range(1, hk + 1): m = np.maximum(m, np.maximum(np.roll(b, d, ax), np.roll(b, -d, ax)))
            b = m
        return b
    bh = -mx(-mx(L, 5), 5) - L          # black top-hat: thin (<=4 texel) dark features, levels
    wh_ = L - mx(-mx(-L, 5) * -1 * -1, 5) if False else None
    lines = []
    longest_list = []
    for T_ in (20,):
        comps = [c for c in g.label_components(bh > T_) if len(c[0]) >= 30]
        n60 = 0; longest = 0.0
        for ys, xs in comps:
            y = ys.astype(np.float64); x = xs.astype(np.float64)
            y = np.where(y - y[0] > 512, y - 1024, np.where(y - y[0] < -512, y + 1024, y)); x = np.where(x - x[0] > 512, x - 1024, np.where(x - x[0] < -512, x + 1024, x))
            cov = np.cov(np.stack([x, y])) + np.eye(2) / 12
            ev = np.linalg.eigvalsh(cov); ln = float(np.sqrt(12 * ev[1])); wd = len(ys) / max(ln, 1)
            if wd <= 6 and ln >= 60: n60 += 1; longest_list.append((round(ln), int(y.mean()) % 1024, int(x.mean()) % 1024, round(float(bh[ys, xs].max()))))
            if wd <= 6: longest = max(longest, ln)
        lines.append((T_, n60, round(longest)))
    longest_list.sort(reverse=True)
    return dict(hairlines_len60=lines, longest=longest_list[:8], thin_dark_share10=float((bh > 10).mean() * 100), thin_dark_share20=float((bh > 20).mean() * 100), thin_dark_max=float(bh.max()),
                shader_p50=float(np.median(gg)), shader_p99=float(np.percentile(gg, 99)), shader_p999=float(np.percentile(gg, 99.9)), shader_max=float(gg.max()),
                E_p999=float(np.percentile(ge, 99.9)), E_max=float(ge.max()), ratio999=float(np.percentile(gg, 99.9) / np.median(gg)))

if __name__ == '__main__':
    a = sys.argv[1:]; outdir = a[0]; os.makedirs(outdir, exist_ok=True)
    iters = 6; dofit = True; kv = {}; aa = None
    i = 1
    while i < len(a):
        if a[i] == '--iters': iters = int(a[i + 1]); i += 2; continue
        if a[i] == '--no-fit': dofit = False; i += 1; continue
        if a[i].startswith('--aa='):
            aa = tuple(tuple(float(x) for x in lv.split(',')) for lv in a[i][5:].split(';')); i += 1; continue
        k, v = a[i].split('=')
        kv[k] = tuple(int(x) for x in v.split(',')) if ',' in v else float(v)
        i += 1
    g.LAVA_P.update(kv)
    if aa: g.LAVA_AA = aa
    t = time.time(); F0 = g.lava_fields(); print('stage1 %.1fs' % (time.time() - t), flush=True)
    lut = fit(F0, g.LAVA_ENC['alpha'], iters, list(g.LAVA_ENC['lut'])) if dofit else list(g.LAVA_ENC['lut'])
    print('LUT', [round(float(x), 3) for x in lut])
    r = g.lava_encode(F0, g.LAVA_ENC['alpha'], lut)
    C, E, N = g.enc(r['C']), g.enc(r['E']), g.enc_normal(r['N'])
    for nm, arr in (('C', C), ('E', E), ('N', N)):
        g.write_png(os.path.join(outdir, 'Lava_%s.png' % nm), arr)
    sp = g.lava_spec()
    print('HAIR', {k: (round(v, 2) if isinstance(v, float) else v) for k, v in hair(C, E, N, sp).items()})
    print(g.lava_report(C, E, N, sp))
    def gate(what, ok, detail): print('GATE: %s %s (%s)' % (what[:70], 'PASS' if ok else 'FAIL', detail))
    g.lava_gates({'Lava_C.png': C, 'Lava_E.png': E, 'Lava_N.png': N}, gate)
    # sheet: shader-model colour 1x, 3x3 and a phone-grazing view
    h_, rgb = g.lava_shader_model(C, E, N, sp); img = rgb / 255.0
    one = lab.fit(img, 512); t3 = lab.fit(lab.tile(img, 3), 512)
    p, hit = lab.persp(lab.tile(img, 2), 24 * 2, size=(1040, 330), cam_h=8.0, pitch_deg=-8.0)
    # magnified crop (x4.6, bilinear-ish via nearest of a 4x upsample) of a 200x200 region around the strongest filament
    out = lab.vstack([lab.hstack([lab.label(one, 'LAVA 1X'), lab.label(t3, 'LAVA 3X3')]), lab.label(p, 'PHONE GRAZING (8 m up, -8 deg)')])
    lab.write(os.path.join(outdir, 'sheet.png'), out)
    np.save(os.path.join(outdir, 'rgb.npy'), (rgb).astype(np.uint8))
    print('wrote', outdir, 'time %.0fs' % (time.time() - t))
