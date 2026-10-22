import re
from common import *
src = open(HERE + '/../../Unity/Assets/Scripts/Tennis/TennisAnnouncer.cs').read()
tennis = re.findall(r'\("([a-z0-9_]+)", "([^"]+)"\)', src)
golf = {
 'welcome_cliffside': ["Welcome to Cliffside, everyone! Mind the edge, and the seagulls.", "Cliffside, folks! Gorgeous views, and plenty of ways to lose a ball."],
 'welcome_wildisles': ["Welcome to the Wild Isles! Sunscreen on, expectations low.", "Wild Isles, everyone! Paradise with teeth."],
 'welcome_magma': ["Welcome to Magma! The floor is lava. Actually, the floor is also lava.", "Magma course, brave souls! Try not to cook your ball."],
 'welcome_resort': ["Welcome to the Resort court, everyone! What a day for tennis.", "Resort court, folks! Sun's out, rackets out."],
 'welcome_skyscraper': ["Welcome to the Skyscraper court! Don't look down. Okay, maybe look down once.", "Skyscraper court, everyone! Up here, even the wind has an opinion."],
 'welcome_volcano': ["Welcome to the Volcano court! The mountain is grumpy today.", "Volcano court, folks! Hit it hard, but not as hard as the mountain."],
 'turn': ["You're up!", "Your shot!"],
 'long_drive': ["What a drive! That ball left the planet!", "Absolute bomb off the tee!", "Crushed it! Crushed!"],
 'fairway': ["Right down the middle. Boring, and perfect.", "Fairway! Textbook.", "Straight as an arrow!"],
 'close_pin': ["That's tucked in tight to the pin!", "Stiff! That's a tap-in!", "Oh, that's a dagger of an approach!"],
 'on_green': ["On the green. Nicely done.", "Green in regulation. Look at you.", "Safely on the putting surface!"],
 'long_putt': ["Are you kidding me? From there?", "Drained it! That was miles!", "Holy putt! Did you see that?"],
 'chip_in': ["Chipped in! Nobody saw that coming, including you!", "It went in from off the green! Unreal!", "Chip-in! Pure theft!"],
 'bunker_save': ["Out of the sand and close! Sand wizard!", "Nice escape from the beach!", "Bunker? What bunker?"],
 'birdie': ["Birdie! Lovely stuff.", "Birdie time!", "Under par! Show off."],
 'eagle': ["Eagle! Now we're talking!", "An eagle! Frame this one!", "Eagle! Somebody get this person a trophy!"],
 'hole_in_one': ["Hole in one! Unbelievable!", "ACE! In one! Absolutely unreal!"],
 'par': ["That's par. Solid and sensible.", "Par. The accountant's birdie."],
 'bogey': ["Bogey. We don't talk about it.", "Bogey. It happens to the best. Not you, apparently."],
 'double': ["Double bogey. Ouch.", "That hole owes you an apology. Actually, no, you owe it one."],
 'water': ["Splash! The fish say thank you.", "Into the water. Bold strategy.", "Swimming lessons for that ball!"],
 'lava': ["Into the lava! That ball is toast.", "Ooh, magma doesn't give refunds!", "Well, that ball's retired."],
 'oob': ["Out of bounds! Where was that going?", "That's out. Way out.", "Out of bounds. Were you aiming at somebody?"],
 'whiff': ["A swing and a miss! Air shot!", "You hit nothing. Impressive, really.", "The ball is still there, by the way."],
 'shank': ["Oh, that's ugly. Turn away, everyone.", "A shank! Where did that even go?"],
 'three_putt': ["Three putts. Have you tried putting it in?", "Three-putt. That green is not impressed."],
 'tap_miss': ["You missed THAT? A child could make that!", "Missed the tap-in. We saw it. Everyone saw it."],
 'tree': ["Straight into the tree. The tree wins.", "Timber! Well, bonk."],
 'ring': ["Through the ring! Fancy!", "Bonus hit! Nicely threaded!"],
 'round_over': ["That's the round! Well played, all!", "Round complete! Good golf, everyone!"],
}
tennis_extra = {
 'ace2': ["Ace! He never saw it!", "Ace! Unreturnable!"],
 'winner': ["What a winner!", "Placed it perfectly!", "Gorgeous shot!"],
 'smash': ["Smashed it!", "Overhead smash! Thunder!"],
 'line': ["Right on the line!", "Chalk flew! Inch perfect!"],
 'long_rally': ["What a rally!", "They just won't miss!", "Incredible rally, this!"],
 'comeback': ["Right back in it!", "The comeback is on!"],
 'net': ["Into the net. Gravity wins again.", "Net! It looked so confident, too."],
 'out2': ["Out! By a mile.", "Way long. The ball is in another court."],
 'dfault': ["Double fault! Oh dear.", "Two serves, zero courts. Double fault."],
 'whiff_t': ["A swing and a miss! Air tennis!", "You hit the air beautifully."],
 'lost_rally': ["All that effort. For nothing.", "Twenty shots, and you blew it. Ouch."],
 'break_point': ["Break point! Tension!", "Break point, folks!"],
 'set_won': ["Set! Beautifully done.", "That's the set!"],
 'match_end': ["Game, set, and match! What a performance!", "That's the match! Take a bow!"],
}
items = []
for k, t in tennis: items.append((f'announcer/tennis/{k}.mp3', dict(text=t)))
for d, pre in ((golf, 'golf'), (tennis_extra, 'tennis')):
    for k, ts in d.items():
        for i, t in enumerate(ts): items.append((f'announcer/{pre}/{k}_{i+1}.mp3', dict(text=t)))
n = sum(len(kw['text']) for _, kw in items)
print(len(items), 'lines', n, 'chars', flush=True)
if __name__ == '__main__':
    import sys
    if 'dry' in sys.argv: sys.exit()
    run(items, lambda text: client.text_to_speech.convert(voice_id=JAX, text=text, model_id='eleven_multilingual_v2', output_format='mp3_44100_128', voice_settings={'stability': .4, 'similarity_boost': .8, 'style': .45}), 'voice')
