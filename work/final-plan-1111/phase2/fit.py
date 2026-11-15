"""fit.py: tops that hug the body (Adnan, 2026-11-12: "the polo should be hugging the arm, especially with how muscular our
frame is. this should be the case for all clothes, golf tennis bowling. should make our character look super fit and
muscular"). numpy only.

A top is refitted in the same coordinates the muscles are built in (armfield: about each arm bone; torsofield: about the
trunk's upright axis). For each of those, over its grid:
  skin     = the body after the muscle fields (base + field), and under a top also the garment worn beneath it (shorts)
  envelope = a TENT over that: stretched knit bridges the grooves between muscles and hangs from an overhang, it is not paint
  target   = envelope + a few millimetres
  shift    = target - where the garment's innermost layer is now
Every layer of the garment at that place moves by the same shift, so hems, cuffs, collars and plackets keep their thickness.
Arms and trunk share the garment by a partition (the arm's own mask; the trunk takes the rest), so nothing is moved twice."""
import numpy as np
import armio, armfield as af, torsofield as tf
from armfield import sstep

# (first version: arm 4 mm, chest 5 mm, waist 11 mm, tents 1.4 / 3.5 cm. It read as a compression shirt: every form of the
# body printed through, with fold lines where the rules met. Now: a close athletic cut, with the ease a knit polo has.)
FIT = dict(arm=0.007,                  # sleeve: clearance over the arm's envelope (m)
           chest=0.010, waist=0.014,   # trunk: over the chest and shoulders; easing toward the waist and hem
           waist_y0=1.04, waist_y1=1.19,
           arm_tent=0.020, trunk_tent=0.055, hang=0.55, flare=0.10, bridge=0.45,   # how far cloth bridges a groove; how steeply it may fall back under an overhang (dr/dy)
           neck_y0=1.31, neck_y1=1.36)                    # the collar and the top of the shoulders by the neck are left as tailored

def _min_table(vals, i, j, shape):
    t = np.full(shape, np.inf); np.minimum.at(t, (i, j), vals)
    if not np.isfinite(t).any(): return None
    for _ in range(400):
        if np.isfinite(t).all(): break
        nb = np.minimum.reduce([np.roll(t, 1, 1), np.roll(t, -1, 1), np.vstack([t[:1], t[:-1]]), np.vstack([t[1:], t[-1:]])])
        t = np.where(np.isinf(t), nb, t)
    return t

def _soft(a, n):
    """`a` smoothed n times (rows clamp, columns wrap): the SHIFT a garment takes is smoothed as a whole, so cell-to-cell steps in
    where its innermost layer was read do not come out as creases in the cloth (her golf polo, a coarse mesh, showed them)."""
    for _ in range(n):
        pad = np.vstack([a[:1], a, a[-1:]]); a = (pad[:-2] + pad[1:-1] + pad[2:]) / 3; a = (np.roll(a, 1, 1) + a + np.roll(a, -1, 1)) / 3
    return a

def _spread(a, nr, nc, op):
    t = a.copy()
    for k in range(1, nr + 1): t = op(t, op(np.vstack([a[k:], np.repeat(a[-1:], k, 0)]), np.vstack([np.repeat(a[:1], k, 0), a[:-k]])))
    t2 = t.copy()
    for k in range(1, nc + 1): t2 = op(t2, op(np.roll(t, k, 1), np.roll(t, -k, 1)))
    return t2

def _tent(a, nr, nc):
    """Never below `a`: a morphological closing (spread, then shrink back), lightly smoothed. It fills grooves and the hollow
    under an overhang up to the reach (nr rows, nc columns; columns wrap) and leaves slopes and convex forms where they are;
    a plain spread would inflate every slope by its rise over the reach."""
    t = _spread(_spread(a, nr, nc, np.maximum), nr, nc, np.minimum)
    for _ in range(2):
        pad = np.vstack([t[:1], t, t[-1:]]); t = (pad[:-2] + pad[1:-1] + pad[2:]) / 3; t = (np.roll(t, 1, 1) + t + np.roll(t, -1, 1)) / 3
    return np.maximum(t, a)

