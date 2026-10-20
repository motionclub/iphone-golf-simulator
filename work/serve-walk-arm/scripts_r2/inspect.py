import csv,sys
from pathlib import Path
p=Path(sys.argv[1]);r=list(csv.DictReader((p/'trace.csv').open()))
num=lambda x,k:float(x[k])
scopes={'pre':[x for x in r if x['phase'] in ['PlayerServeHold','OpponentServe'] and (x['phase']!='OpponentServe' or num(x,'routine_time')<2.2)],'carry':[x for x in r if abs(num(x,'speed'))>.2 and x['phase'] in ['PlayerServeHold','OpponentServe']],'all':r}
for name,s in scopes.items():
 print(name,len(s))
 if not s:continue
 for k in ['deepest_mm','inside_count','ball_palm_m','hand_step_m','hand_speed_change','wrist_above_hips_m']:
  vals=s if k!='ball_palm_m' else [x for x in s if x.get('in_hand')=='1']
  if k in ['hand_step_m','hand_speed_change']:vals=[x for x in vals if not x.get('reset_reason')]
  if vals:
   x=max(vals,key=lambda x:num(x,k));print(k,x[k],'@',x['frame'],x['segment'],x['phase'])
 print('elbow',min(num(x,'elbow_flexion') for x in s),max(num(x,'elbow_flexion') for x in s))
 print('vis',*[round(100*sum(num(x,k) for x in s)/len(s),2) for k in ['game_visible','front_visible','side_visible']])
print('top wrist frames')
for x in sorted(scopes['pre'],key=lambda x:num(x,'hand_step_m'),reverse=True)[:12]:
 print(x['frame'],x['phase'],x['segment'],x['hand_step_m'],x['hand_speed_change'],x['deepest_mm'],x['wrist_above_hips_m'],x['elbow_flexion'])
