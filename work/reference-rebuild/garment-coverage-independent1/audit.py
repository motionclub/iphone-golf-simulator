"""Independent work-only coverage check; does not edit any author/Unity data."""
from pathlib import Path
import json, ctypes, hashlib, argparse, time
import numpy as np
from PIL import Image, ImageDraw

R=Path.cwd(); W=R/'work/reference-rebuild/garment-coverage-independent1'
SIZE=900
lib=ctypes.CDLL(str(W/'raster.dylib'))
lib.raster.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,
                    ctypes.c_int,ctypes.c_bool,ctypes.c_void_p]
lib.exterior.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p]
lib.hits.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,
                  ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p]
def arr(p,k,n): return np.asarray(p[k],dtype=np.float64).reshape(-1,n)
def xf(m,v): return v@m[:3,:3].T+m[:3,3]
def skin(p,v,matrices):
    ids=arr(p,'indices',4).astype(int); weights=arr(p,'weights',4)
    q=np.zeros_like(v)
    for k in range(4):
        m=matrices[ids[:,k]]
        q+=(np.einsum('nij,nj->ni',m[:,:3,:3],v)+m[:,:3,3])*weights[:,k,None]
    return q
def raster(v,t,two=False):
    image=np.zeros((SIZE,SIZE),np.uint8)
    v=np.ascontiguousarray(v,dtype=np.float64)
    t=np.ascontiguousarray(t,dtype=np.int32)
    lib.raster(v.ctypes.data,t.ctypes.data,len(t),SIZE,two,image.ctypes.data)
    return image.astype(bool)
def outside(image):
    image=np.ascontiguousarray(image,dtype=np.uint8);out=np.zeros_like(image)
    lib.exterior(image.ctypes.data,SIZE,out.ctypes.data)
    return out.astype(bool)
def faces_touching(v,t,pixels):
    v=np.ascontiguousarray(v,dtype=np.float64);t=np.ascontiguousarray(t,dtype=np.int32)
    pixels=np.ascontiguousarray(pixels,dtype=np.uint8);out=np.zeros(len(t),np.uint8)
    if pixels.any():lib.hits(v.ctypes.data,t.ctypes.data,len(t),SIZE,pixels.ctypes.data,out.ctypes.data)
    return out.astype(bool)
VIEWS={'front':np.array([[1,0,0],[0,1,0]]),
       'rear':np.array([[-1,0,0],[0,1,0]]),
       'left':np.array([[0,0,-1],[0,1,0]]),
       'right':np.array([[0,0,1],[0,1,0]])}
def project(body,top,basis):
    b=body@basis.T; t=top@basis.T
    lo=t.min(0); hi=t.max(0); centre=(lo+hi)/2
    span=max(.85,float((hi-lo).max())*1.14)
    return (b-centre)*(SIZE/span)+SIZE/2,(t-centre)*(SIZE/span)+SIZE/2,span
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def cases(sport):
    if sport=='golf':
        d=R/'work/reference-rebuild/golf-garment-mask1'
        for sex in ('Male','Female'):
            mask=json.loads((d/f'Mask_{sex}.json').read_text())
            full=json.loads((R/f'proof/reference-rebuild/golf-cloth-control16/poses/{sex.lower()}_Driver_top.json').read_text())
            bottom=next(x for x in full['parts'] if x['name']=='Kit_Bottom')
            for p in sorted(d.glob(sex.lower()+'_*_[0-9][0-9][0-9].npz')):
                q=np.load(p)
                cp=json.loads((R/'proof/reference-rebuild/golf-cloth-control16/matrices'/f'{p.stem}.json').read_text())
                part=next(x for x in cp['parts'] if x['name']=='Kit_Bottom')
                bv=xf(np.array(part.get('rendererToRoot',bottom['rendererToRoot'])).reshape(4,4),skin(bottom,arr(bottom,'vertices',3),arr(part,'skinMatrices',16).reshape(-1,4,4)))
                source={'pose':str(p.relative_to(R)),'mask':str((d/f'Mask_{sex}.json').relative_to(R)),'removedFaceIndices':mask['removedTriangleIndices']}
                yield p.stem,q['body'],q['bodyTriangles'],q['afterBodyTriangles'],q['before'],q['topTriangles'],[(bv,arr(bottom,'triangles',3).astype(int))],source
    else:
        d=R/'proof/reference-rebuild/character-motion-matrices17'
        masks=R/'work/reference-rebuild/garment-weight-transition/mask-check'
        for sex in ('Male','Female'):
            raw=json.loads((d/'poses'/f'{sex.lower()}_intro.json').read_text())
            body,top=raw['parts'][:2]
            bottom=next(x for x in raw['parts'] if x['name']=='Kit_Bottom')
            profile=json.loads((R/f'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_{sex}.json').read_text())
            assert np.max(np.abs(np.array(profile['vertices'])-np.array(top['vertices'])))<3e-7
            triangles=arr(body,'triangles',3).astype(int)
            maskpath=masks/f'BodyMask_{sex.lower()}-current-matrix-canonical.json'
            mask=json.loads(maskpath.read_text()); keep=np.ones(len(triangles),bool)
            keep[np.array(mask['alwaysCoveredFaceIndices'],int)]=False
            assert mask['correspondence']['unmatchedPhysicalFaces']==0
            base=arr(profile,'vertices',3); shapes=[a['shape'] for a in profile['anchors']]
            deltas=np.asarray([a['deltas'] for a in profile['anchors']]).reshape(len(shapes),-1,3)
            for p in sorted((d/'matrices').glob(sex.lower()+'*.json')):
                pose=json.loads(p.read_text()); parts={x['name']:x for x in pose['parts']}
                bpart=parts[body['name']]; tpart=parts['Kit_Top']
                weights=np.array(tpart['shapeWeights'])/100
                sw=np.array([weights[tpart['shapeNames'].index('TailoredSleeve_'+n)] for n in shapes])
                b=xf(arr(bpart,'rendererToRoot',4),skin(body,arr(body,'vertices',3),arr(bpart,'skinMatrices',16).reshape(-1,4,4)))
                t=xf(arr(tpart,'rendererToRoot',4),skin(top,base+np.einsum('s,sni->ni',sw,deltas),arr(tpart,'skinMatrices',16).reshape(-1,4,4)))
                btm=parts['Kit_Bottom']
                bv=xf(arr(btm,'rendererToRoot',4),skin(bottom,arr(bottom,'vertices',3),arr(btm,'skinMatrices',16).reshape(-1,4,4)))
                yield p.stem,b,triangles,triangles[keep],t,arr(top,'triangles',3).astype(int),[(bv,arr(bottom,'triangles',3).astype(int))],{'pose':str(p.relative_to(R)),'mask':str(maskpath.relative_to(R)),'removedFaceIndices':np.where(~keep)[0].tolist()}

