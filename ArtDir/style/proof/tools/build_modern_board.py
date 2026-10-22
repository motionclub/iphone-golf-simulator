"""Companion BEFORE | AFTER | MODERN REF board using the supplied local refs.
Usage: BEFORE AFTER OUTPUT.jpg. No generated or retouched game imagery.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import sys
before,after,out=map(Path,sys.argv[1:]);out.parent.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[4];refs=root/'ArtDir/environment/targets-2026-10-14/refs'
shots=[('tennis_resort_4_surface','modern_mariotennisfever_2026_academy_court.jpg'),
       ('golf_07_clear_1_tee_gameplay','modern_mariokartworld_2025_grass_meadow.jpg'),
       ('golf_12_clear_2_approach','modern_astrobot_2024_water_sky.jpg'),
       ('golf_17_clear_3_green','modern_dkbananza_2025_snow.jpg'),
       ('golf_22_clear_2_approach','modern_dkbananza_2025_warm_canyon.jpg'),
       ('hub_2_walk','modern_tinyglade_2024_cozy_village.jpg')]
w,h=480,270;f=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
sheet=Image.new('RGB',(w*3,38+len(shots)*(h+40)),'#eff1f5');d=ImageDraw.Draw(sheet)
for col,title in enumerate(['BEFORE','AFTER','MODERN REF — supplied fidelity reference']):d.text((col*w+6,10),title,font=f,fill='#19212c')
for row,(name,ref) in enumerate(shots):
    y=38+row*(h+40)
    for col,path in enumerate([before/(name+'.png'),after/(name+'.png'),refs/ref]):
        im=Image.open(path).convert('RGB');im=ImageOps.contain(im,(w,h),Image.Resampling.LANCZOS)
        sheet.paste(im,(col*w+(w-im.width)//2,y+(h-im.height)//2))
    d.text((6,y+h+5),name+' | '+ref.replace('modern_','').replace('.jpg',''),font=f,fill='#19212c')
sheet.save(out,quality=94);print(out)