def _floor(a, nr, nc):
    """Never above `a`: the lower envelope within the reach, smoothed. The garment's innermost layer is read through this, so a
    hem or cuff that sits nearer the skin than the cloth beside it is never pushed under the skin by its neighbours' shift."""
    t = _spread(a, nr, nc, np.minimum)
    for _ in range(2):
        pad = np.vstack([t[:1], t, t[-1:]]); t = (pad[:-2] + pad[1:-1] + pad[2:]) / 3; t = (np.roll(t, 1, 1) + t + np.roll(t, -1, 1)) / 3
    return np.minimum(t, a)

# ------------------------------------------------------------------ arms
def _arm_frames(B, side):
    if side == 'Right': return B["RightUpperArm"] * [-1, 1, 1], B["RightLowerArm"] * [-1, 1, 1], B["RightHand"] * [-1, 1, 1]
    return B["LeftUpperArm"], B["LeftLowerArm"], B["LeftHand"]

def arm_weights(pos, B, T, side):
    """Per point, for the upper arm and the forearm tables: (u, phi, rho, radial direction, weight of this arm's mask there)."""
    p = pos.copy()
    if side == 'Right': p[:, 0] *= -1
    S, E, W = _arm_frames(B, side); uu, uf, ph = af.grids(); mu, mf = af.masks()
    a1 = (E - S) / np.linalg.norm(E - S); a2 = (W - E) / np.linalg.norm(W - E); bis = (a1 + a2) / np.linalg.norm(a1 + a2)
    wf = sstep(-0.02, 0.02, (p - E) @ bis); out = []
    for (a, b, ug, mask, wgt) in ((S, E, uu, mu, 1 - wf), (E, W, uf, mf, wf)):
        ax, f, up = armio.frame(a, b); L = np.linalg.norm(b - a)
        d = p - a; t = d @ ax; r = d - np.outer(t, ax); rho = np.linalg.norm(r, axis=1); phi = np.arctan2(r @ up, r @ f); u = t / L
        inside = (u >= ug[0]) & (u <= ug[-1]); dirn = r / np.maximum(rho, 1e-6)[:, None]
        if side == 'Right': dirn = dirn * [-1, 1, 1]
        top = sstep(-0.20, -0.02, u) if a is S else 1.0      # the fit starts at the shoulder joint: over the top of the shoulder toward the neck the arm's rays only graze the skin
        out.append(dict(u=u, phi=phi, rho=rho, dirn=dirn, w=af.lookup(mask, ug, u, phi) * inside * wgt * top, ug=ug))
    return out

