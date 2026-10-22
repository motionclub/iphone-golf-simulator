"""Smooth implicit foot: smooth union of ellipsoids (+ ankle column) clipped by a floor plane.  Left foot coordinates (world); right = mirror x."""
import numpy as np
Z0 = 0.00247          # sole plane (min z of the start mesh)


def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def ell_sdf(P, c, r, yaw=0.0, pitch=0.0):
    """first-order ellipsoid distance (iq): axes r=(rx,ry,rz) in the local frame (yaw about z, pitch about x)"""
    q = P - c
    cy, sy = np.cos(yaw), np.sin(yaw); cp, sp = np.cos(pitch), np.sin(pitch)
    x = cy * q[:, 0] + sy * q[:, 1]; y = -sy * q[:, 0] + cy * q[:, 1]; z = q[:, 2]
    y2 = cp * y + sp * z; z2 = -sp * y + cp * z
    L = np.stack([x, y2, z2], 1) / r
    k0 = np.linalg.norm(L, axis=1) + 1e-12
    k1 = np.linalg.norm(L / r, axis=1) + 1e-12
    return k0 * (k0 - 1.0) / k1


def col_sdf(P, c, r, z0):
    """vertical elliptic column from z0 upwards (capped bottom smoothly) : c=(cx,cy) r=(rx,ry)"""
    L = np.stack([(P[:, 0] - c[0]) / r[0], (P[:, 1] - c[1]) / r[1]], 1)
    k0 = np.linalg.norm(L, axis=1) + 1e-12
    k1 = np.linalg.norm(L / np.array(r), axis=1) + 1e-12
    d = k0 * (k0 - 1.0) / k1
    return np.maximum(d, z0 - P[:, 2])


# parameter layout: each ellipsoid: cx cy cz rx ry rz yaw pitch (8) ; column: cx cy rx ry (4) ; blend k ; floor blend kf
ELL = ['heel', 'mid', 'ball', 'toe']
NP_E = 8


def unpack(p):
    E = [p[i * NP_E:(i + 1) * NP_E] for i in range(len(ELL))]
    col = p[len(ELL) * NP_E:len(ELL) * NP_E + 4]
    k, kf = p[len(ELL) * NP_E + 4], p[len(ELL) * NP_E + 5]
    return E, col, k, kf


def sdf(P, p):
    E, col, k, kf = unpack(p)
    d = None
    for e in E:
        de = ell_sdf(P, np.array(e[0:3]), np.array(e[3:6]), e[6], e[7])
        d = de if d is None else smin(d, de, k)
    dc = col_sdf(P, col[0:2], col[2:4], 0.045)
    d = smin(d, dc, k)
    # floor: smooth max with (Z0 - z)
    fl = Z0 - P[:, 2]
    h = np.maximum(kf - np.abs(d - fl), 0.0) / kf
    return np.maximum(d, fl) + h * h * kf * 0.25


def grad(P, p, eps=1e-4):
    g = np.zeros_like(P)
    for a in range(3):
        dP = np.zeros(3); dP[a] = eps
        g[:, a] = (sdf(P + dP, p) - sdf(P - dP, p)) / (2 * eps)
    return g


def project(P, p, iters=12, maxd=0.03):
    Q = P.copy()
    for _ in range(iters):
        f = sdf(Q, p); g = grad(Q, p); gn = (g * g).sum(1) + 1e-12
        step = (f / gn)[:, None] * g
        n = np.linalg.norm(step, axis=1, keepdims=True)
        step = step * np.minimum(1.0, 0.01 / np.maximum(n, 1e-12))     # <=1 cm per iteration
        Q = Q - step
    d = np.linalg.norm(Q - P, axis=1)
    over = d > maxd
    Q[over] = P[over] + (Q[over] - P[over]) * (maxd / d[over])[:, None]
    return Q
