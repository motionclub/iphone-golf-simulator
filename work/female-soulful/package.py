"""Package unretimed Unity captures as muted review clips and contact sheets."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess, sys, json

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent
FF=REPO/'work/presentation/video-tools/lib/python3.14/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1'
before=ROOT/'proof'/sys.argv[1]
after=ROOT/'proof'/sys.argv[2]
out=ROOT/'proof/review';out.mkdir(exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22)
def run(args):
    subprocess.run([str(FF),'-hide_banner','-loglevel','error','-y',*map(str,args)],check=True)

manifest={}
for mode in ['idle','wave','joy','slump']:
    for label,source in [('before',before),('after',after)]:
        for prefix in ['f_','detail_']:
            name=f'{label}-{mode}'+('-detail' if prefix=='detail_' else '')+'.mp4'
            run(['-framerate',30,'-i',source/mode/(prefix+'%05d.jpg'),'-an','-c:v','libx264','-crf',21,'-pix_fmt','yuv420p','-movflags','+faststart',out/name])
        manifest[f'{label}-{mode}']={'frames':len(list((source/mode).glob('f_*.jpg'))),'fps':30,'audio':False,'source':str(source/mode)}
    for detail in ['', '-detail']:
        run(['-i',out/f'before-{mode}{detail}.mp4','-i',out/f'after-{mode}{detail}.mp4',
             '-filter_complex','[0:v]scale=640:-2,setsar=1[a];[1:v]scale=640:-2,setsar=1[b];[a][b]hstack=shortest=1[v]',
             '-map','[v]','-an','-c:v','libx264','-crf',21,'-pix_fmt','yuv420p','-movflags','+faststart',out/f'compare-{mode}{detail}.mp4'])
sheet=Image.new('RGB',(1280,4*680+60),'#19212b');draw=ImageDraw.Draw(sheet)
draw.text((16,16),'BEFORE',font=font,fill='white');draw.text((656,16),'CANDIDATE — actual Unity diagnostic',font=font,fill='white')
for row,(mode,n) in enumerate([('idle',30),('wave',30),('joy',30),('slump',45)]):
    for col,source in enumerate([before,after]):
        sheet.paste(Image.open(source/mode/f'detail_{n:05d}.jpg'),(col*640,60+row*680+30))
        draw.text((col*640+12,60+row*680),mode.upper(),font=font,fill='white')
sheet.save(out/'comparison.jpg',quality=93)
(out/'capture-manifest.json').write_text(json.dumps(manifest,indent=2))
