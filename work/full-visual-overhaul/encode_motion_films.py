from pathlib import Path
import json,subprocess,sys
from PIL import Image,ImageDraw
repo=Path(__file__).resolve().parents[2]
encoder=repo/"work/emotes/scripts/enc"
for arg in sys.argv[1:]:
 source=Path(arg).resolve();output=source/"review";output.mkdir(exist_ok=True)
 report=[]
 folders=[source]+[p for p in sorted(source.iterdir()) if p.is_dir() and p.name!="review"]
 for folder in folders:
  label=folder.name if folder!=source else "overview"
  for view in ["game","hero","front","side","wide","visitors"]:
   frames=sorted(folder.glob(view+"_*.png")) or sorted(folder.glob(view+"_*.jpg"))
   if not frames:continue
   with Image.open(frames[0]) as im:w,h=im.size
   movie=output/(label+"_"+view+".mp4")
   result=subprocess.run([str(encoder),str(movie),"30",str(w),str(h)]+[str(p) for p in frames],capture_output=True,text=True)
   entry=dict(name=label,view=view,frames=len(frames),fps=30,duration=len(frames)/30,width=w,height=h,file=str(movie),exit=result.returncode,bytes=movie.stat().st_size if movie.exists() else 0,log=(result.stdout+result.stderr)[-600:])
   report.append(entry);print(source.name,folder.name,view,len(frames),result.returncode,flush=True)
   if result.returncode:raise RuntimeError(entry)
  reviewframes=sorted(folder.glob("hero_*.png")) or sorted(folder.glob("front_*.png")) or sorted(folder.glob("hero_*.jpg")) or sorted(folder.glob("game_*.jpg")) or sorted(folder.glob("front_*.jpg")) or sorted(folder.glob("visitors_*.png")) or sorted(folder.glob("game_*.png"))
  if not reviewframes:continue
  if folder.name.startswith("fx_"):ids=range(8,min(21,len(reviewframes)))
  elif "dive" in source.name:ids=[10,14,18,22,26,30,34,38,42,46,55,75]
  else:ids=[int(i*(len(reviewframes)-1)/11) for i in range(12)]
  chosen=[reviewframes[i] for i in ids if i<len(reviewframes)];tw,th=256,292
  sheet=Image.new("RGB",(tw*4,th*((len(chosen)+3)//4)),(16,36,61));draw=ImageDraw.Draw(sheet)
  for n,p in enumerate(chosen):
   im=Image.open(p).convert("RGB");im.thumbnail((256,264));x=n%4*tw;y=n//4*th;sheet.paste(im,(x+(tw-im.width)//2,y+28));draw.text((x+10,y+8),p.stem,(255,249,238))
  sheet.save(output/(label+"_sequence.jpg"),quality=94)
 (output/"films.json").write_text(json.dumps(report,indent=2))

