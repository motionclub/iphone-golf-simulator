from common import *
import sys
D = ", close microphone, dry, no reverb, no music, no voices"
S = [
('golf/driver', "single golf driver hitting a golf ball, sharp hollow metallic crack of titanium with a natural ring-out", .8),
('golf/iron', "single golf iron hitting a golf ball, crisp compressed click of a pure strike with a light turf brush", .6),
('golf/wedge', "single golf wedge shot, soft click of the ball and a turf thud", .6),
('golf/putter', "single golf putter hitting a golf ball, soft clean tock", .5),
('golf/perfect', "single perfect golf driver strike, loud pure full-bodied metallic crack, clean, natural ring-out", .8),
('golf/cup', "single golf ball rattling into the cup, real plastic cup rattle then settling", .8),
('golf/swing', "single golf club swing whoosh through air", .5),
('tennis/hit_soft', "single dull thin tennis mishit, weak muted tap off the racket frame", .4),
('tennis/hit_sweet', "single solid tennis ball hit, felt ball pock off racket strings", .5),
('tennis/hit_perfect', "single perfect tennis ball hit, deep full clean pock off racket strings, loud", .5),
('tennis/smash', "single hard tennis overhead smash, loud sharp crack off racket strings", .6),
('tennis/serve', "single tennis serve contact, hard crisp pock off racket strings", .5),
('tennis/rival', "single tennis ball hit from far away, distant dull pock", .4),
('tennis/bounce', "single tennis ball bounce on a hard court", .4),
('tennis/bounce_clay', "single tennis ball bounce on a clay court, soft thud", .4),
('tennis/net_cord', "single tennis ball clipping the top net cord, short dull tap", .5),
('tennis/net_hit', "single tennis ball hitting a net, soft slap", .4),
('tennis/whiff', "single tennis racket swing whoosh through air", .5),
]
items = [(f'v4/{n}_{i+1}.mp3', dict(text=p+D, duration_seconds=max(d,.5), prompt_influence=.85)) for n, p, d in S for i in range(4)]
print(len(items), sum(k['duration_seconds'] for _, k in items)*40, 'credits')
if 'dry' not in sys.argv: run(items, lambda **kw: client.text_to_sound_effects.convert(**kw), 'sfx4')
