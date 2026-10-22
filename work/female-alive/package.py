from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess,json
root=Path(__file__).resolve().parents[2]
out=root/'ArtDir/style/alive/after'
ff=root/'work/presentation/video-tools/lib/python3.14/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1'
font='/System/Library/Fonts/Supplemental/Arial.ttf'
try: fnt=ImageFont.truetype(font,23);small=ImageFont.truetype(font,18)
except OSError: fnt=small=ImageFont.load_default()
def run(args):subprocess.run([str(ff),'-hide_banner','-loglevel','error','-y']+list(map(str,args)),check=True)
def encode(folder,stem,path):
 run(['-framerate','30','-i',folder/(stem+'%05d.jpg'),'-an','-c:v','libx264','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',path])
def pair(a,b,path):
 run(['-i',a,'-i',b,'-filter_complex','[0:v]scale=640:-2,setsar=1[a];[1:v]scale=640:-2,setsar=1[b];[a][b]hstack=inputs=2:shortest=1[v]','-map','[v]','-an','-c:v','libx264','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',path])
manifest={}
for mode in ['idle','wave','joy','slump','rally','golf']:
 manifest[mode]={}
 for stage in ['before','after']:
  folder=out/('after-final' if stage=='after' else 'before' if mode=='golf' else 'before-matched')/mode
  stem='f_'
  if mode=='rally':folder=folder/'frames';stem='game_'
  dest=out/f'{stage}-{mode}.mp4';encode(folder,stem,dest)
  manifest[mode][stage]={'source':str(folder.relative_to(root)),'frames':len(list(folder.glob(stem+'*.jpg'))),'fps':30,'muted':True}
 pair(out/f'before-{mode}.mp4',out/f'after-{mode}.mp4',out/f'compare-{mode}.mp4')
 if mode in ['idle','wave','joy','slump']:
  for stage in ['before','after']:encode(out/('after-final' if stage=='after' else 'before-matched')/mode,'detail_',out/f'{stage}-{mode}-detail.mp4')
  pair(out/f'before-{mode}-detail.mp4',out/f'after-{mode}-detail.mp4',out/f'compare-{mode}-detail.mp4')
# Clearly labeled sheets: footage unchanged; diagnostic views explicitly separate.
for kind,rows in [('gameplay',[('idle',60),('wave',30),('joy',30),('slump',45),('rally',300),('golf',65)]),('detail',[('idle',20),('wave',30),('joy',30),('slump',45)])]:
 h=390 if kind=='gameplay' else 670
 sheet=Image.new('RGB',(1280,70+h*len(rows)),'#141b25');d=ImageDraw.Draw(sheet)
 d.text((20,10),'FEMALE ALIVE | BEFORE',font=fnt,fill='white');d.text((660,10),'AFTER',font=fnt,fill='white')
 d.text((20,41),'Gameplay cameras unchanged' if kind=='gameplay' else 'DIAGNOSTIC CAMERA — same live pose, closer front view',font=small,fill='#b9c6d8')
 for row,(mode,n) in enumerate(rows):
  for col,stage in enumerate(['before','after']):
   folder=out/('after-final' if stage=='after' else 'before' if mode=='golf' else 'before-matched')/mode
   stem='detail_' if kind=='detail' else 'f_'
   if mode=='rally':folder=folder/'frames';stem='game_'
   im=Image.open(folder/f'{stem}{n:05}.jpg').resize((640,640 if kind=='detail' else 360))
   y=70+row*h;sheet.paste(im,(col*640,y+30));d.text((col*640+12,y+4),f'{mode.upper()}  {n/30:.2f}s',font=small,fill='white')
 sheet.save(out/f'{kind}-sheet.jpg',quality=92)
# A short review film: labeled side-by-side sections, frames unretimed.
segments=[]
for mode,kind,seconds,start in [('idle','detail',4,0),('wave','detail',4,0),('joy','detail',4,0),('slump','detail',4,0),('rally','gameplay',7,8),('golf','gameplay',4,0)]:
 src=out/f'compare-{mode}{"-detail" if kind=="detail" else ""}.mp4'
 banner=Image.new('RGB',(1280,70),'#141b25');d=ImageDraw.Draw(banner)
 d.text((18,8),f'BEFORE | {mode.upper()}',font=fnt,fill='white');d.text((660,8),'AFTER | FEMALE ALIVE',font=fnt,fill='white')
 d.text((18,40),'DIAGNOSTIC CLOSE VIEW' if kind=='detail' else 'GAMEPLAY CAMERA',font=small,fill='#b9c6d8')
 png=root/'work/female-alive'/f'banner-{mode}.png';banner.save(png)
 seg=root/'work/female-alive'/f'segment-{mode}.mp4';segments.append(seg)
 run(['-ss',str(start),'-i',src,'-loop','1','-i',png,'-filter_complex','[0:v]scale=1280:640:force_original_aspect_ratio=decrease,pad=1280:640:(ow-iw)/2:(oh-ih)/2:color=0x141b25,pad=1280:710:0:70:color=0x141b25[v];[v][1:v]overlay=0:0[o]','-map','[o]','-t',seconds,'-r',30,'-an','-c:v','libx264','-crf',22,'-pix_fmt','yuv420p',seg])
concat=root/'work/female-alive/concat.txt';concat.write_text(''.join(f"file '{s}'\n" for s in segments))
run(['-f','concat','-safe','0','-i',concat,'-an','-c','copy','-movflags','+faststart',out/'female-alive-review.mp4'])
(out/'capture-manifest.json').write_text(json.dumps(manifest,indent=2))
print('Packaged muted clips and review sheets.')
