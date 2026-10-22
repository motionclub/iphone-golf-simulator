from PIL import Image, ImageDraw, ImageFont
import json
R='/workspace/juice/his_refs/'
# regions as fractional boxes (x0,y0,x1,y1)
regions={
'r1':{'sky_upper':(.45,.06,.58,.14),'sky_horizon_glow':(.72,.17,.8,.23),'stone_lit':(.45,.75,.6,.9),'stone_shade':(.0,.9,.12,1.0),'roof_navy':(.08,.25,.14,.29),'foliage':(.04,.14,.1,.2),'glow_window!':(.025,.31,.06,.36)},
'r2':{'sky_top':(.1,.0,.3,.08),'cloud':(.65,.02,.78,.12),'haze_islands':(.55,.30,.62,.36),'water_far':(.25,.40,.5,.44),'court':(.55,.65,.9,.8),'court_surround':(.0,.63,.08,.7),'line_white!':(.495,.60,.505,.70),'foliage_palm':(.27,.12,.31,.17),'stone_deck':(.0,.56,.05,.6)},
'r3':{'sky_top':(.1,.0,.3,.06),'haze_mountains':(.25,.22,.32,.27),'water':(.12,.33,.22,.36),'grass_lit_stripe':(.6,.75,.8,.85),'grass_far':(.45,.40,.6,.45),'grass_shadow':(.1,.8,.25,.95),'foliage':(.88,.05,.97,.25)},
'r4':{'rooftop_sky':(.15,.04,.25,.12),'neon_window!':(.0,.05,.08,.25),'rooftop_court':(.15,.35,.3,.45),'volcano_sky':(.6,.02,.8,.1),'volcano_court':(.6,.36,.8,.42),'ice':(.1,.75,.35,.95),'snow_sky':(.1,.52,.3,.58),'magma_lava!':(.50,.68,.56,.76),'magma_rock':(.86,.8,.9,.86)},
'r5':{'rain_sky':(.05,.02,.25,.1),'rain_grass':(.2,.38,.35,.45),'storm_sky':(.65,.02,.85,.1),'storm_grass':(.7,.38,.85,.45),'fog_sky':(.05,.52,.25,.6),'fog_grass':(.2,.88,.35,.95),'gusty_sky':(.65,.52,.85,.6),'gusty_grass':(.7,.88,.85,.95)},
}
hexs=lambda c:'#%02X%02X%02X'%tuple(c[:3])
out={}
for k,regs in regions.items():
  im=Image.open(R+k+'.png').convert('RGB'); W,H=im.size
  q=im.resize((400,225)).quantize(8,method=Image.Quantize.MEDIANCUT,kmeans=4)
  pal=q.getpalette()[:24]; cnt=sorted(q.getcolors(),reverse=True)
  km=[(n,hexs(pal[i*3:i*3+3])) for n,i in cnt]
  rs={}
  dbg=im.copy(); d=ImageDraw.Draw(dbg)
  for name,(a,b,c,e) in regs.items():
    box=(int(a*W),int(b*H),int(c*W),int(e*H)); crop=im.crop(box)
    # median color
    px=sorted(crop.getdata(),key=lambda p:sum(p)); m=px[int(len(px)*.92)] if name.endswith('!') else px[len(px)//2]; name=name.rstrip('!')
    rs[name]=hexs(m); d.rectangle(box,outline='red',width=3); d.text((box[0]+3,box[1]+3),name,fill='red')
  dbg.resize((836,470)).save(f'dbg_{k}.jpg')
  out[k]={'kmeans':[h for n,h in km],'regions':rs}
json.dump(out,open('palette.json','w'),indent=1)
# swatch image
font=ImageFont.load_default()
rows=sum(1+1 for k in out); S=70
img=Image.new('RGB',(1600,len(out)*230+20),'white'); d=ImageDraw.Draw(img)
y=10
for k,v in out.items():
  d.text((10,y),k+' k-means (by area)',fill='black',font=font)
  for i,h in enumerate(v['kmeans']):
    d.rectangle((10+i*120,y+15,120+i*120,y+70),fill=h); d.text((12+i*120,y+73),h,fill='black',font=font)
  y+=95; d.text((10,y),k+' regions',fill='black',font=font)
  for i,(n,h) in enumerate(v['regions'].items()):
    d.rectangle((10+i*170,y+15,170+i*170,y+70),fill=h); d.text((12+i*170,y+73),n,fill='black',font=font); d.text((12+i*170,y+86),h,fill='black',font=font)
  y+=135
img.save('ART_BIBLE_palette.png')
print(json.dumps(out,indent=1))
