from pathlib import Path
import subprocess,json
from PIL import Image,ImageDraw
repo=Path("/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator")
source=repo/"proof/full-visual-overhaul/tennis-action-film-1"
output=source/"review";output.mkdir(exist_ok=True)
encoder=repo/"work/emotes/scripts/enc"
report=[]
for folder in sorted(source.iterdir()):
 if not folder.is_dir() or folder.name=="review": continue
 for view,dimensions in [("game",(960,540)),("hero",(720,720))]:
  frames=sorted(folder.glob(view+"_*.png"))
  if not frames:continue
  movie=output/(folder.name+"_"+view+".mp4")
  args=[str(encoder),str(movie),"30",str(dimensions[0]),str(dimensions[1])]+[str(f) for f in frames]
  result=subprocess.run(args,capture_output=True,text=True)
  report.append(dict(name=folder.name,view=view,frames=len(frames),fps=30,duration=len(frames)/30,file=str(movie),exit=result.returncode,log=(result.stdout+result.stderr)[-600:]))
  print(folder.name,view,len(frames),result.returncode,flush=True)
 # Every saved33ms frame during the emitter's first333ms, including the event itself.
 indices=list(range(8,21)) if folder.name.startswith("fx_") else [0,30,60,120,180,240,300,360,420,480,540,599]
 choices=[folder/("hero_"+str(i).zfill(5)+".png") for i in indices]
 choices=[p for p in choices if p.exists()]
 if choices:
  width,height=256,290;sheet=Image.new("RGB",(width*4,height*((len(choices)+3)//4)),(16,36,61));draw=ImageDraw.Draw(sheet)
  for n,path in enumerate(choices):
   im=Image.open(path).convert("RGB");im.thumbnail((256,256));x=n%4*width;y=n//4*height
   sheet.paste(im,(x+(256-im.width)//2,y+28));draw.text((x+10,y+8),path.stem.replace("hero_","frame "),(255,249,238))
  sheet.save(output/(folder.name+"_sequence.jpg"),quality=94)
(output/"films.json").write_text(json.dumps(report,indent=2))

