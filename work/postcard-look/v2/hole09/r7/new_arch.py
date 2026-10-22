def _wedge_corners(rng, th0, th1, r_in, r_out, spring, dy, jit=0.012):
    """corners {(ia, iy, ir)} of a ring stone between the angles th0 < th1 (rad, measured from the left springer, x = -R cos th, z = spring + R sin th) and the radii r_in .. r_out."""
    C = {}
    for ia, th in ((0, th0), (1, th1)):
        for iy in (0, 1):
            for ir, rad in ((0, r_in), (1, r_out)):
                rr_ = rad + rng.uniform(-jit, jit)
                th_j = th + rng.uniform(-0.004, 0.004)
                C[(ia, iy, ir)] = np.array([-rr_ * math.cos(th_j), (iy - 0.5) * dy * (1.0 + rng.uniform(-0.04, 0.04)), spring + rr_ * math.sin(th_j)])
    return C


def build_arch(ss, center, phi_deg, ground, G0, r=2.0, t=0.75, depth=1.3, pier_w=1.7, spring=2.7, left_top=5.8, right_top=4.9, seed=0, missing=(6,), outer=True):
    """Broken masonry arch: two rubble piers + a ring of 11 wedge voussoirs + (repair round 3) an outer course of rubble stones laid on the haunches of the ring. center = (x, y) midway between the piers
    (world, m); phi_deg = the direction you look THROUGH the opening (clockwise from +Y, the postcard_lib build_arch convention). The wedges in `missing` (6, just right of the crown) lie in a rubble heap
    under the gap; the left ring (0..5) rings up to the crown from the tall left pier, the right springers (7..10) are seated IN the right pier + the haunch stones that fill the angle between the ring and
    the pier top, so no ring stone hangs over a visible hole (round 2: a cantilevered crown block over a gap, the review's 'floating crown'). Returns dict(missing, height, centre, heap, ...)."""
    rng = random.Random(seed)
    phi = math.radians(phi_deg)
    xl = np.array([math.cos(phi), -math.sin(phi)])            # across the opening (local x)
    yl = np.array([math.sin(phi), math.cos(phi)])             # through the opening (local y)
    c0 = np.array(center, float)
    st_piers = []
    for side, top in ((-1, left_top), (1, right_top)):
        a = c0 + xl * side * (r + pier_w)
        b = c0 + xl * side * r
        p0, p1 = (a, b) if side < 0 else (b, a)
        dd = (p1 - p0) / np.hypot(*(p1 - p0))
        ph = rng.uniform(0, 6.0)
        # the pier is a short wall across the opening, `depth` thick; its broken top swings +-18 % (never below the springer on the opening side)
        prof = (lambda s_, top=top, ph=ph: top * (0.82 + 0.18 * math.sin(2.1 * s_ + ph)))
        rr = lay_wall(ss, rng, p0, dd, pier_w, depth, ground, prof, 0.0, pier_w, door=None, block_l=(0.45, 1.0), end_jitter=0.07)
        st_piers.append(len(rr["stones"]))
    n = 11
    Rl = Matrix.Rotation(-phi, 3, 'Z')
    origin = (c0[0], c0[1], G0)
    fallen = []
    for i in range(n):
        th0 = i * math.pi / n + 0.006
        th1 = (i + 1) * math.pi / n - 0.006
        dy = depth * rng.uniform(0.9, 1.0)
        C = _wedge_corners(rng, th0, th1, r - 0.03, r + t, spring, dy)
        res = ST.build_stone(rng, C, chip_p=0.55, chip_leg=(0.03, 0.09), bevel_p=0.30, top_axis=None, max_faces=13)
        if res is None:
            continue
        P_loc, faces, normals = res
        if i in missing:
            fallen.append((i, P_loc, faces, normals))
        else:
            ss.add_poly(P_loc, faces, normals, origin, Rl, kind="voussoir", rock_sides=False)
    # outer course: irregular stones on the haunches of the ring (left 14..76 deg, right 112..166 deg), radial thickness 0.45-0.8 m, joints not in line with the ring's: they bear on the ring below
    n_outer = 0
    if outer:
        for (a0, a1) in ((math.radians(14.0), math.radians(78.0)), (math.radians(112.0), math.radians(166.0))):
            th = a0 + rng.uniform(0.0, 0.05)
            while th < a1 - 0.10:
                span = rng.uniform(0.17, 0.30)
                th_e = min(a1, th + span)
                if a1 - th_e < 0.12:
                    th_e = a1
                rad_o = r + t + rng.uniform(0.45, 0.80)
                dy = depth * rng.uniform(0.86, 1.0)
                C = _wedge_corners(rng, th + 0.004, th_e - 0.004, r + t - 0.02, rad_o, spring, dy, jit=0.02)
                res = ST.build_stone(rng, C, chip_p=0.7, chip_leg=(0.05, 0.16), bevel_p=0.35, top_axis=None, max_faces=15)
                if res is not None:
                    P_loc, faces, normals = res
                    if ss.add_poly(P_loc, faces, normals, origin, Rl, kind="haunch"):
                        n_outer += 1
                th = th_e
    # the fallen crown wedge: lies in the heap under the gap, tilted, half buried
    heap, first = [], []
    for k, (i, P_loc, faces, normals) in enumerate(fallen):
        mid = np.mean(P_loc, axis=0)
        loc = P_loc - mid
        rel = np.array([rng.uniform(-0.55, 0.55), rng.uniform(-0.7, -0.2) if k == 0 else rng.uniform(0.2, 0.7)])
        posx = c0 + xl * rel[0] + yl * rel[1]
        Rf = Matrix.Rotation(rng.uniform(0, math.tau), 3, 'Z') @ Matrix.Rotation(rng.uniform(-0.45, 0.45), 3, 'X') @ Matrix.Rotation(rng.uniform(-0.45, 0.45), 3, 'Y')
        gz = float(ground(np.array([posx[0]]), np.array([posx[1]]))[0])
        ss.add_poly(loc, faces, normals, (posx[0], posx[1], gz + 0.16), Rf, kind="fallen", rock_sides=False)
    # a heap of small stones round the fallen wedge (under the broken crown): a half-buried first layer, then a few stones resting on it
    for k in range(9):
        sx = rng.uniform(0.45, 0.85)
        ang = rng.uniform(0, math.tau)
        rad_ = rng.uniform(0.2, 1.5)
        rel = np.array([math.cos(ang) * rad_ * 1.1, math.sin(ang) * rad_ * 0.5])
        p = c0 + xl * rel[0] + yl * rel[1]
        gz = float(ground(np.array([p[0]]), np.array([p[1]]))[0])
        sz_h = sx * rng.uniform(0.55, 0.8)
        if ss.stone((p[0], p[1], gz - 0.14), rng.uniform(0, math.tau), sx, sx * rng.uniform(0.6, 1.0), sz_h, top_rag=0.0, chamfer=0.6, tilt=0.06, kind="rubble", split_p=0.0, chip_scale=1.4):
            first.append((float(p[0]), float(p[1]), gz - 0.14 + sz_h * 0.95))
            heap.append((float(p[0]), float(p[1])))
    for (px, py, tz) in first[:4]:
        sx = rng.uniform(0.32, 0.5)
        ss.stone((px + rng.uniform(-0.1, 0.1), py + rng.uniform(-0.1, 0.1), tz - 0.05), rng.uniform(0, math.tau), sx, sx * rng.uniform(0.6, 1.0), sx * rng.uniform(0.5, 0.75),
                 top_rag=0.0, chamfer=0.6, tilt=0.06, kind="rubble", split_p=0.0, chip_scale=1.4)
    return dict(missing=len(fallen), height=max(left_top, right_top), center=tuple(c0), phi=phi_deg, heap=heap, pier_stones=st_piers, outer_stones=n_outer)


