from pathlib import Path
import csv,json,math
import numpy as np
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm')

def load(p):
 return list(csv.DictReader((p/'trace.csv').open()))
def val(r,k): return float(r.get(k,0) or 0)
def xyz(r,n): return np.array([val(r,n+'_'+x) for x in 'xyz'])
def walk(rows): return [r for r in rows if abs(val(r,'speed'))>.2 and (r['phase']=='PlayerServeHold' or r['phase']=='OpponentServe') and val(r,'prepare')<=.001]
def measure(rows):
 if not rows:return {}
 w=max(rows,key=lambda r:val(r,'deepest_mm'))
 return dict(frames=len(rows),depth_mm=val(w,'deepest_mm'),frame=int(w['frame']),inside_share_at_depth_pct=val(w,'inside_pct'),inside_share_max_pct=max(val(r,'inside_pct') for r in rows),bone=w['worst_bone'],ball_palm_max_cm=100*max(val(r,'ball_palm_m') for r in rows),ball_inside_frames=sum(int(r['ball_inside_body']) for r in rows),game_visible_pct=100*sum(int(r['game_visible']) for r in rows)/len(rows),front_visible_pct=100*sum(int(r['front_visible']) for r in rows)/len(rows),elbow_min_deg=min(val(r,'elbow_flexion') for r in rows),elbow_max_deg=max(val(r,'elbow_flexion') for r in rows),length_delta_mm=max(val(r,'length_delta_mm') for r in rows),step_cm=100*max(val(r,'hand_step_m') for r in rows),speed_change=max(val(r,'hand_speed_change') for r in rows),palm_trunk_clearance_min_cm=100*min(val(r,'palm_trunk_clearance_m') for r in rows),hip_lateral_min_cm=100*min(val(r,'hip_lateral_m') for r in rows),hip_lateral_max_cm=100*max(val(r,'hip_lateral_m') for r in rows),wrist_above_hips_max_cm=100*max(val(r,'wrist_above_hips_m') for r in rows))

def comparison(before,after,segments=('control',)):
 # Compare every stationary control frame, not a hand-picked pose.
 b={int(r['frame']):r for r in before if r['segment'] in segments}
 a={int(r['frame']):r for r in after if r['segment'] in segments}
 common=sorted(set(b)&set(a)); result=dict(control_frames=len(common))
 for name in ['palm','ball','strings']:
  result[name+'_max_delta_cm']=100*max((float(np.linalg.norm(xyz(a[i],name)-xyz(b[i],name))) for i in common),default=float('inf'))
 angles=[]
 for i in common:
  for name in ['upper','lower','hand']:
   q=np.array([val(a[i],name+'_q'+k) for k in 'xyzw']);r=np.array([val(b[i],name+'_q'+k) for k in 'xyzw']);q/=np.linalg.norm(q);r/=np.linalg.norm(r)
   angles.append(math.degrees(2*math.acos(min(1,abs(float(np.dot(q,r)))))))
 result['arm_max_delta_deg']=max(angles,default=float('inf'))
 result['PASS']=bool(common) and max(result[n+'_max_delta_cm'] for n in ['palm','ball','strings'])<=1 and result['arm_max_delta_deg']<=2
 return result

all_results={}
for p in sorted((root/'after').glob('*/completed.json')):
 run=p.parent; before=root/'before'/run.name
 if not (before/'completed.json').exists():continue
 ar=load(run);br=load(before);w=walk(ar)
 active=[r for r in ar if r['segment'].startswith(('walk','plant','tap'))]
 if run.name.startswith('opponent-'): active=[r for r in ar if r['segment']!='control' and r['phase']=='OpponentServe' and val(r,'routine_time')<2.2]
 pre=[r for r in ar if r['phase']=='PlayerServeHold']
 if run.name.startswith('opponent-'): pre=[r for r in ar if r['phase']=='OpponentServe' and val(r,'routine_time')<2.2]
 m=measure(w); s=measure(active); pre_m=measure(pre)
 g={}
 g['G1']=bool(s) and s['depth_mm']<=3 and s['inside_share_max_pct']==0
 g['G2']=bool(pre_m) and pre_m['ball_palm_max_cm']<=3.5 and pre_m['ball_inside_frames']==0
 g['G3']=bool(m) and m['game_visible_pct']>=95 and m['front_visible_pct']==100
 g['G4']=bool(m) and m['length_delta_mm']<=.1 and m['elbow_min_deg']>=15 and m['elbow_max_deg']<=60 and m['palm_trunk_clearance_min_cm']>=8 and m['wrist_above_hips_max_cm']<=0
 g['G5']=bool(s) and s['step_cm']<=3 and s['speed_change']<=.6
 c=comparison(br,ar)
 serve=comparison(br,ar,('serve',)) if not run.name.startswith('opponent-') else c
 bw={int(r['frame']):r for r in br}
 length_change=1000*max((abs(val(r,k)-val(bw[int(r['frame'])],k)) for r in ar for k in ['upper_length_m','lower_length_m']),default=float('inf'))
 m['before_after_length_delta_mm']=length_change
 g['G4']=g['G4'] and length_change<=.1
 def right(rows):
  return [r for r in walk(rows) if val(r,'speed')>0]
 rb=measure(right(br)); ra=measure(right(ar)); no_worse=False
 if rb and ra:
  no_worse=all(ra[k]<=rb[k]+1e-5 for k in ['depth_mm','inside_share_max_pct','ball_palm_max_cm','ball_inside_frames','step_cm','speed_change']) and all(ra[k]+1e-5>=rb[k] for k in ['game_visible_pct','front_visible_pct'])
 g['G6']=c['PASS'] and serve['PASS'] and no_worse
 blends=[]; start=None
 for r in ar:
  v=val(r,'carry_blend')
  if start is None and 0<v<1 and int(r['frame'])>0:
   prev=ar[int(r['frame'])-1] if int(r['frame'])<len(ar) else r
   if val(prev,'carry_blend')>=.999:start=val(r,'t')-1/60
  elif start is not None and v<=.001:
   blends.append(val(r,'t')-start);start=None
 if blends:g['G5']=g['G5'] and all(.15-1e-5<=v<=.30+1e-5 for v in blends)
 meta=json.loads((run/'input.json').read_text()) if (run/'input.json').exists() else {}
 all_results[run.name]=dict(before_walk=measure(walk(br)),before_left=measure([r for r in walk(br) if val(r,'speed')<0]),after_walk=m,turn_plant=s,pre_toss=pre_m,pre_toss_without_controls=measure([r for r in pre if r['segment']!='control']),control_comparison=c,serve_comparison=serve,before_right=rb,after_right=ra,right_no_worse=no_worse,walk_to_hold_seconds=blends,gates=g,input=meta)
(root/'report/matrix.json').write_text(json.dumps(all_results,indent=2))
for name,r in all_results.items():
 print(name,' '.join(k+':'+('PASS' if v else 'FAIL') for k,v in r['gates'].items()),'walking_mm',r['after_walk'].get('depth_mm'),'all_transition_mm',r['turn_plant'].get('depth_mm'))
