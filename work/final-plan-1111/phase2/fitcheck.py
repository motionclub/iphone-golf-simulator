"""fitcheck.py [export tag]: a top before and after the fit, by region: clearance to the skin along the skin's normal (cm) and
how many vertices end up under it."""
import sys, numpy as np, armio, armfield as af, posed, fit
tag = sys.argv[1] if len(sys.argv) > 1 else "male_torso"
def gap(pa, top="Kit_Top"):
    bb, tt = pa['Body'], pa[top]; sb = (bb['pos'][:, 1] > 0.80) & (bb['pos'][:, 1] < 1.50)
    P, N, Q = bb['pos'][sb], bb['nrm'][sb], tt['pos']; out = np.empty(len(Q))
    for i in range(0, len(Q), 300):
        d = ((Q[i:i + 300, None, :] - P[None]) ** 2).sum(2); j = d.argmin(1); out[i:i + 300] = ((Q[i:i + 300] - P[j]) * N[j]).sum(1)
    return out * 100
def regions(p0):
    x, y, z = np.abs(p0[:, 0]), p0[:, 1], p0[:, 2]
    arm = (x > 0.215); neck = (y > 1.34) & ~arm
    return [("sleeve", arm), ("shoulder / armpit", (x > 0.15) & ~arm & (y > 1.2) & ~neck), ("collar and neck", neck), ("chest", (z > .06) & (y > 1.17) & (y <= 1.34) & (x <= .15)),
            ("back", (z <= .0) & (y > 1.1) & (y <= 1.34) & (x <= .15)), ("stomach", (z > .06) & (y <= 1.17)), ("lower back and sides", (z <= .06) & (y <= 1.17) | ((z > 0) & (z <= .06) & (x <= .15) & (y <= 1.34) & (y > 1.17)))]
if __name__ == "__main__":
    parts = {n: armio.read(f"export/{tag}/{n}.bin") for n in ("Body", "Kit_Top", "Kit_Bottom")}
    loose = fit.dress(parts, posed.B, posed.mL, posed.mR, fit=False); snug = fit.dress(parts, posed.B, posed.mL, posed.mR, fit=True)
    g0, g1 = gap(loose), gap(snug); p0 = parts['Kit_Top']['pos']
    print("region                 n      before: least  5%  median     after: least  5%  median   under the skin before -> after")
    for name, s in regions(p0):
        if s.sum(): print(f"  {name:20} {s.sum():5d}        {g0[s].min():5.2f} {np.percentile(g0[s],5):5.2f} {np.median(g0[s]):5.2f}          {g1[s].min():5.2f} {np.percentile(g1[s],5):5.2f} {np.median(g1[s]):5.2f}      {int((g0[s]<0).sum()):4d} -> {int((g1[s]<0).sum()):4d}")
