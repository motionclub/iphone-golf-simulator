"""Drop zero-area button-pole triangles without moving any source point."""
from pathlib import Path
import json,numpy as np

def clean(folder,hero):
    folder=Path(folder);g=dict(np.load(folder/'Kit_Top_final.npz'));p=g['pos'];t=g['tri']
    area=np.linalg.norm(np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]]),axis=1)*.5
    keep=area>1e-14;removed=int((~keep).sum())
    if not removed:return 0
    if not np.all(g['panel'][~keep]==7):raise RuntimeError('Degenerate cloth surface needs construction repair')
    for key in ['tri','mat','fabric','part','kind','panel']:g[key]=g[key][keep]
    np.savez(folder/'Kit_Top_final.npz',**g)
    manifest=json.loads((folder/'manifest.json').read_text());piece=next(x for x in manifest['pieces']if x['name']=='Kit_Top')
    piece['triangleCount']=len(g['tri']);piece['submeshes'][0]['count']=len(g['tri'])
    (folder/'manifest.json').write_text(json.dumps(manifest))
    data=json.loads((Path(__file__).parent/'dump-polo'/hero/'hero.json').read_text());bones=data['parts'][0]['bones'];remap=np.zeros(len(bones),np.int32)
    for i,name in enumerate(piece['bones']):remap[bones.index(name)]=i
    with (folder/'Kit_Top.bin').open('wb')as f:
        for array in [p.astype(np.float32),g['nrm'].astype(np.float32),g['uv'].astype(np.float32),remap[g['bi']].astype(np.int32),g['bw'].astype(np.float32),g['tri'].astype(np.int32)]:f.write(array.tobytes())
    return removed

if __name__=='__main__':
    root=Path(__file__).parent;print('Removed zero-area button pole faces:',clean(root/'out/GolfKitHero_Female/unity','GolfKitHero_Female'))
