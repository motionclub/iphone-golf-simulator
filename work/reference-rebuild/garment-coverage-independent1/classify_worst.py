"""Classify existing worst plates without another catalog geometry run."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from collections import deque
sys.path.insert(0,str(Path(__file__).parent));from audit import outside,SIZE,W

def classify(p):
    a=np.array(Image.open(p))
    original=np.all(a[45:45+SIZE,:SIZE]==190,axis=2)
    kept=np.all(a[45:45+SIZE,SIZE:SIZE*2]==190,axis=2)
    # Captions sit in the top35px and are excluded from this image-only replay.
    original[:35]=True;kept[:35]=True
    lost=original&~kept;ext=outside(kept);enclosed=lost&~ext
    visited=np.zeros_like(kept);components=[]
    for y,x in zip(*np.where(enclosed)):
        if visited[y,x]:continue
        queue=deque([(int(y),int(x))]);visited[y,x]=True;pixels=[];baseline_hole=False
        while queue:
            yy,xx=queue.popleft();pixels.append((yy,xx))
            if not original[yy,xx]:baseline_hole=True
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    ny,nx=yy+dy,xx+dx
                    if (dy or dx) and 0<=ny<SIZE and 0<=nx<SIZE and not visited[ny,nx] and not kept[ny,nx] and not ext[ny,nx]:
                        visited[ny,nx]=True;queue.append((ny,nx))
        ys,xs=zip(*pixels)
        components.append({'kind':'existing-background-opening-enlarged' if baseline_hole else 'entirely-new-enclosed-background-hole',
                           'backgroundComponentPixels':len(pixels),
                           'maskAttributablePixels':sum(lost[yy,xx] for yy,xx in pixels).item(),
                           'bbox':[min(xs),min(ys),max(xs),max(ys)]})
    return {'externalEdgeContractionPixels':int((lost&ext).sum()),
            'enclosedChangePixels':int(enclosed.sum()),
            'entirelyNewEnclosedHoleCount':sum(x['kind']=='entirely-new-enclosed-background-hole' for x in components),
            'components':components}

report={}
for sport in ('tennis','golf'):
    result=json.loads((W/f'{sport}-coverage-report.json').read_text());rows=[]
    for row in result['worst']:
        rows.append({'sample':row['sample'],'view':row['view'],'plate':row['plate'],**classify(Path(row['plate']))})
    report[sport]=rows
(W/'worst-region-classification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
