from common import *
import sys
D = ", close microphone, dry, no reverb, no music, no voices"
S = [
('tennis/hit_normal', "single tennis ball hit off racket strings, clean felt ball pock", .5),
('tennis/hit_sweet', "single sweet-spot tennis ball hit, fuller deeper pock off racket strings, clean and punchy", .5),
('tennis/smash', "single hard tennis overhead smash, sharp loud crack off racket strings", .6),
('tennis/mishit', "single tennis mishit off the racket frame, thin dull clunk", .5),
('tennis/serve', "single tennis serve contact, crisp hard pock off racket strings", .5),
('tennis/bounce', "single tennis ball bounce on a hard court", .5),
('tennis/bounce_clay', "single tennis ball bounce on a clay court, soft thud", .5),
('tennis/net_cord', "single tennis ball clipping the top net cord, short dull tap", .5),
('tennis/whiff', "single tennis racket swing whoosh through air, missing the ball", .5),
('golf/driver', "single golf driver hitting a golf ball, sharp hollow metallic crack of titanium with a natural ring-out", .6),
('golf/iron', "single golf iron hitting a golf ball, crisp compressed click of a pure strike with a light turf brush", .5),
('golf/wedge', "single golf wedge shot, soft click of the ball and a turf thud", .5),
('golf/putter', "single golf putter hitting a golf ball, soft clean tock", .5),
('golf/mishit', "single golf mishit, dull thin clunk off the club", .5),
('golf/swing', "single golf club swing whoosh through air", .5),
('golf/land_fairway', "single golf ball landing on a fairway, soft dull thud", .5),
('golf/land_green', "single golf ball landing on a putting green, soft thump and a small bounce", .5),
('golf/land_sand', "single golf ball landing in a sand bunker, soft sandy poof", .5),
('golf/land_water', "single golf ball splashing into a pond, plunk and splash", .6),
('golf/cup', "single golf ball rattling into the cup, real plastic cup rattle then settling", .8),
('ui/confirm', "single soft clean UI confirm click, subtle", .5), ('ui/cancel', "single soft clean UI back click, subtle, lower", .5),
('ui/tick', "single tiny subtle UI tick", .5), ('ui/point_win', "single short soft pleasant two-note positive UI chime", .8),
('ui/point_lose', "single short soft low two-note negative UI tone", .8),
]
items = [(f'v5/{n}_{i+1}.mp3', dict(text=p+D, duration_seconds=d, prompt_influence=.85)) for n, p, d in S for i in range(4)]
print(len(items), sum(k['duration_seconds'] for _, k in items)*40, 'credits')
if 'dry' not in sys.argv: run(items, lambda **kw: client.text_to_sound_effects.convert(**kw), 'sfx5')
