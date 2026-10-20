from pathlib import Path
import subprocess,csv,shutil,json
from PIL import Image,ImageDraw
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm')
ffmpeg='/Users/adnanyonathan/.cache/uv/archive-v0/FAqiNt1vNS62llSz/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1'
out=root/'film';out.mkdir(exist_ok=True)
for sex in ['male','female']:
 name=sex+'-rh-deuce';b=root/'before'/name;a=root/'after'/name
 if not (a/'completed.json').exists():continue
 for view in ['game','front','left','top']:
  target=out/f'{sex}-{view}-before-after.mp4'
  command=[ffmpeg,'-v','error','-y','-i',str(b/f'{view}.mp4'),'-i',str(a/f'{view}.mp4'),'-filter_complex',"[0:v]drawtext=text='BEFORE':x=10:y=10:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.65[l];[1:v]drawtext=text='CANDIDATE - GATES FAIL':x=10:y=10:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.65[r];[l][r]hstack=inputs=2[out]",'-map','[out]','-c:v','libx264','-crf','20','-pix_fmt','yuv420p',str(target)]
  subprocess.run(command,check=True)
  rows_b=list(csv.DictReader((b/'trace.csv').open())); rows_a=list(csv.DictReader((a/'trace.csv').open()));wb=[r for r in rows_b if float(r['speed'])<-.2 and r['phase']=='PlayerServeHold'];worst=max(wb,key=lambda r:float(r['deepest_mm'])); centre=int(worst['frame'])//2
  tile=320; h=180 if view=='game' else 320
  sheet=Image.new('RGB',(tile*4, (h+38)*6),(22,25,31));draw=ImageDraw.Draw(sheet)
  for row,run,rows in [(0,b,rows_b),(3,a,rows_a)]:
   for i in range(12):
    n=max(0,centre-6+i);src=run/f'{view}_{n:05d}.png'
    if not src.exists():continue
    im=Image.open(src).convert('RGB');im.thumbnail((tile,h));x=(i%4)*tile;y=(i//4+row)*(h+38);sheet.paste(im,(x,y));r=next((r for r in rows if int(r['frame'])==n*2),None)
    draw.text((x+5,y+h+6),f'{"BEFORE" if row==0 else "CANDIDATE"} f={n*2} depth={float(r["deepest_mm"]):.2f} mm',fill='white')
  sheet.save(out/f'{sex}-{view}-comparison-sheet.jpg',quality=94)
 print('comparison complete',sex)
