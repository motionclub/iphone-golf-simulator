"""shoefield.py: a rounded toe on the shoes (Adnan, 2026-11-12: "why are the shoes pointy? fix that"). numpy only.

Measured: every men's shoe is 37 to 39 cm long on a 31 cm foot, and over its last third the upper and the sole narrow from
18 cm to under 4 cm: a point. Seen from above the toe is redrawn as a blunt rounded box (a superellipse), and the front of the
shoe is drawn back a little so the toe stops nearer the toes inside it. Laces, heel, height and everything behind the toe
box are untouched. Rest pose, hero frame (z forward); each shoe is measured on its own, so left and right need no mirroring."""
import numpy as np
from armfield import sstep

TOE = dict(zone=0.125,      # how far back from the tip the reshaping reaches (m)
           shorten=0.022,   # how much the tip is drawn back (m)
           round=0.080,     # the length of the rounded end: across this distance the outline goes from full width to the tip (m)
           power=2.4)       # 2 = half an ellipse; higher = squarer, blunter

def round_toe(pos, T=TOE):
    z = pos[:, 2]; tip = z.max(); d = tip - z; D = T['zone']
    # the outline as it is: per station back from the tip, the two edges, read through a short smoothing
    nb = 50; edges = np.linspace(0, D + 0.03, nb + 1); lo = np.full(nb, np.nan); hi = np.full(nb, np.nan)
    for i in range(nb):
        q = pos[(d >= edges[i]) & (d < edges[i + 1]), 0]
        if len(q) > 3: lo[i], hi[i] = q.min(), q.max()
    ok = ~np.isnan(lo); c = (edges[:-1] + edges[1:]) / 2
    lo = np.interp(c, c[ok], lo[ok]); hi = np.interp(c, c[ok], hi[ok])
    for _ in range(2): lo[1:-1] = (lo[:-2] + lo[1:-1] + lo[2:]) / 3; hi[1:-1] = (hi[:-2] + hi[1:-1] + hi[2:]) / 3
    full = np.interp(D, c, hi - lo) / 2                         # half-width where the toe box begins
    mid_at = lambda dd: (np.interp(dd, c, lo) + np.interp(dd, c, hi)) / 2; half_at = lambda dd: np.maximum((np.interp(dd, c, hi) - np.interp(dd, c, lo)) / 2, 1e-4)
    # drawn back: the front zone is compressed along the foot; then the new outline at the new distance from the new tip
    d2 = np.where(d < D, d * (D - T['shorten']) / D, d - T['shorten'])
    t = np.clip(d2 / T['round'], 0, 1); want = full * (1 - (1 - t) ** T['power']) ** (1 / T['power'])
    ratio = want / half_at(d); ratio = 1 + (ratio - 1) * (1 - sstep(D - 0.035, D, d))
    # the centre line: the point swept in toward the big toe; the rounded box keeps half of that sweep
    mid = mid_at(d); mid0 = mid_at(np.full_like(d, D)); mid2 = mid0 + (mid - mid0) * (1 - 0.5 * (1 - sstep(D - 0.035, D, d)))
    out = pos.copy()
    out[:, 0] = np.where(d < D, mid2 + (pos[:, 0] - mid) * ratio, pos[:, 0])
    out[:, 2] = (tip - T['shorten']) - d2
    return out

def profile(pos):
    z = pos[:, 2]; z0, z1 = z.min(), z.max(); rows = []
    for f in (0.5, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98):
        q = pos[(z >= z0 + (z1 - z0) * f) & (z < z0 + (z1 - z0) * min(1.0, f + .03))]
        rows.append((f, np.ptp(q[:, 0]) * 100 if len(q) > 3 else float('nan')))
    return (z1 - z0) * 100, rows

if __name__ == "__main__":
    import armio
    for tag in ("male_build0", "male_golfkit_base"):
        for side in "LR":
            s = armio.read(f"export/{tag}/Kit_Shoe_{side}.bin")['pos']; n = round_toe(s)
            (l0, r0), (l1, r1) = profile(s), profile(n)
            print(f"{tag} shoe {side}: length {l0:.1f} -> {l1:.1f} cm; width by station (heel 0 .. toe 1): " + "  ".join(f"{f:.2f}: {a:.1f}->{b:.1f}" for (f, a), (_, b) in zip(r0, r1)) + f"; largest move {np.linalg.norm(n - s, axis=1).max()*100:.1f} cm")
