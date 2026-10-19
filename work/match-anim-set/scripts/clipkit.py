"""Clip authoring layer: sparse keyed channels -> pose parameter dict per time (-> pose.Solver).

A clip is a dict:
  name, section (WATCH.md section), length (s, multiple of 1/30), contact (s or None), thin (bool), thin_why (list), url, loop (bool),
  keys: list of K(t, src, ease=None, **channels).  Each key names the WATCH.md step(s) it comes from in `src`
  (`S5.F3` = section 5, feet step 3; `READY` = the anchor pose; `LOCK` = a brief lock such as the 0.16 s blend rule).
Every channel is interpolated only between keys that mention it (monotone cubic; `ease` 0..1 flattens the tangent at that key,
1 = zero velocity = a hold when two consecutive keys carry the same value).  READY values anchor t = 0 and t = length unless a key says
otherwise.  The racket orientation is one channel (shaft + face -> quaternion, interpolated with squad)."""
import os
import math

import numpy as np

import kin
import pose as PS
from kin import unit

FPS = int(os.environ.get('MA_GRID', 30))   # the solver's tracking grid. MA_GRID=60 would re-track on a 60 Hz grid (it picks different arm branches); the 60 Hz bake instead
                                           # keeps the approved 30 Hz tracking and samples its continuous curves at 60 Hz (bake.py, MA_HYBRID=1)

VEC_CH = {'rk_wrist', 'pel', 'pel_rot', 'chest_rot', 'head_rot', 'lf_foot', 'rf_foot', 'rk_pos', 'rk_sweet', 'rk_w', 'r_elbow', 'l_elbow', 'l_hand', 'l_palm', 'gaze'}
SCALAR_CH = {'lf_yaw', 'rf_yaw', 'lf_lift', 'rf_lift', 'lf_heel', 'rf_heel', 'lf_knee', 'rf_knee', 'l_attach', 'l_grip', 'r_fing', 'l_fing', 'rk_abs', 'rk_swivel'}
ORI_CH = {'rk_ori'}


def K(t, src, ease=None, **ch):
    ori = None
    if 'shaft' in ch or 'face' in ch:
        ori = (ch.pop('shaft', None), ch.pop('face', None))
    return dict(t=float(t), src=src, ease=ease, ch=ch, ori=ori)


# ------------------------------------------------------------------------------------------------------ interpolation
def _tangents(ts, vs, eases, periodic=False):
    """PCHIP-like tangents (Fritsch-Carlson) per component; vs (n, d); eases scale them toward 0."""
    n = len(ts)
    d = vs.shape[1]
    m = np.zeros((n, d))
    if n == 1:
        return m
    if periodic:
        T = ts[-1] - ts[0]
        tt = np.concatenate([[ts[-2] - T], ts, [ts[1] + T]])
        vv = np.vstack([vs[-2:-1], vs, vs[1:2]])
        h = np.diff(tt)
        delta = np.diff(vv, axis=0) / h[:, None]
        for k in range(n):
            a, b = delta[k], delta[k + 1]
            w1, w2 = 2 * h[k + 1] + h[k], h[k + 1] + 2 * h[k]
            with np.errstate(divide='ignore', invalid='ignore'):
                mk = np.where(a * b > 0, (w1 + w2) / (w1 / a + w2 / b), 0.0)
            m[k] = np.nan_to_num(mk)
    else:
        h = np.diff(ts)
        delta = np.diff(vs, axis=0) / h[:, None]
        if n == 2:
            m[:] = delta[0]
        else:
            for k in range(1, n - 1):
                a, b = delta[k - 1], delta[k]
                w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
                with np.errstate(divide='ignore', invalid='ignore'):
                    mk = np.where(a * b > 0, (w1 + w2) / (w1 / a + w2 / b), 0.0)
                m[k] = np.nan_to_num(mk)
            # one-sided end tangents (shape preserving)
            for k, (dd0, dd1, hh0, hh1) in ((0, (delta[0], delta[1], h[0], h[1])), (n - 1, (delta[-1], delta[-2], h[-1], h[-2]))):
                mm = ((2 * hh0 + hh1) * dd0 - hh0 * dd1) / (hh0 + hh1)
                mm = np.where(np.sign(mm) != np.sign(dd0), 0.0, mm)
                mm = np.where((np.sign(dd0) != np.sign(dd1)) & (np.abs(mm) > 3 * np.abs(dd0)), 3 * dd0, mm)
                m[k] = mm
    e = np.asarray(eases, float)[:, None]
    return m * (1.0 - e)


