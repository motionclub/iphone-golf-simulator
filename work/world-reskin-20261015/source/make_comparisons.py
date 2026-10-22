from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1];proof=root/'proof';out=proof/'comparisons';out.mkdir(exist_ok=True)
font='/System/Library/Fonts/Supplemental/Arial.ttf'
def f(size):return ImageFont.truetype(font,size)
def board(name,title,before,after,width):
 a=Image.open(before).convert('RGB');b=Image.open(after).convert('RGB');assert a.size==b.size
 height=round(a.height*width/a.width);gap=20;pad=24;top=124
 canvas=Image.new('RGB',(width*2+gap+pad*2,height+top+64),'#0c2027');d=ImageDraw.Draw(canvas)
 d.text((pad,18),title,font=f(30),fill='#f2f5ea')
 d.text((pad,65),'BEFORE',font=f(20),fill='#aec8cf');d.text((pad+width+gap,65),'AFTER · PILOT',font=f(20),fill='#b6ebce')
 canvas.paste(a.resize((width,height),Image.Resampling.LANCZOS),(pad,top));canvas.paste(b.resize((width,height),Image.Resampling.LANCZOS),(pad+width+gap,top))
 d.text((pad,top+height+20),'Actual Unity renders · matched camera · live animation and water phase may differ',font=f(17),fill='#aec8cf')
 canvas.save(out/name)
board('Golf_before_after.png','LUMINOUS COAST / GOLF 12',proof/'before-final/golf/hole12_showcase_085.png',proof/'after/golf/hole12_showcase_085.png',600)
board('Golf_gameplay_before_after.png','GOLF 12 / GAMEPLAY',proof/'before-final/golf/hole12_gameplay.png',proof/'after/golf/hole12_gameplay.png',600)
board('Tennis_before_after.png','LUMINOUS COAST / RESORT TENNIS',proof/'before-final/tennis/resort_1_gameplay.png',proof/'after/tennis/resort_1_gameplay.png',960)
board('Tennis_portrait_before_after.png','RESORT TENNIS / PHONE FRAMING',proof/'portrait-before/resort/resort_1_gameplay.png',proof/'portrait-after/resort/resort_1_gameplay.png',600)
board('Golf_aerial_before_after.png','GOLF 12 / COASTAL COMPOSITION',proof/'before-final/golf/hole12_showcase_039.png',proof/'after/golf/hole12_showcase_039.png',600)

board('Golf_overview_before_after.png','GOLF 12 / WHOLE HOLE',proof/'before-final/golf/hole12_preview.png',proof/'after/golf/hole12_preview.png',900)

board('Golf_bridge_before_after.png','GOLF 12 / ISLANDS AND BRIDGE',proof/'before-final/golf/hole12_showcase_025.png',proof/'after/golf/hole12_showcase_025.png',600)
