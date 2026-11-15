"""widths.py: what the eye sees. Width of the arm seen from the front (across) and from the side (front to back), per station,
for each mesh; plus the shoulder cap. cm. Used to compare with the tier 1 target's silhouette (target_widths in this file)."""
import sys, numpy as np, armio, armfield as af

def profile(pos, w, B, side='Left'):
    S, E, W = B[side + "UpperArm"], B[side + "LowerArm"], B[side + "Hand"]
    o = 0 if side == 'Left' else 4
    out = {}
    for name, a, b in (("upper", S, E), ("fore", E, W)):
        ax, f, up = armio.frame(a, b); L = np.linalg.norm(b - a)
        d = pos - a; t = d @ ax; r = d - np.outer(t, ax); rho = np.linalg.norm(r, axis=1); u = t / L
        sel = (w[:, o + 1] + w[:, o + 2] + w[:, o + 3] + w[:, o + 0] > .5) & (rho < .14)
        for k in range(-2, 10):
            s = sel & (u >= k / 10) & (u < (k + 1) / 10)
            if s.sum() < 12: continue
            x, y = r[s] @ up, r[s] @ f
            out[(name, round(k / 10 + .05, 2))] = ((x.max() - x.min()) * 100, (y.max() - y.min()) * 100, x.max() * 100)
    return out, np.linalg.norm(E - S) * 100, np.linalg.norm(W - E) * 100

if __name__ == "__main__":
    torso = armio.read("export/male_torso/Body.bin"); base = armio.read("export/male_build0/Body.bin"); cur = armio.read("export/male_build1/Body.bin"); B = armio.bones("export/male_torso/bones.json")
    T = af.field_tables(torso, B, 'Left'); new = af.apply(torso['pos'], B, T, 'Left')
    H = base['pos'][:, 1].max() - base['pos'][:, 1].min()
    print(f"height {H*100:.1f} cm; shoulder joints {abs(B['LeftUpperArm'][0]-B['RightUpperArm'][0])*100:.1f} cm apart; head width {np.ptp(base['pos'][base['pos'][:,1] > base['pos'][:,1].max()-0.12][:,0])*100:.1f} cm")
    pb, lu, lf = profile(base['pos'], torso['w'], B); pc, _, _ = profile(cur['pos'], torso['w'], B); pn, _, _ = profile(new, torso['w'], B)
    print(f"upper arm {lu:.1f} cm, forearm {lf:.1f} cm")
    print("station       across (seen from the front)        deep (seen from the side)        outer reach from the bone")
    print("              base   build  muscles               base   build  muscles            base  build  muscles")
    for k in sorted(pn, key=lambda k: (k[0] != 'upper', k[1])):
        if k in pb and k in pc:
            print(f"  {k[0]:5} {k[1]:5.2f}  {pb[k][0]:5.1f}  {pc[k][0]:5.1f}  {pn[k][0]:5.1f}                {pb[k][1]:5.1f}  {pc[k][1]:5.1f}  {pn[k][1]:5.1f}             {pb[k][2]:5.1f} {pc[k][2]:5.1f} {pn[k][2]:5.1f}")
