import numpy as np, sys, json
from PIL import Image
from rast import raster
mesh=sys.argv[1]; out=sys.argv[2]
D=np.load(mesh); V,T=D['V'],D['T']
panels={'q3FL':(30,370,340,680),'q3FR':(340,370,650,680),'q3BL':(650,370,960,680),'q3BR':(960,370,1270,680)}
fit={'q3FL':(-4,171.76,151.0,300),'q3FR':(39,169.19,141.0,298),'q3BL':(151,169.19,146.0,300),'q3BR':(215,169.19,111.0,300)}
tiles=[]
for k,(x0,y0,x1,y1) in panels.items():
    pm=np.array(Image.open(f'data/plate_{k}_mask.png'))[y0:y1,x0:x1]>127
    yaw,sc,tx,ty=fit[k]
    m=raster(V,T,yaw,sc,tx,ty,pm.shape,ss=2)
    o=np.zeros(pm.shape+(3,),np.uint8); o[...]=(30,30,30)
    o[pm&m]=(110,110,110); o[pm&~m]=(60,230,150); o[m&~pm]=(255,90,160)
    iou=(pm&m).sum()/(pm|m).sum(); print(k,'full-body IoU',round(iou,4),'xor',(pm^m).sum())
    tiles.append(Image.fromarray(o).resize((pm.shape[1]*3,pm.shape[0]*3),Image.NEAREST))
W=sum(t.width for t in tiles)+10*3; S=Image.new('RGB',(W,tiles[0].height),(0,0,0)); x=0
for t in tiles: S.paste(t,(x,0)); x+=t.width+10
S.save(out); print(S.size)
