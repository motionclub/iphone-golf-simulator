import glob, os, subprocess, numpy as np, soundfile as sf, pyloudnorm as pn, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
def load(p):
    subprocess.run([FF,'-y','-loglevel','quiet','-i',p,'-ac','1','-ar','44100','/tmp/_a.wav'])
    return sf.read('/tmp/_a.wav')
rows=[]
for p in sorted(glob.glob('raw/**/*.mp3',recursive=True)):
    if '/test/' in p: continue
    x,sr=load(p); n=len(x); dur=n/sr
    pk=np.max(np.abs(x))+1e-9; env=np.abs(x)
    act=np.where(env>pk*0.03)[0]
    lead=act[0]/sr if len(act) else dur; tail=(n-act[-1])/sr if len(act) else 0
    clip=float(np.mean(env>0.98))
    try: lufs=pn.Meter(sr).integrated_loudness(x) if dur>0.5 else float('nan')
    except Exception: lufs=float('nan')
    S=np.abs(np.fft.rfft(x))**2; f=np.fft.rfftfreq(n,1/sr); tot=S.sum()+1e-12
    low=S[f<300].sum()/tot; hi=S[f>4000].sum()/tot
    fl=[]
    kind=p.split('/')[1]
    if 'sfx' in p and not any(s in p for s in ('amb','murmur','swell','rally','roll','run_','ovation','erupt','roar','applause','clap')) and dur>1.2: fl.append('long for a one-shot')
    if kind=='sfx' and 'crowd' not in p and 'amb' not in p: 
        if tail>0.4 and dur<4: fl.append(f'dead tail {tail:.1f}s')
    if lead>0.15: fl.append(f'leading silence {lead:.2f}s')
    if clip>0.001: fl.append('clipping')
    if low>0.6: fl.append(f'muddy (low {low:.0%})')
    if hi<0.01 and kind!='announcer': fl.append('dull (no highs)')
    if kind=='announcer' and dur>3.5: fl.append('long line, >3.5s')
    if kind=='announcer' and len(os.path.basename(p))>0 and dur/ max(1,len(open('/dev/null').read())+1)<0: pass
    rows.append((p,dur,20*np.log10(pk),lufs,lead,tail,low,hi,fl))
with open('AUDIT.md','w') as o:
    o.write('# Audit of the first ElevenLabs pass (objective measurements only; I cannot listen)\n\n')
    bad=[r for r in rows if r[8]]
    o.write(f'{len(rows)} files, {len(bad)} flagged.\n\n| file | dur s | peak dB | LUFS | lead s | tail s | low<300Hz | high>4k | flags |\n|---|---|---|---|---|---|---|---|---|\n')
    for r in rows: o.write(f'| {r[0][4:]} | {r[1]:.1f} | {r[2]:.1f} | {r[3]:.0f} | {r[4]:.2f} | {r[5]:.2f} | {r[6]:.0%} | {r[7]:.0%} | {"; ".join(r[8])} |\n')
import collections
c=collections.Counter(f.split(' ')[0] for r in rows for f in r[8]); print(len(rows),len(bad),c)
