"""UV anisotropy of the play-surface meshes (independent re-implementation of postcard_look_verify.uv_aniso_world / g_uv_local_smear: closed form of the singular-value ratio of the UV -> world
Jacobian of every triangle, UV in tile units or not, the ratio is scale free). Loaded by stage_gates.py (blend + FBX) and ground_uv_control.py (a named blend, e.g. the stage before the repair).
Returns {mesh: dict(total_m2 above RATIO, single_m2, worst, n, area_total, worst_area)}."""
import numpy as np

RATIO = 4.0
GROUND = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH")


def stats(objs, ratio=RATIO):
    out = {}
    for o in objs:
        if o.type != 'MESH' or not o.name.startswith(GROUND) or not o.data.uv_layers:
            continue
        me = o.data
        me.calc_loop_triangles()
        nt = len(me.loop_triangles)
        if nt == 0:
            continue
        tv = np.empty(nt * 3, np.int64); me.loop_triangles.foreach_get("vertices", tv); tv = tv.reshape(-1, 3)
        tl = np.empty(nt * 3, np.int64); me.loop_triangles.foreach_get("loops", tl); tl = tl.reshape(-1, 3)
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        M = np.array(o.matrix_world)
        W = co @ M[:3, :3].T + M[:3, 3]
        uvf = np.empty(len(me.loops) * 2); me.uv_layers[0].data.foreach_get("uv", uvf); uvf = uvf.reshape(-1, 2)
        uv = uvf[tl]
        e1, e2 = W[tv[:, 1]] - W[tv[:, 0]], W[tv[:, 2]] - W[tv[:, 0]]
        # world frame of the triangle (area-preserving 2D coordinates inside its own plane): the triangle may be tilted (walls), so use 3D lengths
        l1 = np.linalg.norm(e1, axis=1)
        l2 = np.linalg.norm(e2, axis=1)
        dd = (e1 * e2).sum(1)
        area = 0.5 * np.sqrt(np.maximum(l1 * l1 * l2 * l2 - dd * dd, 0.0))
        d1, d2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
        det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
        good = np.abs(det) > 1e-12 * np.maximum(l1 * l2, 1e-12)
        # Gram matrix of the world -> UV map pulled back: G = J^T J with J = [e1 e2] [d1 d2]^-1 ; its eigenvalues are the squared singular values
        dsafe = np.where(good, det, 1.0)
        inv = np.stack([np.stack([d2[:, 1], -d1[:, 1]], 1), np.stack([-d2[:, 0], d1[:, 0]], 1)], 1) / dsafe[:, None, None]      # inverse of [d1 d2] (columns d1, d2): rows (d2y -d2x ; -d1y d1x)/det transposed below
        # J columns: world derivative wrt u and v = e1 * inv[0,0] + e2 * inv[1,0] ... build explicitly
        Pu = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / dsafe[:, None]
        Pv = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / dsafe[:, None]
        g11, g22, g12 = (Pu * Pu).sum(1), (Pv * Pv).sum(1), (Pu * Pv).sum(1)
        tr, dt = g11 + g22, g11 * g22 - g12 * g12
        disc = np.sqrt(np.maximum(tr * tr / 4.0 - dt, 0.0))
        lmax, lmin = tr / 2.0 + disc, np.maximum(tr / 2.0 - disc, 1e-30)
        r = np.where(good, np.sqrt(lmax / lmin), 1e3)
        r = np.minimum(r, 1e3)
        keep = area > 1e-9
        r, a = r[keep], area[keep]
        big = r > ratio
        out[o.name] = dict(total_m2=float(a[big].sum()), single_m2=float(a[big].max()) if big.any() else 0.0, worst=float(r.max()) if len(r) else 0.0,
                           n_big=int(big.sum()), n=int(len(r)), worst_area=float(a[int(np.argmax(r))]) if len(r) else 0.0, area_total=float(a.sum()))
    return out


LIMIT_TOTAL_M2, LIMIT_SINGLE_M2 = 15.0, 10.0          # the verifier's GROUND_UV_LOCAL_SMEAR limits (every collision-prefix mesh)
OWN_M2 = 0.5                                          # the meshes the hole script authors the UV of (everything but the library-UV'd TERRAIN wall) may keep at most this much area above 4:1


def verdict(st):
    """(ok, text). ok = every mesh within the verifier's limits AND every non-TERRAIN play surface <= OWN_M2 above 4:1 (no single triangle above OWN_M2 either)."""
    bad = []
    for k, v in st.items():
        if v["total_m2"] > LIMIT_TOTAL_M2 or v["single_m2"] > LIMIT_SINGLE_M2:
            bad.append(f"{k}: {v['n_big']} tri > {RATIO:g}:1 cover {v['total_m2']:.1f} m2 (largest {v['single_m2']:.1f}, worst {v['worst']:.0f}:1) over the verifier's {LIMIT_TOTAL_M2:g} / {LIMIT_SINGLE_M2:g}")
        elif not k.startswith("TERRAIN") and (v["total_m2"] > OWN_M2 or v["single_m2"] > OWN_M2):
            bad.append(f"{k}: {v['n_big']} tri > {RATIO:g}:1 cover {v['total_m2']:.1f} m2 (largest {v['single_m2']:.1f}, worst {v['worst']:.0f}:1) over this build's {OWN_M2:g} m2")
    own = {k: v for k, v in st.items() if not k.startswith("TERRAIN")}
    ter = {k: v for k, v in st.items() if k.startswith("TERRAIN")}
    txt = (f"{len(st)} play-surface meshes: above {RATIO:g}:1 the hole-authored ones ({', '.join(sorted(own))}) cover {sum(v['total_m2'] for v in own.values()):.2f} m2 in all (limit {OWN_M2:g}), "
           f"worst {max((v['worst'] for v in own.values()), default=0):.1f}:1; TERRAIN (library wall UV, hidden by the skin) {sum(v['total_m2'] for v in ter.values()):.1f} m2 (largest {max((v['single_m2'] for v in ter.values()), default=0):.1f}, verifier limit {LIMIT_TOTAL_M2:g} / {LIMIT_SINGLE_M2:g})")
    return not bad, ("; ".join(bad) if bad else txt)
