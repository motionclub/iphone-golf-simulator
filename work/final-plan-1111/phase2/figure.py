"""figure.py: the whole figure, measured the way a picture of it is read: widths seen from the front and depths seen from the
side at named places from the neck to the ankle, arms hanging, plus girths. For the base body, the body in the game today, and
the body with the new arms and chest. `table()` is used by the diagnosis board."""
import numpy as np, armio, armfield as af, posed, fit
B = posed.B
def girth_of(x, z):
    cx, cz = (x.max() + x.min()) / 2, (z.max() + z.min()) / 2; a = np.arctan2(z - cz, x - cx); nb = 40; b = np.floor((a + np.pi) / (2 * np.pi) * nb).astype(int) % nb
    r = np.hypot(x - cx, z - cz); R = np.array([np.percentile(r[b == i], 92) if (b == i).any() else np.nan for i in range(nb)])
    ok = ~np.isnan(R); th = (np.arange(nb)[ok] + .5) / nb * 2 * np.pi; px, pz = R[ok] * np.cos(th), R[ok] * np.sin(th)
    return np.hypot(np.roll(px, -1) - px, np.roll(pz, -1) - pz).sum() * 100
def band(p, y, h=.012): return p[(p[:, 1] >= y - h) & (p[:, 1] < y + h)]
def measure(parts):
    rest = parts['Body']['pos']; arms = posed.mL + posed.mR
    trunk = rest[arms < .3]; H = rest[:, 1].max() - rest[:, 1].min(); out = dict(height=H * 100)
    def best(ys, f, pick=max): return pick(f(band(trunk, y)) for y in ys)
    w = lambda q: np.ptp(q[:, 0]) * 100; dp = lambda q: np.ptp(q[:, 2]) * 100; g = lambda q: girth_of(q[:, 0], q[:, 2])
    head = rest[rest[:, 1] > B["Head"][1] + .02]; out['head_w'] = np.ptp(head[np.abs(head[:, 2] - head[:, 2].mean()) < .05][:, 0]) * 100
    chin = B["Head"][1] + .02; out['head_h'] = (rest[:, 1].max() - chin) * 100
    ny = np.arange(B["Neck"][1] + .02, B["Head"][1] + .0, .01); out['neck_w'] = best(ny, w, min); out['neck_g'] = best(ny, g, min)
    out['chest_w'] = best(np.arange(1.17, 1.26, .01), w); out['chest_d'] = best(np.arange(1.17, 1.26, .01), dp); out['chest_g'] = best(np.arange(1.17, 1.26, .01), g)
    out['waist_w'] = best(np.arange(.98, 1.08, .01), w, min); out['waist_d'] = best(np.arange(.98, 1.08, .01), dp, min); out['waist_g'] = best(np.arange(.98, 1.08, .01), g, min)
    hy = np.arange(B["Hips"][1] - .06, B["Hips"][1] + .04, .01); out['hip_w'] = best(hy, w); out['hip_d'] = best(hy, dp); out['hip_g'] = best(hy, g)
    leg = rest[(rest[:, 0] < -0.005) & (arms < .3)]; hipj, knee, ank = B["LeftUpperLeg"], B["LeftLowerLeg"], B["LeftFoot"]
    def legat(y): q = band(leg, y); return (np.ptp(q[:, 0]) * 100, np.ptp(q[:, 2]) * 100, girth_of(q[:, 0], q[:, 2]))
    ty = [hipj[1] + (knee[1] - hipj[1]) * f for f in (.25, .35, .45)]; out['thigh_w'], out['thigh_d'], out['thigh_g'] = max(legat(y) for y in ty)
    out['knee_w'], out['knee_d'], out['knee_g'] = legat(knee[1])
    cy = [knee[1] + (ank[1] - knee[1]) * f for f in (.2, .3, .4)]; out['calf_w'], out['calf_d'], out['calf_g'] = max(legat(y) for y in cy)
    out['ankle_w'], out['ankle_d'], out['ankle_g'] = min(legat(knee[1] + (ank[1] - knee[1]) * f) for f in (.8, .88, .95))
    out['leg_len'] = (hipj[1] - ank[1]) * 100; out['trunk_len'] = (B["Neck"][1] - hipj[1]) * 100
    out['uparm_len'] = np.linalg.norm(B["LeftLowerArm"] - B["LeftUpperArm"]) * 100; out['forearm_len'] = np.linalg.norm(B["LeftHand"] - B["LeftLowerArm"]) * 100
    a = posed.measure("x", parts); out.update(shoulders=a['bare'], uparm_w=a['up'], uparm_d=a['upd'], forearm_w=a['fo'], forearm_d=a['fod'], wrist_w=a['wr'], elbow_w=a['el'], uparm_g=a['gup'], forearm_g=a['gfo'])
    return out
def table():
    t = posed.load("male_torso")
    return [("base body", measure(posed.load("male_build0"))), ("in the game today", measure(posed.load("male_build1"))), ("new arms + chest", measure(fit.dress(t, B, posed.mL, posed.mR, fit=False)))]
if __name__ == "__main__":
    T = table(); keys = list(T[0][1].keys())
    print(f"{'':14}" + "".join(f"{n:>20}" for n, _ in T))
    for k in keys: print(f"{k:14}" + "".join(f"{m[k]:20.1f}" for _, m in T))
