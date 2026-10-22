import sys, numpy as np
sys.path.insert(0,'.')
import loco, kin, clipkit, clips as CL, serve_new
tag=sys.argv[1]
hero=loco.Hero(tag); S=hero.S; S.ready['gaze']=None
d=serve_new.serve(S,hero); d=CL.limit_reach(d,S)
clip=clipkit.Clip(d,S.ready); clip.track(S); S.reset()
for fi,t in enumerate(clip.frame_times()):
    if not (6<=fi<=40 and fi%2==0): continue
    P=clip.params(t); b,h,info=S.solve(P)
    print('f%2d t%.2f shaft_err %5.1f face_err %5.1f  Rwrist swing %5.1f twist %6.1f clamp %4.1f  R_elbow_flex %5.1f R_arm_short %.3f' % (fi,t,info.get('shaft_err_deg',-1),info.get('face_err_deg',-1),info.get('R_wrist_swing_deg',0),info.get('R_wrist_twist_deg',0),info.get('R_wrist_clamp_deg',0),info.get('R_elbow_flex_deg',0),info.get('R_arm_short',0)))
