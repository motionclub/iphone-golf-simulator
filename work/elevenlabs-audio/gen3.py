from common import *
import sys
# (name, literal prompt, seconds) -- 3 takes each; layers are mixed offline by mix3.py
L = [
('t_racket', "single sharp tennis racket string click transient, very short, dry", .5),
('t_club', "single sharp golf club metallic click transient, very short, dry", .5),
('t_putter', "single soft putter tap click, very short, dry", .5),
('b_punch', "single punchy low drum-like thump impact, short, dry", .5),
('b_soft', "single soft low thud, short, dry", .5),
('p_ping', "single bright glassy musical sparkle ping, high pitched, ringing tail", 1.0),
('p_bell', "single bright marimba bell note, clean, ringing tail", 1.0),
('p_chime', "magical bright rising chime shimmer, arcade reward sound", 1.2),
('w_up', "quick bright rising whoosh swoosh, pitch rising", .8),
('w_flight', "long rising whoosh building up in pitch and volume, like a ball flying", 2.0),
('j_jingle', "mini cheerful jingle, three bright ascending bell notes, arcade reward", 1.5),
('j_pop', "single cartoon pop then a twinkling sparkle", 1.0),
('boing', "single bouncy cartoon boing spring", .6),
('zap', "single cartoon zap, descending slide whistle, funny", .6),
('ui_blip', "single clean soft UI blip", .5),
]
items = [(f'v3/layers/{n}_{i+1}.mp3', dict(text=p, duration_seconds=d, prompt_influence=.7)) for n, p, d in L for i in range(3)]
print(len(items), sum(k['duration_seconds'] for _, k in items)*40, 'credits')
if 'dry' not in sys.argv: run(items, lambda **kw: client.text_to_sound_effects.convert(**kw), 'sfx3')
