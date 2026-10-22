from PIL import Image, ImageDraw, ImageFont
import sys
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
S="/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/cddc3a97-f5d7-4f60-9f94-f545502cacdd/scratchpad/shots"
FONT=f"{R}/Unity/Assets/Resources/Fonts/Club/Rubik-ExtraBold.ttf"
K=2  # supersample
NAVY=(13,44,102); GOLD=(255,209,102); WHITE=(255,255,255); BLUE=(31,98,214); BLUE2=(52,120,236)
def font(sz): return ImageFont.truetype(FONT,int(sz*K))
class Ui:
    def __init__(s):
        s.im=Image.new("RGBA",(1920*K,1080*K),(0,0,0,0)); s.d=ImageDraw.Draw(s.im)
    def text(s,xy,t,size,fill=WHITE,anchor="la",outline=NAVY,stroke=None):
        w=stroke if stroke is not None else max(1.6,min(4,size*.075))
        x,y=xy; f=font(size)
        # drop under the lettering
        s.d.text((x*K,(y+w*2.2)*K),t,font=f,fill=outline+(170,),anchor=anchor,stroke_width=int(w*K),stroke_fill=outline+(170,))
        s.d.text((x*K,y*K),t,font=f,fill=fill+(255,),anchor=anchor,stroke_width=int(w*K),stroke_fill=outline+(255,))
    def circle(s,c,r,fill,ring=None,rw=0,shadow=True):
        x,y=c
        if shadow: s.d.ellipse([(x-r-rw)*K,(y-r-rw+7)*K,(x+r+rw)*K,(y+r+rw+7)*K],fill=(0,8,30,80))
        if ring: s.d.ellipse([(x-r-rw)*K,(y-r-rw)*K,(x+r+rw)*K,(y+r+rw)*K],fill=ring+(255,))
        s.d.ellipse([(x-r)*K,(y-r)*K,(x+r)*K,(y+r)*K],fill=fill+(255,))
    def capsule(s,box,fill,shadow=False):
        x0,y0,x1,y1=box; r=(x1-x0)/2
        if shadow: s.d.rounded_rectangle([x0*K,(y0+9)*K,x1*K,(y1+9)*K],radius=r*K,fill=(0,8,30,85))
        s.d.rounded_rectangle([x0*K,y0*K,x1*K,y1*K],radius=r*K,fill=fill+(255,))
    def final(s): return s.im.resize((1920,1080),Image.LANCZOS)

def scoreboard(u,you_g,you_p,riv_g,riv_p):
    u.text((40,40),"EXHIBITION · ONE SET",22)
    u.text((432,44),"GAMES",20,anchor="ma"); u.text((518,44),"PTS",20,anchor="ma")
    for y,name,g,p,server in ((112,"You",you_g,you_p,True),(176,"Rival",riv_g,riv_p,False)):
        if server: u.circle((70,y),13,(214,240,68),WHITE,3)
        u.text((92,y),name,38,anchor="lm")
        u.text((432,y),str(g),42,anchor="mm")
        u.text((518,y),str(p),52,fill=GOLD,anchor="mm")
    u.text((40,206),"SET 1",20)

def swing_button(u):
    c=(1822,846)
    u.circle(c,76,BLUE,WHITE,8)
    d=u.d
    d.ellipse([(c[0]-26)*K,(c[1]-62)*K,(c[0]+26)*K,(c[1]+8)*K],outline=WHITE+(255,),width=int(7*K))
    for dx in (-8,8): d.line([((c[0]+dx)*K),(c[1]-52)*K,((c[0]+dx)*K),(c[1]-2)*K],fill=WHITE+(255,),width=int(4*K))
    for dy in (-38,-22): d.line([((c[0]-18)*K),(c[1]+dy)*K,((c[0]+18)*K),(c[1]+dy)*K],fill=WHITE+(255,),width=int(4*K))
    d.line([c[0]*K,(c[1]+8)*K,c[0]*K,(c[1]+52)*K],fill=GOLD+(255,),width=int(11*K))
    u.text((c[0],c[1]+104),"SWING",28,anchor="ma")

def charge_dots(u,n=3):
    for i in range(n): u.circle((1656,920+50*i),21,GOLD,WHITE,5)

def serve_meter(u,load=.78):
    x0,x1,y0,y1=1747,1803,250,690
    u.capsule((x0-9,y0-9,x1+9,y1+9),WHITE,shadow=True)
    u.capsule((x0,y0,x1,y1),BLUE)
    fh=(y1-y0)*load
    u.capsule((x0+7,y1-fh,x1-7,y1-4),GOLD)
    # sweet spot block (timing window) near the top, with its own rim
    sy=y0+(y1-y0)*.06; sh=(y1-y0)*.12
    u.d.rounded_rectangle([(x0-12)*K,(sy-4)*K,(x1+12)*K,(sy+sh+4)*K],radius=16*K,outline=WHITE+(255,),width=int(5*K))
    u.circle(((x0+x1)/2,y1-fh),30,GOLD,WHITE,6)
    u.text(((x0+x1)/2,y0-58),"SERVE",30,anchor="ma")
    u.text(((x0+x1)/2,y1+34),"78%",38,anchor="ma")

def callout(u):
    u.text((960,96),"You scored",124,anchor="ma",stroke=5)
    u.text((960,238),"OUT  ·  15–0",40,anchor="ma",stroke=3.2)

def build(name,plate,fn):
    u=Ui(); fn(u)
    out=Image.alpha_composite(plate.convert("RGBA"),u.final()).convert("RGB")
    out.save(f"{S}/{name}.png"); return out

plate=Image.open(f"{S}/tennis_plate.png")
a=build("tennis_rally",plate,lambda u:(scoreboard(u,0,0,0,0),swing_button(u),charge_dots(u)))
b=build("tennis_serve",plate,lambda u:(scoreboard(u,0,0,0,15),serve_meter(u),swing_button(u),charge_dots(u)))
c=build("tennis_point",plate,lambda u:(scoreboard(u,0,15,0,0),callout(u),swing_button(u),charge_dots(u)))
