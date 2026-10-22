import numpy as np, soundfile as sf, random, os
from scipy.signal import resample_poly
SR=44100; U='../../Unity/Assets/Resources/Audio/v2/sfx/'; random.seed(3)
out=np.zeros(30*SR)
def clip(n): return sf.read(U+n+'.wav')[0]
last={}
def play(n,t,vol=1.0,pitch=1.0,var=True):
    base=n; v=random.choice([1,2]) if n.split('/')[0]!='crowd' else 1
    if last.get(base)==v: v=3-v
    last[base]=v
    x=clip(f'{n}_{v}')
    p=pitch*random.uniform(.97,1.03); x=resample_poly(x,1000,int(round(1000*p)))*vol
    o=int(t*SR); out[o:o+len(x)]+=x[:len(out)-o]
# tennis rally 0-14 s
t=.5; play('tennis/serve',t,.9); t+=.5
for i in range(1,9):
    pr=1.0
    play('tennis/bounce',t+.35,.5,pr)
    grade=('tennis/hit_soft','tennis/hit_sweet','tennis/hit_sweet','tennis/hit_perfect')[min(3,i//2)]
    if i%2: play('tennis/rival',t+.7,.7,pr)
    else: play(grade,t+.7,.9,pr)
    if i==8: play('tennis/hit_perfect',t+.7,1,pr)
    t+=1.2
play('tennis/smash',t+.3,1); play('tennis/whiff',t+2.4,.8); play('crowd/tennis_applause_short',t+3,.6,1)
# golf hole 15-30 s
g=15.5
play('golf/swing',g,.6); play('golf/driver',g+.4,1); play('golf/perfect',g+13.2,1)
play('golf/thud',g+3.8,.6); play('crowd/golf_clap',g+4.2,.5)
play('golf/swing',g+6,.5); play('golf/wedge',g+6.4,.9); play('crowd/golf_ooh',g+7.6,.5)
play('golf/putter',g+9,.8); play('golf/cup',g+11.4,1); play('crowd/golf_erupt',g+11.6,.7)
out*=0.89/max(.89,np.abs(out).max()) if np.abs(out).max()>.89 else 1
sf.write(os.path.expanduser('~/Desktop/sfx_demo.wav'),out,SR,subtype='PCM_16'); print('peak',np.abs(out).max())
