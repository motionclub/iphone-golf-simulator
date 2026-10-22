from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
W=Path(__file__).resolve().parents[1];R=W.parents[1];A=W/'after_final';B=W/'before_verified';D=R/'ArtDir/screenshots/cloth_overhaul';D.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',22)
def panel(im,size):
 im=im.copy();im.thumbnail(size);out=Image.new('RGB',size,'#eef0f3');out.paste(im,((size[0]-im.width)//2,(size[1]-im.height)//2));return out
views=['collar','sleeve','waist','drawcord','vent_detail','pocket_detail','bottom_front','bottom_side','bottom_back','bottom_other','sock','shoe','shoe_side','sole','full_front','full_back','full_threequarter','match_behind','opponent','match_phone']
for sex in ['male','female']:
 for view in views:
  f=sex+'_'+view
  if not(A/(f+'.png')).exists() or not(B/(f+'.png')).exists():continue
  size=(580,1255) if view in ['opponent','match_phone'] else (960,540) if view=='match_behind' else (760,760)
  out=Image.new('RGB',(size[0]*2,size[1]+45),'#eef0f3');d=ImageDraw.Draw(out)
  for i,(path,label) in enumerate([(B,'BEFORE'),(A,'AFTER')]):out.paste(panel(Image.open(path/(f+'.png')),size),(i*size[0],45));d.text((i*size[0]+15,10),f'{sex} {view} — {label}',font=font,fill='black')
  out.save(D/('SHEET_'+f+'.png'))
items=[
 ('Male collar roll','male_collar',(40,355,1035,720)),('Male real buttons','male_collar',(510,630,740,1079)),('Male rib cuff / trim','male_sleeve',(0,810,420,1079)),('Male double hem stitch','male_vent_detail',(100,690,880,945)),('Male open side vent','male_vent_detail',(250,735,635,955)),('Male waistband / drawcord','male_drawcord',(390,425,735,700)),('Male recessed pocket opening','male_pocket_detail',(170,230,950,830)),('Male turned shorts hem','male_bottom_front',(340,805,1000,1079)),
 ('Female collar / placket','female_collar',(100,375,1000,1050)),('Female rib cuff / trim','female_sleeve',(0,835,370,1079)),('Female knife pleats','female_bottom_back',(140,190,990,960)),('Female waistband','female_bottom_back',(200,0,900,255)),('Female stitched hem','female_bottom_side',(75,575,735,835)),
]
for sex in ['male','female']:
 items +=[(sex.title()+' rib sock cuff',sex+'_sock',(620,290,1079,625)),(sex.title()+' flat shoe laces',sex+'_shoe',(290,355,675,665)),(sex.title()+' toe cap',sex+'_shoe',(240,610,650,860)),(sex.title()+' shoe panel stitching',sex+'_shoe_side',(65,600,990,740)),(sex.title()+' foam midsole',sex+'_shoe_side',(65,640,990,830)),(sex.title()+' rubber herringbone tread',sex+'_sole',(120,160,970,1030))]
out=Image.new('RGB',(2100,5*370),'#eef0f3');d=ImageDraw.Draw(out);records=[]
for i,(label,stem,rect) in enumerate(items):
 if not(A/(stem+'.png')).exists():continue
 im=Image.open(A/(stem+'.png')).crop(rect);out.paste(panel(im,(410,325)),((i%5)*420,(i//5)*370+35));d.text(((i%5)*420+8,(i//5)*370+7),label,font=font,fill='black');records.append({'label':label,'source':str((A/(stem+'.png')).resolve()),'crop_xyxy':rect})
out.save(D/'CONSTRUCTION_SHEET.png');(W/'construction_crops.json').write_text(json.dumps(records,indent=2))
# Fabric close-ups use the actual shader; the ID table lives in GARMENT_SPEC.
fabrics=[('Pique — smooth .10 / sheen .55','male_sleeve',(80,350,290,640)),('Rib — smooth .13 / sheen .38','male_collar',(120,540,415,755)),('Mesh — smooth .16 / sheen .24','male_shoe_side',(410,300,770,545)),('Rubber — smooth .04 / sheen 0','male_sole',(290,340,650,700))]
out=Image.new('RGB',(1680,465),'#eef0f3');d=ImageDraw.Draw(out)
for i,(label,f,rect) in enumerate(fabrics):out.paste(panel(Image.open(A/(f+'.png')).crop(rect),(410,410)),(i*420,50));d.text((i*420+5,7),label,font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18),fill='black')
out.save(D/'FABRIC_SHEET.png')
# All eight catalog picks plus black/white, three independently picked roles, both sexes.
palette=['F2F2F0','3FA9F5','1E2A6E','9EE63A','FFC233','FF6B4A','8A4FFF','2E3138','000000','FFFFFF']
out=Image.new('RGB',(10*180,6*325),'#eef0f3');d=ImageDraw.Draw(out)
for row,(sex,group) in enumerate((s,g) for s in ['male','female'] for g in ['shirt','shorts','shoes']):
 for col,pick in enumerate(palette):
  im=Image.open(A/'palette'/(f'{sex}_{group}_{pick}.png'));out.paste(panel(im,(178,295)),(col*180,row*325+30));d.text((col*180+3,row*325+5),f'{sex} {group} #{pick}',font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',12),fill='black')
out.save(D/'RECOLOUR_GRID.png')
# Four views of the skirt artifact.
out=Image.new('RGB',(4*470,2*520),'#eef0f3');d=ImageDraw.Draw(out)
for row,(path,label) in enumerate([(B,'BEFORE'),(A,'AFTER')]):
 for col,v in enumerate(['front','side','back','other']):out.paste(panel(Image.open(path/('female_bottom_'+v+'.png')),(465,465)),(col*470,row*520+40));d.text((col*470+6,row*520+8),f'{label} — {v}',font=font,fill='black')
out.save(D/'SKORT_FOUR_VIEWS.png')
print('Sheets written to',D)
