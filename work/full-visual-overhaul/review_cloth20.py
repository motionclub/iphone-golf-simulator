from pathlib import Path
from PIL import Image, ImageDraw

r = Path(__file__).resolve().parents[2] / 'proof/full-visual-overhaul'
td = r/'character-pass-20-all33'
gd = r/'golf-characters-pass-5'
out = r/'cloth20-review'
out.mkdir(exist_ok=True)

def sheet(files, name, columns, width=300, height=400):
    canvas=Image.new('RGB',(width*columns,(height+30)*((len(files)+columns-1)//columns)),(16,30,45))
    draw=ImageDraw.Draw(canvas)
    for i,p in enumerate(files):
        im=Image.open(p).convert('RGB'); im.thumbnail((width,height))
        x=i%columns*width; y=i//columns*(height+30)
        canvas.paste(im,(x+(width-im.width)//2,y))
        draw.text((x+5,y+height+4),p.stem,fill=(240,240,230))
    canvas.save(out/name,quality=94)

clips=sorted({p.stem.removeprefix('male_').rsplit('_',1)[0] for p in td.glob('male_*_0.png')})
for group in range(0,len(clips),6):
    files=[td/f'{sex}_{clip}_{sample}.png' for clip in clips[group:group+6] for sex in ['male','female'] for sample in range(3)]
    sheet(files,f'tennis-{group//6+1}.jpg',6,width=280,height=350)
for sex in ['male','female']:
    for club in ['Driver','Iron','PitchingWedge','Wedge','Putter']:
        files=[gd/f'{sex}_{club}_{phase}_{view}.png' for view in ['front34','back34'] for phase in ['address','top','contact','follow']]
        sheet(files,f'golf-{sex}-{club}.jpg',4,width=320,height=425)
sheet(sorted(gd.glob('*_golf_blink_*.png')),'golf-blink.jpg',3,width=450,height=450)
print('\n'.join(str(p) for p in out.glob('*.jpg')))
