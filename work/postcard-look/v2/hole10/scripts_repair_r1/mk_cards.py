"""mk_cards.py: [ (name, cam_xy, (x,y,z), (w,h), n_cards, spread) ... ] -> JSON for smoke_probe.py (system python)."""
import json, math, random, sys
def group(cx, cy, p, wh, n, seed, spread=0.10, face=None):
    rnd = random.Random(seed); out = []
    fx, fy = face if face else (cx, cy)
    # lateral axis perpendicular to the view direction p - cam
    dx, dy = p[0] - fx, p[1] - fy; L = math.hypot(dx, dy); lx, ly = -dy / L, dx / L
    for i in range(n):
        k = (i - (n - 1) / 2.0) if n > 1 else 0.0
        off = k * spread * wh[0] + rnd.uniform(-0.03, 0.03) * wh[0]
        dep = rnd.uniform(-0.04, 0.04) * wh[0]
        s = 1.0 + rnd.uniform(-0.12, 0.12)
        out.append([p[0] + lx * off + dx / L * dep, p[1] + ly * off + dy / L * dep, p[2] + rnd.uniform(-0.04, 0.04) * wh[1], wh[0] * s, wh[1] * s, seed * 10 + i, fx, fy])
    return out
if __name__ == "__main__":
    spec = json.load(open(sys.argv[1])); cards = []
    for g in spec:
        cards += group(g["cam"][0], g["cam"][1], g["p"], g["wh"], g.get("n", 3), g.get("seed", 1), g.get("spread", 0.10), g.get("face"))
    json.dump(cards, open(sys.argv[2], "w")); print(len(cards), "cards")
