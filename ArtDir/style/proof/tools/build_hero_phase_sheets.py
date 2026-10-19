"""Matching phase-to-phase hero views, no retouching. Raw PNGs remain in scratch.
Usage: BEFORE AFTER OUTPUT. Four grids plus an eight-row look-dev grid.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys,json,argparse
parser=argparse.ArgumentParser();parser.add_argument('before',type=Path);parser.add_argument('after',type=Path);parser.add_argument('out',type=Path);parser.add_argument('--before-label',default='previous phase');parser.add_argument('--max-rows',type=int,default=24);args=parser.parse_args()
before,after,out=args.before,args.after,args.out;out.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[4];refs=root/'ArtDir/style/refs'
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
metrics={r['shot']:r for r in json.loads((after/'metrics.json').read_text())} if (after/'metrics.json').exists() else {}
def reference(name):
    ref='r2' if 'resort' in name else 'r1' if '__hub' in name else 'r3';q=None
    if 'skyscraper' in name:ref='r4';q=0
    elif 'volcano' in name:ref='r4';q=1
    elif any('golf_'+n+'_' in name for n in ['10','16','21','22','23']):ref='r4';q=3
    elif 'golf_17_' in name:ref='r4';q=2
    for i,w in enumerate(['rain','storm','fog','gusty']):
        if '_'+w+'__' in name:ref='r5';q=i
    im=Image.open(refs/(ref+'.png')).convert('RGB')
    if q is not None:
        w,h=im.size;x=q%2*w//2;y=q//2*h//2;im=im.crop((x,y,x+w//2,y+h//2))
    return im,ref+(' panel '+str(q+1) if q is not None else '')
for hero in ['MatchHero_Male','MatchHero_Female','GolfKitHero_Male','GolfKitHero_Female','lookdev_']:
    names=sorted(p.name.replace('.mask.png','') for p in after.glob(hero+'*.mask.png') if (before/p.name.replace('.mask','')).exists())
    if not names:continue
    for offset in range(0,len(names),args.max_rows):
        page=names[offset:offset+args.max_rows];suffix="" if len(names)<=args.max_rows else "_"+str(offset//args.max_rows+1).zfill(2)
        w,h=480,270;sheet=Image.new('RGB',(w*3,35+len(page)*(h+48)),'#f2f3f5');d=ImageDraw.Draw(sheet)
        for col,label in enumerate(['BEFORE — '+args.before_label,'AFTER — this phase','REF — appearance target']):d.text((col*w+6,9),label,font=font,fill='#19212c')
        for row,name in enumerate(page):
            ref,label=reference(name);y=35+row*(h+48)
            for col,im in enumerate([Image.open(before/(name+'.png')),Image.open(after/(name+'.png')),ref]):sheet.paste(im.convert('RGB').resize((w,h),Image.Resampling.LANCZOS),(col*w,y))
            caption=name+' | '+label
            if name in metrics:
                m=metrics[name]['after'];caption+=' | face L '+str(m['face'].get('L','hidden'))+' / edge dL '+str(m['silhouetteDeltaL'])
            d.text((6,y+h+6),caption,font=font,fill='#19212c')
        sheet.save(out/(hero.rstrip('_')+suffix+'_before_after_ref.jpg'),quality=93)
print('Hero phase grids:',out)
