"""Emote_PickUp - after a hole-out: bend at the hips to the cup, scoop the ball with the right hand, rise looking at it, put it in the right
hip pocket, relax.  (Golf only: always the empty-handed variant, the putter is put away like the other hole-out moves.)

Beats (30 fps): settle from the walk, head turns down to the cup (0-8) -> hips back and down, trunk folds, left arm out for balance, trail foot
lifts, right hand reaches down into the cup (8-30) -> fingers close on the ball (30-36) -> rise with the ball, head follows it (38-58) -> hold it
at the chest, a short look (58-62) -> hand to the hip pocket, fingers open (62-74) -> hand out, arms relax, head up (76-99).
HAND_GRAB_FRAME / HAND_POCKET_FRAME are the frames the game attaches / releases the ball (see GolferView.PickUpBall)."""
import numpy as np

import std
from ek import to_char, cvec

NAME = 'Emote_PickUp'
N = 100
GRAB, POCKET = 36, 70


def build(H):
    T = std.Tracks(H, N)
    ka = H.k
    S = lambda v: np.array(v) * ka
    Z = (0, 0, 0)
    LA, RA, CH = 0.92, 0.40, 0.0       # trunk folded ~65 deg: chest-space axes of world down / back (see notes in the PR)

    T['hp'] = T.k3([(0, (0, -0.035, 0.012)), (8, (0, -0.035, 0.012)), (20, (0.0, -0.14, -0.20)), (30, (0.0, -0.22, -0.47)), (38, (0.0, -0.22, -0.47)),
                    (52, (0.0, -0.06, -0.03)), (62, (0.0, -0.035, 0.012)), (N - 1, (0, -0.035, 0.012))])
    T['hb'] = T.k3([(0, (-10, 0, -1)), (8, (-10, 0, -1)), (20, (14, 0, -4)), (30, (30, 0, -6)), (38, (30, 0, -6)), (52, (8, 0, -3)), (62, (-10, 0, -1)),
                    (N - 1, (-10, 0, -1))])
    T.torso([(0, Z), (8, Z), (20, (12, 0, 3)), (30, (36, 0, 5)), (38, (36, 0, 5)), (54, (8, 0, 2)), (62, Z), (N - 1, Z)], lags=(0, 2, 4), split=(0.2, 0.35, 0.45))
    # head: looks at the cup, follows the ball up, a look at it, then eyes up
    T.neckhead([(0, Z), (8, (14, 0, -4)), (20, (-18, 0, -3)), (30, (-34, 0, -4)), (38, (-30, 0, -4)), (54, (30, 0, 8)), (62, (26, 0, 6)), (72, (4, 0, 0)),
                (82, Z), (N - 1, Z)], lags=(2, 4))
    for s, lag in (('r', 0), ('l', 2)):
        T['cl_' + s] = T.k3([(0, Z), (30, (-4, 8, 0)), (38, (-4, 8, 0)), (58, Z), (N - 1, Z)], lag=lag)[:, :2]

    hang_l, hang_r = S([-0.21, 0.06, -0.48]), S([0.22, 0.07, -0.48])
    # left arm: out and back for balance while the trunk is folded, then hangs
    T['wl'] = T.k3([(0, hang_l), (8, hang_l), (20, S([-0.34, 0.14, -0.30])), (30, S([-0.36, 0.30, -0.26])), (40, S([-0.36, 0.30, -0.26])),
                    (56, S([-0.24, 0.12, -0.42])), (66, hang_l), (N - 1, hang_l)])
    T['pl'] = T.k3([(0, S([-0.4, -0.5, -0.1])), (30, S([-0.6, -0.2, 0.0])), (N - 1, S([-0.4, -0.5, -0.1]))])
    # right hand: down to the cup, up to the chest, to the hip pocket, out
    reach = S([0.14, 0.50, -0.165])
    chest = S([0.10, 0.20, -0.28])
    pocket = S([0.18, 0.04, -0.53])
    T['wr'] = T.k3([(0, hang_r), (8, hang_r), (20, S([0.18, 0.36, -0.22])), (GRAB - 6, reach), (GRAB, reach), (GRAB + 2, reach), (52, chest), (60, chest),
                    (POCKET - 4, S([0.17, 0.12, -0.42])), (POCKET, pocket), (POCKET + 6, pocket), (86, hang_r), (N - 1, hang_r)])
    T['pr'] = T.k3([(0, S([0.4, -0.5, -0.1])), (30, S([0.5, -0.1, 0.0])), (52, S([0.6, -0.3, 0.0])), (POCKET, S([0.8, -0.6, 0.0])), (86, S([0.4, -0.5, -0.1])),
                    (N - 1, S([0.4, -0.5, -0.1]))])
    T['kn_r'] = T.k3([(0, (-0.1, 0.1, -0.99)), (8, (-0.1, 0.1, -0.99)), (GRAB - 6, (0.0, LA, -RA)), (GRAB + 2, (0.0, LA, -RA)), (52, (-0.3, 0.7, 0.6)),
                      (60, (-0.3, 0.7, 0.6)), (POCKET, (-0.1, 0.3, -0.95)), (86, (-0.1, 0.1, -0.99)), (N - 1, (-0.1, 0.1, -0.99))])
    T['pa_r'] = T.k3([(0, (-1.0, -0.2, 0.0)), (8, (-1.0, -0.2, 0.0)), (GRAB - 6, (-0.3, -RA, -LA)), (GRAB + 2, (-0.3, -RA, -LA)), (52, (-0.2, -0.6, 0.7)),
                      (60, (-0.2, -0.6, 0.7)), (POCKET, (-1.0, -0.2, 0.0)), (N - 1, (-1.0, -0.2, 0.0))])
    T['curl_r_golf'] = T.k1([(0, -0.5), (GRAB - 8, -0.6), (GRAB - 1, -0.9), (GRAB + 4, 0.85), (60, 0.85), (POCKET - 2, 0.85), (POCKET + 3, -0.4), (86, -0.6), (N - 1, -0.6)])
    T['curl_l'] = T.k1([(0, -0.5), (N - 1, -0.5)])
    # trail (left) foot lifts for balance; weight on the right leg
    T['ank_l'] = T.k3([(0, Z), (14, Z), (30, (0.0, -0.10, 0.04)), (40, (0.0, -0.10, 0.04)), (56, Z), (N - 1, Z)])
    T['heel_l'] = T.k1([(0, 0), (14, 0), (30, 38), (40, 38), (56, 0), (N - 1, 0)])
    T['kp_l'] = T.k3([(0, Z), (30, (-0.05, 0.0, 0.0)), (56, Z), (N - 1, Z)])
    pose = std.pose_fn(H, T, golf=True)
    info = H.info = {}

    def pose_dbg(f):
        pose(f)
        if f in (0, 20, 30, GRAB, 52, POCKET, 86):
            import bpy
            bpy.context.view_layer.update()
            w = H.world_mat('RightHand').translation
            c = to_char(np.array(w) - H.hips0)
            for n, v in zip('rfu', c):
                info['hand_%d_%s' % (f, n)] = v
            uc=np.array(H.world_mat('UpperChest').translation)-H.hips0
            info['trunk_%d_deg'%f]=float(np.degrees(np.arctan2(-uc[1],uc[2])))
            for nm in ('Hips','LeftFoot','RightFoot','LeftHand','RightHand'):
                info['z_%d_%s'%(f,nm)]=float(H.world_mat(nm).translation[2])
            hd = to_char(np.array(H.world_mat('Head').translation) - H.hips0)
            info['head_%d_u' % f] = hd[2]
        return None
    return N, pose_dbg
