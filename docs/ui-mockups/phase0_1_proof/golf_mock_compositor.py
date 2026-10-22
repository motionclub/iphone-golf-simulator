from PIL import Image, ImageDraw, ImageFont, ImageChops
import math
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
S="/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/cddc3a97-f5d7-4f60-9f94-f545502cacdd/scratchpad/shots"
FONT=f"{R}/Unity/Assets/Resources/Fonts/Club/Rubik-ExtraBold.ttf"
K=2
OUT=(21,87,184); WHITE=(255,255,255); GOLD=(245,197,66); DARK=(6,61,45); BLUE=(42,132,230)
GREEN=(125,224,122); ORANGE=(255,154,74); SKY=(127,209,255); LIME=(215,240,68); CORAL=(255,91,74)
def font(sz): return ImageFont.truetype(FONT,int(sz*K))
class Ui:
    def __init__(s): s.im=Image.new("RGBA",(1920*K,1080*K),(0,0,0,0)); s.d=ImageDraw.Draw(s.im)
    def text(s,xy,t,size,fill=WHITE,anchor="la",outline=OUT,stroke=None,rot=0,spacing=0.9,align="left"):
        w=stroke if stroke is not None else max(1.6,min(4.5,size*.075)); x,y=xy; f=font(size)
        layer=Image.new("RGBA",s.im.size,(0,0,0,0)); d=ImageDraw.Draw(layer)
        kw=dict(font=f,anchor=anchor,stroke_width=int(w*K),align=align)
        if "\n" in t: kw["spacing"]=int(size*K*(spacing-.8))
        fn=d.multiline_text if "\n" in t else d.text
        fn((x*K,(y+w*2.2)*K),t,fill=outline+(170,),stroke_fill=outline+(170,),**kw)
        fn((x*K,y*K),t,fill=fill+(255,),stroke_fill=outline+(255,),**kw)
        if rot: layer=layer.rotate(rot,center=(x*K,y*K),resample=Image.BICUBIC)
        s.im.alpha_composite(layer)
    def circle(s,c,r,fill,ring=None,rw=0,shadow=True):
        x,y=c
        if shadow: s.d.ellipse([(x-r-rw)*K,(y-r-rw+7)*K,(x+r+rw)*K,(y+r+rw+7)*K],fill=(0,8,30,80))
        if ring: s.d.ellipse([(x-r-rw)*K,(y-r-rw)*K,(x+r+rw)*K,(y+r+rw)*K],fill=ring+(255,))
        s.d.ellipse([(x-r)*K,(y-r)*K,(x+r)*K,(y+r)*K],fill=fill+(255,))
    def button(s,box,fill,rim=WHITE,rw=5,radius=26):
        x0,y0,x1,y1=box
        s.d.rounded_rectangle([x0*K,(y0+8)*K,x1*K,(y1+8)*K],radius=radius*K,fill=(0,8,30,85))
        s.d.rounded_rectangle([(x0-rw)*K,(y0-rw)*K,(x1+rw)*K,(y1+rw)*K],radius=(radius+rw)*K,fill=rim+(255,))
        s.d.rounded_rectangle([x0*K,y0*K,x1*K,y1*K],radius=radius*K,fill=fill+(255,))
    def line(s,x0,x1,y,w=3,color=WHITE):
        s.d.line([x0*K,(y+3)*K,x1*K,(y+3)*K],fill=OUT+(150,),width=int((w+4)*K))
        s.d.line([x0*K,y*K,x1*K,y*K],fill=color+(255,),width=int(w*K))
    def flat(s,t,xy,size,color=DARK,anchor="mm"): s.d.text((xy[0]*K,xy[1]*K),t,font=font(size),fill=color+(255,),anchor=anchor)
    def final(s): return s.im.resize((1920,1080),Image.LANCZOS)

