"""Assemble the rebuilt forefeet into the full Body_M arrays (freed vertex slots reused, extras appended)."""
import sys, pickle, json
import numpy as np
from ff_common import *
from ff_cut import extract_cut
from ff_build import *
from ff_slopes import slopes_fn as default_slopes_fn
from ff_loop import straighten_loop


def assemble(V, F, P=None, f_cut=-0.0804, sides=(+1, -1), slopes_fn=None, verbose=True):
    P = P or DEFAULT
    n0 = len(V)
    Fl = [tuple(f) for f in F]
    cuts = {}; builds = {}
    n_next = n0
    removed_all = np.zeros(len(Fl), bool)
    for side in sides:
        frame = foot_frame(side)
        c = extract_cut(V, F, side, f_cut, frame)
        if P.get('straighten', 0.15) is not None:
            V, st = straighten_loop(V, F, c, side, frame, kappa=P.get('straighten', 0.15), beta=P.get('respace', 0.0))
            c['Lc'] = to_local(V, side, frame)
            if verbose: print('   loop straightened:', st)
        ring = c['ring']
        Lloop = c['Lc'][ring]
        slopes = slopes_fn(V, F, c, side, frame, P) if slopes_fn else None
        B, diag = build_forefoot(P, ring, Lloop, n_next, slopes=slopes)
        n_next += len(B.pos)
        cuts[side] = c; builds[side] = (B, diag)
        removed_all |= c['removed']
        if verbose:
            print(f'side {side:+d}: loop {len(ring)} -> N={diag["N"]} columns, new verts {len(B.pos)}, new faces {len(B.faces)}, freed slots {int(c["free"].sum())}, removed faces {int(c["removed"].sum())}')
    kept_idx = np.where(~removed_all)[0]
    kept_faces = [Fl[i] for i in kept_idx]
    # --- vertex id mapping
    Vnew = V.copy().astype(np.float64)
    extra = []
    idmap = {}
    for side in sides:
        B, diag = builds[side]; c = cuts[side]
        free = list(np.where(c['free'])[0])
        k = 0
        for j in range(len(B.pos)):
            gid = B.N0 + j
            if k < len(free):
                idmap[gid] = int(free[k]); k += 1
            else:
                idmap[gid] = n0 + len(extra); extra.append(None)
        assert k == len(free), f'side {side}: {len(free) - k} freed slots left over; the new foot needs more vertices than it frees'
        # positions (world)
        L = np.array(B.pos)
        W = to_world(L, side, c['frame'])
        for j in range(len(B.pos)):
            m = idmap[B.N0 + j]
            if m < n0: Vnew[m] = W[j]
            else: extra[m - n0] = W[j]
    Vfull = np.vstack([Vnew, np.array(extra)]) if extra else Vnew
    # --- faces
    new_faces = []
    for side in sides:
        B, diag = builds[side]
        for f in B.faces:
            new_faces.append(tuple(idmap.get(int(v), int(v)) if int(v) >= n0 else int(v) for v in f))
    oriented, vis = orient_consistently(new_faces, kept_faces)
    allf = kept_faces + oriented
    tags = {}
    for side in sides:
        B, diag = builds[side]
        for j, tg in enumerate(B.tag): tags[idmap[B.N0 + j]] = (side, tg)
    meta = dict(tags=tags, n_orig=n0, n_final=len(Vfull), n_kept_faces=len(kept_faces), n_new_faces=len(oriented), kept_idx=kept_idx,
                freed={s: np.where(cuts[s]['free'])[0] for s in sides}, idmap=idmap, unvisited=int(len(vis) - sum(vis)))
    return Vfull, allf, meta, cuts, builds


if __name__ == '__main__':
    V, F = load_base()
    Vf, Ff, meta, cuts, builds = assemble(V, F, slopes_fn=default_slopes_fn)
    ne, nb, nm, bad = check_manifold(Ff)
    ne0, nb0, nm0, bad0 = check_manifold([tuple(f) for f in F])
    print('final verts', len(Vf), 'faces', len(Ff), '| edges', ne, 'boundary', nb, 'nonmanifold', nm, 'same-direction pairs', bad)
    print('base          verts', len(V), 'faces', len(F), '| edges', ne0, 'boundary', nb0, 'nonmanifold', nm0, 'same-direction pairs', bad0)
    print('unvisited (orientation not reached):', meta['unvisited'])
    np.save(W + '/data/V_ff0.npy', Vf)
    pickle.dump(dict(faces=Ff, kept_idx=meta['kept_idx'], n_orig=meta['n_orig']), open(W + '/data/F_ff0.pkl', 'wb'))
