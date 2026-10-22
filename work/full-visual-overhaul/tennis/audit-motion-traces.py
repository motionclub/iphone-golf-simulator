"""Review aid for real EmoteFilm trace.csv files; never self-certifies appearance."""
import argparse,csv,json,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--out',type=Path);args=p.parse_args()
report=[]
def point(s):return tuple(float(x) for x in s.split(';'))
for trace in sorted(args.directory.rglob('trace.csv')):
 rows=list(csv.DictReader(trace.open()))
 if not rows or 'emoteActive' not in rows[0]:continue
 active=[r for r in rows if r['emoteActive']=='True']
 jumps={}
 for key in ['hips','rwrist','lwrist','head']:
  choices=[]
  for before,after in zip(rows,rows[1:]):
   a,b=point(before[key]),point(after[key]);dist=math.dist(a,b)
   choices.append((dist,int(after['frame'])))
  jumps[key]=max(choices,default=(0,0))
 last=rows[-1]
 result={'trace':str(trace),'frames':len(rows),'active_frames':len(active),
  'first_active_time':active[0]['clipTime'] if active else None,
  'last_active_time':active[-1]['clipTime'] if active else None,
  'returned_to_idle':last['emoteActive']=='False' and last['playing'].endswith(('_ReadyIdle','_Idle')),
  'final_grip_to_hand_m':float(last['gripHandDist']),
  'max_grip_to_hand_m':max(float(r['gripHandDist']) for r in rows),
  'min_racket_y_m':min(float(r['racketLowY']) for r in rows),
  'largest_body_jumps_m_and_frame':jumps,
  'review_flag':any(d>.30 for d,f in jumps.values())}
 # Both released props and in-hand motions should end at their carried transform.
 result['numerical_continuity_pass']=bool(active) and result['returned_to_idle'] and result['final_grip_to_hand_m']<.145 and not result['review_flag']
 report.append(result)
out=args.out or args.directory/'motion-trace-review.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2))
print(json.dumps({'files':len(report),'numerical_passes':sum(r['numerical_continuity_pass'] for r in report),'report':str(out)},indent=2))
print('Actual frame strips / films still require visual review; numerical continuity cannot certify arm intersections or acting quality.')