def _hermite(t, ts, vs, m, periodic=False):
    n = len(ts)
    if n == 1:
        return vs[0].copy()
    if periodic:
        T = ts[-1] - ts[0]
        tt = (t - ts[0]) % T + ts[0]
        t = tt
    if t <= ts[0]:
        return vs[0].copy()
    if t >= ts[-1]:
        return vs[-1].copy()
    k = int(np.searchsorted(ts, t, side='right') - 1)
    h = ts[k + 1] - ts[k]
    s = (t - ts[k]) / h
    h00 = 2 * s ** 3 - 3 * s ** 2 + 1
    h10 = s ** 3 - 2 * s ** 2 + s
    h01 = -2 * s ** 3 + 3 * s ** 2
    h11 = s ** 3 - s ** 2
    return h00 * vs[k] + h10 * h * m[k] + h01 * vs[k + 1] + h11 * h * m[k + 1]


def _squad(qs, ts, t, eases, periodic=False):
    n = len(ts)
    if n == 1:
        return qs[0].copy()
    if t <= ts[0]:
        return qs[0].copy()
    if t >= ts[-1]:
        return qs[-1].copy()
    k = int(np.searchsorted(ts, t, side='right') - 1)
    q0, q1 = qs[k], qs[k + 1]
    if np.dot(q0, q1) < 0:
        q1 = -q1

    def inner(i):
        qi = qs[i]
        qn = qs[min(i + 1, n - 1)]
        qp = qs[max(i - 1, 0)]
        if np.dot(qi, qn) < 0:
            qn = -qn
        if np.dot(qi, qp) < 0:
            qp = -qp
        if i == 0 or i == n - 1:
            return qi
        ci = kin.qconj(qi)
        l1 = kin.qlog(kin.qmul(ci, qn))
        l2 = kin.qlog(kin.qmul(ci, qp))
        e = eases[i]
        return kin.qmul(qi, kin.qexp(-(l1 + l2) / 4.0 * (1.0 - e)))
    s0, s1 = inner(k), inner(k + 1)
    if np.dot(s0, q0) < 0:
        s0 = -s0
    if np.dot(s1, q1) < 0:
        s1 = -s1
    s = (t - ts[k]) / (ts[k + 1] - ts[k])
    a = kin.qslerp(q0, q1, s)
    b = kin.qslerp(s0, s1, s)
    return kin.qslerp(a, b, 2 * s * (1 - s))


def _ori_to_quat(shaft, face):
    """authoring-frame (shaft, face) -> quaternion of the frame [X=Y x Z, Y=shaft, Z=face orthogonalised]."""
    R = PS.frame_from_axes(unit(shaft), face)
    q = kin.mat_to_quat(R)
    return q


def _quat_to_ori(q):
    R = kin.quat_to_mat(q)
    return R[:, 1], R[:, 2]


