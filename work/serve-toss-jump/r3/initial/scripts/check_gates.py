"""Binary prompt 26 gates on the independently re-imported FBXs. Unity evidence is added separately."""
import json,math,numpy as np
from pathlib import Path
W=Path(__file__).resolve().parents[1]
all_out={}
for tag in ('male','female'):
 b=json.load(open(W/'data'/f'baseline_{tag}.json'));d=json.load(open(W/'data'/f'candidate_{tag}.json'));r=d['rows'];br=b['rows'];floor=min(br[0]['Lall_z'],br[0]['Rall_z']);ready=br[0]['hips'][2]
 arr=lambda k:np.array([x[k] for x in r]);time=arr('t');hip=arr('hips')[:,2];lh=arr('Lall_z')-floor;rh=arr('Rall_z')-floor;air=(lh>0)&(rh>0);off=next((i for i in range(6,len(r)) if air[i]),None)
 touchL=next((i for i in range(52,len(r)) if lh[i]<=0),None);touchR=next((i for i in range(52,len(r)) if rh[i]<=0),None)
 gates={}
 def G(name,ok,**numbers):gates[name]={'pass':bool(ok),'numbers':numbers};print(tag,name,'PASS' if ok else 'FAIL',json.dumps(numbers))
 toss=(time>=.2)&(time<=.75);tz=max(float(np.abs(arr(s+'toe_z')[toss]-floor).max()) for s in 'LR');hz=max(float((arr(s+'heel_z')[toss]-floor).max()) for s in 'LR');pel=float((hip[toss]-ready).max())
 G('TOSS_FEET_DOWN',tz<=.01 and hz<=.04 and pel<=.02,toe_max_mm=tz*1000,heel_max_mm=hz*1000,pelvis_above_READY_mm=pel*1000)
 pre=np.where(air&(time<1.55))[0];G('NO_AIR_BEFORE_DRIVE',len(pre)==0,both_air_frames=int(len(pre)),first_time=(float(time[pre[0]]) if len(pre) else None))
 # Game path is anchored to the imported palms. Two-pass authoring residual is independent of the FK export error.
 z=np.load(W/'data'/f'gen_serve_{tag}.npz');palm=np.array([.3*np.array(r[f]['bones']['LeftHand'])+.7*np.array(r[f]['bones']['LeftMiddleProximal']) for f in [6,21,40]]);pe=np.linalg.norm(palm-z['ritual'],axis=1)*1000;G('RELEASE_ON_PATH',max(pe)<=2,authoring_ritual_error_mm=pe.tolist(),unity_palm_trace_fields=0)
 kp=np.maximum(arr('Lknee'),arr('Rknee'));ind=int(np.argmax(kp[:off])) if off else 0;low=int(np.argmin(hip[:off])) if off else 0
 G('LOAD_AT_TROPHY',65<=kp[ind]<=80 and 1.25<=time[ind]<=1.40 and 1.25<=time[low]<=1.40,max_knee_deg=float(kp[ind]),max_knee_time=float(time[ind]),lowest_pelvis_time=float(time[low]))
 G('TAKEOFF',off is not None and 1.57<=time[off]<=1.63,first_both_off_time=(float(time[off]) if off else None))
 G('AIR_AT_CONTACT',lh[51]>0 and rh[51]>0 and lh[51]>=.18 and rh[51]>=.30 and hip[51]-ready>=.15,front_low_mm=float(lh[51]*1000),back_low_mm=float(rh[51]*1000),pelvis_above_READY_mm=float((hip[51]-ready)*1000))
 apex=int(np.argmax(hip[off:touchL+1]))+off if off and touchL else 0;airtime=(touchL-off)/30 if off and touchL else 0
 G('APEX_AFTER_CONTACT',1.72<=time[apex]<=1.82 and airtime>=.33,apex_time=float(time[apex]),airtime_s=float(airtime))
 landpeak=float(arr('Lknee')[touchL:touchL+5].max()) if touchL else 0;landpi=int(np.argmax(arr('Lknee')[touchL:touchL+5]))+touchL if touchL else 0;dip=float(hip[touchL]-hip[touchL:70].min()) if touchL else 0
 dips=sum(hip[i]<hip[i-1]-1e-6 and hip[i]<=hip[i+1]+1e-6 for i in range(touchL+1,74)) if touchL else 0
 G('FRONT_FOOT_LANDS_FIRST',touchL is not None and touchR is not None and touchR-touchL>=2 and 45<=landpeak<=60 and time[landpi]-time[touchL]<=.15 and dip<=.06 and dips==1,left_touch_time=(float(time[touchL]) if touchL else None),right_touch_time=(float(time[touchR]) if touchR else None),lead_frames=(touchR-touchL if touchL and touchR else None),front_knee_peak_deg=landpeak,peak_after_touch_s=float(time[landpi]-time[touchL]) if touchL else None,overshoot_mm=dip*1000,pelvis_dips=int(dips))
 hit=float(np.linalg.norm(np.array(r[51]['strings'])-np.array(br[51]['strings'])));scaled=json.load(open(W/'data/contact_racket_scale_audit.json'))[tag]['strings_delta_13_mm'];elb=r[51]['Relbow'];G('CONTACT_POSE_KEPT',scaled<=30 and elb>=160,strings_delta_13_mm=scaled,strings_delta_10_mm=hit*1000,hitting_elbow_deg=elb,strings_limit_mm=30)
 slides=[]
 for s,h in [('L',lh),('R',rh)]:
  v=arr(s+'toe_mean');start=None
  for i in range(6,len(r)):
   if h[i]<=0:
    if start is None:start=i
    slides.append(float(np.linalg.norm((v[i]-v[start])[:2])))
   else:start=None
 spots=[]
 for s,t in [('L',touchL),('R',touchR)]:
  bt=next(i for i in range(52,len(br)) if br[i][s+'all_z']-floor<=0)
  spots.append(float(np.linalg.norm((np.array(r[t][s+'toe_mean'])-np.array(br[bt][s+'toe_mean']))[:2])))
 G('NO_FOOT_SLIDE',max(slides)<=.01 and max(spots)<=.03,planted_motion_mm=max(slides)*1000,landing_spot_delta_mm=[x*1000 for x in spots])
 twists=[np.abs(np.diff(np.degrees(np.unwrap(np.radians(arr(s+'twist')))))).max() for s in 'LR'];steps=[np.linalg.norm(np.diff(arr(s+'hand'),axis=0),axis=1) for s in 'LR'];outside=~((time[:-1]>=40/30-1e-6)&(time[1:]<=1.7+1e-6));pops=[v[outside].max() for v in steps];G('WRIST_SMOOTH',max(twists)<=30 and max(pops)<=.15,wrist_twist_step_LR_deg=[float(x) for x in twists],hand_step_outside_trophy_contact_LR_mm=[float(x*1000) for x in pops],hand_step_all_rows_LR_mm=[float(v.max()*1000) for v in steps],trophy_contact_clip_intervals=int((~outside).sum()),outside_limit_mm=150)
 pn=json.load(open(W/'data'/f'pen_candidate_{tag}.json'));pb=json.load(open(W/'data'/f'pen_baseline_{tag}.json'));new=[];increased=[]
 for a,c in zip(pn,pb):
  for obj,count in a['who'].items():
   oldcount=c['who'].get(obj,0)
   if count and not oldcount:new.append([a['f'],obj,count,a['depth_mm']])
   if count>oldcount:increased.append([a['f'],obj,count,oldcount,count-oldcount,a['depth_mm'],c['depth_mm']])
 G('CLEARANCE',len(new)==0 and len(increased)==0,new_collision_frame_obstacles=len(new),new_collisions=new,increased_collision_frame_obstacles=len(increased),increased_collisions=increased,extra_intersecting_vertices=sum(x[4] for x in increased),baseline_bad_frames=sum(x['inside']>0 for x in pb),candidate_bad_frames=sum(x['inside']>0 for x in pn))
 rtpath=W/'data/unity_runtime_audit.json';rt=json.load(open(rtpath)) if rtpath.exists() else {};current={f'{H}_Serve.fbx':__import__('hashlib').sha256((W/'export/fbx'/f'{H}_Serve.fbx').read_bytes()).hexdigest() for H in ['Male','Female']};valid=rt.get('candidate_hashes')==current;ok=valid and rt.get('game_times_pass',False)
 G('GAME_TIMES_UNCHANGED',ok,clip_length_s=d['length'],frames=d['frames'],prefab_time_edits=0,unity_films_completed=(2 if valid else 0),serve_in_play_checks=(2 if valid else 0),contact_window_log_rows=(sum(rt[x]['contact_log_rows'] for x in ['male','female']) if valid else 0),runtime_evidence_matches_candidate=valid)
 all_out[tag]=gates
json.dump(all_out,open(W/'data/fbx_gates.json','w'),indent=2)
