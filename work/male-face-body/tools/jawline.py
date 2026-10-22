"""Front-view jaw outline from the game-frame mesh (eval/<tag>_mesh.npz): z-buffer, jaw edge = lowest row (per column) of the face
sheet where depth jumps back to the neck by > 6 mm. Prints rise (mm above the chin bottom) per |x|; optional ref parabola."""
import sys, numpy as np
R = .25
def zbuf(tag):
    d = np.load(f'eval/{tag}_mesh.npz'); G = d['G']; tri = d['tri']
    T = G[tri]; keep = (T[:, :, 1].max(1) < -30) & (T[:, :, 1].min(1) > -175) & (np.abs(T[:, :, 0]).min(1) < 90) & (T[:, :, 2].max(1) > -120)
    T = T[keep]
    W, H = int(180 / R), int(145 / R)            # x -90..90, y -175..-30
    Z = np.full((H, W), -1e9)
    for t in T:
        px = (t[:, 0] + 90) / R; py = (-30 - t[:, 1]) / R
        x0, x1 = int(max(px.min(), 0)), int(min(px.max() + 1, W - 1)); y0, y1 = int(max(py.min(), 0)), int(min(py.max() + 1, H - 1))
        if x1 < x0 or y1 < y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        (ax, ay), (bx, by), (cx, cy) = zip(px, py)
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9: continue
        l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den; l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den; l3 = 1 - l1 - l2
        m = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
        z = l1 * t[0, 2] + l2 * t[1, 2] + l3 * t[2, 2]
        sub = Z[y0:y1 + 1, x0:x1 + 1]; upd = m & (z > sub); sub[upd] = z[upd]
    return Z
def jaw(Z):
    W = Z.shape[1]; out = {}
    for xmm in range(0, 66, 3):
        col = int((xmm + 90) / R)
        c = Z[:, col]; best = None
        for r in range(int(70 / R), Z.shape[0] - 2):    # from y = -100 down
            if c[r] > -1e8 and (c[r + 1] < c[r] - 6 or c[r + 1] < -1e8):
                best = r; break
        out[xmm] = None if best is None else -30 - (best + 1) * R
    return out
if __name__ == '__main__':
    for tag in sys.argv[1:]:
        Z = zbuf(tag); np.save(f'eval/{tag}_zbuf.npy', Z); j = jaw(Z); y0 = j[0]
        print(tag, 'chin', y0, {k: (round(v - y0, 1) if v is not None else None) for k, v in j.items()})
    s = .977
    print('ref  ', {x: round(.0078 * (x / s) ** 2 * s, 1) for x in range(0, 66, 3)})
