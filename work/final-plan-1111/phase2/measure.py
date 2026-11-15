import sys, numpy as np, armio
for tag in sys.argv[1:]:
    m = armio.read(f"export/{tag}/Body.bin"); B = armio.bones(f"export/{tag}/bones.json")
    S, E, W = B["LeftUpperArm"], B["LeftLowerArm"], B["LeftHand"]
    print(f"== {tag}: S {np.round(S,3)} E {np.round(E,3)} W {np.round(W,3)}  upper {np.linalg.norm(E-S)*100:.1f} cm  fore {np.linalg.norm(W-E)*100:.1f} cm")
    armw = m['w'][:, 1] + m['w'][:, 2] + m['w'][:, 0] * 0
    for name, a, b, col in (("upper", S, E, 1), ("fore", E, W, 2)):
        u, rho, phi, L = armio.coords(m['pos'], a, b)
        sel = (m['w'][:, 1] + m['w'][:, 2] + m['w'][:, 3] > .5) & (rho < .12)
        print(f" {name}: u | mean radius cm | front/back half-width | up/down half-height | ratio | girth cm")
        for k in range(10):
            s = sel & (u >= k / 10) & (u < (k + 1) / 10)
            if s.sum() < 12: continue
            r, ph = rho[s], phi[s]
            def half(c): 
                q = np.abs(np.cos(ph - c)) > .9
                return r[q].mean() if q.sum() else float('nan')
            fb = (half(0) + half(np.pi)) / 2; ud = (half(np.pi / 2) + half(-np.pi / 2)) / 2
            print(f"   {k/10:.1f}  {r.mean()*100:5.2f}   {fb*100:5.2f}   {ud*100:5.2f}   {fb/ud:4.2f}   {2*np.pi*r.mean()*100:5.1f}")
