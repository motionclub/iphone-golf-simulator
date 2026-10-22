"""lava_v5.py <outdir> [key=value ...] [--iters N] [--no-fit] : v5 lava experiments (Blender's python3.13).
Overrides LAVA_P keys (floats; dz_cyc=a,b), computes stage 1, rank-fits the tone curve to crater.jpg's pool (lava_v3.fit logic with the in-memory fields),
writes Lava_C/E/N.png into <outdir>, prints the generator's lava gates and writes <outdir>/sheet.png (GolfLava shader-model previews)."""
import sys, os, time, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); TOOLS = os.path.join(HERE, '..', '..', '..', 'tools')
sys.path.insert(0, TOOLS)
import lab
g = lab.gl
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

def shade(C, E, N, sp):
    h, rgb = g.lava_shader_model(C, E, N, sp)
    return rgb / 255.0

def sheet(path, C, E, N):
    sp = g.lava_spec(); img = shade(C, E, N, sp)
    one = lab.fit(img, 512); t3 = lab.fit(lab.tile(img, 3), 512)
    p, hit = lab.persp(lab.tile(img, 2), 24 * 2, size=(1040, 330), cam_h=8.0, pitch_deg=-8.0)
    ref = g.read_png(os.path.join(HERE, '..', 'refs', 'crater_lava_crop.png'))[..., :3].astype(np.float64) / 255 if os.path.exists(os.path.join(HERE, '..', 'refs', 'crater_lava_crop.png')) else None
    top = lab.hstack([lab.label(one, 'LAVA 1X'), lab.label(t3, 'LAVA 3X3')])
    out = lab.vstack([top, lab.label(p, 'PHONE GRAZING (8 m up, -8 deg)')])
    lab.write(path, out)

if __name__ == '__main__':
    a = sys.argv[1:]; outdir = a[0]; os.makedirs(outdir, exist_ok=True)
    iters = 6; dofit = True; kv = {}
    i = 1
    while i < len(a):
        if a[i] == '--iters': iters = int(a[i + 1]); i += 2; continue
        if a[i] == '--no-fit': dofit = False; i += 1; continue
        k, v = a[i].split('=')
        kv[k] = tuple(int(x) for x in v.split(',')) if ',' in v else float(v)
        i += 1
    g.LAVA_P.update(kv)
    t = time.time(); F0 = g.lava_fields(); print('stage1 %.1fs' % (time.time() - t), flush=True)
    lut = fit(F0, g.LAVA_ENC['alpha'], iters, list(g.LAVA_ENC['lut'])) if dofit else list(g.LAVA_ENC['lut'])
    print('LUT', [round(float(x), 3) for x in lut])
    r = g.lava_encode(F0, g.LAVA_ENC['alpha'], lut)
    C, E, N = g.enc(r['C']), g.enc(r['E']), g.enc_normal(r['N'])
    for nm, arr in (('C', C), ('E', E), ('N', N)):
        g.write_png(os.path.join(outdir, 'Lava_%s.png' % nm), arr)
    sp = g.lava_spec()
    print(g.lava_report(C, E, N, sp))
    res = []
    def gate(what, ok, detail): print('GATE: %s %s (%s)' % (what[:60], 'PASS' if ok else 'FAIL', detail))
    g.lava_gates({'Lava_C.png': C, 'Lava_E.png': E, 'Lava_N.png': N}, gate)
    sheet(os.path.join(outdir, 'sheet.png'), C, E, N)
    print('wrote', outdir)
