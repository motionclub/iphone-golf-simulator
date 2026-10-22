import numpy as np, soundfile as sf, random, os, shutil
from scipy.signal import resample_poly
SR=44100; U='../../Unity/Assets/Resources/Audio/v2/sfx/'; random.seed(5)
out=np.zeros(30*SR); last={}
def play(n,t,vol=1.0):
    v=1 if n.startswith('crowd') else random.choice([1,2])
    if last.get(n)==v and not n.startswith('crowd'): v=3-v
    last[n]=v
    x=sf.read(U+f'{n}_{v}.wav')[0]; p=random.uniform(.97,1.03)
    x=resample_poly(x,1000,int(round(1000*p)))*vol; o=int(t*SR); out[o:o+len(x)]+=x[:len(out)-o]
t=.6; play('tennis/serve',t); t+=.6
seq=['hit_normal','hit_normal','hit_sweet','hit_normal','hit_sweet','hit_normal','mishit','hit_sweet']
for i,h in enumerate(seq):
    play('tennis/bounce' if i!=3 else 'tennis/bounce_clay',t+.3,.9)
    if i%2: play('tennis/hit_normal' if h=='hit_normal' else 'tennis/'+h,t+.65,.9)
    else: play('tennis/'+h,t+.65,1)
    t+=1.15
play('tennis/net_cord',t+.2,1); play('tennis/smash',t+1.4,1); play('tennis/whiff',t+3.0,1)
g=15.8
play('golf/swing',g,.8); play('golf/driver',g+.45,1); play('golf/land_fairway',g+3.6,1)
play('golf/swing',g+5.2,.8); play('golf/wedge',g+5.6,1); play('golf/land_green',g+7.0,1)
play('golf/putter',g+9.0,1); play('golf/cup',g+10.9,1); play('crowd/golf_erupt',g+11.2,.8)
pk=np.abs(out).max(); out*=0.89/pk if pk>.89 else 1
D=os.path.expanduser('~/Desktop/SFX_Review'); shutil.rmtree(D,ignore_errors=True); os.makedirs(D)
sf.write(D+'/00_demo_rally_and_golf_hole.wav',out,SR,subtype='PCM_16')
new=['tennis/hit_normal','tennis/hit_sweet','tennis/smash','tennis/mishit','tennis/serve','tennis/bounce','tennis/bounce_clay','tennis/net_cord','tennis/whiff',
 'golf/driver','golf/iron','golf/wedge','golf/putter','golf/mishit','golf/swing','golf/land_fairway','golf/land_green','golf/land_sand','golf/land_water','golf/cup',
 'ui/confirm','ui/cancel','ui/tick','ui/point_win','ui/point_lose']
for n in new:
    for v in (1,2): shutil.copy(U+f'{n}_{v}.wav',D+f"/{n.replace('/','_')}_{v}.wav")
print(len(os.listdir(D)),'files')