def arm_fit_tables(T, B, side, gpos):
    """Per arm table: the garment's shift and its innermost clearance, or None where the garment does not reach."""
    out = []; W = arm_weights(gpos, B, T, side)
    for seg, (bt, dt) in zip(W, ((T['bu'], T['du']), (T['bf'], T['df']))):
        ug = seg['ug']; base = af.lookup(bt, ug, seg['u'], seg['phi']); c = seg['rho'] - base
        sel = (seg['w'] > .05) & (c > -0.012) & (c < 0.075)
        if sel.sum() < 80: out.append(None); continue
        # a SLEEVE goes round the arm. The edge of an armhole (her tank, her bowling shirt) only passes beside it, and fitting
        # that edge to the arm wrapped it outward round the shoulder.
        # (judged on the OUTER half of the arm, within 5 cm of its skin, below the shoulder joint: with the arms hanging, the
        # trunk's own cloth lies beside the inner arm and must not count)
        near = (c > -0.012) & (c < 0.05) & (seg['u'] >= ug[0]) & (seg['u'] <= ug[-1])
        cover = np.zeros((af.NU, 24), bool); cover[np.clip(np.rint((seg['u'][near] - ug[0]) / (ug[-1] - ug[0]) * (af.NU - 1)).astype(int), 0, af.NU - 1), np.floor((seg['phi'][near] + np.pi) / (2 * np.pi) * 24).astype(int) % 24] = True
        outer = np.abs(np.angle(np.exp(1j * ((np.arange(24) + .5) / 24 * 2 * np.pi - np.pi - np.pi / 2)))) < np.radians(100)
        rows = cover[(ug > 0.12) & (ug < 1.0)][:, outer]
        if rows.mean(1).max() < 0.6: out.append(None); continue   # (her golf sleeve, a coarse mesh, reaches 0.79; an armhole edge 0.07)
        i = np.rint((seg['u'][sel] - ug[0]) / (ug[-1] - ug[0]) * (af.NU - 1)).astype(int); j = np.rint((seg['phi'][sel] + np.pi) / (2 * np.pi) * af.NPHI).astype(int) % af.NPHI
        cin = _floor(_min_table(c[sel], np.clip(i, 0, af.NU - 1), j, (af.NU, af.NPHI)), 3, 3)
        L = 0.24; du = (ug[-1] - ug[0]) * L / (af.NU - 1); dp = 2 * np.pi * 0.06 / af.NPHI
        env = _tent(bt + dt, max(1, round(FIT['arm_tent'] / du)), max(1, round(FIT['arm_tent'] / dp)))
        for _ in range(2):
            pad = np.vstack([env[:1], env, env[-1:]]); env = (pad[:-2] + pad[1:-1] + pad[2:]) / 3; env = (np.roll(env, 1, 1) + env + np.roll(env, -1, 1)) / 3
        env = np.maximum(env, bt + dt)
        out.append(dict(shift=_soft(env + FIT['arm'] - (bt + cin), 4), cin=cin, base=bt))
    return out