class Clip:
    def __init__(self, d, ready):
        d = dict(d)
        d['keys'] = [dict(k, ch=dict(k['ch'])) for k in d['keys']]
        self.name = d['name']
        self.length = float(d['length'])
        self.loop = bool(d.get('loop', False))
        self.ready = ready
        # time warp (piecewise linear old -> new) so every clip leaves READY smoothly and the finish gets room for its hold
        w = d.get('warp')
        if w:
            xs = [a for a, b in w]
            ys = [b for a, b in w]
            for k in d['keys']:
                k['t'] = float(np.interp(k['t'], xs, ys))
            if d['contact'] is not None:
                d['contact'] = float(np.interp(d['contact'], xs, ys))
            if d.get('hold'):
                d['hold'] = tuple(float(np.interp(h, xs, ys)) for h in d['hold'])
        if d['contact'] is not None:
            d['contact'] = round(d['contact'] * FPS) / FPS
            for k in d['keys']:                      # the keys that pin the sweet spot sit exactly on the contact frame
                if k['ch'].get('rk_abs') == 1.0:
                    k['t'] = d['contact']
        if d.get('hold'):
            d['hold'] = (round(d['hold'][0] * FPS) / FPS, round(d['hold'][1] * FPS) / FPS)
        self.d = d
        keys = sorted(d['keys'], key=lambda k: k['t'])
        self.keys = keys
        self.channels = {}
        self._build(keys)

    def _build(self, keys):
        L = self.length
        chans = {}
        for k in keys:
            for c, v in k['ch'].items():
                chans.setdefault(c, []).append((k['t'], v, k['ease']))
            if k['ori'] is not None:
                chans.setdefault('rk_ori', []).append((k['t'], k['ori'], k['ease']))
        # READY anchors
        for c in list(chans):
            lst = chans[c]
            if c == 'rk_ori':
                continue
            rv = self._ready_val(c)
            if lst[0][0] > 1e-6:
                lst.insert(0, (0.0, rv if rv is not None else lst[0][1], 1.0))
            if lst[-1][0] < L - 1e-6 and not self.loop:
                lst.append((L, rv if rv is not None else lst[-1][1], 1.0))
        if 'rk_ori' in chans:
            lst = chans['rk_ori']
            ready_o = (self.ready['rk_shaft'], self.ready['rk_face'])
            if lst[0][0] > 1e-6:
                lst.insert(0, (0.0, ready_o, 1.0))
            if lst[-1][0] < L - 1e-6 and not self.loop:
                lst.append((L, ready_o, 1.0))
        # pack
        hold = self.d.get('hold')
        for c, lst in chans.items():
            lst = sorted(lst, key=lambda x: x[0])
            ts = np.array([x[0] for x in lst])
            ez = np.array([1.0 if x[2] is None and (i == 0 or i == len(lst) - 1) else (0.0 if x[2] is None else x[2]) for i, x in enumerate(lst)])
            if c == 'rk_ori':
                # carry face forward when a key gives only the shaft (and vice versa)
                qs = []
                last = (self.ready['rk_shaft'], self.ready['rk_face'])
                for x in lst:
                    sh, fc = x[1]
                    sh = last[0] if sh is None else sh
                    fc = last[1] if fc is None else fc
                    last = (sh, fc)
                    q = _ori_to_quat(sh, fc)
                    if qs and np.dot(q, qs[-1]) < 0:
                        q = -q
                    qs.append(q)
                qs = np.array(qs)
                if hold:
                    ts, qs, ez = self._hold_ori(ts, qs, ez, hold)
                self.channels[c] = dict(ts=ts, qs=qs, ez=ez, kind='ori')
            else:
                vs = np.array([np.atleast_1d(np.asarray(x[1], float)) for x in lst])
                if hold:
                    ts, vs, ez = self._hold_vec(ts, vs, ez, hold)
                m = _tangents(ts, vs, ez, periodic=self.loop)
                if c in self.SPH_CH and self.ready.get('sh_half_A') is not None and len(ts) > 1 and not self.loop:
                    # hand positions swing around the shoulder: the direction follows great-circle arcs between the keys at a speed given by a monotone
                    # cubic of the travelled angle, the radius is a monotone cubic of its own, so a path between two keys never cuts through the shoulder
                    # (a Cartesian blend does, and the arm then flips)
                    s0 = np.array([self.SPH_CH[c] * float(self.ready['sh_half_A']), 0.0, 0.0])
                    rel = vs - s0
                    nr = np.linalg.norm(rel, axis=1, keepdims=True)
                    dirn = rel / np.maximum(nr, 1e-9)
                    rho = np.maximum(nr, self.SPH_RMIN[c])
                    al = np.arccos(np.clip(np.sum(dirn[:-1] * dirn[1:], axis=1), -1.0, 1.0))
                    th = np.concatenate([[0.0], np.cumsum(al)]).reshape(-1, 1)
                    self.channels[c] = dict(ts=ts, vs=vs, m=m, kind='sph', s0=s0, rho=rho, dirn=dirn, th=th,
                                            m_r=_tangents(ts, rho, ez, periodic=False), m_th=_tangents(ts, th, ez, periodic=False))
                else:
                    self.channels[c] = dict(ts=ts, vs=vs, m=m, kind='vec')

    def resolve(self, solver, densify=True):
        """solve the racket-arm swivel + the feasible racket orientation (wrist angles inside their anatomical box) at every key that carries a
        racket intent and at the two READY anchors; the clip then interpolates those ABSOLUTE orientations (squad) and swivels.  `densify` then adds
        keys wherever the interpolated orientation would leave the wrist box (it projects the interpolated orientation onto the nearest feasible one),
        so the racket moves smoothly and stays anatomical.  The authored intent is kept in `cmd_ori` for the error report."""
        times = sorted(set(round(k['t'], 6) for k in self.keys if k['ori'] is not None))
        L = self.length
        if not times:
            return
        if times[0] > 1e-6:
            times = [0.0] + times
        if (not self.loop) and times[-1] < L - 1e-6:
            times = times + [L]
        self.cmd_ori = self.channels.get('rk_ori')
        self._res = {}
        prev = None
        for t in times:
            P = self.params(t)
            P['rk_mode'] = 'fit'
            solver.reset()
            if prev is not None:
                solver.state['R'] = dict(phi=prev[0], wr=prev[1])
            P['prior_w'] = 0.05
            b, h, info = solver.solve(P)
            self._res[t] = (info['rk_swivel_deg'], np.array(info['shaft_a']), np.array(info['face_a']), list(map(float, info['rk_fit_flex_dev_twist'])))
            prev = (info['rk_swivel_deg'], np.array(info['rk_fit_flex_dev_twist']))
        self._rebuild_resolved()
        self.dense_added = []
        if densify:
            for pass_ in range(4):
                bad = []
                for tt in np.arange(0.0, L + 1e-9, 1.0 / 60.0):
                    P = self.params(tt)
                    P['rk_nolim'] = True
                    solver.reset()
                    b, h, info = solver.solve(P)
                    sw, tw = info['R_wrist_swing_deg'], abs(info['R_wrist_twist_deg'])
                    if sw > 100.0 or tw > 112.0:
                        bad.append((tt, max(sw / 100.0, tw / 112.0)))
                if not bad:
                    break
                # cluster the violations (0.1 s apart) and add one key at the worst frame of each cluster
                bad.sort()
                clusters, cur = [], [bad[0]]
                for x in bad[1:]:
                    if x[0] - cur[-1][0] <= 0.1:
                        cur.append(x)
                    else:
                        clusters.append(cur)
                        cur = [x]
                clusters.append(cur)
                added = 0
                for cl in clusters:
                    tn = round(max(cl, key=lambda x: x[1])[0], 6)
                    if any(abs(tn - tk) < 0.012 for tk in self._res):
                        continue
                    P = self.params(tn)
                    P2 = dict(P)
                    P2['rk_mode'] = 'fit'
                    P2['rk_w'] = [0.3, 1.0]
                    near = max([tk for tk in self._res if tk < tn], default=None)
                    solver.reset()
                    if near is not None:
                        solver.state['R'] = dict(phi=self._res[near][0], wr=np.array(self._res[near][3]))
                    P2['prior_w'] = 0.05
                    b, h, info = solver.solve(P2)
                    self._res[tn] = (info['rk_swivel_deg'], np.array(info['shaft_a']), np.array(info['face_a']), list(map(float, info['rk_fit_flex_dev_twist'])))
                    self.dense_added.append(tn)
                    added += 1
                if not added:
                    break
                self._rebuild_resolved()
        tk = sorted(self._res)
        self.resolved = dict(times=tk, swivel=[self._res[x][0] for x in tk], wrist=[self._res[x][3] for x in tk], densified=sorted(self.dense_added))

    SPH_CH = {'rk_pos': 1.0, 'l_hand': -1.0}            # channels interpolated around the shoulder (+1 right, -1 left)
    SPH_RMIN = {'rk_pos': 0.55, 'l_hand': 0.55}         # never closer than this (arm lengths) at a key (the wrist itself is held >= 0.5 arm lengths from the shoulder by the IK)

    # ---------------------------------------------------------------------------------------------------------------- tracker
    TRK_STEPS = (10.0, 5.0, 5.0, 10.0)           # grid steps of (swivel, flex, dev, twist) in degrees
    TRK_WIN = (4, 6, 5, 7)                       # transition windows in grid steps
    TRK_SC = (35.0, 25.0, 15.0, 35.0)            # scales of the quadratic transition costs (degrees)

    @classmethod
    def _relax(cls, B, lam):
        """min-plus transform of B (swivel, flex, dev, twist) with the separable windowed quadratic transition cost."""
        out = B
        for ax in range(4):
            w = cls.TRK_WIN[ax]
            acc = out.copy()
            n = out.shape[ax]
            for s in range(1, min(w, n - 1) + 1):
                pen = np.float32(lam * (s * cls.TRK_STEPS[ax] / cls.TRK_SC[ax]) ** 2)
                d = [slice(None)] * 4
                u = [slice(None)] * 4
                d[ax], u[ax] = slice(0, n - s), slice(s, None)
                np.minimum(acc[tuple(d)], out[tuple(u)] + pen, out=acc[tuple(d)])
                d[ax], u[ax] = slice(s, None), slice(0, n - s)
                np.minimum(acc[tuple(d)], out[tuple(u)] + pen, out=acc[tuple(d)])
            out = acc
        return out

    TRK_LAM = 0.5
    TRK_ANCHOR = True

    def track(self, solver, passes=2, lam=None, pw=0.6, box=(10.0, 10.0, 20.0)):
        """choose, for every frame, the elbow swivel and the three wrist angles of the racket arm so that the racket follows the authored orientation
        as well as a smooth arm allows: Viterbi search over (swivel x flex x dev x twist) grids with a windowed quadratic transition cost (this is what
        stops the one-frame arm flips of a per-frame nearest-feasible fit), first and last frame forced to the READY state, then a local continuous
        refine inside a small box around the chosen cell.  `passes` = 2 re-places the wrist joint for the orientation the first pass achieved."""
        lam = self.TRK_LAM if lam is None else lam
        frames = self.frame_times()
        N = len(frames)
        self.cmd_ori = self.channels.get('rk_ori')
        self._trk = None
        if self.loop:
            # the idle loop moves the racket hand by a few millimetres only: the arm keeps its READY configuration (no per-frame search, so the loop closes exactly)
            rdy = solver.ready_fit()
            self._trk = dict(frames=np.array(frames), phi=np.full(N, rdy['phi']), shaft=np.tile(rdy['shaft'], (N, 1)), face=np.tile(rdy['face'], (N, 1)),
                             wrist=np.tile(rdy['wr'], (N, 1)), pole=np.tile(rdy['pole'], (N, 1)), phiL=np.full(N, rdy['phiL']))
            self.resolved = dict(times=list(map(float, frames)), swivel=[float(rdy['phi'])] * N, wrist=[], densified=[])
            return
        ang, Dg = solver._wrist_grid()
        fl, dv, tw = np.unique(ang[:, 0]), np.unique(ang[:, 1]), np.unique(ang[:, 2])
        shp = (len(fl), len(dv), len(tw))
        regc = 0.00035 * (ang ** 2).sum(1)
        ready = solver.ready_fit()
        guess = None
        for pas in range(passes):
            node = []
            poles = []
            axes = []
            nat_offs = []
            C1 = C2 = None
            solver.reset()
            for i, t in enumerate(frames):
                P = self.params(t)
                P['rk_mode'] = 'cands2'
                if guess is not None:
                    P['rk_guess_shaft'], P['rk_guess_face'] = guess[0][i], guess[1][i]
                b, h, info = solver.solve(P)                 # sequential: the elbow reference direction is parallel-transported from frame to frame
                cd = info['cands2']
                poles.append(np.array(cd['pole'])); axes.append(np.array(cd['axis'])); nat_offs.append(float(cd['nat_offset']))
                if C1 is None:
                    Cm = Dg @ cd['R0'] @ solver.R_rh
                    C1, C2 = Cm[:, :, 1], Cm[:, :, 2]
                Ql, cmd, phis = cd['Ql'], cd['Rk_cmd'], cd['phis']
                vs = np.einsum('jab,a->jb', Ql, cmd[:, 1])
                vf = np.einsum('jab,a->jb', Ql, cmd[:, 2])
                ash = np.degrees(np.arccos(np.clip(vs @ C1.T, -1.0, 1.0)))
                afc = np.degrees(np.arccos(np.clip(vf @ C2.T, -1.0, 1.0)))
                ph_nat = phis + cd['nat_offset']
                cost = (cd['ws'] * (ash / 25.0) ** 2 + cd['wf'] * (afc / 25.0) ** 2 + regc[None, :]
                        + (0.30 * (ph_nat / 50.0) ** 2 + 0.4 * (ph_nat / 100.0) ** 4 + cd['torso'] + (cd['short'] * 40.0) ** 2)[:, None])
                node.append(cost.reshape((len(phis),) + shp).astype(np.float32))
            J = len(phis)
            # contact frames (sweet spot pinned): the racket position and orientation are coupled through the 40 cm lever, so the cell is taken from the
            # full per-frame search with that coupling (global swivel search + fixed-point wrist fit) and forced
            anchors = {}
            for i, t in enumerate(frames):
                Pa = self.params(t)
                if self.TRK_ANCHOR and float(Pa.get('rk_abs', 0.0)) >= 0.99 and 0 < i < N - 1:
                    Pa['rk_mode'] = 'anchor'
                    Pa['r_pole_w'] = poles[i]
                    solver.reset()
                    b, h, info = solver.solve(Pa)
                    an = info['anchor']
                    anchors[i] = (float(an['phi']), np.array(an['wrist'], float), np.array(an['shaft'], float), np.array(an['face'], float))
            # forced first / last state = the READY elbow direction and wrist (the transported reference at the end may differ from the READY one by delta)
            ue = axes[-1]
            pe = poles[-1]
            pr = ready['pole'] - np.dot(ready['pole'], ue) * ue
            pr = pr / np.linalg.norm(pr)
            delta = math.degrees(math.atan2(float(np.dot(ue, np.cross(pe, pr))), float(np.dot(pe, pr))))
            phi_end = float(np.clip(ready['phi'] + delta, phis[0], phis[-1]))
            jr0 = int(np.argmin(np.abs(phis - ready['phi'])))
            jr1 = int(np.argmin(np.abs(phis - phi_end)))
            fr0 = (jr0, int(np.argmin(np.abs(fl - ready['wr'][0]))), int(np.argmin(np.abs(dv - ready['wr'][1]))), int(np.argmin(np.abs(tw - ready['wr'][2]))))
            fr1 = (jr1,) + fr0[1:]
            forcing = [(0, fr0), (N - 1, fr1)]
            for k, (ph_a, wr_a, _sa, _fa) in anchors.items():
                forcing.append((k, (int(np.argmin(np.abs(phis - ph_a))), int(np.argmin(np.abs(fl - wr_a[0]))), int(np.argmin(np.abs(dv - wr_a[1]))), int(np.argmin(np.abs(tw - wr_a[2]))))))
            for k, fr in forcing:
                forced = np.full(node[k].shape, np.float32(1e4))
                forced[fr] = node[k][fr]
                node[k] = forced
            hold = self.d.get('hold')
            hold_edge = [False] * N                  # edge i -> i+1 lies inside the finish hold: the arm does not move there
            if hold:
                for i in range(N - 1):
                    if frames[i] >= hold[0] - 1e-6 and frames[i + 1] <= hold[1] + 1e-6:
                        hold_edge[i] = True
            beta = [None] * N
            beta[N - 1] = node[N - 1]
            for i in range(N - 2, -1, -1):
                beta[i] = node[i] + (beta[i + 1] if hold_edge[i] else self._relax(beta[i + 1], lam))
            # forward decode inside the transition window
            s = tuple(int(x) for x in np.unravel_index(int(np.argmin(beta[0])), beta[0].shape))
            path = [s]
            win, steps, sc = self.TRK_WIN, self.TRK_STEPS, self.TRK_SC
            for i in range(N - 1):
                if hold_edge[i]:
                    path.append(s)
                    continue
                lo = [max(0, s[a] - win[a]) for a in range(4)]
                hi = [min(beta[i + 1].shape[a], s[a] + win[a] + 1) for a in range(4)]
                sub = beta[i + 1][lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2], lo[3]:hi[3]].astype(np.float64)
                pen = 0.0
                for a in range(4):
                    off = (np.arange(lo[a], hi[a]) - s[a]) * steps[a] / sc[a]
                    shape = [1, 1, 1, 1]
                    shape[a] = -1
                    pen = pen + lam * (off ** 2).reshape(shape)
                tot = sub + pen
                k = np.unravel_index(int(np.argmin(tot)), tot.shape)
                s = tuple(int(lo[a] + k[a]) for a in range(4))
                path.append(s)
            phi_p = np.array([phis[p_[0]] for p_ in path])
            wr_p = np.array([[fl[p_[1]], dv[p_[2]], tw[p_[3]]] for p_ in path])
            phi_s = phi_p.copy()
            for i in range(1, N - 1):
                if i in anchors:
                    continue
                phi_s[i] = 0.25 * phi_p[i - 1] + 0.5 * phi_p[i] + 0.25 * phi_p[i + 1]
            phi_s[0], phi_s[-1] = ready['phi'], phi_end
            # local continuous refine in a box around the chosen cell
            shafts, faces, wrs = [], [], []
            for i, t in enumerate(frames):
                if i == 0 or i == N - 1:
                    shafts.append(ready['shaft']); faces.append(ready['face']); wrs.append(ready['wr'])
                    continue
                if i in anchors:                                   # the converged pose of the exhaustive coupled search, used as it is
                    shafts.append(anchors[i][2]); faces.append(anchors[i][3]); wrs.append(anchors[i][1])
                    continue
                P = self.params(t)
                P['rk_mode'] = 'fit'
                P['rk_phi_fixed'] = float(phi_s[i])
                P['prior_w'] = pw
                P['rk_wbox'] = list(box) if i not in anchors else [4.0, 4.0, 8.0]
                P['r_pole_w'] = poles[i]
                solver.reset()
                solver.state['R'] = dict(phi=float(phi_s[i]), wr=np.array(wr_p[i], float), pole=None)
                b, h, info = solver.solve(P)
                shafts.append(np.array(info['shaft_a'])); faces.append(np.array(info['face_a'])); wrs.append(np.array(info['rk_fit_flex_dev_twist'], float))
            # frames where the sweet spot is (partly) pinned: the racket position and orientation are coupled through the lever, so the tracked orientation is
            # replaced by the nearest orientation that the arm can actually hold at that sweet-spot position (exact coupled search around the tracked swivel)
            for i, t in enumerate(frames):
                if i == 0 or i == N - 1 or i in anchors:
                    continue
                Pa = self.params(t)
                if float(Pa.get('rk_abs', 0.0)) < 0.05:
                    continue
                Pa['rk_mode'] = 'anchor'
                Pa['r_pole_w'] = poles[i]
                Pa['rk_shaft'], Pa['rk_face'] = shafts[i], faces[i]
                Pa['rk_w'] = [1.0, 1.0]
                Pa['anchor_phi'] = float(phi_s[i])
                Pa['anchor_phi_win'] = 40.0
                solver.reset()
                b, h, info = solver.solve(Pa)
                an = info['anchor']
                shafts[i], faces[i], wrs[i] = np.array(an['shaft'], float), np.array(an['face'], float), np.array(an['wrist'], float)
                phi_s[i] = float(an['phi'])
            guess = (shafts, faces)
        self._trk = dict(frames=np.array(frames), phi=phi_s, shaft=np.array(shafts), face=np.array(faces), wrist=np.array(wrs), pole=np.array(poles))
        self.resolved = dict(times=list(map(float, frames)), swivel=list(map(float, phi_s)), wrist=[list(map(float, w)) for w in wrs], densified=[])
        self.track_left(solver)

    def track_left(self, solver, lamL=1.0):
        """swivel of the OFF arm while it holds the racket: candidate costs per frame (with the right arm already tracked), then a Viterbi path per run of
        frames so the left elbow cannot hop between basins from one frame to the next."""
        frames = self.frame_times()
        N = len(frames)
        solver.reset()
        cands = [None] * N
        for i, t in enumerate(frames):
            P = self.params(t)
            P['l_mode'] = 'cands'
            b, h, info = solver.solve(P)
            cands[i] = info.get('candsL')
        phiL = np.full(N, np.nan)
        i = 0
        while i < N:
            if cands[i] is None:
                i += 1
                continue
            j = i
            while j < N and cands[j] is not None:
                j += 1
            run = list(range(i, j))
            phis = cands[i]['phis']
            costs = np.array([cands[k]['costs'] for k in run])
            n, J = costs.shape
            rdyL = solver.ready_fit()
            for a_, k_ in enumerate(run):                       # the first / last frame of the clip are the READY pose (same elbow direction, whatever the carried-over reference is)
                if k_ == 0 or k_ == N - 1:
                    ph_t = rdyL['phiL'] if k_ == 0 else float(np.clip(rdyL['phiL'] + rdyL['natL'] - cands[k_]['nat_off'], phis[0], phis[-1]))
                    jr = int(np.argmin(np.abs(phis - ph_t)))
                    forced = np.full(J, 1e4)
                    forced[jr] = costs[a_, jr]
                    costs[a_] = forced
            step = float(phis[1] - phis[0])
            win = int(round(40.0 / step))
            pen = lamL * ((np.arange(-win, win + 1) * step / 20.0) ** 2)
            acc = costs[0].copy()
            back = np.zeros((n, J), int)
            for a in range(1, n):
                best = np.full(J, np.inf)
                arg = np.zeros(J, int)
                for s in range(-win, win + 1):
                    lo, hi = max(0, -s), min(J, J - s)
                    if hi <= lo:
                        continue
                    cand = acc[lo + s:hi + s] + pen[s + win]
                    upd = cand < best[lo:hi]
                    best[lo:hi] = np.where(upd, cand, best[lo:hi])
                    arg[lo:hi] = np.where(upd, np.arange(lo, hi) + s, arg[lo:hi])
                acc = costs[a] + best
                back[a] = arg
            k = int(np.argmin(acc))
            path = [k]
            for a in range(n - 1, 0, -1):
                k = int(back[a][k])
                path.append(k)
            path = path[::-1]
            for a, kk in zip(run, path):
                phiL[a] = phis[kk]
            i = j
        self._trk['phiL'] = phiL

    def _rebuild_resolved(self):
        tk = sorted(self._res)
        ts = np.array(tk)
        ez = np.zeros(len(ts))
        ez[0] = 1.0
        ez[-1] = 1.0
        vals = np.array([self._res[x][0] for x in tk]).reshape(-1, 1)
        self.channels['rk_swivel'] = dict(ts=ts, vs=vals, m=_tangents(ts, vals, ez, periodic=False), kind='vec')
        qs = []
        for x in tk:
            q = _ori_to_quat(self._res[x][1], self._res[x][2])
            if qs and np.dot(q, qs[-1]) < 0:
                q = -q
            qs.append(q)
        self.channels['rk_ori'] = dict(ts=ts, qs=np.array(qs), ez=ez, kind='ori')

    def _hold_vec(self, ts, vs, ez, hold):
        t0, t1 = hold
        # value of the channel at t0 (monotone-cubic through the existing keys), then a flat segment t0..t1
        m = _tangents(ts, vs, ez, periodic=False)
        v0 = _hermite(t0, ts, vs, m)
        keep = [i for i in range(len(ts)) if ts[i] < t0 - 1e-6 or ts[i] > t1 + 1e-6]
        ts2 = np.concatenate([ts[keep], [t0, t1]])
        vs2 = np.vstack([vs[keep], v0[None, :], v0[None, :]])
        ez2 = np.concatenate([ez[keep], [1.0, 1.0]])
        o = np.argsort(ts2, kind='stable')
        return ts2[o], vs2[o], ez2[o]

    def _hold_ori(self, ts, qs, ez, hold):
        t0, t1 = hold
        q0 = _squad(qs, ts, t0, ez)
        keep = [i for i in range(len(ts)) if ts[i] < t0 - 1e-6 or ts[i] > t1 + 1e-6]
        ts2 = np.concatenate([ts[keep], [t0, t1]])
        qs2 = np.vstack([qs[keep], q0[None, :], q0[None, :]])
        ez2 = np.concatenate([ez[keep], [1.0, 1.0]])
        o = np.argsort(ts2, kind='stable')
        return ts2[o], qs2[o], ez2[o]

    def _ready_val(self, c):
        v = self.ready[c]
        return v

    def params(self, t):
        P = {}
        for c, ch in self.channels.items():
            if ch['kind'] == 'ori':
                q = _squad(ch['qs'], ch['ts'], t, ch['ez'], periodic=False)
                sh, fc = _quat_to_ori(q)
                P['rk_shaft'], P['rk_face'] = sh, fc
            elif ch['kind'] == 'sph':
                r_ = float(_hermite(t, ch['ts'], ch['rho'], ch['m_r'])[0])
                th_, dn = ch['th'][:, 0], ch['dirn']
                x = float(np.clip(_hermite(t, ch['ts'], ch['th'], ch['m_th'])[0], th_[0], th_[-1]))
                k = min(int(np.searchsorted(th_, x, side='right')) - 1, len(th_) - 2)
                k = max(k, 0)
                w = th_[k + 1] - th_[k]
                if w < 1e-9:
                    u_ = dn[k]
                else:
                    f = (x - th_[k]) / w
                    ang = w
                    u_ = dn[k] if ang < 1e-6 else (math.sin((1 - f) * ang) * dn[k] + math.sin(f * ang) * dn[k + 1]) / math.sin(ang) if ang < math.pi - 1e-3 else unit((1 - f) * dn[k] + f * dn[k + 1])
                P[c] = ch['s0'] + r_ * u_
            else:
                v = _hermite(t, ch['ts'], ch['vs'], ch['m'], periodic=self.loop)
                P[c] = v if c in VEC_CH else float(v[0])
        # a foot that travels is not planted: it is lifted by an arc that grows with its ground speed (no skating on the floor)
        for fk in ('lf', 'rf'):
            chf = self.channels.get(fk + '_foot')
            if chf is None or len(chf['ts']) < 2:
                continue
            dt_ = 0.002
            pa = _hermite(min(t + dt_, chf['ts'][-1]), chf['ts'], chf['vs'], chf['m'], periodic=self.loop)
            pb = _hermite(max(t - dt_, chf['ts'][0]), chf['ts'], chf['vs'], chf['m'], periodic=self.loop)
            span = min(t + dt_, chf['ts'][-1]) - max(t - dt_, chf['ts'][0])
            v_ = float(np.linalg.norm(pa - pb)) / span if span > 1e-9 else 0.0
            lift_v = 0.14 * (1.0 - math.exp(-v_ / 1.2))
            P[fk + '_lift'] = max(float(P.get(fk + '_lift', 0.0)), lift_v)
        trk = getattr(self, '_trk', None)
        if trk is not None:
            i = int(round(t * FPS))
            if 0 <= i < len(trk['frames']) and abs(trk['frames'][i] - t) < 1e-6:
                P['rk_mode'] = 'fixed'
                P['rk_shaft'] = trk['shaft'][i]
                P['rk_face'] = trk['face'][i]
                P['rk_swivel'] = float(trk['phi'][i])
                if trk.get('pole') is not None:
                    P['r_pole_w'] = trk['pole'][i]
                if trk.get('phiL') is not None and np.isfinite(trk['phiL'][i]):
                    P['l_swivel_fixed'] = float(trk['phiL'][i])
                return P
        if 'rk_swivel' in self.channels:
            P['rk_mode'] = 'fixed'
        return P

    def intent(self, t):
        ch = getattr(self, 'cmd_ori', None) or self.channels.get('rk_ori')
        q = _squad(ch['qs'], ch['ts'], t, ch['ez'])
        return _quat_to_ori(q)

    def frame_times(self):
        n = int(round(self.length * FPS))
        return [i / FPS for i in range(n + 1)]
