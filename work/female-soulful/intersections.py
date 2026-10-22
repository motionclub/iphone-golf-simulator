"""Exact edge/triangle intersection audit of visible skin and garment outer walls.
Broad-phase BVH overlap is followed by segment/triangle tests, not normal rays.
Blender -b --factory-startup --python intersections.py -- HERO [CLIP]
"""
from pathlib import Path
import sys,json,numpy as np
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root.parent/'clothing-v2/py'))
import cv2io,glib as G,correctives_rt as RT
cv2io.DUMP=str(root/'dump-current');hero=cv2io.Hero(sys.argv[sys.argv.index('--')+1]);arg=sys.argv[sys.argv.index('--')+2:];filt=arg[0] if arg else ''
u=root/'out'/hero.id/'unity';cv=np.load(u/'cover.npz');hidden=np.zeros(len(hero.body.pos),bool)
for k in cv.files:hidden|=cv[k]
bt=hero.body.tri[~hidden[hero.body.tri].all(1)];corr=np.load(u/'correctives.npz')

def crosses(a,b):
 # Vectorized Moller-Trumbore with finite segments, including edges of both triangles.
 hit=np.zeros(len(a),bool)
 for first,second in [(a,b),(b,a)]:
  e1=second[:,1]-second[:,0];e2=second[:,2]-second[:,0]
  for k in range(3):
   d=first[:,(k+1)%3]-first[:,k];p=np.cross(d,e2);det=(e1*p).sum(1)
   valid=np.abs(det)>1e-12;inv=np.divide(1,det,out=np.zeros_like(det),where=valid)
   s=first[:,k]-second[:,0];v=(s*p).sum(1)*inv;q=np.cross(s,e1);w=(d*q).sum(1)*inv;t=(e2*q).sum(1)*inv
   hit|=valid&(v>1e-5)&(w>1e-5)&(v+w<1-1e-5)&(t>1e-5)&(t<1-1e-5)
 return hit
pieces={p:np.load(u/(p+'_final.npz')) for p in ['Kit_Top','Kit_Bottom']};result={p:{}for p in pieces}
for clip in hero.clips:
 if filt and filt not in clip['name']:continue
 bf,bones=hero.clip(clip['name'])
 for piece,g in pieces.items():
  gt=g['tri'][g['part']==0];worst={'pairs':0,'frame':-1,'skinTriangles':0}
  for fi in range(0,len(bf),2):
   bp=bf[fi].astype(float);skin=hero.skin_matrices(bones[fi].astype(float));base=g['pos']+(RT.blend(hero,bones[fi].astype(float),corr) if piece=='Kit_Top' else 0);gp=cv2io.lbs(base,g['bi'],g['bw'],skin)
   btree=BVHTree.FromPolygons(bp.tolist(),bt.tolist(),all_triangles=True);gtree=BVHTree.FromPolygons(gp.tolist(),gt.tolist(),all_triangles=True)
   candidates=np.array(btree.overlap(gtree),int).reshape(-1,2)
   if not len(candidates):continue
   pairs=candidates[crosses(bp[bt[candidates[:,0]]],gp[gt[candidates[:,1]]])]
   if len(pairs)>worst['pairs']:
    worst={'pairs':len(pairs),'frame':fi,'skinTriangles':int(len(np.unique(pairs[:,0]))),'restCentre':np.mean(hero.body.pos[bt[np.unique(pairs[:,0])]],axis=(0,1)).tolist()}
  result[piece][clip['name']]=worst
 print(clip['name'],[(p,result[p][clip['name']]['pairs'])for p in pieces],flush=True)
(root/'proof'/('intersections-'+hero.id+('-'+filt if filt else '')+'.json')).write_text(json.dumps(result,indent=2))
