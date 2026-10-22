"""Explicit FIX_PROMPT gates; masks and PNGs only, never color-thresholded skin.
Detail uses the documented Lab-L four-neighbour Laplacian RMS; original 6.8
threshold did not name an estimator, so it is reported provisionally.
"""
from pathlib import Path
import json,argparse,numpy as np
from PIL import Image
from measure import morph
p=argparse.ArgumentParser();p.add_argument('captures',type=Path);p.add_argument('out',type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
rows=json.loads((a.captures/'metrics.json').read_text());main=[r for r in rows if not r['shot'].startswith('lookdev_')];play=[r for r in main if '__a_gameplay' in r['shot']]
faces=[r for r in main if 'L' in r['after']['face']]
fail={'face':[],'silhouette':[],'darkest5':[]};world=[]
for r in main:
 m=r['after'];n=r['shot']
 if 'L' in m['face'] and not 45<=m['face']['L']<=65:fail['face'].append({'shot':n,'L':m['face']['L']})
 if '__a_gameplay' in n:
  if m['silhouetteDeltaL']<15:fail['silhouette'].append({'shot':n,'dL':m['silhouetteDeltaL']})
  if not 3<=m['heroDarkest5MeanL']<=12:fail['darkest5'].append({'shot':n,'L':m['heroDarkest5MeanL']})
 before=a.captures/'paired-before'/(n+'.png')
 if before.exists():
  ids=np.array(Image.open(a.captures/(n+'.mask.png')).convert('RGB'));mask=morph(ids.max(axis=-1)>200,31,True)
  old=np.array(Image.open(before).convert('RGB')).astype(int);new=np.array(Image.open(a.captures/(n+'.png')).convert('RGB')).astype(int);delta=np.abs(new-old)[~mask]
  world.append({'shot':n,'meanAbsoluteRgb':round(float(delta.mean()),6),'fractionOver2':round(float((delta.max(axis=1)>2).mean()),6)})
summary={'captures':len(main),'gameplay':len(play),'visibleFaces':len(faces),'faceLPass':len(faces)-len(fail['face']),'silhouettePass':len(play)-len(fail['silhouette']),
 'saturationMeanAcrossGameplay':round(float(np.mean([r['after']['heroSaturationMean'] for r in play])),4),
 'darkest5MeanAcrossGameplay':round(float(np.mean([r['after']['heroDarkest5MeanL'] for r in play])),3),
 'darkest5ShotPass':len(play)-len(fail['darkest5']),
 'detailRmsMeanAcrossGameplay':round(float(np.mean([r['after']['heroDetailRmsL'] for r in play])),3),
 'worldMaxMeanAbsoluteRgb':max([x['meanAbsoluteRgb'] for x in world],default=None),'failures':fail,'world':world}
(a.out/'fix-gates.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['failures','world']},indent=2))
