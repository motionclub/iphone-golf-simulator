"""torso_measure.py: the torso by height (rest pose, arms left out): width across, depth front to back, how far the front and
the back stand from the spine line, girth. Base, the 11-11 build's torso (what the muscle arm sits on), and the chest model."""
import sys, numpy as np, armio, posed
sk = posed.sk['Body']; arms = posed.mL + posed.mR
def girth(x, z):
    a = np.arctan2(z - z.mean(), x - x.mean()); nb = 48; b = np.floor((a + np.pi) / (2 * np.pi) * nb).astype(int) % nb
    r = np.hypot(x - x.mean(), z - z.mean()); R = np.array([np.percentile(r[b == i], 90) if (b == i).any() else np.nan for i in range(nb)])
    ok = ~np.isnan(R); th = (np.arange(nb)[ok] + .5) / nb * 2 * np.pi; px, pz = R[ok] * np.cos(th), R[ok] * np.sin(th)
    return np.hypot(np.roll(px, -1) - px, np.roll(pz, -1) - pz).sum()
def profile(pos, ys):
    out = []
    for y in ys:
        s = (arms < .3) & (pos[:, 1] >= y - .012) & (pos[:, 1] < y + .012)
        p = pos[s]; out.append((y, np.ptp(p[:, 0]) * 100, np.ptp(p[:, 2]) * 100, p[:, 2].max() * 100, p[:, 2].min() * 100, girth(p[:, 0], p[:, 2]) * 100))
    return out
YS = [1.36, 1.33, 1.30, 1.27, 1.24, 1.21, 1.18, 1.15, 1.12, 1.09, 1.06, 1.03, 1.00, 0.97, 0.94, 0.90]
if __name__ == "__main__":
    sets = [("base", posed.load("male_build0")['Body']['pos']), ("build torso", posed.load("male_torso")['Body']['pos'])]
    for name, pos in sets:
        print(f"== {name}: height | width | depth | front z | back z | girth (cm)")
        for y, w, d, f, b, g in profile(pos, YS): print(f"   {y:4.2f}   {w:5.1f}  {d:5.1f}   {f:5.1f}  {b:6.1f}   {g:5.1f}")
