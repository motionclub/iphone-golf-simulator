from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import shutil,csv
W=Path(__file__).resolve().parents[1];D=W/'proof/pass02';O=Path('/Users/adnanyonathan/Documents/Codex/2026-10-06/open-3/outputs');G=O/'Frame_breakdown_pass_2'
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',27)
normal=[0]*12+list(range(105))+[104]*18;slow=[70]*12+[i for i in range(70,96) for _ in range(4)]+[95]*18
sequence=[(i,'normal speed') for i in normal]+[(i,'quarter speed') for i in slow]
out=D/'front-combined';out.mkdir(exist_ok=True)
for n,(i,speed) in enumerate(sequence):
 frame=Image.new('RGB',(1800,1080),(40,47,55));draw=ImageDraw.Draw(frame)
 for x,sex in [(0,'Male'),(900,'Female')]:
  frame.paste(Image.open(D/'front'/sex/f'{i:04}.png').convert('RGB'),(x,60))
  draw.text((x+24,18),f'Front · {sex} · F{i+1:03} · {speed}',font=font,fill='#f5d179' if 76<=i<=89 else '#eef2f4')
 draw.line((900,12,900,1060),fill=(66,74,82),width=2);frame.save(out/f'{n:04}.png')
print('ASSEMBLED FRONT',len(sequence),flush=True)
for sex in ['Male','Female']:
 for i in range(105):shutil.copy2(D/'front'/sex/f'{i:04}.png',G/'frames'/f'front_{sex}_{i+1:03}.png')
for start in range(0,105,15):
 sheet=Image.new('RGB',(2700,2940),(25,30,36));draw=ImageDraw.Draw(sheet)
 draw.text((28,20),f'PASS 2 · FRONT VIEW · F{start+1:03}–F{start+15:03}',font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',42),fill='#eef3f6')
 draw.text((28,77),'MALE left / FEMALE right · Original 30 fps swing time',font=font,fill='#b9c7d1')
 for j,i in enumerate(range(start,start+15)):
  x=j%3*900;y=140+j//3*555;draw.text((x+22,y+8),f'F{i+1:03} · {i/30:.3f}s',font=font,fill='#f5d179')
  for offset,sex in [(0,'Male'),(450,'Female')]:sheet.paste(Image.open(G/'frames'/f'front_{sex}_{i+1:03}.png').convert('RGB').resize((450,500),Image.Resampling.LANCZOS),(x+offset,y+43))
 sheet.save(G/'sheets'/f'front_{start+1:03}-{start+15:03}.jpg',quality=96,subsampling=0)
p=G/'index.html';s=p.read_text().replace('<option value="side">Side</option>','<option value="side">Side</option><option value="front">Front</option>')
s=s.replace('function videoSequence(){return','function videoSequence(){if(view.value===\'front\')return [...Array(12).fill(0),...Array.from({length:105},(_,i)=>i),...Array(18).fill(104),...Array(12).fill(70),...Array.from({length:26},(_,i)=>[i+70,i+70,i+70,i+70]).flat(),...Array(18).fill(95)];return')
s=s.replace('render();\n</script>','if(new URLSearchParams(location.search).get("view")==="front")view.value="front";render();\n</script>');p.write_text(s)
p=G/'video_frame_index.csv';rows=list(csv.DictReader(p.open()));rows=[r for r in rows if r['view']!='front']
for n,(i,_) in enumerate(sequence):rows.append(dict(view='front',video_frame=n+1,video_seconds=f'{n/30:.3f}',swing_frame=f'F{i+1:03}',swing_seconds=f'{i/30:.3f}'))
with p.open('w') as f:
 writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
print('FRONT GALLERY READY',flush=True)
