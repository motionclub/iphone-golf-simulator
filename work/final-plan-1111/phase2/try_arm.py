import sys, numpy as np, armio, armfield as af
body = armio.read("export/male_torso/Body.bin"); cur = armio.read("export/male_build1/Body.bin"); B = armio.bones("export/male_build0/bones.json")
T = af.field_tables(body, B, 'Left')
new = af.apply(body['pos'], B, T, 'Left')
mv = np.linalg.norm(new - body['pos'], axis=1)
print(f"moved {int((mv > 1e-4).sum())} of {len(mv)} vertices, largest {mv.max()*1000:.1f} mm; field range {T['du'].min()*1000:.1f}..{T['du'].max()*1000:.1f} mm upper, {T['df'].min()*1000:.1f}..{T['df'].max()*1000:.1f} mm fore")
print("station        base girth | 11-11 build | muscles      front-back/across: base, build, muscles")
rb, rc, rn = af.girths(body['pos'], body['w'], B), af.girths(cur['pos'], cur['w'], B), af.girths(new, body['w'], B)
for (n, u, g0, f0, a0), (_, _, g1, f1, a1), (_, _, g2, f2, a2) in zip(rb, rc, rn):
    print(f"  {n:5} {u:.2f}   {g0*100:5.1f} cm   {g1*100:5.1f} cm   {g2*100:5.1f} cm        {f0/a0:4.2f}  {f1/a1:4.2f}  {f2/a2:4.2f}")
