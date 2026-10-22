import csv,json,sys
from pathlib import Path
p=Path(sys.argv[1]);r=list(csv.DictReader((p/'trace.csv').open()))
result={}
for key in ['ball_exclusion','reset_reason']:
 out=[]
 for x in r:
  reason=x[key];f=int(x['frame'])
  if not reason:continue
  if out and out[-1]['reason']==reason and out[-1]['last']+1==f:out[-1]['last']=f
  else:out.append({'first':f,'last':f,'reason':reason})
 result[key]=out
(p/'excluded-ranges.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
