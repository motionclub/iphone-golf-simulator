"""lava8.py <outdir> [--set '<json of LAVA_P overrides>'] [--iters N] [--no-fit] [--crop x0,y0] : v8 lava experiments (Blender's python3.13).
Runs stage 1 (+ optional tone-curve fit), encode, writes Lava_C/E/N.png + rgb.npy + sheet.png (1x tile, a Game-view-like near crop at x1.5, a phone-grazing view) and prints
the Game-view-comparable statistics of the SHADER MODEL image (what GolfLava paints) and of crater.jpg's pool."""
import sys, os, time, json, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
sys.path.insert(0, os.path.join(ROOT, 'work/postcard-look/v2/tools')); sys.path.insert(0, os.path.join(ROOT, 'work/postcard-look/v2/tex/v7/tools'))
import lab
import lava_try as lt

def hsv(rgb):
    a = rgb / 255.0; r, gg, b = a[..., 0], a[..., 1], a[..., 2]; mx = a.max(-1); mn = a.min(-1); d = mx - mn
    h = np.zeros_like(mx); m = d > 1e-9
    rm = m & (mx == r); gm = m & (mx == gg) & ~rm; bm = m & ~rm & ~gm
    h[rm] = ((gg - b)[rm] / d[rm]) % 6; h[gm] = (b - r)[gm] / d[gm] + 2; h[bm] = (r - gg)[bm] / d[bm] + 4
    return h * 60, np.where(mx > 1e-9, d / np.maximum(mx, 1e-9), 0), mx

def stats(rgb):
    L = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    h, s, v = hsv(rgb)
    # thin bright veins: white top-hat of the luminance, 9-px opening
    def mx(a, k):
        hk = k // 2; b = a
        for ax in (0, 1):
            m = b
            for d in range(1, hk + 1): m = np.maximum(m, np.maximum(np.roll(b, d, ax), np.roll(b, -d, ax)))
            b = m
        return b
    op = -mx(-mx(L, 7) * 1.0, 7)  # approximate opening: erode via -max(-.)
    op = -mx(-L, 7); op = mx(op, 7)
    th = L - op
    return dict(lum_mean=round(float(L.mean()), 1), lum_sd=round(float(L.std()), 1), p10=round(float(np.percentile(L, 10)), 1), p50=round(float(np.percentile(L, 50)), 1), p90=round(float(np.percentile(L, 90)), 1), p99=round(float(np.percentile(L, 99)), 1),
                V_lt_040=round(float((v < .4).mean()), 4), V_lt_055=round(float((v < .55).mean()), 4), G_gt_120=round(float((rgb[..., 1] > 120).mean()), 4), G_gt_140=round(float((rgb[..., 1] > 140).mean()), 4),
                vein_share=round(float((th > 12).mean()), 4), vein_share20=round(float((th > 20).mean()), 4), in_band=round(float(((h >= 8) & (h <= 28) & (s >= .75) & (v >= .7)).mean()), 4))

