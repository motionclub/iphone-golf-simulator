# lighting tweak set: one squad (tennis resort), six looks; each = v2 base + overrides
import json, copy, make2
from PIL import Image
from squad_v2 import squad, COLS
BASE=json.load(open('v2_tune.json'))
V=[
 ("venue","Venue sun (v2)",{}),
 ("golden","Golden hour",dict(sunAzEl=[70,22],sunColor=[1.0,0.76,0.52],warm=0.07,sat=1.2,fill=850,shadowAlpha=0.55)),
 ("midday","Bright midday",dict(sunAzEl=[35,55],sunColor=[1.0,0.96,0.9],fill=1050,sky=520,warm=0.02,con=1.0,sat=1.08,expo=1.55)),
 ("punchy","Punchy",dict(sun=1150,fill=760,con=1.12,sat=1.2,shadowAlpha=0.66,warm=0.04)),
 ("backlit","Backlit glow",dict(sunAzEl=[155,35],sunColor=[1.0,0.84,0.62],rim=1500,rimColor=[1.0,0.86,0.66],fill=1250,sky=480,expo=1.6,warm=0.05,sat=1.15)),
 ("overcast","Soft overcast",dict(sun=430,sky=720,fill=1050,amb=320,con=1.0,sat=1.06,shadowAlpha=0.35,warm=0.02,expo=1.6)),
]
out={}
for key,label,ov in V:
    make2.T.clear(); make2.T.update(dict(sun=720,minEl=28,sky=330,fill=420,fillFloor=0.55,gnd=200,rim=260,amb=110,sat=1.18,con=1.10,warm=0.05,expo=1.0)); make2.T.update(BASE); make2.T.update(ov)
    img,heroes,_=make2.render("tw_"+key,"tennis-resort",squad("tennis",COLS))
    img.save(f"../img/tw_{key}.jpg",quality=86)
    img.crop((840,360,1080,940)).resize((240,580)).save(f"../img/tw_{key}_lead.jpg",quality=88)
    out[key]=dict(label=label,leader=make2.measure(heroes,(860,390,1060,930)),darkest=make2.measure(heroes,(240,420,400,830)),face=make2.face(img,(930,405,980,450)))
    print(key,out[key])
json.dump(out,open('../renders/tweaks.json','w'),indent=1)
