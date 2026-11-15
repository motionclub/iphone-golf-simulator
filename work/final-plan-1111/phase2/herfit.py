"""herfit.py [tag ...]: her tops refitted on her own, unchanged body (fit.dress grow=False), checked region by region."""
import sys, os, numpy as np, armio, fit, herfit_measure as hm
def load(tag):
    parts = {n[:-4]: armio.read(f"export/{tag}/{n}") for n in sorted(os.listdir(f"export/{tag}")) if n.endswith(".bin")}
    B = armio.bones(f"export/{tag}/bones.json"); sk = armio.read_skin(f"export/{tag}/Body.skin")
    return parts, B, armio.membership(sk, sk, "Left"), armio.membership(sk, sk, "Right")
def fitted(tag, do=True):
    parts, B, mL, mR = load(tag); return parts, fit.dress(parts, B, mL, mR, fit=do, grow=False, under=("Kit_Bottom", "Kit_Belt"))
if __name__ == "__main__":
    for tag in sys.argv[1:] or ("female_tennis", "female_golfkit", "female_bowlingkit"):
        parts, new = fitted(tag); t0 = parts['Kit_Top']['pos']; t1 = new['Kit_Top']['pos']
        g0 = hm.gap(parts['Body'], parts['Kit_Top']); g1 = hm.gap(new['Body'], new['Kit_Top']); mv = np.linalg.norm(t1 - t0, axis=1) * 100
        print(f"== {tag}: body moved {np.linalg.norm(new['Body']['pos'] - parts['Body']['pos'], axis=1).max()*1000:.2f} mm; top moved median {np.median(mv):.2f}, largest {mv.max():.2f} cm; widest |x| {np.abs(t0[:,0]).max()*100:.1f} -> {np.abs(t1[:,0]).max()*100:.1f} cm")
        y = t0[:, 1]
        for y0 in (1.30, 1.25, 1.20, 1.15, 1.10, 1.05, 1.00):
            s = (y >= y0) & (y < y0 + .05)
            if s.sum() > 20: print(f"    y {y0:.2f}: cloth to skin median {np.median(g0[s]):4.1f} -> {np.median(g1[s]):4.1f}, 95% {np.percentile(g0[s],95):4.1f} -> {np.percentile(g1[s],95):4.1f}; width {np.ptp(t0[s][:,0])*100:5.1f} -> {np.ptp(t1[s][:,0])*100:5.1f}; under skin {int((g0[s]<0).sum())} -> {int((g1[s]<0).sum())}")
