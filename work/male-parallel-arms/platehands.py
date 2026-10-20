from PIL import Image
P='../../ArtDir/hero/base_lock/'
im=Image.open(P+'male_multiangle_body.jpg').convert('RGB')
bd=Image.open(P+'male_body_bald.jpg').convert('RGB')
boxes={'ma_front_R':(60,165,110,215),'ma_front_L':(265,165,315,215),'ma_back_L':(360,165,410,215),'ma_back_R':(560,165,610,215),
 'ma_leftprof':(755,165,805,225),'ma_rightprof':(1060,165,1110,225),'ma_q3FL_R':(60,490,110,540),'ma_q3FL_L':(265,490,315,540)}
tiles=[]
for k,b in boxes.items():
    c=im.crop(b).resize(((b[2]-b[0])*6,(b[3]-b[1])*6),Image.LANCZOS); tiles.append((k,c))
W=sum(t[1].width for t in tiles[:4]); S=Image.new('RGB',(1200,720),(30,30,30))
x=0;y=0
for i,(k,c) in enumerate(tiles):
    S.paste(c,((i%4)*300,(i//4)*360 if False else (i//4)*330))
S.save('proof/plate_hands_sheet.png'); print(S.size)
