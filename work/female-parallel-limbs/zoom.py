import sys
from PIL import Image
plate=Image.open('../../ArtDir/hero/base_lock/female_body_plain.jpg').convert('RGB')
pre,out=sys.argv[1],sys.argv[2]
f=Image.open(f'{pre}_front.png').convert('RGB'); b=Image.open(f'{pre}_back.png').convert('RGB')
def crop(im,box,s=3): c=im.crop(box); return c.resize((c.width*s,c.height*s),Image.LANCZOS)
regs={'hand_front':((330,330,420,430),(330,330,420,430),3),'foot_front':((350,600,520,690),(350,600,520,690),3),
      'hand_back':((730,330,800,430),(730,330,800,430),3),'foot_back':((760,600,930,690),(760,600,930,690),3)}
for name,(bp,bm,s) in regs.items():
    src=plate; mod=f if 'front' in name else b
    A=crop(src,bp,s); B=crop(mod,bm,s)
    W=Image.new('RGB',(A.width*2+10,A.height),(255,255,255)); W.paste(A,(0,0)); W.paste(B,(A.width+10,0)); W.save(f'{out}_{name}.png')
