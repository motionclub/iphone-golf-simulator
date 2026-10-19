# Blender -b --python preview.py -- <out.png> <exr> [<exr> ...] : sqrt-tonemapped sheet over a blue bg, plus alpha
import bpy,sys,numpy as np
a=sys.argv[sys.argv.index('--')+1:];out=a[0];fs=a[1:]
ims=[]
for f in fs:
    im=bpy.data.images.load(f);p=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4);ims.append(p);bpy.data.images.remove(im)
peak=max(np.percentile(p[...,0],99.7) for p in ims)
tiles=[]
for p in ims:
    l=np.clip(p[...,:3]/peak,0,1)**(1/2.2);al=p[...,3:4]
    bg=np.array([.25,.45,.75],np.float32)
    tiles.append(l+bg*(1-al))
h,w=tiles[0].shape[:2];cols=4;rows=(len(tiles)+cols-1)//cols
S=np.zeros((h*rows,w*cols,4),np.float32);S[...,3]=1
for i,t in enumerate(tiles):
    r,c=i//cols,i%cols;S[(rows-1-r)*h:(rows-r)*h,c*w:(c+1)*w,:3]=t
img=bpy.data.images.new('s',w*cols,h*rows);img.pixels[:]=S.ravel();img.filepath_raw=out;img.file_format='PNG';img.save()
print('peak',peak)