def plate(name,view,body,masked,top,top2,span):
    original=body|top; kept=masked|top; off=masked|top2
    panels=[]
    enclosed=(original&~kept)&~outside(kept)
    for label,m,color in [('Original Body + Top',original,(190,190,190)),
                           ('Masked Body + Top',kept,(190,190,190)),
                           ('Lost coverage (magenta)',original,(120,120,120)),
                           ('Top two-sided recovery',off,(160,160,160))]:
        a=np.full((SIZE,SIZE,3),30,np.uint8);a[m]=color
        if label.startswith('Lost'):
            a[original&~kept]=(255,30,170);a[enclosed]=(255,180,25)
        if label.startswith('Top two'):a[(original&~kept)&off]=(30,220,240);a[original&~off]=(255,30,170)
        im=Image.fromarray(a[::-1]);draw=ImageDraw.Draw(im);draw.text((12,12),label,fill=(255,255,255));panels.append(im)
    out=Image.new('RGB',(SIZE*2,SIZE*2+45),(20,20,20))
    for i,p in enumerate(panels):out.paste(p,((i%2)*SIZE,(i//2)*SIZE+45))
    ImageDraw.Draw(out).text((12,12),f'{name} / {view} / {span:.3f}m span / binary pixel-centre coverage, CullBack Body',fill='white')
    path=W/f'{name}_{view}_coverage.png';out.save(path);return str(path.relative_to(R))

def run(sport,limit):
    rows=[];worst=[];started=time.time();ncase=0;face_counts={};mask_hashes={}
    for name,b,bt,bm,t,tt,extras,source in cases(sport):
        if limit and ncase>=limit:break
        removed=np.array(source.pop('removedFaceIndices'),int)
        sex=name.split('_')[0];count=face_counts.setdefault(sex,{'all':np.zeros(len(bt),int),'interior':np.zeros(len(bt),int)})
        mask_hashes[source['mask']]=sha(R/source['mask'])
        for view,basis in VIEWS.items():
            pb,pt,span=project(b,t,basis)
            rb=raster(pb,bt);rm=raster(pb,bm);rt=raster(pt,tt);rt2=raster(pt,tt,True)
            centre=(t@basis.T).min(0)+(t@basis.T).max(0);centre/=2
            for v,tri in extras:
                rp=raster((v@basis.T-centre)*(SIZE/span)+SIZE/2,tri)
                rb|=rp;rm|=rp
            orig=rb|rt;kept=rm|rt;origoff=rb|rt2;keptoff=rm|rt2
            lost=orig&~kept;lostoff=origoff&~keptoff;gain=origoff&~orig
            enclosed=lost&~outside(kept)
            enclosedoff=lostoff&~outside(keptoff)
            count['all'][removed]+=faces_touching(pb,bt[removed],lost)
            count['interior'][removed]+=faces_touching(pb,bt[removed],enclosed)
            yy,xx=np.where(lost)
            row={'sample':name,'view':view,'lostCoveragePixelsCullBack':int(lost.sum()),
                 'lostCoveragePixelsTwoSidedTop':int(lostoff.sum()),
                 'enclosedBackgroundChangePixelsCullBack':int(enclosed.sum()),
                 'enclosedBackgroundChangePixelsTwoSidedTop':int(enclosedoff.sum()),
                 'externalSilhouetteLossPixels':int((lost&~enclosed).sum()),
                 'maskLossRecoveredByTwoSidedTop':int((lost&keptoff).sum()),
                 'originalCoverageGainedByTwoSidedTop':int(gain.sum()),
                 'lostAreaMm2':float(lost.sum()*(span/SIZE*1000)**2),
                 'lostBBoxPixels':[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())] if len(xx) else None,
                 'spanM':span,**source}
            rows.append(row)
            key=int(enclosed.sum())*1000000+int(lost.sum())
            if len(worst)<4 or key>worst[-1][0]:
                if key:row['plate']=plate(name,view,rb,rm,rt,rt2,span)
                worst.append((key,row));worst=sorted(worst,key=lambda x:x[0],reverse=True)[:4]
        ncase+=1
        if ncase%20==0: print(f'{sport} {ncase} poses {time.time()-started:.1f}s',flush=True)
    for sex,count in face_counts.items():
        data={'basis':'Body face index from current-matrix canonical tennis source or control16 golf baseline. Projection overlap only. External silhouette losses may be desirable skin-bulge removal; do not automatically restore these faces. Enclosed-background-change overlap is separately listed; this can be an existing limb gap enlarging. No mask edits.',
              'silhouetteChangeFaceIndices':np.where(count['all']>0)[0].tolist(),
              'silhouetteChangeViewCounts':count['all'][count['all']>0].tolist(),
              'enclosedBackgroundChangeFaceIndices':np.where(count['interior']>0)[0].tolist(),
              'enclosedBackgroundChangeViewCounts':count['interior'][count['interior']>0].tolist()}
        (W/f'{sport}-{sex}-diagnostic-face-indices.json').write_text(json.dumps(data,indent=2)+'\n')
    result={'scope':'Work-only source projection: exact original Top/Bottom and unchanged Body coordinates/weights, triangle-mask only. Four orthographic views at900px; pixel-centre binary coverage, Body/Bottom CullBack; Top CullBack and two-sided control. No display body crop, no Unity/native claim. Mask-attributable external silhouette loss may be intentional removal of clipping skin and requires visual review. Enclosed-background changes are separated by8-connected exterior flood-fill; these include enlargement of existing limb gaps. Entirely new hole components require baseline-component comparison (see worst-region-classification). This cannot certify skin bleed, shading, fold quality, all intervening poses or all perspective views.',
            'sport':sport,'samples':ncase,'views':len(rows),'elapsedSeconds':time.time()-started,
            'viewsWithLostCoverage':sum(r['lostCoveragePixelsCullBack']>0 for r in rows),
            'viewsWithAtLeast10LostPixels':sum(r['lostCoveragePixelsCullBack']>=10 for r in rows),
            'maxLostPixels':max((r['lostCoveragePixelsCullBack'] for r in rows),default=0),
            'maxLostPixelsTwoSidedTop':max((r['lostCoveragePixelsTwoSidedTop'] for r in rows),default=0),
            'maxOriginalTopCullRecovery':max((r['originalCoverageGainedByTwoSidedTop'] for r in rows),default=0),
            'viewsWithEnclosedBackgroundChanges':sum(r['enclosedBackgroundChangePixelsCullBack']>0 for r in rows),
            'maxEnclosedBackgroundChangePixels':max((r['enclosedBackgroundChangePixelsCullBack'] for r in rows),default=0),
            'viewsWithEnclosedBackgroundChangesTwoSidedTop':sum(r['enclosedBackgroundChangePixelsTwoSidedTop']>0 for r in rows),
            'maxEnclosedBackgroundChangePixelsTwoSidedTop':max((r['enclosedBackgroundChangePixelsTwoSidedTop'] for r in rows),default=0),
            'maskHashes':mask_hashes,
            'worst':[r for _,r in worst], 'rows':rows}
    (W/f'{sport}-coverage-report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','worst')},indent=2),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--sport',choices=['golf','tennis','both'],default='both');parser.add_argument('--limit',type=int,default=0);a=parser.parse_args()
    for sport in ('tennis','golf') if a.sport=='both' else [a.sport]:run(sport,a.limit)
