"""Compose proof/SKIN_liveliness_Fair_Tan_Deep.png and the six-tone strip from skin/unity/*.png + skin/measure_cases_final.json"""
import json
from PIL import Image, ImageDraw, ImageFont
R='../../ArtDir/hero/base_lock/'
M=json.load(open('skin/measure_cases_final.json'))
def font(sz):
    for f in ('/System/Library/Fonts/Helvetica.ttc','/System/Library/Fonts/SFNS.ttf'):
        try: return ImageFont.truetype(f,sz)
        except Exception: pass
    return ImageFont.load_default()
F=font(22); Fs=font(17)
def label(im,xy,text,fnt=Fs,fill=(255,255,255)):
    d=ImageDraw.Draw(im); w=d.textlength(text,font=fnt); x,y=xy
    d.rectangle((x-4,y-3,x+w+6,y+fnt.size+4),fill=(0,0,0)); d.text((x,y),text,font=fnt,fill=fill)
ref=Image.open(R+'male_head_detail.jpg').convert('RGB'); refF=ref.crop((22,66,432,352))
T=400
def unity(name,view): return Image.open(f'skin/unity/{name}__{view}.png').convert('RGB').crop((100,60,800,760)).resize((T,T),Image.LANCZOS)
def plate_tile():
    t=Image.new('RGB',(T,T),(34,34,36)); p=refF.resize((T,int(T*286/410)),Image.LANCZOS); t.paste(p,(0,(T-p.size[1])//2)); label(t,(8,8),'PLATE  skinish S .46–.48'); return t
rows=[('Fair','fair'),('Tan  (default; held — already on-plate chroma)','tan'),('Deep','deep')]
cols=['PLATE energy reference','BEFORE  old palette, same Lit stack','AFTER  retuned palette, Male_Form_Skin.mat','AFTER  3/4 view']
G=10; W=G+4*(T+G); H=70+len(rows)*(T+40)+(T+40)
sh=Image.new('RGB',(W,H),(22,22,24)); d=ImageDraw.Draw(sh)
d.text((G,8),'SKIN LIVELINESS — real Unity render, HeroBase studio lights; ONE mesh, ONE material asset, tone swapped through _BaseColor only',font=F,fill=(255,214,120))
for j,c in enumerate(cols): d.text((G+j*(T+G),42),c,font=Fs,fill=(150,200,255))
y=68
for lab,key in rows:
    b=M['before_'+key]; a=M['after_'+key]
    tiles=[plate_tile(),unity('before_'+key,'head_front'),unity('after_'+key,'head_front'),unity('after_'+key,'head_q')]
    for j,t in enumerate(tiles):
        sh.paste(t,(G+j*(T+G),y))
    label(sh,(G+1*(T+G)+8,y+T-30),f'S {b["S"]:.3f}   V {b["V"]:.2f}   H {b["H"]:.0f}°')
    label(sh,(G+2*(T+G)+8,y+T-30),f'S {a["S"]:.3f}   V {a["V"]:.2f}   H {a["H"]:.0f}°')
    d.text((G,y+T+8),lab,font=F,fill=(255,200,80)); y+=T+40
bd=M['before_default']; ad=M['after_default']
tiles=[plate_tile(),unity('before_default','head_front'),unity('after_default','head_front'),unity('after_default','torso_q')]
for j,t in enumerate(tiles): sh.paste(t,(G+j*(T+G),y))
label(sh,(G+1*(T+G)+8,y+T-30),f'S {bd["S"]:.3f}   V {bd["V"]:.2f}   H {bd["H"]:.0f}°'); label(sh,(G+2*(T+G)+8,y+T-30),f'S {ad["S"]:.3f}   V {ad["V"]:.2f}   H {ad["H"]:.0f}°')
d.text((G,y+T+8),'HeroBase default skin: BEFORE flat (.74,.555,.435)  ->  AFTER palette Tan (SkinTones[2]); same studio',font=F,fill=(255,200,80))
sh.save('skin/SKIN_liveliness_Fair_Tan_Deep.png'); print(sh.size)
# six-tone strip
names=['fair','light','tan','olive','brown','deep']; S6=330
st=Image.new('RGB',(G+6*(S6+G),2*(S6+34)+40),(22,22,24)); d=ImageDraw.Draw(st)
d.text((G,8),'All six SkinTones — BEFORE (top, old palette) / AFTER (bottom, retuned palette), same mesh + same material asset',font=F,fill=(255,214,120))
for i,n in enumerate(names):
    for r,pre in enumerate(('before_','after_')):
        im=Image.open(f'skin/unity/{pre}{n}__head_front.png').convert('RGB').crop((100,60,800,760)).resize((S6,S6),Image.LANCZOS); x=G+i*(S6+G); yy=40+r*(S6+34)
        st.paste(im,(x,yy)); mm=M[pre+n]; label(st,(x+6,yy+S6-28),f'{n}  S {mm["S"]:.3f}  V {mm["V"]:.2f}')
st.save('skin/SKIN_six_tones_before_after.png'); print(st.size)
