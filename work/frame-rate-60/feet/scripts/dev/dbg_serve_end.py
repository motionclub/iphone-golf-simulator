import sys, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet/scripts')
import loco, clipkit, clips as CL, serve_new, kin
hero = loco.Hero('male'); S = hero.S; S.ready['gaze'] = None
d = serve_new.serve(S, hero); d = CL.limit_reach(d, S)
clip = clipkit.Clip(d, S.ready)
for t in (2.30, 2.50):
    P = clip.params(t)
    print('t', t, {k: (np.round(v,3).tolist() if hasattr(v,'__len__') else v) for k,v in P.items() if k in ('pel','pel_rot','lf_foot','rf_foot','lf_lift','rf_lift','lf_heel','rf_heel','lf_yaw','rf_yaw')})
    S.reset(); b,h,i = S.solve(P)
    Q,Pos = hero.rig.fk(b,h)
    for s in 'LR':
        hip = Pos[hero.rig.idx[('Left' if s=='L' else 'Right')+'UpperLeg']]; an = i['lf_ankle' if s=='L' else 'rf_ankle']
        print('  ', s, 'hip', np.round(hip,3), 'ankle', np.round(an,3), 'dist %.3f' % np.linalg.norm(an-hip), 'max reach %.3f' % np.sqrt(S.t_len**2+S.s_len**2+2*S.t_len*S.s_len*np.cos(np.radians(9)))) 
    print('   drop', i.get('pelvis_auto_drop'), 'hips z', Pos[hero.rig.idx['Hips']][2])
