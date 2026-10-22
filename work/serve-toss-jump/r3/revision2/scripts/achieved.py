"""achieved.py <scripts dir with serve_new.py> <male|female> : solve that Serve and print the ACHIEVED racket shaft / face (stance frame, az/el deg) and the commanded ones per frame"""
import sys, numpy as np
sd, tag = sys.argv[1], sys.argv[2]
sys.path.insert(0, sd)
import loco, kin, clipkit, clips as CL, serve_new
hero = loco.Hero(tag); S = hero.S; S.ready['gaze'] = None
d = serve_new.serve(S, hero); d = CL.limit_reach(d, S)
clip = clipkit.Clip(d, S.ready); clip.track(S); S.reset()
def azel(v):
    v = np.asarray(v, float); v = v / np.linalg.norm(v)      # (r, f, u)
    return np.degrees(np.arctan2(v[0], v[1])), np.degrees(np.arcsin(v[2]))
for fi, t in enumerate(clip.frame_times()):
    if (10 <= fi <= 20) or fi in (24, 30, 36, 40):
        P = clip.params(t); b, h, info = S.solve(P)
        sa, fa = azel(info['shaft_a']), azel(info['face_a'])
        print('f%2d t%.2f ACHIEVED shaft az %6.1f el %5.1f | face az %6.1f el %5.1f   Rwrist swing %5.1f twist %6.1f' % (fi, t, sa[0], sa[1], fa[0], fa[1], info.get('R_wrist_swing_deg', 0), info.get('R_wrist_twist_deg', 0)))
