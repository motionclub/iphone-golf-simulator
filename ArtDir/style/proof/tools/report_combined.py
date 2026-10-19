"""Report the combined hero gates without treating hidden skin as a pass.
Usage: RAW_CAPTURE OUTPUT LOBBY_REFERENCE_METRICS
"""
from pathlib import Path
import json,sys,numpy as np
src,out,lobby=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=True)
rows=json.loads((src/'metrics.json').read_text());refs=json.loads(lobby.read_text())
main=[r for r in rows if not r['shot'].startswith('lookdev_')]
play=[r for r in main if r['shot'].endswith('__a_gameplay')]
faces=[r for r in main if 'L' in r['after']['face']]
fail={k:[] for k in ['faceL','faceAB','lobbyFaceDeltaL','silhouette','darkest5','saturation','detail','shirt']}
for r in main:
    n,m=r['shot'],r['after'];f=m['face'];hero=n.split('__')[0]
    if 'L' in f:
        if not 45<=f['L']<=65:fail['faceL'].append({'shot':n,'L':f['L']})
        if not (10<=f['a']<=20 and 18<=f['b']<=30):fail['faceAB'].append({'shot':n,'a':f['a'],'b':f['b']})
        d=abs(f['L']-refs[hero]['faceLab'][0])
        if d>8:fail['lobbyFaceDeltaL'].append({'shot':n,'deltaL':round(d,2)})
    s=m['shirt']
    if 'L' in s and (s['L']<25 or s.get('hueError',999)>12):fail['shirt'].append({'shot':n,**s})
    if r in play:
        for key,field,ok in [('silhouette','silhouetteDeltaL',lambda v:v>=15),('darkest5','heroDarkest5MeanL',lambda v:3<=v<=12),('saturation','heroSaturationMean',lambda v:v>=.62),('detail','heroDetailRmsL',lambda v:v>=6.8)]:
            if not ok(m[field]):fail[key].append({'shot':n,'value':m[field]})
summary={'source':str(src),'captureCount':len(rows),'mainCaptures':len(main),'gameplay':len(play),'visibleFaces':len(faces),'unmeasurableFaces':len(main)-len(faces),
    'faceLPass':len(faces)-len(fail['faceL']),'faceABPass':len(faces)-len(fail['faceAB']),'lobbyFaceDeltaLPass':len(faces)-len(fail['lobbyFaceDeltaL']),
    'silhouettePass':len(play)-len(fail['silhouette']),'darkest5Pass':len(play)-len(fail['darkest5']),
    'saturationShotPass':len(play)-len(fail['saturation']),'saturationMean':round(float(np.mean([r['after']['heroSaturationMean'] for r in play])),4),
    'detailShotPass':len(play)-len(fail['detail']),'detailMean':round(float(np.mean([r['after']['heroDetailRmsL'] for r in play])),3),
    'detailEstimator':'Lab-L four-neighbour Laplacian RMS at native capture resolution; 6.8 target estimator was unspecified, so comparison is provisional',
    'faceLRange':[min(r['after']['face']['L'] for r in faces),max(r['after']['face']['L'] for r in faces)],
    'visualGate':'PASS' if not any(fail.values()) and len(rows)==344 else 'FAIL',
    'devicePerformance':'UNTESTED — deferred by Adnan','failures':fail}
(out/'combined-gates.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='failures'},indent=2))
