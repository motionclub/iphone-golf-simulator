from pathlib import Path
p=Path('work/emote-overhaul/scripts/check_gates2.py');s=p.read_text()
anchor="    # ============================================================================ THRUST\n"
insert='''    # R2 additions: exported hand axes and elbow geometry, every requested frame.
    swim = (t >= 0.55 - 1e-9) & (t <= 3.40 + 1e-9)
    kscale = h.H.A / 0.505
    Rp = h.Q(c, 'Hips') @ h.rig.Rrest[ix['Hips']].T
    left_axis = Rp @ np.array([1.0, 0.0, 0.0])
    palm = h.Q(c, 'RightHand')[:, :, 2]
    thumb = h.Q(c, 'RightHand')[:, :, 0]
    palm_angle = np.degrees(np.arccos(np.clip(np.einsum('ni,ni->n', palm, left_axis), -1, 1)))
    thumb_angle = np.degrees(np.arccos(np.clip(thumb[:, 2], -1, 1)))
    shoulder, elbow, wrist = [h.P(c, n) for n in ('RightUpperArm', 'RightLowerArm', 'RightHand')]
    reach_m = np.linalg.norm(wrist - shoulder, axis=1)
    a, b = shoulder - elbow, wrist - elbow
    elbow_deg = np.degrees(np.arccos(np.clip(np.einsum('ni,ni->n', a, b) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)), -1, 1)))
    R[c]['C8'] = line(float(palm_angle[swim].max()) <= 25.0, gate='SCUBA_PALM_SIDEWAYS', max_deg=float(palm_angle[swim].max()), limit_deg=25.0, frames_checked=int(swim.sum()))
    R[c]['C9'] = line(float(thumb_angle[swim].max()) <= 35.0, gate='SCUBA_THUMB_UP', max_deg=float(thumb_angle[swim].max()), limit_deg=35.0, frames_checked=int(swim.sum()))
    R[c]['C10'] = line(float(reach_m[swim].min()) >= 0.50 * kscale and float(elbow_deg[swim].min()) >= 155.0, gate='SCUBA_REACH', min_reach_m=float(reach_m[swim].min()), required_m=0.50 * kscale, min_elbow_deg=float(elbow_deg[swim].min()), required_elbow_deg=155.0)
    fingers_p = np.einsum('nji,nj->ni', Rp, h.Q(c, 'RightHand')[:, :, 1])
    yaw_sw = np.degrees(np.arctan2(-fingers_p[:, 0], -fingers_p[:, 1]))[loop]
    zcy = np.where(np.diff(np.sign(yaw_sw - yaw_sw.mean())) != 0)[0]
    period_y = 2.0 * float(np.mean(np.diff(zcy))) / FPS if len(zcy) > 3 else 0.0
    yaw_p2p = float(np.ptp(yaw_sw))
    R[c]['C11'] = line(yaw_p2p >= 50.0 and abs(period_y - 22.0 / FPS) <= 0.04 and len(zcy) / 2.0 >= 3.5 and solver_clips[c].NLOOPS == 4 and solver_clips[c].F_PERIOD == 22, gate='SCUBA_SWEEP_KEPT', yaw_p2p_deg=yaw_p2p, required_deg=50.0, cycles_crossings=len(zcy)/2.0, authored_cycles=solver_clips[c].NLOOPS, period_s=period_y, required_period_s=22.0/FPS)

'''
assert anchor in s;s=s.replace(anchor,insert+anchor)
start=s.index('    ok3 = all(');end=s.index("    Qc = h.Q(c, 'UpperChest')",start)
s=s[:start]+'''    # R2 T3 replacement: the arms pull back as the pelvis drives forward.
    Rp = h.Q(c, 'Hips') @ h.rig.Rrest[ix['Hips']].T
    forward = Rp @ FWD
    right = Rp @ np.array([-1.0, 0.0, 0.0])
    chest = 0.5 * (h.P(c, 'LeftUpperArm') + h.P(c, 'RightUpperArm'))
    hipw = h.P(c, 'Hips')
    driver = solver_clips[c]
    back_mask = (t >= 0.45 - 1e-9) & (t <= 1.95 + 1e-9) & np.array([driver.th(t_)[0] <= 0.1 for t_ in t])
    fwd_min, height_abs, elbow_back, belt_err, lateral, elbow_at_hit, elbow_forward, corr, sync_world = [], [], [], [], [], [], [], [], []
    for side in ('Left', 'Right'):
        w, sh, el = [h.P(c, side + n) for n in ('Hand', 'UpperArm', 'LowerArm')]
        ahead_w = np.einsum('ni,ni->n', w - chest, forward)
        dh = w[:, 2] - sh[:, 2]
        fwd_min.append(float(ahead_w[back_mask].min()))
        height_abs.append(float(np.abs(dh[back_mask]).max()))
        a, b = sh - el, w - el
        ed = np.degrees(np.arccos(np.clip(np.einsum('ni,ni->n', a, b) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)), -1, 1)))
        elbow_forward.append(float(ed[back_mask].min()))
        eb = np.einsum('ni,ni->n', el - chest, forward)
        lat = np.abs(np.einsum('ni,ni->n', w - hipw, right))
        wh = h.A(c, side + 'Hand')[:, 1]
        for i, ht in enumerate(hit_t):
            kh = int(round(ht * FPS))
            elbow_back.append(float(eb[kh]))
            belt_err.append(float(abs(w[kh, 2] - hipw[kh, 2])))
            lateral.append(float(lat[kh]))
            elbow_at_hit.append(float(ed[kh]))
            win = np.where((t >= ht - driver.RISE - 1e-9) & (t <= ht + hold[i] + driver.FALL + 1e-9))[0]
            pv, wv = hips[win, 1], wh[win]
            corr.append(float(np.corrcoef(pv, wv)[0, 1]))
            kp = next(f for f in win if hips[f, 1] >= pv.max() - 1e-5)
            kw = next(f for f in win if wh[f] <= wv.min() + 1e-5)
            sync_world.append(abs(kp - kw))
    kscale = h.H.A / 0.505
    R[c]['T7'] = line(min(fwd_min) >= 0.40 * kscale and max(height_abs) <= 0.15 and min(elbow_forward) >= 150.0, gate='THRUST_ARMS_FORWARD_AT_BACK', min_forward_m=fwd_min, required_m=0.40*kscale, max_height_error_m=height_abs, height_limit_m=0.15, min_elbow_deg=elbow_forward, frames_checked=int(back_mask.sum()))
    R[c]['T8'] = line(max(belt_err) <= 0.12 and min(lateral) >= 0.15*kscale and max(lateral) <= 0.35*kscale and max(elbow_back) < 0.0, gate='THRUST_ARMS_BACK_AT_HIT', max_belt_error_m=max(belt_err), belt_limit_m=0.12, lateral_range_m=[min(lateral),max(lateral)], lateral_limits_m=[0.15*kscale,0.35*kscale], max_elbow_ahead_m=max(elbow_back), elbow_deg=elbow_at_hit)
    R[c]['T9'] = line(max(sync_world) <= 1, gate='THRUST_SYNC', frames_apart_each_hand=sync_world, limit_frames=1)
    R[c]['T10'] = line(max(corr) <= -0.8, gate='THRUST_OPPOSITE', correlation_each_hand_hit=corr, limit=-0.8)
''' + s[end:]
p.write_text(s);print('Added C8-C11; replaced T3 with T7-T10; unchanged other gate predicates')
