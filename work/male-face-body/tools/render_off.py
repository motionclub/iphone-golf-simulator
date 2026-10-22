"""Tiny numpy software renderer (orthographic, z-buffer, smooth Lambert + soft key) for quick form checks of the game-frame head
without a Blender/Unity slot.  render(G, tri, yaw_deg, out.png, half=130, res=700, centre=(0,-35,0))   G in mm (face frame: x right,
y up, z forward toward the camera at yaw 0).  Positive yaw turns the camera toward the hero's left (image shows his right cheek)."""
import numpy as np
from PIL import Image

SMOOTH_N = 3     # ~ the game's HeroSkinNormals (5-12 mm continuous normals) on ~3 mm edges; 0 = raw geometric normals
def vnormals(G, tri, passes=None):
    n = np.zeros_like(G); c = np.cross(G[tri[:, 1]] - G[tri[:, 0]], G[tri[:, 2]] - G[tri[:, 0]])
    for k in range(3): np.add.at(n, tri[:, k], c)
    n = -n / np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    for _ in range(SMOOTH_N if passes is None else passes):
        f = n[tri].sum(1); acc = np.zeros_like(n)
        for k in range(3): np.add.at(acc, tri[:, k], f)
        acc = np.where((np.einsum('ij,ij->i', acc, n) > 0)[:, None], acc, n)
        n = acc / np.maximum(np.linalg.norm(acc, axis=1), 1e-12)[:, None]
    return n

def render(G, tri, yaw, out=None, half=130, res=700, centre=(0, -35, 0), keep=None, color=(.86, .66, .52)):
    a = np.radians(yaw); R = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    P = (G - np.array(centre)) @ R.T; N = vnormals(G, tri) @ R.T
    if keep is not None: tri = tri[keep]
    s = res / (2 * half); px = P[:, 0] * s + res / 2; py = res / 2 - P[:, 1] * s
    Z = np.full((res, res), -1e9); I = np.zeros((res, res, 3)); A = np.zeros((res, res), bool)
    T = tri[(P[tri][:, :, 2].max(1) > -1e8)]
    L = np.array([-.35, .45, .82]); L /= np.linalg.norm(L)
    for t in T:
        xs, ys = px[t], py[t]
        x0, x1 = int(max(xs.min(), 0)), int(min(xs.max() + 1, res - 1)); y0, y1 = int(max(ys.min(), 0)), int(min(ys.max() + 1, res - 1))
        if x1 < x0 or y1 < y0: continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        (ax, ay), (bx, by), (cx, cy) = zip(xs, ys)
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12: continue
        l1 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / den; l2 = ((cy - ay) * (X - cx) + (ax - cx) * (Y - cy)) / den; l3 = 1 - l1 - l2
        m = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        if not m.any(): continue
        z = l1 * P[t[0], 2] + l2 * P[t[1], 2] + l3 * P[t[2], 2]
        sub = Z[y0:y1 + 1, x0:x1 + 1]; upd = m & (z > sub)
        if not upd.any(): continue
        n = l1[..., None] * N[t[0]] + l2[..., None] * N[t[1]] + l3[..., None] * N[t[2]]; n /= np.maximum(np.linalg.norm(n, axis=-1), 1e-12)[..., None]
        sh = .30 + .70 * np.clip(n @ L, 0, 1) + .12 * np.clip(n[..., 2], 0, 1)
        sub[upd] = z[upd]; I[y0:y1 + 1, x0:x1 + 1][upd] = (np.array(color)[None, None] * sh[..., None])[upd]; A[y0:y1 + 1, x0:x1 + 1][upd] = True
    img = np.where(A[..., None], I, .88); img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    if out: Image.fromarray(img).save(out)
    return img, A
