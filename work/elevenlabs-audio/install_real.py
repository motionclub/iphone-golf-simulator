import os, shutil, subprocess, numpy as np, soundfile as sf, imageio_ffmpeg
from scipy.signal import stft, istft, butter, sosfilt
FF = imageio_ffmpeg.get_ffmpeg_exe(); SR = 44100
V = os.path.abspath('../../Unity/Assets/Resources/Audio/v2'); S = V + '/sfx'; REAL = os.path.expanduser('~/Desktop/SFX_Review/real/')
def rd(n, k): return sf.read(f'{REAL}{n}_cand{k}.wav')[0]
def hp(x, hz): return sosfilt(butter(2, hz, 'high', fs=SR, output='sos'), x)
def rms(x): return 20*np.log10(np.sqrt(np.mean(hp(x[:SR//2], 200)**2))+1e-9)
def denoise(x):   # light spectral subtraction: noise floor = low percentile per bin
    f, t, Z = stft(x, SR, nperseg=1024); m = np.abs(Z); nf = np.percentile(m, 15, axis=1, keepdims=True)
    m2 = np.maximum(m - 1.6*nf, 0.12*m); return istft(m2*np.exp(1j*np.angle(Z)), SR)[1][:len(x)]
def level(x, tier):   # gain only (no clipping, no saturation): reach the RMS target but stay under the tier's peak ceiling
    r, c = tier; g = min(10**((r-rms(x))/20), 10**(c/20)/(np.abs(x).max()+1e-9)); return x*g
P=(-17,-1); Sx=(-19,-2); N=(-20,-3); Q=(-22,-4); UI=(-30,-10)
# game file -> (candidate, denoise?, tier)
M = {'tennis/hit_normal': (('tennis_hit_normal',1), 0, N), 'tennis/hit_sweet': (('tennis_hit_normal',1), 0, Sx), 'tennis/smash': (('tennis_smash',2), 0, P),
     'tennis/mishit': (('tennis_whoosh',1), 0, Q), 'tennis/whiff': (('tennis_whoosh',1), 0, Q), 'tennis/serve': (('tennis_serve',2), 0, Sx),
     'tennis/bounce': (('tennis_bounce_clay',1), 0, Q), 'tennis/bounce_clay': (('tennis_bounce_clay',1), 0, Q), 'tennis/net_cord': (('tennis_net_cord',3), 0, Q),
     'golf/driver': (('golf_driver',2), 1, P), 'golf/iron': (('golf_iron',2), 1, Sx), 'golf/wedge': (('golf_wedge',1), 0, N), 'golf/putter': (('golf_putter',2), 0, Q),
     'golf/mishit': (('golf_mishit',2), 0, Q), 'golf/swing': (('golf_swing',3), 0, Q), 'golf/land_sand': (('golf_land_sand',3), 0, Q),
     'golf/land_water': (('golf_land_water',3), 0, Q), 'golf/cup': (('golf_cup',3), 0, N),
     'ui/confirm': (('ui_click_soft',3), 0, UI), 'ui/cancel': (('ui_back',2), 0, UI), 'ui/tick': (('ui_tick',2), 0, UI)}
for name, ((c, k), dn, tier) in M.items():
    x = rd(c, k); x = denoise(x) if dn else x
    for v in (1, 2):
        p = f'{S}/{name}_{v}.wav'
        if v == 2: 
            if os.path.exists(p): os.remove(p)
            continue
        sf.write(p, level(x, tier), SR, subtype='PCM_16')
for dead in ('golf/land_fairway', 'golf/land_green', 'tennis/hit_soft', 'tennis/hit_perfect', 'golf/perfect'):
    for v in (1, 2):
        p = f'{S}/{dead}_{v}.wav'
        if os.path.exists(p): os.remove(p)
# announcer point won / lost over a short music bed
subprocess.run([FF, '-y', '-loglevel', 'quiet', '-i', V + '/music/game_light.ogg', '-ac', '1', '-ar', str(SR), '/tmp/_mus.wav'], check=True)
mus = sf.read('/tmp/_mus.wav')[0]
def stinger(voice_mp3, start):
    subprocess.run([FF, '-y', '-loglevel', 'quiet', '-i', voice_mp3, '-ac', '1', '-ar', str(SR), '/tmp/_v.wav'], check=True)
    v = sf.read('/tmp/_v.wav')[0]; a = np.where(np.abs(v) > np.abs(v).max()*.03)[0]; v = v[a[0]:a[-1]+int(.15*SR)]
    n = int((len(v)/SR + 1.0)*SR); bed = mus[int(start*SR):int(start*SR)+n].copy(); bed = bed/(np.abs(bed).max()+1e-9)*.18
    env = np.ones(n); f = int(.15*SR); env[:f] = np.linspace(0, 1, f); env[-int(.5*SR):] = np.linspace(1, 0, int(.5*SR)); bed *= env
    out = bed.copy(); o = int(.05*SR); out[o:o+len(v)] += v/np.abs(v).max()*.7; return out
for nm, src, st in (('point_win_1', 'win_1_1', 0), ('point_win_2', 'win_2_1', 0), ('point_lose_1', 'lose_1_1', 24), ('point_lose_2', 'lose_2_1', 24)):
    sf.write(f'{S}/ui/{nm}.wav', level(stinger(f'raw/v6/{src}.mp3', st), Q), SR, subtype='PCM_16')
print(sorted(os.listdir(S + '/tennis')), sorted(os.listdir(S + '/golf')), sorted(os.listdir(S + '/ui')))