def icon(u,kind,c,r=52,color=WHITE):
    x,y=c; d=u.d
    u.circle(c,r,{"green":(92,194,58),"fairway":BLUE,"rough":(47,110,43),"bunker":(241,211,140),"water":(42,139,234),"oob":(224,53,47)}[kind],WHITE,6)
    if kind=="green":
        d.line([(x-8)*K,(y+30)*K,(x-8)*K,(y-30)*K],fill=WHITE+(255,),width=int(6*K)); d.polygon([((x-8)*K,(y-30)*K),((x+26)*K,(y-18)*K),((x-8)*K,(y-6)*K)],fill=(232,53,47,255))
    elif kind=="fairway" or kind=="bunker":
        d.ellipse([(x-16)*K,(y-16)*K,(x+16)*K,(y+16)*K],fill=WHITE+(255,),outline=(150,170,190,255),width=int(3*K))
    elif kind=="rough":
        for dx,ang in ((-14,-14),(0,0),(14,14)): d.line([(x+dx)*K,(y+26)*K,(x+dx+ang*.5)*K,(y-24)*K],fill=(184,240,106,255),width=int(7*K))
    elif kind=="water":
        d.ellipse([(x-22)*K,(y-8)*K,(x+22)*K,(y+32)*K],fill=WHITE+(255,)); d.polygon([((x-19)*K,(y+2)*K),((x+19)*K,(y+2)*K),(x*K,(y-34)*K)],fill=WHITE+(255,))
    elif kind=="oob": u.text((x,y+4),"!",64,anchor="mm",outline=(115,13,13),stroke=3)

def build(plate,fn,dim=0):
    u=Ui(); 
    base=plate.convert("RGBA")
    if dim: base=Image.alpha_composite(base,Image.new("RGBA",base.size,(0,18,40,int(255*dim))))
    fn(u); return Image.alpha_composite(base,u.final()).convert("RGB")

# ---------- A. strike word
def strike(word,col,shape,cy=150):
    def f(u):
        u.text((960,cy),word,172,fill=col,anchor="mm",stroke=7,rot=3)
        if shape: u.text((960,cy+118),shape,54,anchor="mm",stroke=3.5,rot=3)
    return f
# ---------- B. landing
LAND={"GREEN":("green",(125,224,90),"142 YD TO PIN","CARRY 238 YD · TOTAL 261 YD"),
      "FAIRWAY":("fairway",WHITE,"121 YD TO PIN","CARRY 224 YD · TOTAL 248 YD"),
      "ROUGH":("rough",(184,240,106),"168 YD TO PIN","CARRY 201 YD · TOTAL 207 YD"),
      "BUNKER":("bunker",(241,211,140),"34 YD TO PIN","CARRY 169 YD · TOTAL 169 YD"),
      "WATER":("water",(108,184,255),"+1 PENALTY","CARRY 232 YD"),
      "OUT OF BOUNDS":("oob",(255,110,98),"+1 PENALTY · REPLAY FROM TEE","CARRY 251 YD")}
def landing(name):
    kind,col,detail,stats=LAND[name]
    def f(u):
        sz=124 if len(name)<9 else 96
        wd=font(sz).getlength(name)/K
        icon(u,kind,(960+60-wd/2-92,292))
        u.text((960+60,290),name,sz,fill=col,anchor="mm",stroke=6,rot=2)
        u.text((960,402),detail,56,fill=GOLD,anchor="mm",stroke=4)
        u.text((960,470),stats,34,anchor="mm",stroke=2.6)
    return f
# ---------- C. shot result (top right) + footer
def shot_result(u):
    X=1884
    u.text((X,40),"ADNAN · FAIRWAY",30,fill=GOLD,anchor="ra")
    u.text((X,78),"248 yd",110,anchor="ra",stroke=6)
    u.text((X,206),"TOTAL DISTANCE",26,anchor="ra"); u.text((X,240),"CARRY  224 yd",26,anchor="ra")
    u.text((X,288),"ROLL  24 yd     APEX  41 yd",24,fill=GOLD,anchor="ra")
    u.text((X,336),"121 yd TO PIN",44,anchor="ra",stroke=3.4)
    u.text((1664,840),"CHOOSE AN EMOTE",22,anchor="ma")
    for i,l in enumerate(("WAVE","SCUBA","SPIKE")):
        cx=1664+(i-1)*150; u.button((cx-70,880,cx+70,952),GOLD,radius=24); u.flat(l,(cx,917),24)
    u.button((1444,974,1884,1054),BLUE,radius=28); u.text((1664,1014),"NEXT SHOT",36,anchor="mm",stroke=0.01,outline=BLUE)
