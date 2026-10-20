"""Garment outer-shell construction from the (union) body SDF: ease field -> blur -> clearance union -> surface nets -> clip."""
import time
import numpy as np
from kitlib import *
from sdf import *
from fitbody import *
from kit_common import enforce_clearance, resolve_overlaps, enforce_clearance_zone


class Shell:
    """Result container: mesh (V, F), the smooth field + grid for analytic normals/clearance, and the cut function."""
    pass


def build_shell(bodies, gender, tag, lo, hi, h, ease_fn, blur_mm=15.0, min_clear=0.0025, cut_fn=None, band=0.09,
                taubin_iters=4, extra_field=None, verbose=True, mask_fn=None, enforce=None, fit=False, despike_thresh=0.006, obstacles=None):
    """ease_fn(X,Y,Z) -> ease array (broadcastable) in metres; cut_fn(V)-> c (positive = removed); extra_field(g,S,X,Y,Z)->F to union."""
    t0 = time.time()
    g, S = cached_sdf(gender, bodies, lo, hi, h, tag, band=band, mask_fn=mask_fn, fit=fit)
    X, Y, Z = g.coords()
    ease = ease_fn(X, Y, Z)
    Sg = gauss3(S - ease, blur_mm * 1e-3 / h)
    mc = min_clear(X, Y, Z) if callable(min_clear) else min_clear
    Sg = np.minimum(Sg, S - mc)
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
        V2, F2 = clean_sheet(V2, F2)
    else:
        V2, F2 = Vq, T
    # alternate clearance enforcement and cusp removal: enforcing alone yanks crease vertices out into knife-edge fins (armpit, groin)
    for rnd in range(4):
        nfl = 0
        if despike_thresh:
            V2, nfl = despike(V2, F2, despike_thresh)
            if verbose and nfl:
                print(f'  shell[{tag}] round {rnd}: despike smoothed up to {nfl} cusp vertices')
        if enforce is not None:
            trees, cmin = enforce[:2]
            V2 = enforce_clearance(V2, F2, trees, cmin, iters=8, verbose=verbose and rnd == 0)
        for ob in (obstacles or []):                                  # closed obstacles built earlier (the waistband): stay >= cmin outside them, pushed horizontally
            otree, ocmin, ozlo, ozhi = ob[:4]
            V2 = enforce_clearance_zone(V2, F2, otree, ocmin, ozlo, ozhi, axis=(ob[4] if len(ob) > 4 else None))
        if not nfl:
            break
    if enforce is not None and len(enforce) > 2 and enforce[2]:
        V2 = resolve_overlaps(V2, F2, enforce[2], verbose=verbose)
        if despike_thresh:
            V2, nfl = despike(V2, F2, despike_thresh)
    if cut_fn is not None:
        V2, F2 = clean_sheet(V2, F2, tol=6e-4)           # the clearance projection can drop two vertices on top of each other: merge those slivers
        V2, F2, nsplit = split_nonmanifold(V2, F2)       # two sheets of the iso-surface touching along an edge (toe gaps): give each sheet its own vertices
        if verbose and nsplit:
            print(f'  shell[{tag}] split {nsplit} non-manifold vertices')
    sh.V, sh.F = V2, F2
    if verbose:
        print(f'  shell[{tag}] clipped tris {len(F2)} loops {[len(l) for l in boundary_loops(F2)]}  ({time.time()-t0:.1f}s)')
    return sh
