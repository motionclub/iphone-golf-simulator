"""Build stable shell/outer-surface correspondence from Clothing V2 metadata.
Usage: python build_skirt_profile.py Kit_Bottom_final.npz SkirtCloth.json
"""
import json
import sys
from pathlib import Path
import numpy as np

mesh = np.load(sys.argv[1])
p = mesh['pos'].astype('<f4')
shell = np.unique(mesh['tri'][mesh['kind'] == 11])
outer = np.unique(mesh['tri'][(mesh['kind'] == 11) & (mesh['part'] == 0)])
_, first = np.unique(np.round(p[outer], 5), axis=0, return_index=True)
controls = outer[first]
points = p[controls]
guide = []
for chunk in np.array_split(shell, max(1, len(shell) // 256)):
    distances = ((p[chunk, None] - points[None]) ** 2).sum(2)
    guide.extend(distances.argmin(1).tolist())
lookup = {tuple(np.round(p[v], 5)): i for i, v in enumerate(controls)}
triangles = np.array([[lookup[tuple(np.round(p[v], 5))] for v in t] for t in mesh['tri'][(mesh['kind'] == 11) & (mesh['part'] == 0)]])
neighbors = [set() for _ in controls]
faces = [[] for _ in controls]
for face, tri in enumerate(triangles):
    for i, v in enumerate(tri):
        neighbors[v].update([int(tri[(i+1)%3]), int(tri[(i+2)%3])])
        faces[v].append(face)
def pack(rows):
    flat, offsets = [], [0]
    for row in rows:
        flat.extend(sorted(row)); offsets.append(len(flat))
    return flat, offsets
neighbor_values, neighbor_offsets = pack(neighbors)
face_values, face_offsets = pack(faces)
position_hash = 2166136261
for value in p.tobytes():
    position_hash = ((position_hash ^ value) * 16777619) & 0xffffffff
profile = dict(vertexCount=len(p), positionHash=position_hash,
               band=np.unique(mesh['tri'][mesh['kind']==12]).tolist(), shell=shell.tolist(), controls=controls.tolist(), guide=guide, triangles=triangles.reshape(-1).tolist(), neighbors=neighbor_values, neighborOffsets=neighbor_offsets, faces=face_values, faceOffsets=face_offsets)
Path(sys.argv[2]).write_text(json.dumps(profile, separators=(',', ':')))
print(f'{len(shell)} shell vertices, {len(controls)} outer guides')
