"""Right-hand analysis shared by the socket solve and the finger rig (runs inside Blender; numpy only).
Hand frame (all unit vectors, right handed): u along the fingers (wrist -> tips), v across the palm towards the THUMB, p = v x u palm normal
(out of the palm).  The hero faces -Y, so the character's right hand is on world -X."""
import collections
import numpy as np


def edges_of(me):
    E = np.empty(len(me.edges) * 2, np.int64)
    me.edges.foreach_get('vertices', E)
    return E.reshape(-1, 2)


def adjacency(n, E):
    adj = [[] for _ in range(n)]
    for a, b in E:
        adj[a].append(int(b)); adj[b].append(int(a))
    return adj


def components(idx_mask, adj):
    n = len(adj)
    seen = np.zeros(n, bool)
    comps = []
    for s in np.where(idx_mask)[0]:
        if seen[s]:
            continue
        st = [int(s)]; seen[s] = True; comp = [int(s)]
        while st:
            u = st.pop()
            for v in adj[u]:
                if idx_mask[v] and not seen[v]:
                    seen[v] = True; st.append(v); comp.append(v)
        comps.append(np.array(comp))
    comps.sort(key=lambda c: -len(c))
    return comps


def hand_region(co, adj, tag):
    """indices of the right hand (arm component below the wrist)."""
    xcut, wz = (-0.45, 0.97) if tag == 'male' else (-0.19, 0.88)
    comps = components(co[:, 0] < xcut, adj)
    arm = comps[0]
    return arm[co[arm, 2] < wz]


def pca_frame(P, refine=True):
    c = P.mean(0)
    U_, S_, Vt = np.linalg.svd(P - c, full_matrices=False)
    u, v = Vt[0].copy(), Vt[1].copy()
    if u[2] > 0:
        u = -u
    if v[1] > 0:
        v = -v
    p = np.cross(v, u)
    assert p[0] > 0, p
    return c, u, v, p


def to_hand(P, fr):
    c, u, v, p = fr
    d = P - c
    return np.stack([d @ u, d @ v, d @ p], 1)


def from_hand(Q, fr):
    c, u, v, p = fr
    return c + Q[:, 0:1] * u + Q[:, 1:2] * v + Q[:, 2:3] * p
