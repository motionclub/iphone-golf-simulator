import glob, os, re, subprocess, collections, numpy as np, soundfile as sf, pyloudnorm as pn, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe(); SR = 44100
OUT = os.path.abspath('../../Unity/Assets/Resources/Audio/v2')
def load(p, ch):
    subprocess.run([FF,'-y','-loglevel','quiet','-i',p,'-ac',str(ch),'-ar',str(SR),'/tmp/_p.wav'], check=True)
    x,_ = sf.read('/tmp/_p.wav'); return x
def trim(x, thresh_db=-42, pre=.004, fade=.02):
    m = np.abs(x) if x.ndim == 1 else np.abs(x).max(1)
    pk = m.max()+1e-9; act = np.where(m > pk*10**(thresh_db/20))[0]
    if not len(act): return x
    a = max(0, act[0]-int(pre*SR)); b = min(len(x), act[-1]+int(.03*SR))
    y = x[a:b].copy(); n = min(int(fade*SR), len(y)//2)
    y[-n:] *= np.linspace(1, 0, n)[:, None] if y.ndim == 2 else np.linspace(1, 0, n)
    return y
def peak_norm(x, db=-1.0): return x * (10**(db/20)/(np.abs(x).max()+1e-9))
def score(x):
    S = np.abs(np.fft.rfft(x))**2; f = np.fft.rfftfreq(len(x), 1/SR); t = S.sum()+1e-12
    low = S[f < 300].sum()/t; hi = S[f > 3000].sum()/t
    clip = np.mean(np.abs(x) > .98)
    return hi - low - 50*clip - 0.3*len(x)/SR
def wav(path, x):
    os.makedirs(os.path.dirname(path), exist_ok=True); sf.write(path, x, SR, subtype='PCM_16')
report = []
# SFX: best 2 of 4 (by objective score), mono, trimmed, -1 dBFS
groups = collections.defaultdict(list)
for p in glob.glob('raw/v2/sfx/**/*.mp3', recursive=True): groups[re.sub(r'_\d+\.mp3$', '', p)].append(p)
for g, ps in sorted(groups.items()):
    loop = any(k in g for k in ('move/', 'murmur', 'swell', 'rally', 'amb/'))
    cands = []
    for p in sorted(ps):
        x = load(p, 1); x = x if loop else trim(x)
        cands.append((score(x), p, x))
    cands.sort(key=lambda c: -c[0])
    for rank, (s, p, x) in enumerate(cands[:2 if len(cands) > 2 else 1]):
        rel = g.replace('raw/v2/sfx/', ''); 
        wav(f'{OUT}/sfx/{rel}_{rank+1}.wav', peak_norm(x))
        report.append((rel, rank+1, os.path.basename(p), round(len(x)/SR, 2), round(s, 2)))
# Voice: keep all 3 takes, trimmed, ~-18 LUFS with -1 dBFS ceiling
m = pn.Meter(SR)
for p in sorted(glob.glob('raw/v2/voice/*.mp3')):
    x = trim(load(p, 1), -40, .02, .04)
    try: x = pn.normalize.loudness(x, m.integrated_loudness(x), -18.0) if len(x)/SR > .4 else x
    except Exception: pass
    if np.abs(x).max() > .89: x = x*.89/np.abs(x).max()
    wav(f'{OUT}/voice/{os.path.basename(p)[:-4]}.wav', x)
# Music: stereo, 2 s equal-power self-crossfade for a seamless loop, -16 LUFS, OGG
for p in sorted(glob.glob('raw/v2/music/*.mp3')):
    x = load(p, 2); n = 2*SR; head, tail = x[:n], x[-n:]
    t = np.linspace(0, np.pi/2, n)[:, None]
    seam = tail*np.cos(t) + head*np.sin(t)
    y = np.concatenate([seam, x[n:-n]])   # loop point: end of y flows into start of y
    y = pn.normalize.loudness(y, m.integrated_loudness(y), -16.0)
    if np.abs(y).max() > .95: y = y*.95/np.abs(y).max()
    base = f'{OUT}/music/{os.path.basename(p)[:-4]}'; os.makedirs(os.path.dirname(base), exist_ok=True)
    sf.write(base+'.wav', y, SR, subtype='PCM_16')
    subprocess.run([FF,'-y','-loglevel','quiet','-i',base+'.wav','-c:a','libvorbis','-q:a','6',base+'.ogg']); os.remove(base+'.wav')
with open('KEPT.md', 'w') as o:
    o.write('# Kept SFX (best 2 of 4 by objective score: fewer lows, more highs, no clipping, shorter)\n\n| sound | rank | source take | dur s | score |\n|---|---|---|---|---|\n')
    for r in report: o.write('| ' + ' | '.join(map(str, r)) + ' |\n')
print('done', len(report))
