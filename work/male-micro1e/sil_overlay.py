import sys
from PIL import Image
d=sys.argv[1]; M='../male-silhouette/'
tiles=[]
for v in ['bald_front','bald_back']:
    t=Image.open(M+v+'_target.png'); r=Image.open(d+'/'+v+'.png')
    tm=(t.split()[3] if t.mode=='RGBA' else t.convert('L')); rm=r.split()[3]
    W,H=rm.size
    out=Image.new('RGB',(W,H),(30,30,30)); po=out.load(); tp=tm.load(); rp=rm.load()
    for y in range(H):
        for x in range(W):
            a=tp[x,y]>127; b=rp[x,y]>127
            if a and b: po[x,y]=(110,110,110)
            elif a: po[x,y]=(60,230,150)      # reference only (green)
            elif b: po[x,y]=(255,90,160)      # model only (pink)
    out.save(f'{d}/{v}_overlay.png'); tiles.append(out)
# crops: hands region + head
def crop(img,box,sc=3): c=img.crop(box); return c.resize((c.width*sc,c.height*sc),Image.NEAREST)
f,b=tiles
Lh=crop(f,(100,300,210,400)); Rh=crop(f,(520,300,630,400))
Lb=crop(b,(660,300,770,400)); Rb=crop(b,(1080,300,1190,400))
hd=crop(f,(300,150,410,260))
S=Image.new('RGB',(Lh.width*4+30,Lh.height+Lh.height),(0,0,0))
S.paste(Lh,(0,0)); S.paste(Rh,(Lh.width+10,0)); S.paste(Lb,(2*Lh.width+20,0)); S.paste(Rb,(3*Lh.width+30,0))
S.paste(hd,(0,Lh.height)); S.save(f'{d}/overlay_hands.png'); print(S.size)
