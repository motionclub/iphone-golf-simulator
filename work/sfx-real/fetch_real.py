import re, os, time, json, subprocess, urllib.parse, urllib.request
import numpy as np, soundfile as sf, imageio_ffmpeg
from scipy.signal import butter, sosfilt
FF = imageio_ffmpeg.get_ffmpeg_exe(); SR = 44100; UA = {'User-Agent': 'Mozilla/5.0'}
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.expanduser('~/Desktop/SFX_Review/real'); os.makedirs(OUT, exist_ok=True)
os.makedirs(HERE + '/raw', exist_ok=True)
def get(url): return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
# name: (queries, max duration s)
Q = {
 'tennis_hit_normal': (['tennis racket hit ball', 'tennis ball hit'], 1.5), 'tennis_smash': (['tennis smash', 'tennis hard hit'], 2),
 'tennis_mishit': (['tennis racket frame hit', 'tennis mishit', 'racket hit', 'wood hit dull', 'tennis racket'], 2), 'tennis_serve': (['tennis serve', 'tennis serve hit', 'tennis racket hit', 'tennis ball hit'], 2),
 'tennis_bounce_hard': (['tennis ball bounce', 'ball bounce hard court'], 1.5), 'tennis_bounce_clay': (['tennis ball bounce clay', 'ball bounce dirt', 'ball bounce', 'soft ball bounce', 'ball drop'], 1.5),
 'tennis_net_cord': (['tennis net', 'ball hits net', 'net', 'rope tap', 'tennis'], 2), 'tennis_whoosh': (['racket swing whoosh', 'tennis swing'], 1.5),
 'golf_driver': (['golf driver hit', 'golf drive'], 3), 'golf_iron': (['golf iron hit', 'golf shot'], 3), 'golf_wedge': (['golf chip shot', 'golf wedge', 'golf pitch', 'golf ball hit'], 3),
 'golf_putter': (['golf putt', 'golf putter', 'putt', 'golf ball tap'], 2.5), 'golf_mishit': (['golf shank', 'golf bad hit', 'golf club hit ball'], 3), 'golf_swing': (['golf club swing whoosh', 'golf swing', 'club swing', 'swing whoosh', 'whoosh'], 2),
 'golf_land_fairway': (['golf ball land grass', 'ball thud grass', 'ball thud', 'ball drop grass', 'soft thud'], 2), 'golf_land_green': (['golf ball bounce green', 'ball landing grass soft', 'golf ball bounce', 'small ball drop', 'ball bounce soft'], 2),
 'golf_land_sand': (['golf ball sand bunker', 'ball lands sand', 'sand impact', 'sand thud', 'sand'], 2.5), 'golf_land_water': (['golf ball splash water', 'ball splash pond', 'small splash', 'water plop', 'splash'], 3),
 'golf_cup': (['golf ball cup hole', 'golf ball drops in hole', 'ball drop plastic', 'ball rattle', 'golf ball'], 3),
 'ui_click_soft': (['ui soft click', 'soft button click'], 1), 'ui_back': (['ui back click', 'ui cancel'], 1), 'ui_tick': (['ui tick', 'tiny click'], .6),
 'ui_chime_win': (['positive notification chime', 'success chime'], 2.5), 'ui_chime_lose': (['negative notification soft', 'error tone soft', 'fail sound', 'wrong answer soft', 'error'], 2.5),
}
log = []
used_global = set()
for name, (qs, maxd) in Q.items():
    seen, picks = set(), []
    for q in qs:
        if len(picks) >= 3: break
        url = 'https://freesound.org/search/?q=' + urllib.parse.quote_plus(q) + '&f=license%3A%22Creative+Commons+0%22&s=downloads+desc'
        try: h = get(url).decode('utf8', 'ignore')
        except Exception as e: print('ERR', q, e); continue
        time.sleep(1.2)
        for m in re.finditer(r'data-sound-id="(\d+)"\s+data-username="([^"]+)".*?data-mp3="([^"]+)".*?data-title="([^"]*)"\s+data-duration="([\d.]+)"', h, re.S):
            sid, user, mp3, title, dur = m.groups(); dur = float(dur)
            if sid in seen or sid in used_global or not (0.08 <= dur <= maxd): continue
            seen.add(sid); used_global.add(sid); picks.append((sid, user, mp3.replace('-lq.', '-hq.'), title, dur, q))
            if len(picks) >= 3: break
    for k, (sid, user, mp3, title, dur, q) in enumerate(picks, 1):
        try:
            page = get(f'https://freesound.org/people/{user}/sounds/{sid}/').decode('utf8', 'ignore')
            cc0 = 'Creative Commons 0' in page or 'publicdomain/zero' in page
            if not cc0: print('SKIP not CC0', sid); continue
            raw = f'{HERE}/raw/{name}_{k}.mp3'; open(raw, 'wb').write(get(mp3)); time.sleep(.8)
            subprocess.run([FF, '-y', '-loglevel', 'quiet', '-i', raw, '-ac', '1', '-ar', str(SR), '/tmp/_r.wav'], check=True)
            x, _ = sf.read('/tmp/_r.wav'); x = sosfilt(butter(1, 30, 'high', fs=SR, output='sos'), x)   # gentle rumble cut only
            a = np.where(np.abs(x) > 10**(-50/20) * max(np.abs(x).max(), 1e-6))[0]
            if len(a): x = x[max(0, a[0] - int(.005 * SR)): a[-1] + int(.03 * SR)]
            n = min(int(.025 * SR), len(x) // 2); x[-n:] *= np.linspace(1, 0, n)
            sf.write(f'{OUT}/{name}_cand{k}.wav', x, SR, subtype='PCM_16')
            log.append((name, k, sid, user, title, dur, f'https://freesound.org/people/{user}/sounds/{sid}/', q))
            print(name, k, sid, title, dur, flush=True)
        except Exception as e: print('ERR', name, sid, e)
with open(HERE + '/LICENSES.md', 'w') as o:
    o.write('# Real foley candidates: sources and licenses\n\nAll files are from Freesound, filtered to **Creative Commons 0** (public domain dedication; commercial use OK, no attribution required) and each sound page was checked for the CC0 notice at download time. They are the site\'s 128 kbps MP3 *previews* (the originals need a login), lightly edited: 30 Hz rumble cut, silence trimmed, 25 ms fade-out, no other processing.\n\n| candidate | Freesound id | author | title | dur s | source URL | search |\n|---|---|---|---|---|---|---|\n')
    for r in log: o.write(f'| {r[0]}_cand{r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | {r[7]} |\n')
json.dump(log, open(HERE + '/candidates.json', 'w'))
print('done', len(log))
