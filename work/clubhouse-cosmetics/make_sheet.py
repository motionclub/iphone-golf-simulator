from PIL import Image,ImageDraw,ImageFont,ImageOps
from pathlib import Path
P=Path(__file__).resolve().parent/'proof'
try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',28);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)
except OSError:font=small=ImageFont.load_default()
sheet=Image.new('RGB',(1600,1080),(239,242,244));d=ImageDraw.Draw(sheet)
d.text((40,24),'PARTY GEAR / ORIGINAL CLUB SIZE',(22,34,47),font=font)
d.text((40,63),'Actual Unity renders · Same grip, per-club dimensions and animation contact reference',(69,82,94),font=small)
for i,(style,name) in enumerate([('hockey','ICEBREAKER'),('slugger','HOME RUN'),('balloon','POP HOUND'),('candy','SUGAR RUSH')]):
 im=Image.open(P/f'party_{style}_male_club.png').convert('RGB')
 # Keep full-length imported geometry; each is framed identically in the proof camera.
 im.thumbnail((380,570));x=20+i*400;sheet.paste(im,(x,110));detail=Image.open(P/f'party_{style}_male_detail.png').convert('RGB')
 hsv=detail.convert('HSV');mask=hsv.getchannel('S').point(lambda s:255 if s>45 else 0)
 counts=[sum(mask.crop((0,y,mask.width,y+1)).getdata())/255 for y in range(mask.height)]
 dense=[y for y,count in enumerate(counts) if count>=max(12,max(counts)*.2)]
 assert dense, 'No visible cosmetic head in '+style
 y0,y1=min(dense),max(dense)+1;box=mask.crop((0,y0,mask.width,y1)).getbbox();assert box
 detail=detail.crop((max(0,box[0]-40),max(0,y0-40),min(detail.width,box[2]+40),min(detail.height,y1+40)))
 detail=ImageOps.contain(detail,(380,270));sheet.paste(detail,(x+(380-detail.width)//2,660+(270-detail.height)//2));d.text((x+15,945),name,(22,34,47),font=font)
 d.text((x+15,990),'Driver · Iron · Wedge · Putter',(69,82,94),font=small)
sheet.save(P/'clubhouse-clubs.png')
balls=Image.new('RGB',(1600,480),(239,242,244));d=ImageDraw.Draw(balls)
for i,(style,name) in enumerate([('orbit','ORBIT'),('melon','WATERMELON'),('checker','RACE DAY'),('sunset','SUNSET')]):
 im=Image.open(P/f'ball_{style}.png').convert('RGB');im.thumbnail((380,400));balls.paste(im,(i*400+10,10));d.text((i*400+30,430),name,(22,34,47),font=font)
balls.save(P/'clubhouse-balls.png')
print('Wrote actual Unity review sheets')
