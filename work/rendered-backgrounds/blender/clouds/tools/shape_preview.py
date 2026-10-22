# python3 tools/shape_preview.py out.png : silhouettes + fake lighting of all 8 coverage grids (numpy only)
import sys,types,numpy as np
sys.modules['bpy']=types.ModuleType('bpy');sys.modules['openvdb']=types.ModuleType('openvdb')
src=open(__file__.replace('tools/shape_preview.py','build_clouds.py')).read()
src=src[:src.index('# ---------------------------------------------------------------- scene')]
sys.argv=['x'];ns={'__file__':__file__.replace('tools/shape_preview.py','build_clouds.py')};exec(src,ns)
from PIL import Image
tiles=[]
for i in range(8):
    cov,lo,dims,kind=ns['coverage_grid'](i,.09)
    dens=np.clip((cov-.25)*3,0,1)*6*.09
    # light from upper right, march along +x... crude: transmittance from top-right diagonal
    tau_y=np.cumsum(dens,axis=1)  # view along +y from front
    T=np.exp(-tau_y)
    light=np.exp(-np.cumsum(dens[::-1,:,::-1],axis=0)[::-1,:,::-1]*.7-np.cumsum(dens[:,:,::-1],axis=2)[:,:,::-1]*.7)
    rad=(dens*T*(.25+light)).sum(1);al=1-T[:,-1,:]
    img=np.dstack([rad/ max(rad.max(),1e-6)]*3)*al[...,None]+np.array([.25,.45,.75])*(1-al[...,None])
    im=Image.fromarray((np.clip(img,0,1)**(1/2.2)*255).astype(np.uint8).transpose(1,0,2)[::-1])
    tiles.append(im.resize((400,int(400*im.height/im.width))))
H=max(t.height for t in tiles);S=Image.new('RGB',(1600,2*H),(60,110,190))
for i,t in enumerate(tiles):S.paste(t,((i%4)*400,(i//4)*H+H-t.height))
S.save(sys.argv[1] if len(sys.argv)>1 else 'shape.png')