# ---------- D. hole-out
def holeout(u):
    u.circle((560,170),104,BLUE,WHITE,10); u.text((560,160),"4",110,anchor="mm",stroke=5); u.text((560,232),"STROKES",24,anchor="mm",stroke=2)
    u.text((1180,170),"PAR",200,fill=SKY,anchor="mm",stroke=8,rot=2)
    u.text((960,326),"HOLE 1 OF 5  ·  CLIFFSIDE",38,anchor="mm"); u.text((960,372),"PAR 4  ·  HOLED FROM 14 FT",32,fill=GOLD,anchor="mm",stroke=2.6)
    xs=[640+i*150 for i in range(5)]; tx=1520
    for y,l in ((470,"HOLE"),(570,"PAR"),(670,"YOU")): u.text((330,y),l,28,anchor="lm",stroke=2.4)
    u.line(300,1640,520,3,(255,255,255)); u.line(300,1640,620,3,(255,255,255))
    pars=[4,4,5,3,3]
    for i,x in enumerate(xs):
        cur=i==0; c=GOLD if cur else WHITE
        u.text((x,470),str(i+1),50,fill=c,anchor="mm"); u.text((x,570),str(pars[i]),50,fill=c,anchor="mm")
        u.text((x,670),"4" if cur else "–",54 if cur else 44,fill=c,anchor="mm")
    u.d.rounded_rectangle([(xs[0]-34)*K,718*K,(xs[0]+34)*K,726*K],radius=4*K,fill=GOLD+(255,))
    u.text((tx,470),"TOTAL",28,anchor="mm",stroke=2.4); u.text((tx,570),"19",50,fill=GOLD,anchor="mm"); u.text((tx,670),"4",54,fill=GOLD,anchor="mm"); u.text((tx+34,684),"E",24,anchor="lm",stroke=2)
    for i,l in enumerate(("WAVE","SCUBA","SPIKE")):
        cx=960+(i-1)*290; u.button((cx-120,770,cx+120,836),GOLD,radius=26); u.flat(l,(cx,803),26)
    u.button((560,900,1360,1030),GOLD,radius=34); u.flat("NEXT HOLE  ›",(960,946),56)
    u.flat("2  ·  NEEDLE  ·  PAR 4  ·  343 YD",(960,1000),26)
    u.d.rounded_rectangle([600*K,1018*K,1320*K,1024*K],radius=3*K,fill=(6,61,45,70)); u.d.rounded_rectangle([600*K,1018*K,1230*K,1024*K],radius=3*K,fill=DARK+(255,))
def glyph(u,i,c):
    x,y=c; d=u.d
    if i==0:
        pts=[]
        for k in range(10):
            a=-math.pi/2+k*math.pi/5; rr=26 if k%2==0 else 11; pts.append(((x+rr*math.cos(a))*K,(y+rr*math.sin(a)+2)*K))
        d.polygon(pts,fill=WHITE+(255,))
    elif i==1:
        d.line([(x-20)*K,(y+16)*K,(x+16)*K,(y-16)*K],fill=WHITE+(255,),width=int(8*K)); d.polygon([((x+22)*K,(y-22)*K),((x+22)*K,(y+2)*K),((x-2)*K,(y-22)*K)],fill=WHITE+(255,))
    else:
        d.ellipse([(x-18)*K,(y-8)*K,(x+18)*K,(y+28)*K],fill=WHITE+(255,)); d.line([(x+4)*K,(y+10)*K,(x+4)*K,(y-30)*K],fill=WHITE+(255,),width=int(6*K)); d.polygon([((x+4)*K,(y-30)*K),((x+26)*K,(y-22)*K),((x+4)*K,(y-14)*K)],fill=(232,53,47,255))
