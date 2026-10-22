"""P5 preparation: repeatable fabric normal/relief tiles, not garment bakes.

Run with Blender's bundled Python (numpy). Does not reserve fabric IDs or pack
M channels: the final GARMENT_SPEC is owned by prompt 29 and is not yet released.
"""
import json, math, struct, zlib
from pathlib import Path
import numpy as np

W = Path(__file__).resolve().parents[1]
OUT = W / 'maps' / 'fabric_prototypes'
OUT.mkdir(parents=True, exist_ok=True)

def png(path, a):
    a=np.ascontiguousarray(a,dtype=np.uint8);h,w=a.shape[:2]
    colour=0 if a.ndim==2 else 2 if a.shape[2]==3 else 6
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    raw=b''.join(b'\0'+a[j].tobytes() for j in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,colour,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))

n=512;y,x=np.mgrid[0:n,0:n]/n
tau=2*np.pi
rng=np.random.default_rng(3005)
noise=rng.normal(0,1,(n,n))
fields={
    'performance_knit': .010*np.cos(tau*32*x)*np.cos(tau*32*y)+.003*np.sin(tau*64*y),
    'twill': .012*np.sin(tau*32*(x-y))+.003*np.cos(tau*64*x),
    'pleated_twill': .012*np.sin(tau*32*(x-y))+.035*np.cos(tau*6*x),
    'cap_twill': .013*np.sin(tau*28*(x-y))+.004*np.cos(tau*56*y),
    'leather': .0014*noise+.002*np.cos(tau*13*x)*np.sin(tau*11*y),
    'synthetic_leather': .0009*noise+.0015*np.cos(tau*16*x)*np.cos(tau*16*y),
    'rubber': .002*np.cos(tau*10*x)*np.cos(tau*10*y),
}
rows=[]
for name,height in fields.items():
    dx=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))*.5
    dy=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))*.5
    v=np.stack([-dx*32,dy*32,np.ones_like(dx)],axis=-1)
    v/=np.linalg.norm(v,axis=-1,keepdims=True)
    normal=np.uint8(np.clip((v*.5+.5)*255+.5,0,255))
    relief=np.uint8(np.clip((height-height.min())/(height.max()-height.min())*255,0,255))
    png(OUT/f'{name}_N_DRAFT.png',normal);png(OUT/f'{name}_RELIEF_DRAFT.png',relief)
    rows.append(dict(fabric_key='golf.'+name,numeric_id=None,normal=str((OUT/f'{name}_N_DRAFT.png').relative_to(W)),relief=str((OUT/f'{name}_RELIEF_DRAFT.png').relative_to(W)),size=[n,n],normal_space='tangent OpenGL +Y prototype — reconcile with 29',tile_seam_p99_rgb_levels=float(np.percentile(np.abs(normal[0].astype(float)-normal[-1].astype(float)),99)),status='prototype input, not garment AO/cavity/trim/fabric M bake'))

def astc_mips(size,block=6):
    total=0
    while True:
        total+=math.ceil(size/block)**2*16
        if size==1:return total
        size=max(1,size//2)
plan=[('polo',1024),('bottom',1024),('shoe_shared_lr',1024),('glove',512),('headwear',512)]
allocated=sum(2*astc_mips(s) for _,s in plan)
manifest=dict(seed=3005,status='P5 PREPARATION ONLY; GARMENT_SPEC in progress; no final M packing or IDs',fabrics=rows,planned_per_hero=dict(format='ASTC 6x6',mips=True,textures=[dict(garment=k,size=s,maps=['N','M'],bytes=2*astc_mips(s)) for k,s in plan],bytes=allocated,MB=allocated/1e6,MiB=allocated/2**20,limit_MB=6))
(W/'data/fabric_prototypes.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Prepared',len(rows),'fabric tiles. Planned final N+M bytes/hero:',allocated,'— uninstalled/unmeasured')
