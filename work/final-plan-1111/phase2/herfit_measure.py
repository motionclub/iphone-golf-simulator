"""herfit_measure.py: how her clothes sit on her, per kit: cloth to skin along the skin's normal (cm), by height band, for the top
and the bottom, in the rest pose; plus her own outline (width, depth) and each garment's at the same heights."""
import sys, os, numpy as np, armio
def gap(body, cloth):
    P, N = body['pos'], body['nrm']; Q = cloth['pos']; out = np.empty(len(Q)); idx = np.empty(len(Q), int)
    for i in range(0, len(Q), 300):
        d = ((Q[i:i + 300, None, :] - P[None]) ** 2).sum(2); j = d.argmin(1); out[i:i + 300] = ((Q[i:i + 300] - P[j]) * N[j]).sum(1); idx[i:i + 300] = j
    return out * 100
if __name__ == "__main__":
    for tag in ("female_tennis", "female_golfkit", "female_bowlingkit"):
        parts = {n[:-4]: armio.read(f"export/{tag}/{n}") for n in sorted(os.listdir(f"export/{tag}")) if n.endswith(".bin")}
        B = armio.bones(f"export/{tag}/bones.json"); b = parts['Body']
        print(f"== {tag}: height {np.ptp(b['pos'][:,1])*100:.0f} cm; shoulder joints at y {B['LeftUpperArm'][1]:.2f}, x {abs(B['LeftUpperArm'][0])*100:.1f}; elbow y {B['LeftLowerArm'][1]:.2f}; hips y {B['Hips'][1]:.2f}; knee y {B['LeftLowerLeg'][1]:.2f}; parts {[ (n, len(p['pos'])) for n, p in parts.items()]}")
        for name in ("Kit_Top", "Kit_Bottom"):
            c = parts[name]; g = gap(b, c); y = c['pos'][:, 1]; x = np.abs(c['pos'][:, 0])
            print(f"  {name}: y {y.min():.2f}..{y.max():.2f}, widest |x| {x.max()*100:.1f} cm")
            for y0 in np.arange(np.floor(y.max() * 20) / 20, y.min() - .001, -0.05):
                s = (y >= y0) & (y < y0 + .05)
                if s.sum() < 20: continue
                bb = b['pos'][(b['pos'][:, 1] >= y0) & (b['pos'][:, 1] < y0 + .05)]
                print(f"    y {y0:4.2f}..{y0+.05:4.2f}: cloth to skin 5% {np.percentile(g[s],5):5.1f}  median {np.median(g[s]):5.1f}  95% {np.percentile(g[s],95):5.1f}   garment width {np.ptp(c['pos'][s][:,0])*100:5.1f} depth {np.ptp(c['pos'][s][:,2])*100:5.1f}   body width {np.ptp(bb[:,0])*100:5.1f} depth {np.ptp(bb[:,2])*100:5.1f}   under skin {int((g[s]<0).sum())}")
