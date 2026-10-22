import re, os, time, json, subprocess, urllib.parse, urllib.request
import numpy as np, soundfile as sf, imageio_ffmpeg
from scipy.signal import butter, sosfilt
FF = imageio_ffmpeg.get_ffmpeg_exe(); SR = 44100; UA = {'User-Agent': 'Mozilla/5.0'}
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.expanduser('~/Desktop/SFX_Review/real_tennis_landings'); os.makedirs(OUT, exist_ok=True)
os.makedirs(HERE + '/raw_tennis_landings', exist_ok=True)
def get(url): return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
# name: (queries, max duration s)
Q = {
 'tennis_bounce_hard': (['tennis ball bounce', 'tennis ball bounce hard court', 'tennis ball bounce asphalt', 'tennis ball drop', 'tennis ball floor', 'bouncing tennis ball', 'ball bounce concrete', 'rubber ball bounce floor', 'ball bounce single', 'bounce'], 90),
 'tennis_bounce_clay': (['tennis ball bounce clay', 'tennis ball bounce dirt', 'tennis ball bounce sand', 'tennis ball soft bounce', 'ball bounce dirt', 'ball bounce gravel', 'ball bounce soft ground', 'felt ball bounce', 'ball drop dirt', 'ball thud ground'], 90),
}
log = []
used_global = set()
for name, (qs, maxd) in Q.items():
    seen, picks = set(), []
    for q in qs:
        if len(picks) >= 5: break
        url = 'https://freesound.org/search/?q=' + urllib.parse.quote_plus(q) + '&f=license%3A%22Creative+Commons+0%22&s=downloads+desc'
        try: h = get(url).decode('utf8', 'ignore')
        except Exception as e: print('ERR', q, e); continue
        time.sleep(1.2)
        for m in re.finditer(r'data-sound-id="(\d+)"\s+data-username="([^"]+)".*?data-mp3="([^"]+)".*?data-title="([^"]*)"\s+data-duration="([\d.]+)"', h, re.S):
            sid, user, mp3, title, dur = m.groups(); dur = float(dur)
            if any(w in title.lower() for w in ('racket','racquet','serve','hit','smash','paddle','ping','pong','fence','ambience','crowd','match','game')) or sid in seen or sid in used_global or not (0.08 <= dur <= maxd): continue
            seen.add(sid); used_global.add(sid); picks.append((sid, user, mp3.replace('-lq.', '-hq.'), title, dur, q))
            if len(picks) >= 5: break
    for k, (sid, user, mp3, title, dur, q) in enumerate(picks, 1):
        try:
            page = get(f'https://freesound.org/people/{user}/sounds/{sid}/').decode('utf8', 'ignore')
            cc0 = 'Creative Commons 0' in page or 'publicdomain/zero' in page
            if not cc0: print('SKIP not CC0', sid); continue
            raw = f'{HERE}/raw_tennis_landings/{name}_{k}.mp3'; open(raw, 'wb').write(get(mp3)); time.sleep(.8)
            subprocess.run([FF, '-y', '-loglevel', 'quiet', '-i', raw, '-ac', '1', '-ar', str(SR), '/tmp/_r.wav'], check=True)
            x, _ = sf.read('/tmp/_r.wav'); x = sosfilt(butter(1, 30, 'high', fs=SR, output='sos'), x)   # gentle rumble cut only
            m = np.abs(x); kk = int(.005 * SR); env = np.convolve(m, np.ones(kk) / kk, 'same'); pk = env.max()
            on = np.where(env > .12 * pk)[0]; s0 = max(0, (on[0] if len(on) else 0) - int(.02 * SR))
            seg = env[s0:s0 + int(1.2 * SR)]; ev = seg.max(); lo = np.where(seg < .01 * ev)[0]; lo = lo[lo > int(.30 * SR)]
            end = s0 + (lo[0] if len(lo) else len(seg)) + int(.05 * SR); x = x[s0:end]
            n = min(int(.025 * SR), len(x) // 2); x[-n:] *= np.linspace(1, 0, n)
            sf.write(f'{OUT}/{name}_cand{k}.wav', x, SR, subtype='PCM_16')
            log.append((name, k, sid, user, title, dur, f'https://freesound.org/people/{user}/sounds/{sid}/', q))
            print(name, k, sid, title, dur, flush=True)
        except Exception as e: print('ERR', name, sid, e)
with open(HERE + '/LICENSES_tennis_landings.md', 'w') as o:
    o.write('# Real foley candidates: sources and licenses\n\nAll files are from Freesound, filtered to **Creative Commons 0** (public domain dedication; commercial use OK, no attribution required) and each sound page was checked for the CC0 notice at download time. They are the site\'s 128 kbps MP3 *previews* (the originals need a login), lightly edited: 30 Hz rumble cut, silence trimmed, 25 ms fade-out, no other processing.\n\n| candidate | Freesound id | author | title | dur s | source URL | search |\n|---|---|---|---|---|---|---|\n')
    for r in log: o.write(f'| {r[0]}_cand{r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | {r[7]} |\n')
json.dump(log, open(HERE + '/candidates_tennis_landings.json', 'w'))
print('done', len(log))
