"""Repack only UV coordinates; preserve source vertices, triangles, normals and roles."""
from pathlib import Path
import sys,json
import numpy as np
W=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(W/'python-deps'))
import xatlas
rows=[]
for path in sorted((W/'export/kit_v2').glob('*_Kit_*.npz')):
 if len(sys.argv)>1 and not path.stem.startswith(sys.argv[1]+'_'):continue
 if len(sys.argv)>2 and not path.stem.endswith('_'+sys.argv[2]):continue
 d=dict(np.load(path));p=d['P'];tri=d['tri'];loops=d['triloops']
 size=2048 if path.stem.endswith('_Top') else 512 if any(s in path.stem for s in ['Head','Glove']) else 1024
 a=xatlas.Atlas();a.add_mesh(p.astype(np.float32),tri.astype(np.uint32))
 c=xatlas.ChartOptions();c.max_iterations=4;c.fix_winding=True
 k=xatlas.PackOptions();k.resolution=size;k.padding=max(3,round(size*6/1024));k.bruteForce=True;k.rotate_charts=True
 a.generate(chart_options=c,pack_options=k)
 mapping,indices,uv=a[0]
 assert np.array_equal(mapping[indices],tri),'Atlas changed triangle order'
 # Preserve loop indices and every geometry channel. Blender FBX receives the
 # same loop UVs from the associated NPZ in apply_golf_uv.py.
 d['uv'][loops.ravel()]=uv[indices.ravel()]
 area3=np.linalg.norm(np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]]),axis=1).sum()*.5
 u=d['uv'][loops];ab=u[:,1]-u[:,0];ac=u[:,2]-u[:,0];area2=np.abs(ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0]).sum()*.5
 density=float(np.sqrt(area2/area3)*size/100)
 if path.stem.endswith('_Top') and density>18:
  factor=18/density;d['uv']=(d['uv']-.5)*factor+.5;area2*=factor*factor
 np.savez_compressed(path,**d)
 row=dict(piece=path.stem,width=a.width,height=a.height,occupancy=float(area2),densityPxCm=float(np.sqrt(area2/area3)*size/100),charts=a.chart_count,gutterPixels=k.padding)
 rows.append(row);print(row,flush=True)
(W/'data/uv_atlas_final.json').write_text(json.dumps(rows,indent=2)+'\n')
