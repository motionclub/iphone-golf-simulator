import sys, colorsys
from PIL import Image, ImageChops
import statistics
base='review_R/out2/shots/'
def px(f): return Image.open(f).convert('RGB')
# determinism vs builder
for n in ['crater_lava_phone','crater_lava_down','crater_basalt_noemission','crater_wall_lights_on','sea_hole09_aerial','smoke_card']:
    a=px(base+n+'.jpg'); b=px('runtime/shots/s26/'+n+'.jpg')
    d=ImageChops.difference(a,b); print(n,'maxdiff',max(d.getextrema(), key=lambda e:e[1]))
def hsv_stats(f, region=None):
    im=px(f)
    if region: im=im.crop(region)
    data=list(im.getdata()); N=len(data)
    inband=0; clipG=0; cream=0; dark=0
    sr=sg=sb=0
    for r,g,b in data:
        h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255); h*=360
        sr+=r;sg+=g;sb+=b
        if 8<=h<=28 and s>=.75 and v>=.70: inband+=1
        if g>=250: clipG+=1
        if s<.5 and v>.8: cream+=1
        if v<.5: dark+=1
    print(f.split('/')[-1],region,'N',N,'mean',(round(sr/N),round(sg/N),round(sb/N)),'inband %.1f%%'%(100*inband/N),'Gclip %.2f%%'%(100*clipG/N),'cream %.2f%%'%(100*cream/N),'dark(v<.5) %.1f%%'%(100*dark/N))
hsv_stats(base+'crater_lava_phone.jpg',(0,700,900,1600))
hsv_stats(base+'crater_lava_down.jpg')
hsv_stats(base+'crater_wall_lights_on.jpg',(0,1230,900,1600))
