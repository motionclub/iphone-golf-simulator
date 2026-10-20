import sys
sys.path.insert(0,'work/reference-rebuild/golf-garment-panel1');from common import *
from mathutils import Vector
from mathutils.bvhtree import BVHTree
for sex in ('Male','Female'):
 report=json.loads((W/'source-report.json').read_text())[sex];name=report['worst'][0];q=np.load(W/(name+'.npz'));p=json.loads((W/f'Panel_{sex}.json').read_text());base=p['originalVertexCount'];v=q['body'];tri=q['bodyTriangles'];bvh=BVHTree.FromPolygons([Vector(v) for v in v],[tuple(t) for t in tri],all_triangles=True);rows=[]
 for i,pv in enumerate(q['after'][base:]):
  h,n,f,d=bvh.find_nearest(Vector(pv));s=float((Vector(pv)-h).dot(n));
  if s<-.003:rows.append((s,i,p['sourceBodyBarycentrics'][i]['domain'],pv.tolist()))
 rows.sort();print(sex,name,len(rows),rows[:12]);print('bydomain',{d:sum(t[2]==d for t in rows) for d in ('Left','Right','Waist')})
