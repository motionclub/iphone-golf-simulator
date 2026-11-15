"""tune.py key=value ...: the muscle model with overrides, as the eye sees it (front and side widths, cm) against the tier 1
target's silhouette and the base body."""
import sys, numpy as np, armio, armfield as af, widths
P = dict(af.P)
for a in sys.argv[1:]:
    k, v = a.split("="); P[k] = float(v)
torso = armio.read("export/male_torso/Body.bin"); base = armio.read("export/male_build0/Body.bin"); B = armio.bones("export/male_torso/bones.json")
_sk = armio.read_skin("export/male_skin/Body.skin"); torso['armLeft'] = armio.membership(_sk, _sk, "Left")
T = af.field_tables(torso, B, 'Left', P); new = af.apply(torso['pos'], B, T, 'Left')
pb, lu, lf = widths.profile(base['pos'], torso['w'], B); pn, _, _ = widths.profile(new, torso['w'], B)
# the target's forearm, read off the turnaround (front and back view = across, side view = deep), 3.27 px per cm
TGT = {("fore", .15): (11.6, 11.6), ("fore", .25): (11.6, 11.3), ("fore", .35): (11.6, 11.3), ("fore", .45): (11.3, 11.3), ("fore", .55): (10.4, 10.4),
       ("fore", .65): (9.5, 9.8), ("fore", .75): (8.3, 9.2), ("fore", .85): (7.6, 8.3), ("fore", .95): (7.0, 8.0), ("fore", .05): (11.3, 10.4), ("upper", .75): (11.3, 12.8)}
print("station        across: base  new  target      deep: base  new  target     outer reach: base new")
for k in sorted(pn, key=lambda k: (k[0] != 'upper', k[1])):
    if k not in pb: continue
    t = TGT.get(k, (float('nan'),) * 2)
    print(f"  {k[0]:5} {k[1]:5.2f}        {pb[k][0]:5.1f} {pn[k][0]:5.1f} {t[0]:5.1f}             {pb[k][1]:5.1f} {pn[k][1]:5.1f} {t[1]:5.1f}             {pb[k][2]:5.1f} {pn[k][2]:5.1f}")
g = {(n, round(u, 2)): gg for n, u, gg, fb, ac in af.girths(new, torso['w'], B)}
up = max(v for (n, u), v in g.items() if n == 'upper' and .4 <= u <= .7); fo = max(v for (n, u), v in g.items() if n == 'fore' and .1 <= u <= .5)
el = min([v for (n, u), v in g.items() if n == 'upper' and u >= .85] + [v for (n, u), v in g.items() if n == 'fore' and u <= .06]); wr = min(v for (n, u), v in g.items() if n == 'fore' and u >= .8)
reach = max(pn[k][2] for k in pn if k[0] == 'upper' and k[1] <= .45)
S = abs(B['LeftUpperArm'][0] - B['RightUpperArm'][0]) * 100
print(f"girth: upper arm {up*100:.1f}  elbow {el*100:.1f}  forearm {fo*100:.1f}  wrist {wr*100:.1f} cm   upper/forearm {up/fo:.2f}")
print(f"shoulder: outer reach {reach:.1f} cm -> about {S + 2*reach:.1f} cm across with the arms down (target 58-59)")
mv = np.linalg.norm(new - torso['pos'], axis=1); print(f"largest move {mv.max()*1000:.1f} mm")
