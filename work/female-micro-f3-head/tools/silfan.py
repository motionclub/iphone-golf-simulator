"""dense ray-fan evaluation of Phi -> silhouette half-width per height (front view) + where (y) the widest point lies"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, geo, fl

def fan(H, az_max=125.0, naz=300, th0=75.0, th1=150.0, nth=240):
    az = np.radians(np.linspace(0, az_max, naz)); th = np.radians(np.linspace(th0, th1, nth))
    A, T = np.meshgrid(az, th)
    u = np.stack([np.sin(T) * np.sin(A), -np.sin(T) * np.cos(A), np.cos(T)], -1).reshape(-1, 3)   # az=0 -> -y (front), az=90 -> +x
    P = H.phi(u)
    return P

def hw_by_z(P, zs, tol=0.0008):
    out = []; ys = []
    for z in zs:
        m = (np.abs(P[:, 2] - z) < tol) & (P[:, 1] < 0.05) & (P[:, 0] > 0)
        if m.sum() < 3: out.append(np.nan); ys.append(np.nan); continue
        i = np.argmax(P[m, 0]); out.append(P[m, 0][i]); ys.append(P[m, 1][i])
    return np.array(out), np.array(ys)
