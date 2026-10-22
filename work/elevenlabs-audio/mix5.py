import os, glob, shutil, subprocess, numpy as np, soundfile as sf, pyloudnorm as pn, imageio_ffmpeg
from scipy.signal import butter, sosfilt
FF = imageio_ffmpeg.get_ffmpeg_exe(); SR = 44100
V = os.path.abspath('../../Unity/Assets/Resources/Audio/v2/sfx'); meter = pn.Meter(SR)
for g in ('tennis', 'golf', 'ui'):          # start clean from the pre-gimmick backup
    shutil.rmtree(f'{V}/{g}', ignore_errors=True); shutil.copytree(f'v2_backup/{g}', f'{V}/{g}')
for dead in ('tennis/whiff_zap_1','tennis/whiff_zap_2','golf/flight_1','golf/flight_2','tennis/hit_soft_1','tennis/hit_soft_2','tennis/hit_perfect_1','tennis/hit_perfect_2','golf/perfect_1','golf/perfect_2','golf/thud_1','golf/thud_2','golf/splash_1','golf/splash_2'):
    if os.path.exists(f'{V}/{dead}.wav'): os.remove(f'{V}/{dead}.wav')
def lufs(x):   # short-clip loudness: K-ish weighted (200 Hz high-pass) RMS over a 0.5 s window, in dB (re full scale)
    y = x[:SR//2] if len(x) > 2000 else x
    y = sosfilt(butter(2, 200, 'high', fs=SR, output='sos'), y)
    return 20*np.log10(np.sqrt(np.mean(y**2))+1e-9)
def load(p):
    subprocess.run([FF,'-y','-loglevel','quiet','-i',p,'-ac','1','-ar',str(SR),'/tmp/_m.wav'], check=True); return sf.read('/tmp/_m.wav')[0]
def trim(x, cap):
    a = np.where(np.abs(x) > np.abs(x).max()*.06)[0]; x = x[max(0, a[0]-int(.003*SR)):] if len(a) else x
    x = x[:int(cap*SR)].copy(); n = min(int(.06*SR), len(x)//2); x[-n:] *= np.linspace(1, 0, n); return x
def finish(x, tier):   # tier = (rms target dB, peak ceiling dB): match loudness first, never exceed the tier's peak ceiling, no clipping
    rms_t, ceil = tier
    g = 10**((rms_t-lufs(x))/20); g = min(g, 10**(ceil/20)/(np.abs(x).max()+1e-9))
    y = x*g
    if tier == (-17, -1) and lufs(y) < rms_t:      # perfect/big tier: gentle saturation so the cleanest hit is also the fullest
        base = y/np.abs(y).max()
        for d in np.arange(1.2, 5, .3):
            z = np.tanh(base*d); z = z/np.abs(z).max()*10**(ceil/20); y = z
            if lufs(z) >= rms_t: break
    return y
def bright(x):
    S = np.abs(np.fft.rfft(x))**2; f = np.fft.rfftfreq(len(x), 1/SR); t = S.sum()+1e-12
    return S[f > 3000].sum()/t - S[f < 300].sum()/t
cr = [0 and lufs(sf.read(p)[0]) for p in glob.glob(V+'/crowd/*_1.wav') if not any(k in p for k in ('murmur', 'swell', 'rally'))]
REF = -13.8; print('crowd ref', round(REF, 1))
# name: (tier dB over crowd, max length s, lowpass Hz or 0, prefer 'dull'?)
P=(-17,-1); S=(-19,-2); N=(-20,-3); Q=(-22,-4); M=(-25,-7); O=(-23,-5); UI=(-30,-10)
R = {'tennis/hit_normal': (N, .4, 0, 0), 'tennis/hit_sweet': (S, .5, 0, 0), 'tennis/smash': (P, .55, 0, 0), 'tennis/mishit': (M, .3, 2600, 1),
     'tennis/serve': (S, .45, 0, 0), 'tennis/bounce': (Q, .35, 0, 0), 'tennis/bounce_clay': (Q, .35, 0, 0), 'tennis/net_cord': (Q, .4, 0, 1), 'tennis/whiff': (Q, .45, 0, 0),
     'golf/driver': (P, .6, 0, 0), 'golf/iron': (S, .45, 0, 0), 'golf/wedge': (N, .45, 0, 0), 'golf/putter': (Q, .35, 0, 0), 'golf/mishit': (M, .3, 2600, 1),
     'golf/swing': (Q, .5, 0, 0), 'golf/land_fairway': (O, .4, 0, 1), 'golf/land_green': (O, .4, 0, 1), 'golf/land_sand': (O, .45, 0, 1), 'golf/land_water': (O, .6, 0, 0),
     'golf/cup': ((-21,-3), .8, 0, 0),
     'ui/confirm': (UI, .4, 0, 0), 'ui/cancel': (UI, .4, 0, 0), 'ui/tick': (UI, .25, 0, 0), 'ui/point_win': (UI, .7, 0, 0), 'ui/point_lose': (UI, .7, 0, 0)}
rep = []
for name, (db, cap, lp, dull) in R.items():  # db = tier
    c = []
    for i in range(1, 5):
        x = trim(load(f'raw/v5/{name}_{i}.mp3'), cap); c.append((bright(x) * (-1 if dull else 1), i, x))
    c.sort(key=lambda t: -t[0])
    for rank, (s, i, x) in enumerate(c[:2]):
        if lp: x = sosfilt(butter(2, lp, 'low', fs=SR, output='sos'), x)
        sf.write(f'{V}/{name}_{rank+1}.wav', finish(x, db), SR, subtype='PCM_16'); rep.append((name, rank+1, i, len(x)/SR))
for grp in ('tennis', 'golf', 'ui'):
    for p in glob.glob(f'{V}/{grp}/*.wav'):
        nm = f'{grp}/'+os.path.basename(p)[:-6]
        if nm in R: continue
        x, _ = sf.read(p); sf.write(p, finish(x, UI if grp == 'ui' else O), SR, subtype='PCM_16')
with open('LOUDNESS.md', 'w') as o:
    o.write(f'# Loudness ladder (active-portion RMS dB, peak ceiling per tier; UI 6+ dB under a normal hit)\n\n| sound | dur s | LUFS | peak dBFS |\n|---|---|---|---|\n')
    for grp in ('tennis', 'golf', 'ui'):
        for p in sorted(glob.glob(f'{V}/{grp}/*_1.wav')):
            x, _ = sf.read(p); o.write(f'| {grp}/{os.path.basename(p)[:-6]} | {len(x)/SR:.2f} | {lufs(x):.1f} | {20*np.log10(np.abs(x).max()):.1f} |\n')
print(open('LOUDNESS.md').read())
