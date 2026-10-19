"""D65 CIELAB medians from linearized sRGB; segmentation masks from scratch-only test.
No colour-based selection of skin or shirts. The mask determines sample membership.
Silhouette: absolute difference of median inner 3px edge L and outer 3px ring L.
"""
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np
import json, argparse, colorsys

def lab(rgb):
    c=rgb.astype(float)/255
    c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
    xyz=np.stack([(.4124564*c[...,0]+.3575761*c[...,1]+.1804375*c[...,2])/.95047,
                  .2126729*c[...,0]+.7151522*c[...,1]+.0721750*c[...,2],
                  (.0193339*c[...,0]+.1191920*c[...,1]+.9503041*c[...,2])/1.08883],axis=-1)
    f=np.where(xyz>(6/29)**3,np.cbrt(xyz),xyz/(3*(6/29)**2)+4/29)
    return np.stack([116*f[...,1]-16,500*(f[...,0]-f[...,1]),200*(f[...,1]-f[...,2])],axis=-1)

def morph(m,size,expand):
    # Binary square morphology via a summed-area table; same edge replication as
    # PIL Min/MaxFilter, without the O(size²) cost for the 31px world exclusion.
    radius=size//2
    padded=np.pad(m.astype(np.int32),radius,mode='edge')
    integral=np.pad(padded.cumsum(0).cumsum(1),((1,0),(1,0)))
    count=integral[size:,size:]-integral[:-size,size:]-integral[size:,:-size]+integral[:-size,:-size]
    return count>0 if expand else count==size*size

def measure(image,mask):
    rgb=np.array(Image.open(image).convert('RGB'));ids=np.array(Image.open(mask).convert('RGB')); ll=lab(rgb)
    hero=ids.max(axis=-1)>200;edge=hero & ~morph(hero,7,False);ring=morph(hero,7,True)&~hero
    out={}
    # Whole-hero metrics use the unlit ID silhouette, with boundaries eroded.
    # Detail: RMS of a four-neighbour Lab-L Laplacian, in L units per pixel at 1600x900.
    # This estimator is explicit: the prompt supplied no definition for its 6.8 target.
    interior=morph(hero,3,False)
    pix=rgb[interior].astype(float)/255
    peak=pix.max(axis=-1);trough=pix.min(axis=-1)
    sat=(peak-trough)/np.maximum(peak,1e-8)
    values=ll[...,0][interior]
    q=np.percentile(values,5)
    lap=4*ll[...,0]-np.roll(ll[...,0],1,0)-np.roll(ll[...,0],-1,0)-np.roll(ll[...,0],1,1)-np.roll(ll[...,0],-1,1)
    out['heroSaturationMean']=round(float(sat.mean()),4)
    out['heroSaturationMedian']=round(float(np.median(sat)),4)
    out['heroDarkest5MeanL']=round(float(values[values<=q].mean()),3)
    out['heroP05L']=round(float(q),3)
    out['heroDetailRmsL']=round(float(np.sqrt(np.mean(lap[interior]**2))),3)
    for name,ch in [('face',0),('shirt',1)]:
        m=(ids[...,ch]>240)&(np.delete(ids,ch,axis=2).max(axis=-1)<10)
        m=morph(m,3,False);count=int(m.sum())
        if count<12:out[name]={'pixels':count,'status':'not visible / insufficient pixels'};continue
        v=np.median(ll[m],axis=0);colour=np.median(rgb[m],axis=0);h,s,_=colorsys.rgb_to_hsv(*(colour/255))
        out[name]={'pixels':count,'L':round(float(v[0]),2),'a':round(float(v[1]),2),'b':round(float(v[2]),2),'hue':round(h*360,2),'saturation':round(s,3),'rgb':[int(x) for x in colour]}
    out['edgeL']=round(float(np.median(ll[...,0][edge])),2);out['ringL']=round(float(np.median(ll[...,0][ring])),2);out['silhouetteDeltaL']=round(abs(out['edgeL']-out['ringL']),2)
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('captures',type=Path);p.add_argument('--before',type=Path);p.add_argument('--output',type=Path);p.add_argument('--incremental',action='store_true');a=p.parse_args();rows=[]
    output=a.output or a.captures/'metrics.json';old={r['shot']:r for r in json.loads(output.read_text())} if a.incremental and output.exists() else {}
    palette={}
    if (a.captures/'palette.tsv').exists():
        for line in (a.captures/'palette.tsv').read_text().splitlines():
            v=line.split('\t');palette[v[0].replace('.mask.png','')]=float(v[1])
    for mask in sorted(a.captures.glob('*.mask.png')):
        name=mask.name.replace('.mask.png','');image=mask.with_name(name+'.png')
        if not image.exists():continue
        if name in old:rows.append(old[name]);continue
        r={'shot':name,'after':measure(image,mask)}
        if a.before and (a.before/(name+'.png')).exists():r['before']=measure(a.before/(name+'.png'),mask)
        if name in palette:
            r['paletteHue']=palette[name]
            for key in ['before','after']:
                if key in r and 'hue' in r[key]['shirt']:r[key]['shirt']['hueError']=round(abs((r[key]['shirt']['hue']-palette[name]+180)%360-180),2)
        rows.append(r)
    output.write_text(json.dumps(rows,indent=2)+'\n')
    for r in rows:
        if '__b_close' in r['shot']:print(r['shot'],r['after']['face'],r['after']['shirt'])
if __name__=='__main__':main()
