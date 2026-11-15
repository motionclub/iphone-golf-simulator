"""crumple.py: where the field folds the skin. Edges of the body mesh that the muscle field shortens or stretches most, and
triangles whose normal turns most, listed by arm station (u, phi)."""
import sys, numpy as np, armio, armfield as af
P = dict(af.P)
for a in sys.argv[1:]:
    k, v = a.split("="); P[k] = float(v)
torso = armio.read("export/male_torso/Body.bin"); B = armio.bones("export/male_torso/bones.json")
_sk = armio.read_skin("export/male_skin/Body.skin"); torso['armLeft'] = armio.membership(_sk, _sk, "Left")
T = af.field_tables(torso, B, 'Left', P); old = torso['pos']; new = af.apply(old, B, T, 'Left')
tri = armio.full_tris("export/male_torso/BodyFull.tri")
def nrm(p):
    n = np.cross(p[tri[:, 1]] - p[tri[:, 0]], p[tri[:, 2]] - p[tri[:, 0]]); return n / np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
turn = np.degrees(np.arccos(np.clip((nrm(old) * nrm(new)).sum(1), -1, 1)))
c = old[tri].mean(1); mv = np.linalg.norm(new - old, axis=1)[tri].max(1)
S, E, W = B["LeftUpperArm"], B["LeftLowerArm"], B["LeftHand"]
uu, _, phu, _ = armio.coords(c, S, E); uf, _, phf, _ = armio.coords(c, E, W)
moved = mv > 1e-4
print(f"triangles moved {moved.sum()}; normal turn: median {np.median(turn[moved]):.1f}, 95% {np.percentile(turn[moved], 95):.1f}, 99% {np.percentile(turn[moved], 99):.1f}, max {turn[moved].max():.1f} deg; over 25 deg: {(turn > 25).sum()}, over 40: {(turn > 40).sum()}")
bad = np.where(turn > 25)[0]
H, xe, ye = np.histogram2d(uu[bad], np.degrees(phu[bad]), bins=[np.arange(-0.6, 1.5, .15), np.arange(-180, 181, 45)])
print("upper-arm station (rows u, cols phi from -180 in 45 deg steps): count of triangles turned > 25 deg")
for i, row in enumerate(H): 
    if row.sum(): print(f"  u {xe[i]:5.2f}..{xe[i+1]:5.2f}  " + " ".join(f"{int(x):4d}" for x in row))
H, xe, ye = np.histogram2d(uf[bad], np.degrees(phf[bad]), bins=[np.arange(-0.3, 1.2, .15), np.arange(-180, 181, 45)])
print("forearm station")
for i, row in enumerate(H):
    if row.sum(): print(f"  u {xe[i]:5.2f}..{xe[i+1]:5.2f}  " + " ".join(f"{int(x):4d}" for x in row))