if __name__ == '__main__':
    a = sys.argv[1:]; outdir = a[0]; os.makedirs(outdir, exist_ok=True)
    iters = 6; dofit = True; kv = {}; crop = (300, 300)
    i = 1
    while i < len(a):
        if a[i] == '--iters': iters = int(a[i + 1]); i += 2; continue
        if a[i] == '--no-fit': dofit = False; i += 1; continue
        if a[i] == '--set': kv = json.loads(a[i + 1]); i += 2; continue
        if a[i] == '--drho': lt.D_RHO[:] = [float(x) for x in a[i + 1].split(',')]; i += 2; continue
        if a[i] == '--dheat': lt.D_HEAT[:] = [float(x) for x in a[i + 1].split(',')]; i += 2; continue
        if a[i] == '--crop': crop = tuple(int(x) for x in a[i + 1].split(',')); i += 2; continue
        i += 1
    for k, v in kv.items():
        if k in ('quantile', 'd_rho', 'd_heat'): continue
        g.LAVA_P[k] = tuple(tuple(x) if isinstance(x, list) else x for x in v) if isinstance(v, list) else v
    t = time.time(); F0 = g.lava_fields(); print('stage1 %.1fs' % (time.time() - t), flush=True)
    if kv.get('quantile'): g.LAVA_ENC['quantile'] = 1; dofit = False
    if 'd_rho' in kv: g.LAVA_ENC['d_rho'] = tuple(kv['d_rho'])
    if 'd_heat' in kv: g.LAVA_ENC['d_heat'] = tuple(kv['d_heat'])
    lut0 = list(g.LAVA_ENC['lut'])
    if g.LAVA_P.get('rank', 0): lut0 = [float(x) for x in np.interp(g.LAVA_LUT_X, lt.D_RHO, lt.D_HEAT)]
    lut = lt.fit(F0, g.LAVA_ENC['alpha'], iters, lut0, lt.D_RHO, lt.D_HEAT) if dofit else lut0
    print('LUT', [round(float(x), 3) for x in lut])
    r = g.lava_encode(F0, g.LAVA_ENC['alpha'], lut)
    C, E, N = g.enc(r['C']), g.enc(r['E']), g.enc_normal(r['N'])
    for nm, arr in (('C', C), ('E', E), ('N', N)):
        g.write_png(os.path.join(outdir, 'Lava_%s.png' % nm), arr)
    sp = g.lava_spec()
    h_, rgb = g.lava_shader_model(C, E, N, sp)
    np.save(os.path.join(outdir, 'rgb.npy'), rgb.astype(np.uint8))
    print('STATS', json.dumps(stats(rgb)))
    img_ = (rgb / 255.0)[:1020, :1020].reshape(170, 6, 170, 6, 3).mean((1, 3)); L14 = g.lum(img_.astype(np.float32)); b4 = L14[:168, :168].reshape(42, 4, 42, 4).mean((1, 3))
    print('REGIONAL block-mean sd at 14 cm/px: %.1f/255 (gate >= 24.5)' % (b4.std() * 255))
    print(g.lava_report(C, E, N, sp).split('\n')[0])
    def gate(what, ok, detail): print('GATE: %s %s (%s)' % (what[:70], 'PASS' if ok else 'FAIL', detail[:300]))
    g.lava_gates({'Lava_C.png': C, 'Lava_E.png': E, 'Lava_N.png': N}, gate)
    img = rgb / 255.0
    x0, y0 = crop
    cr = img[y0:y0 + 400, x0:x0 + 400]
    # x1.5 bilinear
    def bil(a, n):
        h, w = a.shape[:2]; ys = (np.arange(n) + .5) * h / n - .5; xs = (np.arange(n) + .5) * w / n - .5
        y0_ = np.clip(np.floor(ys).astype(int), 0, h - 2); x0_ = np.clip(np.floor(xs).astype(int), 0, w - 2); fy = np.clip(ys - y0_, 0, 1)[:, None, None]; fx = np.clip(xs - x0_, 0, 1)[None, :, None]
        return (a[y0_][:, x0_] * (1 - fx) * (1 - fy) + a[y0_][:, x0_ + 1] * fx * (1 - fy) + a[y0_ + 1][:, x0_] * (1 - fx) * fy + a[y0_ + 1][:, x0_ + 1] * fx * fy)
    crim = bil(cr, 600)
    one = lab.fit(img, 512)
    p, hit = lab.persp(lab.tile(img, 2), 24 * 2, size=(1040, 330), cam_h=8.0, pitch_deg=-8.0)
    out = lab.vstack([lab.hstack([lab.label(one, 'LAVA 1X'), lab.label(crim, 'NEAR x1.5 (400px crop)')]), lab.label(p, 'PHONE GRAZING (8 m up, -8 deg)')])
    lab.write(os.path.join(outdir, 'sheet.png'), out)
    g.write_png(os.path.join(outdir, 'near.png'), g.enc(crim))
    print('wrote', outdir, 'time %.0fs' % (time.time() - t))
