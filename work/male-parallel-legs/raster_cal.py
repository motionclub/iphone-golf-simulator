import sys; sys.path.insert(0,'.')
import raster
from raster import *
V=np.load('data/V_start.npy')
import json
bl=json.load(open('proof/s0/sil.json')); print('blender:',bl)
base_project=raster.project
for dx,dy in ((0,0),(-0.5,-0.5),(0.5,0.5),(-0.5,0.5),(0.5,-0.5),(0,-0.5),(-0.5,0)):
    def proj(V,v,dx=dx,dy=dy):
        px,py=base_project(V,v); return px+dx,py+dy
    raster.project=proj
    r=metrics(V,('bald_front','bald_back'))
    print(dx,dy,'front %.3f back %.3f | legs %.3f %.3f'%(r['bald_front']['total'],r['bald_back']['total'],r['bald_front']['leg'],r['bald_back']['leg']))
