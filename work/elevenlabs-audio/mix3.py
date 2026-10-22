import os, glob, shutil, subprocess, numpy as np, soundfile as sf, pyloudnorm as pn, imageio_ffmpeg
from scipy.signal import resample_poly
FF = imageio_ffmpeg.get_ffmpeg_exe(); SR = 44100
U = os.path.abspath('../../Unity/Assets/Resources/Audio/v2/sfx'); BK = 'v2_backup'
if not os.path.exists(BK): shutil.copytree(U, BK)
meter = pn.Meter(SR)
def lufs(x):
    y = np.concatenate([x, np.zeros(max(0, SR - len(x)))]); 
    try: return meter.integrated_loudness(y)
    except Exception: return -40
def layer(name, take):
    subprocess.run([FF,'-y','-loglevel','quiet','-i',f'raw/v3/layers/{name}_{take}.mp3','-ac','1','-ar',str(SR),'/tmp/_l.wav'], check=True)
    x, _ = sf.read('/tmp/_l.wav'); a = np.where(np.abs(x) > np.abs(x).max()*.08)[0]
    return x[a[0]:] if len(a) else x   # align on the onset
def shift(x, st):
    if not st: return x
    r = 2**(st/12); return resample_poly(x, 1000, int(round(1000*r)))
def mix(recipe, take, length):
    out = np.zeros(int(length*SR)+SR)
    for lay, db, delay, st in recipe:
        x = shift(layer(lay, take), st) * 10**(db/20); o = int(delay*SR)
        out[o:o+len(x)] += x[:len(out)-o]
    out = out[:int(length*SR)]; n = int(.05*SR); out[-n:] *= np.linspace(1, 0, n)
    return out
def finish(x, target):
    x = x * 10**((target - lufs(x))/20)
    for _ in range(3):                         # soft-limit, re-match, keep peaks under -1 dBFS
        x = np.tanh(x*1.2)/np.tanh(1.2) if np.abs(x).max() > .8 else x
        x = x * 10**((target - lufs(x))/20)
        if np.abs(x).max() <= .891: break
    if np.abs(x).max() > .891: x = x*.891/np.abs(x).max()
    return x
# crowd reference: median loudness of the (untouched) crowd shots
cr = [lufs(sf.read(p)[0]) for p in glob.glob(U+'/crowd/*_1.wav') if 'murmur' not in p and 'swell' not in p and 'rally' not in p]
REF = float(np.median(cr)); print('crowd ref LUFS', round(REF, 1))
T = dict(soft=REF+1, normal=REF+2.5, sweet=REF+4, perfect=REF+6.5, big=REF+5, ui=REF+2.5-6, flight=REF+0)
R = {  # name: (recipe, length, tier)   recipe = (layer, dB, delay s, semitones)
 'tennis/hit_soft': ([('t_racket',-3,0,0),('b_soft',-6,0,0),('p_bell',-24,.01,0)], .30, 'soft'),
 'tennis/hit_sweet': ([('t_racket',0,0,0),('b_punch',-4,0,0),('p_bell',-10,.01,0)], .50, 'sweet'),
 'tennis/hit_perfect': ([('t_racket',0,0,0),('b_punch',-3,0,0),('p_ping',-6,.01,2),('p_chime',-9,.03,0),('w_up',-14,0,0)], .80, 'perfect'),
 'tennis/smash': ([('t_racket',2,0,0),('b_punch',1,0,-2),('p_ping',-6,.01,0),('w_up',-10,0,0)], .80, 'big'),
 'tennis/serve': ([('t_racket',0,0,0),('b_punch',-3,0,0),('w_up',-8,0,0),('p_bell',-12,.01,0)], .60, 'sweet'),
 'tennis/rival': ([('t_racket',-6,0,0),('b_soft',-4,0,0)], .30, 'soft'),
 'tennis/whiff': ([('w_up',-4,0,-3)], .50, 'normal'),
 'tennis/whiff_zap': ([('zap',0,0,0)], .50, 'normal'),
 'tennis/bounce': ([('boing',-4,0,0),('b_soft',-8,0,0)], .45, 'soft'),
 'tennis/bounce_clay': ([('boing',-6,0,-3),('b_soft',-6,0,0)], .45, 'soft'),
 'tennis/net_cord': ([('t_putter',-3,0,0),('boing',-12,0,-5)], .45, 'soft'),
 'tennis/net_hit': ([('b_soft',-3,0,0),('t_putter',-6,0,0)], .40, 'soft'),
 'golf/driver': ([('t_club',0,0,0),('b_punch',2,0,0),('p_ping',-8,.01,0),('w_up',-14,0,0)], .90, 'big'),
 'golf/iron': ([('t_club',0,0,0),('b_punch',-3,0,0),('p_bell',-12,.01,0)], .60, 'sweet'),
 'golf/wedge': ([('t_club',-3,0,0),('b_soft',0,0,0),('p_bell',-16,.01,0)], .45, 'normal'),
 'golf/putter': ([('t_putter',0,0,0),('b_soft',-6,0,0),('p_bell',-14,.02,0)], .45, 'soft'),
 'golf/perfect': ([('t_club',0,0,0),('b_punch',0,0,0),('p_ping',-4,.01,2),('p_chime',-7,.03,0),('w_up',-12,0,0)], 1.0, 'perfect'),
 'golf/cup': ([('j_pop',0,0,0),('j_jingle',-6,.10,0),('b_soft',-8,0,0)], 1.4, 'perfect'),
 'golf/flight': ([('w_flight',0,0,0)], 2.0, 'flight'),
}
for name, (rec, ln, tier) in R.items():
    for v in (1, 2):
        x = finish(mix(rec, v, ln), T[tier]); p = f'{U}/{name}_{v}.wav'
        os.makedirs(os.path.dirname(p), exist_ok=True); sf.write(p, x, SR, subtype='PCM_16')
# untouched-by-recipe gameplay clips: re-match by loudness only
for grp in ('tennis', 'golf', 'ui'):
    for p in glob.glob(f'{U}/{grp}/*.wav'):
        nm = f'{grp}/' + os.path.basename(p)[:-6]
        if nm in R: continue
        x, _ = sf.read(p); tier = 'ui' if grp == 'ui' else 'soft'
        if nm in ('tennis/slide', 'golf/swing', 'golf/lava', 'golf/leaves'): tier = 'normal'
        sf.write(p, finish(x, T[tier]), SR, subtype='PCM_16')
rep = []
for grp in ('tennis', 'golf', 'ui'):
    for p in sorted(glob.glob(f'{U}/{grp}/*_1.wav')):
        x, _ = sf.read(p); rep.append((f'{grp}/' + os.path.basename(p)[:-6], len(x)/SR, lufs(x), 20*np.log10(np.abs(x).max())))
with open('LOUDNESS.md', 'w') as o:
    o.write(f'# Loudness ladder (crowd shots median {REF:.1f} LUFS)\n\n| sound | dur s | LUFS | peak dBFS |\n|---|---|---|---|\n')
    for r in rep: o.write(f'| {r[0]} | {r[1]:.2f} | {r[2]:.1f} | {r[3]:.1f} |\n')
print(open('LOUDNESS.md').read())
