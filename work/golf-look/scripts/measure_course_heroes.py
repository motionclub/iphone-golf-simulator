"""Measure exact proof material masks; empty regions are unmeasured, never PASS."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
D=Path(sys.argv[1]);rows=[]
def linear(c):return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def erode(m):
    result=m.copy()
    for dy in [-1,0,1]:
        for dx in [-1,0,1]:result &= np.roll(np.roll(m,dy,0),dx,1)
    result[:1]=False;result[-1:]=False;result[:,:1]=False;result[:,-1:]=False
    return result
for p in sorted(D.glob('*_semantic.png')):
    if p.name.endswith('_shoes_semantic.png'): continue
    source=p.with_name(p.name.replace('_semantic',''))
    rgb=np.asarray(Image.open(source).convert('RGB'))
    ids=np.asarray(Image.open(p).convert('RGB'))
    r={'file':source.name,'mask':p.name,'regions':{}}
    for name,col in [('skin',[255,0,0]),('polo',[0,255,0]),('trim',[0,0,255]),('eyes',[255,255,0])]:
        m=erode(np.max(np.abs(ids.astype(int)-np.array(col)),axis=-1)<=3);v=rgb[m]
        if not len(v):r['regions'][name]={'pixels':0,'status':'FAIL/unmeasured'};continue
        y=linear(v/255.)@np.array([.2126,.7152,.0722])
        f=np.where(y>(6/29)**3,np.cbrt(y),y/(3*(6/29)**2)+4/29)
        lab=116*f-16
        r['regions'][name]={'pixels':len(v),'mean_Lstar':float(lab.mean()),'median_Lstar':float(np.median(lab)),
                'any_channel_255_percent':float(np.any(v==255,axis=1).mean()*100),
                'any_channel_ge250_percent':float(np.any(v>=250,axis=1).mean()*100)}
    rows.append(r)
out=D/'hero_pixel_measures.json';out.write_text(json.dumps({'clip_definitions':'255 is actual 8-bit saturation; >=250 retained as stricter near-clip diagnostic',
        'method':'exact unlit material identities, 1px erosion; CIE L* from linear sRGB luminance, no brightness-selected pixels','rows':rows},indent=2)+'\n')
for r in rows:
    if '_chest' in r['file']:print(r['file'],{n:{k:v for k,v in d.items() if k in ['pixels','median_Lstar','any_channel_255_percent']} for n,d in r['regions'].items()})
