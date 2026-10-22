from common import *
import sys
# (name, prompt, seconds, loop, variants)
S = [
# golf contact
('golf/driver', "Golf driver hitting a ball off the tee, loud sharp metallic crack with a deep boom and a long ringing tail", 1.8, 0, 3),
('golf/iron', "Golf iron shot, crisp mid-weight click-thwack, short ring", 1.2, 0, 3),
('golf/wedge', "Golf wedge chip, soft bright tick with a little grass brush", 1.0, 0, 3),
('golf/putter', "Golf putter tapping a ball on a green, soft low wooden tock, very quiet and dull, no ring", 0.8, 0, 3),
('golf/perfect', "Perfect golf strike sweet spot, pure bell-like ping then a rising sparkle", 1.5, 0, 2),
('golf/swing_light', "Golf club swoosh through air, light", 0.8, 0, 2),
('golf/swing_heavy', "Golf club powerful fast whoosh through air, heavy", 1.0, 0, 2),
('golf/cup', "Golf ball dropping into the cup, rattle then hollow plunk", 1.2, 0, 2),
('golf/splash', "Golf ball splashing into a pond, plunk and ripples", 1.5, 0, 2),
('golf/lava', "Ball dropping into lava, sizzling hiss and bubbling pop", 2.0, 0, 1),
('golf/ice_skid', "Golf ball skidding across ice, high scraping slide", 1.5, 0, 1),
('golf/thud', "Golf ball landing with a dull thud on soft ground", 0.8, 0, 2),
('golf/leaves', "Golf ball crashing into leaves and bushes, rustle", 1.2, 0, 2),
('golf/knock_wood', "Golf ball knocking against a wooden post", 0.7, 0, 2),
('golf/knock_stone', "Golf ball clacking against a stone", 0.7, 0, 2),
('golf/sand', "Golf ball landing in a bunker, soft sandy poof", 1.0, 0, 2),
('golf/roll_green', "Golf ball rolling on a smooth green, soft steady hiss", 4.0, 1, 1),
('golf/flag', "Golf flagstick tink and flag flutter", 1.0, 0, 1),
# tennis contact
('tennis/hit_soft', "Tennis racket hitting ball softly, gentle pop", 0.7, 0, 3),
('tennis/hit_sweet', "Tennis racket sweet-spot hit, clean punchy pop with a bright ping", 0.8, 0, 3),
('tennis/hit_perfect', "Perfect tennis ground stroke, crisp loud thwock with a satisfying sparkle", 1.0, 0, 2),
('tennis/smash', "Tennis overhead smash, explosive crack then a deep thud", 1.2, 0, 3),
('tennis/serve', "Tennis serve hit, sharp snap with whoosh", 1.0, 0, 3),
('tennis/rival', "Tennis ball hit from far away, light dull pop", 0.7, 0, 2),
('tennis/toss', "Tennis serve ball toss, tiny whoosh and a racket-less quiet air flick", 0.8, 0, 1),
('tennis/whiff', "Tennis racket swing through air missing the ball, swish", 0.8, 0, 2),
('tennis/bounce_hard', "Tennis ball bouncing on hard court, springy tok", 0.6, 0, 3),
('tennis/bounce_clay', "Tennis ball bouncing on clay, soft thud with a puff of dust", 0.6, 0, 2),
('tennis/net_cord', "Tennis ball clipping the net cord, dull twang", 0.8, 0, 2),
('tennis/net_hit', "Tennis ball hitting the net mesh, soft slap", 0.8, 0, 1),
('tennis/slide', "Tennis shoes sliding and braking on a court, squeak", 0.9, 0, 3),
('tennis/land', "Player landing from a jump on a tennis court, shoe thump", 0.6, 0, 2),
# footsteps (loops)
('move/run_grass', "Person running on grass, steady footsteps, rubber soles", 4.0, 1, 1),
('move/run_court', "Person running on a hard tennis court, steady squeaky footsteps", 4.0, 1, 1),
('move/run_stone', "Person running on stone paving, steady footsteps", 4.0, 1, 1),
('move/run_sand', "Person running on sand, soft steady footsteps", 4.0, 1, 1),
('move/run_ice', "Person running on ice, short skating footsteps", 4.0, 1, 1),
('move/run_lava_rock', "Person running on cooled lava rock, crunchy footsteps", 4.0, 1, 1),
# ui
('ui/tick', "Soft UI tick", 0.5, 0, 1), ('ui/ready', "Friendly game ready chime", 1.0, 0, 1),
('ui/confirm', "Bright UI confirm blip", 0.5, 0, 1), ('ui/cancel', "Soft UI cancel blip, lower", 0.5, 0, 1),
('ui/nav', "Subtle menu navigation click", 0.5, 0, 1), ('ui/fanfare', "Short triumphant brass fanfare for winning", 3.0, 0, 1),
('ui/whistle', "Referee whistle, short single blast", 1.0, 0, 1), ('ui/point_win', "Happy rising sting, point scored", 1.2, 0, 1),
('ui/point_lose', "Sad descending trombone sting, point lost", 1.5, 0, 1), ('ui/countdown', "Countdown beep, one tone", 0.5, 0, 1),
# crowd golf
('crowd/golf_murmur', "Small golf gallery murmur, polite quiet chatter and distant birds", 10.0, 1, 1),
('crowd/golf_hush', "Golf crowd going quiet, shushing, then silence with a faint breeze", 3.0, 0, 1),
('crowd/golf_clap', "Polite golf clap, about thirty people, short", 3.0, 0, 2),
('crowd/golf_swell', "Golf crowd excitement building rising murmur, anticipation, loop", 6.0, 1, 1),
('crowd/golf_inhale', "Crowd collective sharp inhale, holding breath", 1.5, 0, 1),
('crowd/golf_erupt', "Golf crowd erupting in cheers and applause after ball drops in the hole", 4.0, 0, 2),
('crowd/golf_groan', "Golf crowd collective groan 'ohhh' disappointed lip-out", 2.5, 0, 2),
('crowd/golf_ooh', "Golf crowd 'ooooh' near miss, then light clap", 2.5, 0, 2),
('crowd/golf_aww', "Golf crowd soft sympathetic 'awww'", 2.0, 0, 1),
('crowd/golf_roar', "Golf crowd huge roar of astonishment and celebration, whistling, hole in one", 5.0, 0, 1),
# crowd tennis
('crowd/tennis_murmur', "Tennis stadium crowd low murmur between points, programs rustling", 10.0, 1, 1),
('crowd/tennis_hush', "Tennis crowd hushed silence before a serve, a cough far away", 3.0, 0, 1),
('crowd/tennis_rally', "Tennis crowd murmuring and rising during a rally, quiet 'ooh' on each shot, loop", 8.0, 1, 1),
('crowd/tennis_ooh', "Tennis crowd 'ooooh' at a close line call", 2.0, 0, 2),
('crowd/tennis_applause_short', "Tennis crowd short applause after a point", 3.0, 0, 2),
('crowd/tennis_applause_long', "Tennis crowd long loud applause with cheers for set point won", 6.0, 0, 1),
('crowd/tennis_sigh', "Tennis crowd sighing after a fault", 1.5, 0, 1),
('crowd/tennis_ovation', "Tennis stadium standing ovation, roaring applause and whistling, match end", 8.0, 0, 1),
# grunts
('grunt/m_ground', "Male tennis player effort grunt on a ground stroke, short", 0.7, 0, 3),
('grunt/m_power', "Male tennis player loud effort grunt on a hard forehand", 0.9, 0, 3),
('grunt/m_serve', "Male tennis player grunt on a serve, rising effort", 0.9, 0, 3),
('grunt/m_smash', "Male tennis player roar-grunt on an overhead smash", 1.0, 0, 3),
('grunt/m_reach', "Male tennis player stretching effort grunt reaching wide", 0.8, 0, 2),
('grunt/m_frustrated', "Male tennis player frustrated exhale after losing a point", 1.0, 0, 2),
('grunt/f_ground', "Female tennis player effort grunt on a ground stroke, short", 0.7, 0, 3),
('grunt/f_power', "Female tennis player loud effort grunt on a hard forehand", 0.9, 0, 3),
('grunt/f_serve', "Female tennis player grunt on a serve, rising effort", 0.9, 0, 3),
('grunt/f_smash', "Female tennis player loud grunt on an overhead smash", 1.0, 0, 3),
('grunt/f_reach', "Female tennis player stretching effort grunt reaching wide", 0.8, 0, 2),
('grunt/f_frustrated', "Female tennis player frustrated exhale after losing a point", 1.0, 0, 2),
# ambience
('amb/resort', "Tropical resort tennis court ambience, ocean waves, distant birds, light breeze", 10.0, 1, 1),
('amb/skyscraper', "Rooftop ambience high above a city, steady wind, faint distant traffic", 10.0, 1, 1),
('amb/volcano', "Volcano ambience, deep rumble, distant bubbling lava, hot wind", 10.0, 1, 1),
('amb/cliffside', "Seaside cliff ambience, crashing waves, seagulls, wind", 10.0, 1, 1),
('amb/wildisles', "Tropical island jungle ambience, insects, birds, gentle surf", 10.0, 1, 1),
('amb/magma', "Magma course ambience, low rumble, crackling lava, hissing steam", 10.0, 1, 1),
]
items = []
for n, p, d, loop, v in S:
    for i in range(v):
        items.append((f'sfx/{n}_{i+1}.mp3', dict(text=p, duration_seconds=d, loop=bool(loop), prompt_influence=.5)))
secs = sum(kw['duration_seconds'] for _, kw in items)
print(len(items), 'gens', secs, 's', secs * 40, 'credits')
if 'dry' not in sys.argv:
    run(items, lambda **kw: client.text_to_sound_effects.convert(**kw), 'sfx')
