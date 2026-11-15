import numpy as np, armio, armfield as af
body = armio.read("export/male_build0/Body.bin"); B = armio.bones("export/male_build0/bones.json")
T = af.field_tables(body, B, 'Left'); uu, uf, ph = af.grids()
angs = [0, 45, 90, 135, 180, -135, -90, -45]
def row(t, ug, u): return " ".join(f"{af.lookup(t, ug, np.array([u]), np.array([a * af.DEG]))[0]*100:5.1f}" for a in angs)
print("radius cm at phi =   front   45  outer  135   back -135  inner  -45      (base | muscles)")
for name, bt, tt, ug, us in (("upper", T['bu'], T['tu'], uu, [-.5, -.4, -.3, -.2, -.1, 0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.0, 1.1]), ("fore", T['bf'], T['tf'], uf, [-.1, 0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.0])):
    for u in us: print(f" {name} u={u:5.2f}   {row(bt, ug, u)}   |   {row(tt, ug, u)}")
