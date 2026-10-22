from pathlib import Path
import sys
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
p=r/'work/emote-overhaul/scripts/make_film2.py'
s=p.read_text().replace("NAMES = ['Emote_Spike', 'Emote_Scuba', 'Emote_Thrust']", "NAMES = ['Emote_Scuba', 'Emote_Thrust']")
s=s.replace("W + '/film'", "W + '/film_r2'").replace("W + '/proof'", "W + '/proof_r2'").replace('{W}/film/', '{W}/film_r2/').replace('{W}/proof/', '{W}/proof_r2/')
exec(compile(s,str(p),'exec'))