# ------------------------------------------------------------------ trunk
def trunk_fit_table(TT, gpos, free, under=()):
    yg, tg = tf.grids(); x, y, z = gpos[:, 0], gpos[:, 1], gpos[:, 2] - tf.ZC
    rho = np.hypot(x, z); th = np.arctan2(x, z); c = rho - tf.lookup(TT['base'], y, th)
    sel = (free > .5) & (y > tf.Y0) & (y < tf.Y1) & (c > -0.012) & (c < 0.10)
    if sel.sum() < 80: return None
    iy = np.rint((y[sel] - tf.Y0) / (tf.Y1 - tf.Y0) * (tf.NY - 1)).astype(int); it = np.rint((th[sel] + np.pi) / (2 * np.pi) * tf.NT).astype(int) % tf.NT
    cin = _floor(_min_table(c[sel], iy, it, (tf.NY, tf.NT)), 3, 2)
    have = np.zeros((tf.NY, tf.NT), bool); have[iy, it] = True; tucked_below = -1.0
    dy = (tf.Y1 - tf.Y0) / (tf.NY - 1); dt = 2 * np.pi * 0.18 / tf.NT
    ease = FIT['chest'] + (FIT['waist'] - FIT['chest']) * (1 - sstep(FIT['waist_y0'], FIT['waist_y1'], yg))[:, None]
    skin = TT['base'] + TT['d'] + ease                    # what the cloth must clear: the body with its ease ...
    if 'zone' in TT: skin = skin + TT['zone'] * np.maximum(TT['mid'] - TT['base'], 0)
    for q in under:                                       # ... and what is worn beneath (the top stays just outside its outer face)
        xq, yq, zq = q[:, 0], q[:, 1], q[:, 2] - tf.ZC; ok = (yq > tf.Y0) & (yq < tf.Y1)
        o = np.full((tf.NY, tf.NT), -np.inf)
        np.maximum.at(o, (np.rint((yq[ok] - tf.Y0) / (tf.Y1 - tf.Y0) * (tf.NY - 1)).astype(int), np.rint((np.arctan2(xq, zq)[ok] + np.pi) / (2 * np.pi) * tf.NT).astype(int) % tf.NT), np.hypot(xq, zq)[ok])
        for _ in range(2): o = np.maximum.reduce([o, np.roll(o, 1, 1), np.roll(o, -1, 1), np.vstack([o[:1], o[:-1]]), np.vstack([o[1:], o[-1:]])])
        # Where a top and what is worn beneath it share a height (a tucked golf polo, a tank meeting a skirt's waistband, a
        # shirt hanging over trousers) the top stays as tailored and the fit takes over a little above: pushing the top clear of
        # the waistband widened her hems by 4 cm (2026-11-12).
        if np.isfinite(o).any() and yq[ok].max() > y[sel].min(): tucked_below = max(tucked_below, float(yq[ok].max()))
    env = _tent(skin, max(1, round(FIT['trunk_tent'] / dy)), max(1, round(FIT['trunk_tent'] / dt)))
    for i in range(tf.NY - 2, -1, -1): env[i] = np.maximum(env[i], env[i + 1] - FIT['hang'] * dy)       # cloth hangs from the chest
    # The hem stays where it was tailored, and from it the cloth runs up in a nearly straight line until it meets the body:
    # a shirt pulled in at the waist and let out again over the hips reads as a peplum, not as a fitted shirt.
    hem = int(np.clip(np.ceil((y[sel].min() - tf.Y0) / dy) + 1, 0, tf.NY - 1)); line = TT['base'][hem] + cin[hem]
    for i in range(hem, tf.NY): env[i] = np.maximum(env[i], line - FIT['flare'] * dy * (i - hem))
    env[:hem] = np.maximum(env[:hem], (TT['base'] + cin)[:hem])
    # The collar stays where it was tailored too, and below it the cloth comes in to the chest along a straight bridge (the
    # body's upper chest falls away from the collar; pulling the cloth onto it left a ridge under the collar).
    nk = int(np.clip(np.floor((FIT['neck_y0'] - tf.Y0) / dy), 0, tf.NY - 1)); top = TT['base'][nk] + cin[nk]
    for i in range(nk, -1, -1): env[i] = np.maximum(env[i], top - FIT['bridge'] * dy * (nk - i))
    obstacle = skin.copy()
    for _ in range(4):                                   # one smooth surface: the rules above meet in creases otherwise
        pad = np.vstack([env[:1], env, env[-1:]]); env = (pad[:-2] + pad[1:-1] + pad[2:]) / 3; env = (np.roll(env, 1, 1) + env + np.roll(env, -1, 1)) / 3
    env = np.maximum(env, obstacle)
    wy = np.ones(tf.NY) if tucked_below < 0 else sstep(tucked_below + 0.005, tucked_below + 0.06, yg)
    return dict(shift=_soft(env - (TT['base'] + cin), 4), cin=cin, wy=wy)