# ---------- E. round card
def roundcard(u):
    L=140
    u.text((L,60),"ROUND COMPLETE",40,anchor="la"); u.text((L,106),"2 under par",170,fill=GOLD,anchor="la",stroke=7)
    xs=[520+i*150 for i in range(5)]; tx=1380
    pars=[4,4,5,3,3]; you=[4,3,5,3,2]
    for y,l in ((380,"HOLE"),(480,"PAR"),(580,"YOU")): u.text((L,y),l,30,anchor="lm",stroke=2.4)
    u.line(L-10,1500,430,3); u.line(L-10,1500,530,3)
    for i,x in enumerate(xs):
        u.text((x,380),str(i+1),50,anchor="mm"); u.text((x,480),str(pars[i]),50,anchor="mm")
        s=you[i]
        if s<pars[i]: u.d.ellipse([(x-34)*K,(580-34)*K,(x+34)*K,(580+34)*K],outline=LIME+(255,),width=int(6*K))
        u.text((x,580),str(s),54,fill=GOLD if s<pars[i] else WHITE,anchor="mm")
    u.text((tx,380),"TOTAL",30,anchor="mm",stroke=2.4); u.text((tx,480),"19",50,anchor="mm"); u.text((tx,580),"17",56,fill=GOLD,anchor="mm"); u.text((tx+44,594),"−2",28,fill=LIME,anchor="lm",stroke=2.4)
    for i,(t,v) in enumerate((("PERFECT STRIKES","3"),("LONGEST DRIVE","268 yd"),("FAIRWAYS HIT","4 / 5"))):
        cx=L+150+i*440; u.circle((cx-120,740),44,BLUE,WHITE,5)
        glyph(u,i,(cx-120,740))
        u.text((cx-56,712),t,26,anchor="lm",stroke=2.2); u.text((cx-56,762),v,56,fill=GOLD,anchor="lm")
    u.button((L,880,L+560,980),GOLD,radius=30); u.flat("PLAY AGAIN",(L+280,930),46)
    u.button((L+620,880,L+1100,980),BLUE,radius=30); u.text((L+860,930),"MAIN MENU",42,anchor="mm",stroke=0.01,outline=BLUE)
# ---------- F. events
def events(u):
    u.text((960,110),"Gust!",130,fill=(120,200,255),anchor="mm",stroke=6)
    u.text((960,214),"WIND NOW 12 MPH  ·  LEFT → RIGHT",42,anchor="mm",stroke=3)
    u.text((960,300),"Bounty!  +50",64,fill=GOLD,anchor="mm",stroke=4)

p1=Image.open(f"{S}/plate_hole1.png"); p7=Image.open(f"{S}/plate_hole7.png")
OUTS={}
def save(n,im): im.save(f"{S}/golf_{n}.png"); OUTS[n]=im
save("strike_perfect",build(p1,strike("PERFECT!",GOLD,"DRAW")))
words=[("PERFECT!",GOLD,"DRAW"),("GREAT!",GREEN,"FADE"),("GOOD",WHITE,"STRAIGHT"),("THIN",ORANGE,"SLICE")]
sheet=Image.new("RGB",(1920,1080))
for i,(w,c,sh) in enumerate(words):
    sheet.paste(build(p1,strike(w,c,sh,cy=170)).resize((960,540),Image.LANCZOS),((i%2)*960,(i//2)*540))
save("strike_words",sheet)
save("landing_fairway",build(p1,landing("FAIRWAY")))
ls=Image.new("RGB",(2880,1080))
for i,n in enumerate(LAND):
    ls.paste(build(p7,landing(n)).resize((960,540),Image.LANCZOS),((i%3)*960,(i//3)*540))
save("landing_sheet",ls)
save("shot_result",build(p1,shot_result))
save("holeout",build(p7,holeout,dim=.0))
save("roundcard",build(p7,roundcard,dim=.32))
save("events",build(p1,events))
