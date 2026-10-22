import sys; sys.path.insert(0,'tools'); from seg import *
from PIL import ImageDraw
def grid(name, box, out, step=20, scale=2):
    im=Image.open(S+name+'.png').convert('RGB').crop(box)
    im=im.resize((im.width*scale, im.height*scale), Image.LANCZOS); d=ImageDraw.Draw(im)
    for x in range(0, im.width, step*scale):
        d.line([(x,0),(x,im.height)], fill=(255,0,0) if (x//scale)%100==0 else (255,180,180), width=1)
        if (x//scale)%100==0: d.text((x+2,2), str(x//scale+box[0]), fill=(200,0,0))
    for y in range(0, im.height, step*scale):
        d.line([(0,y),(im.width,y)], fill=(0,0,255) if (y//scale)%100==0 else (180,180,255), width=1)
        if (y//scale)%100==0: d.text((2,y+2), str(y//scale+box[1]), fill=(0,0,200))
    im.save(out)
if __name__=='__main__':
    a=sys.argv[1:]; grid(a[0], tuple(int(v) for v in a[1].split(',')), a[2], int(a[3]) if len(a)>3 else 20, int(a[4]) if len(a)>4 else 2)
