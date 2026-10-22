from pathlib import Path
import csv,json,math,sys
P=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=P/'work/serve-walk-arm';stage=sys.argv[1];out=W/'report_r2'
def read(p):return list(csv.DictReader(p.open()))
def n(x,k):return float(x[k])
def pre(x,role):return x['phase']=='PlayerServeHold' if role=='player' else x['phase']=='OpponentServe' and n(x,'routine_time')<2.2
def first_release(r,role):
 for i in range(1,len(r)):
  if pre(r[i-1],role) and not pre(r[i],role) and (r[i]['phase']=='PlayerServeToss' if role=='player' else r[i]['phase']=='OpponentServe'):return i
 return None
def peak(r,k):
 if not r:return None
 x=max(r,key=lambda x:n(x,k));return {'value':n(x,k),'frame':int(x['frame']),'segment':x['segment'],'phase':x['phase']}
def vis(r,k):return 100*sum(int(x[k]) for x in r)/len(r) if r else None
def ranges(r,k):
 out=[]
 for x in r:
  reason=x[k];f=int(x['frame'])
  if not reason:continue
  if out and out[-1]['reason']==reason and out[-1]['last']+1==f:out[-1]['last']=f
  else:out.append({'first':f,'last':f,'reason':reason})
 return out
results={}
for p in sorted((W/stage).glob('*/trace.csv')):
 if not (p.parent/'completed.json').exists():continue
 name=p.parent.name;role=name.split('-')[0];r=read(p);bpath=W/'before_r2_final'/name/'trace.csv';b=read(bpath) if bpath.exists() else []
 ps=[x for x in r if pre(x,role)];f=first_release(r,role);bs=first_release(b,role) if b else None
 # Cover the first 0.2 seconds of EVERY toss start, including Refeed and later opponent points.
 releases=[i for i in range(1,len(r)) if pre(r[i-1],role) and not pre(r[i],role) and (r[i]['phase']=='PlayerServeToss' if role=='player' else r[i]['phase']=='OpponentServe')]
 start_scope={j for i in releases for j in range(i,min(i+13,len(r)))}
 scoped=[x for i,x in enumerate(r) if pre(x,role) or i in start_scope]
 held=[x for x in r if x['in_hand']=='1'];carry=[x for x in ps if abs(n(x,'speed'))>.2 and n(x,'prepare')<=.001]
 sm=[x for x in scoped if not x['reset_reason']];ik=[x for x in r if n(x,'tossWeight')>.001 and not x['reset_reason']]
 marker='wrist_above_belt_m' if 'wrist_above_belt_m' in r[0] else 'wrist_above_hips_m'
 d={'complete':(p.parent/'completed.json').exists(),'frames':len(r),'scope_frames':len(scoped),'carry_frames':len(carry),'G1_mm':peak(scoped,'deepest_mm'),'G1_inside_vertices':peak(scoped,'inside_count'),'G2_m':peak(held,'ball_palm_m'),'G3':{k:vis(carry,k) for k in ['game_visible','front_visible','side_visible']},'G4_elbow': [min(n(x,'elbow_flexion') for x in carry),max(n(x,'elbow_flexion') for x in carry)] if carry else None,'G4_belt_marker':marker,'G4_wrist_above_belt_m':peak(carry,marker),'G5_step_m':peak(sm,'hand_step_m'),'G5_delta_speed':peak(sm,'hand_speed_change'),'all_IK_step_m':peak(ik,'hand_step_m'),'all_IK_delta_speed':peak(ik,'hand_speed_change'),'excluded_ranges':{k:ranges(r,k) for k in ['ball_exclusion','reset_reason']},'G7_root_target_equal_pct':100*sum(x['root_frame']==x['target_frame']==x['unity_frame'] for x in ik)/len(ik) if ik else 0}
 if f is not None and bs is not None:
  delta={k:math.dist([n(r[f],k+'_'+a) for a in 'xyz'],[n(b[bs],k+'_'+a) for a in 'xyz'])*1000 for k in ['wrist','palm','elbow','ball']}
  contact=lambda rows: next((int(x['frame']) for x in rows if x['phase']=='Rally'),None)
  d['G6_release']={'candidate_frame':int(r[f]['frame']),'baseline_frame':int(b[bs]['frame']),'pose_delta_mm':delta,'candidate_first_rally_frame':contact(r),'baseline_first_rally_frame':contact(b)}
 gates={'G1':bool(scoped) and d['G1_mm']['value']==0 and d['G1_inside_vertices']['value']==0,'G2':bool(held) and d['G2_m']['value']<=.035,'G3':not carry or d['G3']['game_visible']>=90 and d['G3']['front_visible']>=95 and d['G3']['side_visible']>=95,'G4':not carry or d['G4_elbow'][0]>=15 and d['G4_elbow'][1]<=60 and d['G4_wrist_above_belt_m']['value']<=0,'G5':bool(sm) and d['G5_step_m']['value']<=.03 and d['G5_delta_speed']['value']<=.6,'G7':d['G7_root_target_equal_pct']==100}
 # Also retain the stricter entire-IK result; no post-reach motion is removed from the trace.
 gates['G5_ALL_IK']=bool(ik) and d['all_IK_step_m']['value']<=.03 and d['all_IK_delta_speed']['value']<=.6
 if 'G6_release' in d:
  t=d['G6_release'];gates['G6_NO_WALK_RELEASE']=max(t['pose_delta_mm'][k] for k in ['wrist','palm','elbow'])<=5 and t['candidate_frame']==t['baseline_frame'] and t['candidate_first_rally_frame']==t['baseline_first_rally_frame']
 if carry:
  directional={direction:[x for x in carry if direction in x['segment']] for direction in ['left','right']}
  metrics={direction:{'depth':peak(q,'deepest_mm')['value'],'ball_palm':peak([x for x in q if x['in_hand']=='1'],'ball_palm_m')['value'],'game':vis(q,'game_visible'),'front':vis(q,'front_visible'),'side':vis(q,'side_visible'),'elbow_range_violation':max(0,15-min(n(x,'elbow_flexion') for x in q),max(n(x,'elbow_flexion') for x in q)-60),'belt_violation':max(0,max(n(x,marker) for x in q)),'step':peak([x for x in q if not x['reset_reason']],'hand_step_m')['value'],'delta_speed':peak([x for x in q if not x['reset_reason']],'hand_speed_change')['value']} for direction,q in directional.items() if q}
  d['directional_metrics']=metrics
  if len(metrics)==2:
   left,right=metrics['left'],metrics['right'];gates['G6_RIGHT_NO_WORSE']=all(right[k]>=left[k] for k in ['game','front','side']) and all(right[k]<=left[k]+(4e-6 if k=='step' else 2e-4 if k=='delta_speed' else 1e-6) for k in ['depth','ball_palm','elbow_range_violation','belt_violation','step','delta_speed'])
 d['gates']=gates;results[name]=d
(out/(stage+'-matrix.json')).write_text(json.dumps(results,indent=2))
for name,d in results.items():print(name,d['frames'],'complete',d['complete'],'FAILED',[k for k,v in d['gates'].items() if not v], 'depth',d['G1_mm'],'step',d['G5_step_m'],'delta',d['G5_delta_speed'])
