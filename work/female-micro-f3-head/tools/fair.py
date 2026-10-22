"""Implicit local fairing of a vertex region: minimise the (edge-length-normalised) umbrella Laplacian energy of the region and its 1-ring
with a Tikhonov anchor to the original positions; everything outside the region (and any frozen vertices) stays fixed.
No displacement of anything outside `free`; used for the chin underside and the ear transition band."""
import numpy as np


def vertex_adj(F, n):
    adj = [set() for _ in range(n)]
    for f in F:
        m = len(f)
        for i in range(m):
            a, b = int(f[i]), int(f[(i + 1) % m]); adj[a].add(b); adj[b].add(a)
    return adj


def fair(P, adj, free, frozen=(), lam=0.05, rings=1):
    """returns the maximum displacement (m); P is modified in place"""
    free = np.array(sorted(set(int(i) for i in free) - set(int(i) for i in frozen)), np.int64)
    if len(free) == 0: return 0.0
    fi = {int(v): k for k, v in enumerate(free)}
    S = set(int(v) for v in free)
    for _ in range(rings):
        for v in list(S): S |= adj[v]
    S = sorted(S)
    nf = len(free)
    h = {}
    for v in S:
        nb = list(adj[v])
        h[v] = float(np.mean(np.linalg.norm(P[nb] - P[v], axis=1))) if nb else 1e-3
    A = np.zeros((len(S), nf)); Bk = np.zeros((len(S), 3))
    for r, v in enumerate(S):
        nb = list(adj[v]); wgt = 1.0 / h[v]
        # row: (X_v - mean(X_nb)) / h_v
        if v in fi: A[r, fi[v]] += wgt
        else: Bk[r] += wgt * P[v]
        for u in nb:
            c = -wgt / len(nb)
            if u in fi: A[r, fi[u]] += c
            else: Bk[r] += c * P[u]
    # normal equations  (A^T A + lam D) X = -A^T Bk + lam D X0   with D = diag(1/h^2)
    D = np.array([1.0 / h[int(v)] ** 2 for v in free])
    M = A.T @ A + lam * np.diag(D)
    X0 = P[free].copy()
    rhs = -A.T @ Bk + lam * D[:, None] * X0
    X = np.linalg.solve(M, rhs)
    disp = np.linalg.norm(X - X0, axis=1)
    P[free] = X
    return float(disp.max())