# ------------------------------------------------------------------ one garment
def fit_top(gpos, B, TL, TR, TT, under=()):
    """A top refitted: (displacement per vertex, how much of each vertex the fit took, 0..1; the rest follows the skin by the
    slack rule). TL, TR: armfield.field_tables for the left arm and (mirrored) the right; TT: torsofield.tables."""
    disp = np.zeros_like(gpos); taken = np.zeros(len(gpos)); zone = np.zeros(len(gpos))
    for side, T in (("Left", TL), ("Right", TR)):
        tabs = arm_fit_tables(T, B, side, gpos); segs = arm_weights(gpos, B, T, side)
        # the shoulder and the armpit: neither set of coordinates describes the hollow there, so the trunk's fit keeps out
        # of it and the cloth the arm's mask does not take stays as tailored (following the skin by the slack rule)
        up = segs[0]; near = 1 - sstep(0.03, 0.07, up['rho'] - af.lookup(T['bu'], up['ug'], up['u'], up['phi']))
        zone = np.maximum(zone, near * sstep(-0.55, -0.40, up['u']) * (1 - sstep(0.30, 0.45, up['u'])))
        for seg, tab in zip(segs, tabs):
            if tab is None: continue
            c = seg['rho'] - af.lookup(tab['base'], seg['ug'], seg['u'], seg['phi']); cin = af.lookup(tab['cin'], seg['ug'], seg['u'], seg['phi'])
            mine = seg['w'] * (1 - sstep(cin + 0.02, cin + 0.05, c))
            disp += seg['dirn'] * (af.lookup(tab['shift'], seg['ug'], seg['u'], seg['phi']) * mine)[:, None]; taken = np.maximum(taken, mine)
    free = 1 - taken; total = taken.copy()
    tab = trunk_fit_table(TT, gpos, free, under)
    if tab is not None:
        x, y, z = gpos[:, 0], gpos[:, 1], gpos[:, 2] - tf.ZC; rho = np.hypot(x, z); th = np.arctan2(x, z)
        c = rho - tf.lookup(TT['base'], y, th); cin = tf.lookup(tab['cin'], y, th)
        w = free * (1 - zone) * np.interp(y, tf.grids()[0], tab['wy']) * (1 - sstep(cin + 0.02, cin + 0.05, c)) * (1 - sstep(FIT['neck_y0'], FIT['neck_y1'], y)) * ((y > tf.Y0) & (y < tf.Y1))
        total = total + w
        amt = tf.lookup(tab['shift'], y, th) * w; r = np.maximum(rho, 1e-6)
        disp[:, 0] += x / r * amt; disp[:, 2] += z / r * amt
    return disp, np.clip(total, 0, 1)

def dress(parts, B, mL, mR, P=None, chest=True, fit=True, tops=("Kit_Top",), under=("Kit_Bottom",), grow=True):
    """The whole hero: body with the arm (and chest) fields, every garment following; tops refitted when fit=True.
    grow=False: the body stays exactly as it is (her: "the female has good proportions") and only the clothes are refitted."""
    P = P or af.P
    body = dict(parts['Body'], armLeft=mL, armRight=mR)
    TL = af.field_tables(body, B, 'Left', P)
    mb = dict(body, pos=body['pos'] * [-1, 1, 1], armLeft=mR, armRight=mL, w=np.concatenate([body['w'][:, 4:], body['w'][:, :4]], 1))
    Bm = {k.replace("Left", "#").replace("Right", "Left").replace("#", "Right"): v * [-1, 1, 1] for k, v in B.items()}
    TR = af.field_tables(mb, Bm, 'Left', P); TT = tf.tables(body) if chest else None
    if not grow:
        for T in (TL, TR): T['du'] = T['du'] * 0; T['df'] = T['df'] * 0
        base = tf.base_table(body); TT = dict(base=base, d=np.zeros_like(base), zone=np.zeros_like(base), mid=base); chest = True
    out = {}
    for n, m in parts.items():
        cloth = n != 'Body'
        p = af.apply(af.apply(m['pos'], B, TL, 'Left', cloth=cloth), B, TR, 'Right', cloth=cloth)
        if chest: p = p + tf.apply(m['pos'], TT, cloth=cloth, arms=(B, TL, TR)) - m['pos']
        out[n] = dict(m, pos=p)
    if fit:
        TT2 = TT or dict(base=tf.base_table(body), d=np.zeros((tf.NY, tf.NT)))
        below = [out[u]['pos'] for u in under if u in out]
        for n in tops:
            if n not in parts: continue
            d, w = fit_top(parts[n]['pos'], B, TL, TR, TT2, below); rest = parts[n]['pos']
            out[n]['pos'] = rest + d + (1 - w)[:, None] * (out[n]['pos'] - rest)
        import shoefield
        for n in parts:
            if n.startswith("Kit_Shoe") and grow: out[n]['pos'] = shoefield.round_toe(out[n]['pos'])      # (his pointed toe box, 2026-11-12; her shoes are not touched)
    return out
