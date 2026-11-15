"""arm_gates.py: the male arm gates of Phase 2, measured on the mesh: girth along the arm for the base body, the 11-11 build and
the muscle model; where each is thickest and thinnest; how oval the upper arm is."""
import numpy as np, armio, armfield as af
torso = armio.read("export/male_torso/Body.bin"); base = armio.read("export/male_build0/Body.bin"); cur = armio.read("export/male_build1/Body.bin"); B = armio.bones("export/male_torso/bones.json")
T = af.field_tables(torso, B, 'Left'); new = af.apply(torso['pos'], B, T, 'Left')
def table(pos): return {(n, round(u, 2)): (g, fb / ac) for n, u, g, fb, ac in af.girths(pos, torso['w'], B)}
tb, tc, tn = table(base['pos']), table(cur['pos']), table(new)
print("station       base    11-11 build   muscles   (girth cm; front-back / across in brackets)")
for k in sorted(tn, key=lambda k: (k[0] != 'upper', k[1])):
    if k in tb and k in tc: print(f"  {k[0]:5} {k[1]:.2f}   {tb[k][0]*100:5.1f} ({tb[k][1]:.2f})   {tc[k][0]*100:5.1f} ({tc[k][1]:.2f})   {tn[k][0]*100:5.1f} ({tn[k][1]:.2f})")
def summary(t, name):
    up = max(g for (n, u), (g, r) in t.items() if n == 'upper' and .4 <= u <= .7)
    el = min([g for (n, u), (g, r) in t.items() if n == 'upper' and u >= .85] + [g for (n, u), (g, r) in t.items() if n == 'fore' and u <= .06])
    fo = max(g for (n, u), (g, r) in t.items() if n == 'fore' and .1 <= u <= .5)
    wr = min(g for (n, u), (g, r) in t.items() if n == 'fore' and u >= .8)
    oval = np.mean([r for (n, u), (g, r) in t.items() if n == 'upper' and .4 <= u <= .7])
    print(f"{name:12} upper arm {up*100:4.1f}  elbow {el*100:4.1f}  forearm {fo*100:4.1f}  wrist {wr*100:4.1f} cm   upper/forearm {up/fo:.2f}   elbow/upper {el/up:.2f}   upper-arm oval {oval:.2f}")
summary(tb, "base"); summary(tc, "11-11 build"); summary(tn, "muscles")
mv = np.linalg.norm(new - torso['pos'], axis=1); print(f"moved {int((mv > 1e-4).sum())} body vertices, largest {mv.max()*1000:.1f} mm")
