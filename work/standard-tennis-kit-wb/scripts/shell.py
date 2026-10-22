"""Garment outer-shell construction from the (union) body SDF: ease field -> blur -> clearance union -> surface nets -> clip."""
import time
import numpy as np
from kitlib import *
from sdf import *
from fitbody import *
from kit_common import enforce_clearance, resolve_overlaps


class Shell:
    """Result container: mesh (V, F), the smooth field + grid for analytic normals/clearance, and the cut function."""
    pass


def build_shell(bodies, gender, tag, lo, hi, h, ease_fn, blur_mm=15.0, min_clear=0.0025, cut_fn=None, band=0.09,
                taubin_iters=4, extra_field=None, verbose=True, mask_fn=None, enforce=None, fit=False):
    """ease_fn(X,Y,Z) -> ease array (broadcastable) in metres; cut_fn(V)-> c (positive = removed); extra_field(g,S,X,Y,Z)->F to union."""
    t0 = time.time()
    g, S = cached_sdf(gender, bodies, lo, hi, h, tag, band=band, mask_fn=mask_fn, fit=fit)
    X, Y, Z = g.coords()
    ease = ease_fn(X, Y, Z)
    Sg = gauss3(S - ease, blur_mm * 1e-3 / h)
    Sg = np.minimum(Sg, S - min_clear)
    if extra_field is not None:
        Sg = np.minimum(Sg, extra_field(g, S, X, Y, Z))
    Vq, Q = surface_nets(Sg, g)
    T = quads_to_tris(Vq, Q)
    if taubin_iters:
        Vq = taubin(Vq, T, taubin_iters)
    if verbose:
        print(f'  shell[{tag}] raw tris {len(T)}  ({time.time()-t0:.1f}s)')
    sh = Shell()
    sh.g, sh.S, sh.Sg = g, S, Sg
    sh.Vraw, sh.Traw = Vq, T
    if cut_fn is not None:
        c = cut_fn(Vq)
        V2, F2, _, _ = clip_mesh(Vq, T, c)
        V2, F2 = keep_largest(V2, F2)
    else:
        V2, F2 = Vq, T
    if enforce is not None:
        trees, cmin = enforce[:2]
        V2 = enforce_clearance(V2, F2, trees, cmin, verbose=verbose)
        if len(enforce) > 2 and enforce[2]:
            V2 = resolve_overlaps(V2, F2, enforce[2], verbose=verbose)
    sh.V, sh.F = V2, F2
    if verbose:
        print(f'  shell[{tag}] clipped tris {len(F2)} loops {[len(l) for l in boundary_loops(F2)]}  ({time.time()-t0:.1f}s)')
    return sh
