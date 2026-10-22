from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys,json,numpy as np
r=Path(__file__).resolve().parents[1];stage=r/sys.argv[1];dest=stage/'proof';dest.mkdir(exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',20)
for sex in ['male','female']:
 before=Image.open(r/'ear-before'/f'{sex}_front_sheet.png');after=Image.open(stage/f'{sex}_front_sheet.png');quarter=Image.open(stage/f'{sex}_threequarter_sheet.png')
 board=Image.new('RGB',(1200,680),'#ece8df');d=ImageDraw.Draw(board)
 refs=[(100,278,170,428),(383,278,453,428)] if sex=='male' else [(166,264,234,389),(410,264,478,389)]
 currents=[(635,278,705,428),(929,278,999,428)] if sex=='male' else [(698,264,766,389),(952,264,1020,389)]
 for row in range(2):
  for col,(im,box,label) in enumerate([(after,refs[row],'Reference'),(before,currents[row],'Before ears pass'),(after,currents[row],'Current')]):
   crop=im.crop(box);crop.thumbnail((270,285),Image.Resampling.LANCZOS)
   # Uniform enlargement of untouched render pixels; identical current/before bounds.
   scale=min(270/crop.width,285/crop.height);crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
   board.paste(crop,(col*300+(300-crop.width)//2,row*335+40));d.text((col*300+15,row*335+12),label,fill='#222',font=font)
 box=(567,270,656,418) if sex=='male' else (625,261,715,385)
 crop=quarter.crop(box);scale=min(280/crop.width,540/crop.height);crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
 board.paste(crop,(910,65));d.text((905,12),'Current 3/4',fill='#222',font=font)
 board.save(dest/f'{sex}_ears.png')
 progress=Image.new('RGB',(1635,750),'#ece8df');progress.paste(after.crop((0,0,545,750)),(0,0));progress.paste(before.crop((545,0,1090,750)),(545,0));progress.paste(after.crop((545,0,1090,750)),(1090,0));d=ImageDraw.Draw(progress)
 for i,label in enumerate(['LOCKED REFERENCE','BEFORE EARS PASS','CURRENT EARS']):
  d.rectangle((i*545,0,(i+1)*545,50),fill='#ece8df');d.text((i*545+20,20),sex.upper()+' / '+label,fill='black',font=font)
 progress.save(dest/f'{sex}_ear_progress.png')
