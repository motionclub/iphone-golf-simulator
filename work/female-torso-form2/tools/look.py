"""python3 tools/look.py <coords.npy|tag> [tag]  -> applies coords to START_torso_candidate.blend (positions only), renders chest+glute close-ups, builds a sheet
vs the plate.  Output: proof/scratch/<tag>_sheet.png"""
import sys, subprocess, os
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form2/tools')
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
WD='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form2'
B='/Applications/Blender.app/Contents/MacOS/Blender'
ROOT='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
FB=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',22)
def run(cmd): return subprocess.run(cmd,capture_output=True,text=True)
def apply(npy,out_blend,start=WD+'/START_torso_candidate.blend'):
    r=run([B,'-b',start,'--python',WD+'/tools/apply_coords.py','--',npy,out_blend]); 
    if 'saved' not in r.stdout: print(r.stdout[-800:],r.stderr[-800:]); raise SystemExit('apply failed')
MC=WD+'/tools/soft_plate_matcap.png'
def render(blend,prefix,zc,scale,views,mc=None,res='700x700'):
    mc=mc or MC
    r=run([B,'-b',blend,'--python',WD+'/tools/render_views.py','--',prefix,str(zc),str(scale),mc,views,res])
def plate_crop(kind,zc,half,size=700):
    S=0.0025954198473282443
    bald=Image.open(ROOT+'/ArtDir/hero/base_lock/female_body_bald.jpg').convert('RGB')
    cx=440 if kind=='front' else 847
    c=bald.crop((int(cx-half/S),int(679-(zc+half)/S),int(cx+half/S),int(679-(zc-half)/S))).resize((size,size),Image.LANCZOS)
    return ImageEnhance.Contrast(c).enhance(1.6)
def sheet_tile(sheet,cx,zc,half,size=700,top=False):
    S2b=1.7039/290.5; V0b=668.5
    y0=V0b-(zc+half)/S2b; y1=V0b-(zc-half)/S2b; w=half/S2b
    c=sheet.crop((int(cx-w),int(y0),int(cx+w),int(y1))).resize((size,size),Image.LANCZOS)
    return ImageEnhance.Contrast(c).enhance(1.6)
def label(im,t,xy=(8,8)):
    d=ImageDraw.Draw(im); w=d.textlength(t,font=FB); d.rectangle([xy[0]-4,xy[1]-3,xy[0]+w+6,xy[1]+27],fill=(0,0,0)); d.text(xy,t,font=FB,fill=(255,255,255)); return im
if __name__=='__main__':
    src=sys.argv[1]; tag=sys.argv[2] if len(sys.argv)>2 else os.path.basename(src).replace('.npy','')
    os.makedirs(WD+'/proof/scratch',exist_ok=True)
    blend=f'{WD}/proof/scratch/{tag}.blend'
    apply(src,blend)
    render(blend,f'{WD}/proof/scratch/{tag}_chest',1.22,0.50,'front,y25,y-25,side')
    render(blend,f'{WD}/proof/scratch/{tag}_glute',0.90,0.55,'back,y-155,y155,side')
    sheet=Image.open(ROOT+'/ArtDir/hero/base_lock/female_multiangle_body.jpg').convert('RGB')
    W=Image.new('RGB',(700*4,700*4))
    # row0: plate chest: front bald crop, 3/4FL, 3/4FR, left profile ; row1: model chest
    p=[plate_crop('front',1.22,0.25),sheet_tile(sheet,168,1.22,0.25),sheet_tile(sheet,472,1.22,0.25)]
    # profile plate tile (top row sheet): left profile centre ~ (790,)
    S2=1.7039/288.5; V0=338.5; zc=1.22; half=0.25; cx=790; y0=V0-(zc+half)/S2; y1=V0-(zc-half)/S2; w=half/S2
    pr=sheet.crop((int(cx-w),int(y0),int(cx+w),int(y1))).resize((700,700),Image.LANCZOS); p.append(ImageEnhance.Contrast(pr).enhance(1.6))
    names=['plate front','plate 3/4 FL','plate 3/4 FR','plate L profile']
    for i,(im,n) in enumerate(zip(p,names)): W.paste(label(im,n),(i*700,0))
    for i,(v,n) in enumerate(zip(('front','y25','y-25','side'),('model front','model +25','model -25','model side'))):
        W.paste(label(Image.open(f'{WD}/proof/scratch/{tag}_chest_{v}.png').convert('RGB'),n),(i*700,700))
    g=[plate_crop('back',0.90,0.275),sheet_tile(sheet,775,0.90,0.275),sheet_tile(sheet,1078,0.90,0.275)]
    zc=0.90; half=0.275; y0=V0-(zc+half)/S2; y1=V0-(zc-half)/S2; w=half/S2
    pr=sheet.crop((int(cx-w),int(y0),int(cx+w),int(y1))).resize((700,700),Image.LANCZOS); g.append(ImageEnhance.Contrast(pr).enhance(1.6))
    for i,(im,n) in enumerate(zip(g,['plate back','plate 3/4 BL','plate 3/4 BR','plate L profile'])): W.paste(label(im,n),(i*700,1400))
    for i,(v,n) in enumerate(zip(('back','y-155','y155','side'),('model back','model back -155','model back +155','model side'))):
        W.paste(label(Image.open(f'{WD}/proof/scratch/{tag}_glute_{v}.png').convert('RGB'),n),(i*700,2100))
    W.resize((1960,1960),Image.LANCZOS).save(f'{WD}/proof/scratch/{tag}_sheet.png'); print('sheet',f'{WD}/proof/scratch/{tag}_sheet.png')
