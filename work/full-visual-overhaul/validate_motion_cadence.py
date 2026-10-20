"""Independent actual-frame CSV audit. Strict film traces must sample each game frame."""
from pathlib import Path
import argparse, csv, json, math, sys
from collections import defaultdict
p=argparse.ArgumentParser();p.add_argument('roots',nargs='+');p.add_argument('--strict',action='store_true');p.add_argument('--out',required=True);a=p.parse_args()
results=[]
for root in a.roots:
 for path in sorted(Path(root).rglob('trace.csv')):
  groups=defaultdict(list);errors=[]
  with path.open(newline='') as f:
   reader=csv.DictReader(f);columns=reader.fieldnames or []
   if 'unityFrame' not in columns:errors.append('Missing actual unityFrame column')
   for line,row in enumerate(reader,2):
    if None in row or any(v is None for v in row.values()):errors.append(f'Malformed CSV row {line}');continue
    key=tuple((k,row[k]) for k in ['scenario','role','sex','visitor'] if k in row)
    try:
     actual=int(row['unityFrame']);logical=int(row['frame'])
     t=float(row['t']) if 't' in row else None
     if t is not None and not math.isfinite(t):raise ValueError('nonfinite time')
     groups[key].append((logical,actual,t,line))
    except (KeyError,ValueError) as e:errors.append(f'Invalid clock row {line}: {e}')
  summaries=[]
  for key,rows in groups.items():
   gaps=[];bad=[]
   for before,after in zip(rows,rows[1:]):
    logical=after[0]-before[0];actual=after[1]-before[1]
    if actual<=0:bad.append(f'Non-increasing actual frame at CSV row {after[3]}')
    if a.strict and (logical!=1 or actual!=1):bad.append(f'Film frame skip/repeat at row {after[3]}: logical {logical}, actual {actual}')
    if actual>1:gaps.append({'line':after[3],'frames':actual})
    if a.strict and before[2] is not None and after[2] is not None and abs(after[2]-before[2]-1/60)>.0035:
     bad.append(f'60Hz time mismatch at CSV row {after[3]}')
   errors.extend(bad)
   summaries.append(dict(group=dict(key),rows=len(rows),firstActual=rows[0][1],lastActual=rows[-1][1],gameSeconds=(rows[-1][1]-rows[0][1])/60,skips=gaps[:20]))
  if not groups:errors.append('No auditable trace groups')
  results.append(dict(path=str(path.resolve()),status='FAIL' if errors else 'PASS',strict=a.strict,errors=errors[:30],errorCount=len(errors),groups=summaries))
report=dict(status='PASS' if results and all(r['status']=='PASS' for r in results) else 'FAIL',scope='Actual Unity-frame cadence only; separate visual, trigger, return and physics gates required.',traces=results)
out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],traces=len(results),failed=sum(r['status']=='FAIL' for r in results))))
sys.exit(report['status']!='PASS')
