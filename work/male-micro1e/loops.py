"""Quad-mesh edge-loop utilities (numpy). Needs sculpt_core.FACES loaded (use cache file faces.npy)."""
import numpy as np
from collections import defaultdict

def build(faces, nv):
    edge_faces = defaultdict(list)
    for fi, f in enumerate(faces):
        for k in range(4):
            a, b = int(f[k]), int(f[(k+1) % 4])
            edge_faces[(min(a,b), max(a,b))].append(fi)
    vert_edges = defaultdict(list)
    for (a, b) in edge_faces:
        vert_edges[a].append(b); vert_edges[b].append(a)
    return edge_faces, vert_edges

def next_in_loop(prev, cur, faces, edge_faces, vert_edges):
    """edge loop continuation: at valence-4 vertex cur, go to the neighbour opposite to prev (not sharing a face with prev-cur edge)."""
    nb = vert_edges[cur]
    if len(nb) != 4:
        return None
    e = (min(prev, cur), max(prev, cur))
    sharing = set()
    for fi in edge_faces[e]:
        for v in faces[fi]:
            sharing.add(int(v))
    cand = [v for v in nb if v != prev and v not in sharing]
    if len(cand) == 1:
        return cand[0]
    return None

def walk_loop(a, b, faces, edge_faces, vert_edges, maxlen=400):
    loop = [a, b]
    prev, cur = a, b
    for _ in range(maxlen):
        nxt = next_in_loop(prev, cur, faces, edge_faces, vert_edges)
        if nxt is None:
            return loop, False
        if nxt == loop[0]:
            return loop, True
        loop.append(nxt); prev, cur = cur, nxt
    return loop, False
