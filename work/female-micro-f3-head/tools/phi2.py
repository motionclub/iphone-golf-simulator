"""Phi variants for the MicroF2 lower face. Imports the F1 analytic head (geo/loftf) and lets us swap the chin construction.
make_head(front_base=None, prof=None, prm=None) ; sagittal(H, th) ; plate_profile() ; eval on the staged patch directions U."""
import sys, json, copy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, geo, loftf, fl, meshlib as ml

FRONT_BASE0 = list(loftf.FRONT_BASE)
PROF0 = json.load(open(fl.W / 'data/prof_corr.json'))
C = geo.C


def make_head(front_base=None, prof='orig', prm=None, hook=None):
    loftf.FRONT_BASE = list(front_base) if front_base is not None else list(FRONT_BASE0)
    H = geo.Head(prm)
    if prof != 'orig': H.prof_corr = prof
    if hook: hook(H)
    loftf.FRONT_BASE = list(FRONT_BASE0)
    return H


def sagittal(H, th=None, x=0.0):
    """Phi along the ray fan in the sagittal plane x=0 (through C): returns (y,z) mm polyline"""
    th = np.radians(np.linspace(20, 178, 800)) if th is None else th
    u = np.stack([np.zeros_like(th) + 1e-9, -np.sin(th), np.cos(th)], 1)
    u /= np.linalg.norm(u, axis=1, keepdims=True)
    P = H.phi(u)
    return np.stack([P[:, 1] * 1000, P[:, 2] * 1000], 1)


def plate_profile():
    sil = json.load(open(fl.W / 'data/sil.json'))
    rows = [r for r in range(66, 253) if str(r) in sil['left'] and sil['left'][str(r)] and sil['right'].get(str(r))]
    pl = np.array([(fl.ycolL(sil['left'][str(r)][0]) * 1000, fl.zrow(r) * 1000) for r in rows])
    pr = np.array([(fl.ycolR(sil['right'][str(r)][1] + 1) * 1000, fl.zrow(r) * 1000) for r in rows])
    return pl, pr


def plate_underline():
    """under-chin line of the plate profile: for columns (y) between chin and neck, the lowest foreground row above the collar. returns (y mm, z mm)"""
    from PIL import Image
    src = np.asarray(Image.open(fl.PLATES / 'female_head_detail.jpg').convert('RGB')).astype(float)
    return src
