#!/usr/bin/env python3
"""measure.py <frames_dir> [tag ...]: swing timing + pops from GolfSwingSpeedFilm traces.

Per take (frames_dir/<tag>/trace.csv + events.txt):
  phone_top / phone_ball : phone at the top / crossing the ball (motion takes; synthetic profile, known)
  scr_top   : first frame the golfer is in the downswing (phase 2), or the club head's farthest frame before impact
  scr_impact: the frame the shown clip time first reaches the clip's impact time (the club at the ball)
  ball      : the first frame the ball moves
  downswing_s = scr_impact - (frame the club head starts down) ; through_s = impact -> club head at rest in the finish
  pops: frames where the club head moves > POP_RATIO x the larger of its neighbours' moves + POP_MM (the PlayMode test's rule),
        or where the shown clip time goes backwards during the swing (a rewind)
"""
import sys, os, csv, math

POP_RATIO, POP_MM = 2.5, 30.0   # SwingSmoothnessTests.AssertNoPops: d > 2.5 x max(neighbours) + 30 mm

def vec(s):
    if not s: return None
    return tuple(float(x) for x in s.split(';'))

def dist(a, b): return math.dist(a, b) if a and b else 0.0

def impact_time(path):
    tag = os.path.basename(path.rstrip('/'))
    for l in open(os.path.join(os.path.dirname(path.rstrip('/')), 'summary.txt')):
        if l.startswith(tag + ':'):
            return float(l.split('impact=')[1].split()[0])
    return None

def take(path):
    rows = list(csv.DictReader(open(os.path.join(path, 'trace.csv'))))
    ev = [l.strip() for l in open(os.path.join(path, 'events.txt')) if l.strip()]
    summary = {}
    head = [vec(r['clubHead']) for r in rows]
    t = [float(r['clipTime']) for r in rows]
    ph = [int(r['gvPhase']) for r in rows]
    clip = rows[0]['clip']
    # club head per-frame travel (mm)
    d = [0.0] + [dist(head[i], head[i - 1]) * 1000 for i in range(1, len(rows))]
    # the swing: from the first phase-2 frame (or the touch strike) to the finish
    k2 = next((i for i, p in enumerate(ph) if p in (2, 5)), None)
    ball = next((int(e.split()[0]) for e in ev if 'ball moves' in e), None)
    flight = next((int(e.split()[0]) for e in ev if '->Flight' in e), None)
    summary['clip'] = clip
    summary['k_strike'] = k2
    summary['k_flight'] = flight
    summary['k_ball'] = ball
    # impact on screen: club head nearest the ball's start (ball row of frame 0)
    b0 = vec(rows[0]['ball'])
    if k2 is not None and b0:
        win = range(k2, min(len(rows), k2 + 40))
        it = impact_time(path)
        # impact on screen: the first frame the shown clip reaches the clip's impact time (the club at the ball as authored)
        ki = next((i for i in win if t[i] >= it - 1e-4), None) if it else None
        if ki is None: ki = min(win, key=lambda i: dist(head[i], b0))
        summary['k_scr_impact'] = ki
        summary['impact_gap_mm'] = round(dist(head[ki], b0) * 1000)
        # top on screen: the club head's slowest frame between the backswing and the impact (where it turns round)
        lo = max(0, k2 - 30)
        kt = min(range(lo, ki), key=lambda i: d[i] if i > 0 else 1e9)
        summary['k_scr_top'] = kt
        summary['scr_downswing_s'] = round((ki - kt) / 60, 3)
        # strike -> impact
        summary['strike_to_impact_s'] = round((ki - k2) / 60, 3)
        # through: impact -> club head below 5% of its peak speed
        peak = max(d[k2:ki + 3])
        kf = next((i for i in range(ki + 1, len(rows)) if d[i] < 0.05 * peak), len(rows) - 1)
        summary['through_s'] = round((kf - ki) / 60, 3)
        summary['peak_head_mps'] = round(peak * 60 / 1000, 1)
        summary['ball_vs_impact_frames'] = (ball - ki) if ball is not None else None
    # phone timeline (motion takes): stage column
    st = [r['stage'] for r in rows]
    if rows[0]['phoneAngle']:
        ang = [float(r['phoneAngle']) for r in rows]
        kd = next((i for i, s in enumerate(st) if s == 'downswing'), None)
        kb = next((i for i in range(kd or 0, len(rows)) if ang[i] <= 0), None) if kd is not None else None
        summary['k_phone_top_end'] = kd
        summary['k_phone_ball'] = kb
        if kb is not None and 'k_scr_impact' in summary:
            summary['screen_minus_phone_impact_frames'] = summary['k_scr_impact'] - kb
        if kd is not None and 'k_scr_top' in summary:
            summary['screen_minus_phone_top_frames'] = summary['k_scr_top'] - kd
    # pops
    pops = []
    floor = 10.0 if clip == 'Putt' else POP_MM   # a putter head moves cm, not m: 30 mm would hide a putt's snap
    for i in range(2, len(rows) - 2):
        nb = max(d[i - 1], d[i + 1])
        if d[i] > POP_RATIO * nb + floor:
            pops.append((i, round(d[i]), round(nb)))
    # clip time rewinds while swinging (2 downswing, 5 through)
    rew = [(i, round(t[i - 1], 3), round(t[i], 3)) for i in range(1, len(rows)) if ph[i] in (2, 5) and ph[i - 1] in (2, 5) and t[i] < t[i - 1] - 1e-4]
    # per-frame acceleration spikes of the club head through the downswing (jerkiness)
    acc = [abs(d[i + 1] - d[i]) for i in range(1, len(rows) - 1)]
    summary['pops'] = pops
    summary['rewinds'] = rew
    summary['max_head_step_mm'] = round(max(d))
    summary['max_head_step_frame'] = d.index(max(d))
    if k2 is not None:
        seg = d[max(1, k2 - 30): min(len(d), k2 + 60)]
        accs = [abs(seg[i + 1] - seg[i]) for i in range(len(seg) - 1)]
        summary['max_accel_step_mm'] = round(max(accs))
    summary['events'] = ev
    return summary

if __name__ == '__main__':
    root = sys.argv[1]
    tags = sys.argv[2:] or sorted(x for x in os.listdir(root) if os.path.isdir(os.path.join(root, x)))
    for tg in tags:
        p = os.path.join(root, tg)
        if not os.path.exists(os.path.join(p, 'trace.csv')): continue
        s = take(p)
        print(f'== {tg}')
        for k, v in s.items():
            if k == 'events': continue
            print(f'  {k}: {v}')
