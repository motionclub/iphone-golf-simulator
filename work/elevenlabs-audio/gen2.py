from common import *
import sys
D = ", dry, close mic, no reverb, no music, no background"
# (name, literal prompt, seconds, variants)
S = [
('golf/driver', "single golf driver hitting a ball off a tee, sharp loud crack", 1.0),
('golf/iron', "single golf iron hitting a ball, crisp click", .7),
('golf/wedge', "single golf wedge chip, soft tick", .6),
('golf/putter', "single golf putter tapping a ball, soft low tock", .5),
('golf/perfect', "single golf ball struck perfectly, pure bright ping", .8),
('golf/swing', "single golf club swoosh through air", .6),
('golf/cup', "single golf ball dropping into the cup, short plunk", .8),
('golf/splash', "single small ball splash into water", .9),
('golf/lava', "single short hiss of a ball dropping into lava", 1.0),
('golf/thud', "single dull ball thud on soft ground", .5),
('golf/leaves', "single ball rustling into bushes", .8),
('golf/knock_wood', "single ball knock on wood", .5),
('golf/knock_stone', "single ball clack on stone", .5),
('golf/sand', "single ball landing in sand, soft poof", .7),
('tennis/hit_soft', "single soft tennis ball hit off a racket, gentle pop", .5),
('tennis/hit_sweet', "single crisp tennis ball hit off a racket, clean pop", .5),
('tennis/hit_perfect', "single perfect tennis ball hit off a racket, punchy thwock", .5),
('tennis/smash', "single tennis overhead smash, explosive crack", .7),
('tennis/serve', "single tennis serve hit, sharp snap", .6),
('tennis/rival', "single distant tennis ball hit, light pop", .5),
('tennis/whiff', "single tennis racket swish through air", .5),
('tennis/bounce', "single tennis ball bounce on hard court", .5),
('tennis/bounce_clay', "single tennis ball bounce on clay, soft thud", .5),
('tennis/net_cord', "single tennis ball clipping a net cord, short twang", .6),
('tennis/net_hit', "single tennis ball hitting net mesh, soft slap", .5),
('tennis/slide', "single sneaker slide and brake on a tennis court, short squeak", .7),
('tennis/land', "single sneaker landing thump on a court", .5),
('ui/tick', "single soft UI tick", .5), ('ui/confirm', "single bright UI confirm blip", .5),
('ui/cancel', "single low UI cancel blip", .5), ('ui/ready', "single friendly chime", .8),
('ui/whistle', "single short referee whistle blast", .8), ('ui/point_win', "short happy rising sting", 1.0),
('ui/point_lose', "short sad descending sting", 1.0), ('ui/fanfare', "short triumphant brass fanfare", 2.0),
('grunt/m_ground', "single short male tennis grunt of effort", .6), ('grunt/m_power', "single loud male tennis grunt of effort", .7),
('grunt/m_serve', "single male tennis serve grunt", .7), ('grunt/m_smash', "single male overhead smash grunt", .8),
('grunt/m_frustrated', "single male frustrated exhale", .8),
('grunt/f_ground', "single short female tennis grunt of effort", .6), ('grunt/f_power', "single loud female tennis grunt of effort", .7),
('grunt/f_serve', "single female tennis serve grunt", .7), ('grunt/f_smash', "single female overhead smash grunt", .8),
('grunt/f_frustrated', "single female frustrated exhale", .8),
]
CROWD = [  # shorter, 2 variants
('crowd/golf_clap', "polite clap of thirty people", 2.0), ('crowd/golf_erupt', "crowd cheering and applauding", 2.5),
('crowd/golf_groan', "crowd groan 'ohhh' disappointed", 1.8), ('crowd/golf_ooh', "crowd 'ooooh' near miss", 1.8),
('crowd/golf_aww', "crowd soft sympathetic 'awww'", 1.5), ('crowd/golf_roar', "crowd big roar and whistles", 3.0),
('crowd/golf_inhale', "crowd collective sharp inhale", 1.0), ('crowd/golf_hush', "crowd going quiet, soft shush", 2.0),
('crowd/tennis_ooh', "crowd 'ooooh' at a close call", 1.5), ('crowd/tennis_applause_short', "short crowd applause", 2.5),
('crowd/tennis_applause_long', "long loud crowd applause with cheers", 4.0), ('crowd/tennis_sigh', "crowd sigh", 1.2),
('crowd/tennis_hush', "stadium crowd hushed, near silence", 2.0), ('crowd/tennis_ovation', "stadium crowd standing ovation, roaring applause", 4.0),
]
LOOPS = [
('move/run_grass', "steady footsteps running on grass", 3.0), ('move/run_court', "steady footsteps running on a hard tennis court", 3.0),
('move/run_stone', "steady footsteps running on stone", 3.0), ('move/run_sand', "steady footsteps running on sand", 3.0),
('move/run_ice', "short steady skating footsteps on ice", 3.0), ('move/run_lava_rock', "steady footsteps on crunchy rock", 3.0),
('crowd/golf_murmur', "soft quiet golf gallery murmur", 6.0), ('crowd/golf_swell', "crowd murmur rising with anticipation", 5.0),
('crowd/tennis_murmur', "low stadium crowd murmur", 6.0), ('crowd/tennis_rally', "crowd murmur with quiet 'ooh' during a rally", 6.0),
('amb/resort', "tropical beach, gentle waves and birds", 6.0), ('amb/skyscraper', "steady rooftop wind, faint city", 6.0),
('amb/volcano', "deep rumble and bubbling lava", 6.0), ('amb/cliffside', "ocean waves crashing, gulls, wind", 6.0),
('amb/wildisles', "jungle insects and birds, soft surf", 6.0), ('amb/magma', "low rumble, crackling lava, steam hiss", 6.0),
]
items = []
for n, p, d in S:   items += [(f'v2/sfx/{n}_{i+1}.mp3', dict(text=p+D, duration_seconds=d, prompt_influence=.7)) for i in range(4)]
for n, p, d in CROWD: items += [(f'v2/sfx/{n}_{i+1}.mp3', dict(text=p+D.replace(', close mic',''), duration_seconds=d, prompt_influence=.7)) for i in range(2)]
for n, p, d in LOOPS: items += [(f'v2/sfx/{n}_1.mp3', dict(text=p+', no music', duration_seconds=d, loop=True, prompt_influence=.7))]
print(len(items), sum(k['duration_seconds'] for _, k in items) * 40, 'credits')
if 'dry' not in sys.argv: run(items, lambda **kw: client.text_to_sound_effects.convert(**kw), 'sfx2')
