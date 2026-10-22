import sys
sys.path.insert(0, '.')
exec(open('photo.py').read().split("if __name__ == '__main__':")[0])
up = 2
for name in ('front', 'q3L'):
    N, m = load_normals(Path('r/nrm0') / f'{name}_nrm.exr')
    lum = plate_lum(name, up)
    r0, r1, c0, c1 = [v * up for v in DOME[name]]
    mm_ = m[r0:r1, c0:c1]
    print(name, 'dome mask coverage', mm_.mean())
    # luminance vs normal components (binned)
    Ns = N[r0:r1, c0:c1][mm_]; Ls = lum[r0:r1, c0:c1][mm_]
    print(' lum mean %.1f std %.1f' % (Ls.mean(), Ls.std()))
    for comp, nm in ((0, 'nx (right)'), (1, 'ny (up)'), (2, 'nz (toward cam)')):
        bins = np.linspace(-1, 1, 9)
        out = []
        for i in range(8):
            sel = (Ns[:, comp] >= bins[i]) & (Ns[:, comp] < bins[i + 1])
            out.append('%.0f' % Ls[sel].mean() if sel.sum() > 30 else '--')
        print('  lum by', nm, out)
    # best fit with b>0
    best = None
    for az in range(-80, 81, 4):
        for el in range(-20, 81, 4):
            l = light_vec(az, el); s = np.clip(Ns @ l, 0, None)
            A = np.stack([np.ones_like(s), s], axis=1); sol = np.linalg.lstsq(A, Ls, rcond=None)[0]
            if sol[1] <= 0: continue
            rms = np.sqrt(np.mean((A @ sol - Ls) ** 2))
            if best is None or rms < best[0]: best = (rms, az, el, sol[0], sol[1])
    print(' best b>0:', best)
