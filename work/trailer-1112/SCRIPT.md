# MOTIONSPORTS — "Settle It" (script, draft 2)

A wordless short film, about 2 minutes · 24 fps · 2.39:1 widescreen · no narration, no dialogue.
Draft 1 was a mood montage. This draft is a story with two characters, after studying how Overwatch does it.

## What I took from the Overwatch films

Watched: the 2014 *Cinematic Trailer* and the short *Dragons* (frame sheets of both), plus Blizzard's own write-up of how the shorts are made. *The Last Bastion* is their fully wordless short, which is the model for telling ours without narration.

1. **One small story, not a tour.** Each film is one character wanting one thing, an obstacle, a turn, and a last image that lands. No feature list.
2. **Personality before action.** They spend the first third on faces, hands and rituals (Hanzo laying out his offering, the kid brother's wide eyes). The action only matters because we already know who is doing it.
3. **Someone to watch it through.** The museum trailer is seen through two brothers; their reactions carry the awe and the jokes.
4. **Fights are short exchanges, then a reaction.** One signature move at a time, clear geography (a wide silhouette, then a tight insert), then cut to a face.
5. **Quiet is used.** Setup shots hold 3 to 6 seconds. The fast cutting is saved for a few bursts.
6. **One colour world per place** (purple dusk and warm lanterns in *Dragons*; white and blue in the museum), with faces lit by a soft key and a strong rim.
7. **They end on feeling, then the logo.** Tracer's wink, the kid's "whoa", Hanzo alone with the offering.

## The story in one line

A show-off who has never lost meets a rival who doesn't say a word. Best of three: rooftop, volcano, neon lanes. We never find out who wins, because by the end that is not the point.

## The two characters

- **Him** (red polo): the showman. Plays to the crowd, big gestures, big swings. He is the one we follow, and the one who changes.
- **Her** (lime top, white skirt): the mystery. Arrives out of the dark, economical, unreadable under the cap. Like the masked challenger in *Dragons*, she is shot from behind, in silhouette and in mid shots until the story lets us see her smile.
- **The umpire in the chair:** our audience. His head snaps left and right with the ball; he flinches, he leans in.

---

## Scene 1 — The challenge · rooftop, night (0:00 – 0:22)

- Black. City wind. The court lights thump on one bank at a time.
- He is alone on the court, warming up for nobody: push-ups on the baseline, a wave to the stands. The umpire watches, unimpressed.
- At the far end, one light is still off. A tennis ball bounces out of that darkness, rolls across the court and stops against his shoe.
- He looks up. She walks out of the dark, racket low, face hidden by the brim. She stops at her baseline and waits.
- Close on him: the grin. He flicks the ball up with his racket and beckons: bring it.

**Caption:** ROUND ONE

## Scene 2 — Tennis (0:22 – 0:52)

- His serve. The toss climbs past the city lights in extreme slow motion. Strings meet ball, the picture snaps to full speed and the music hits.
- She returns it without seeming to move. His grin fades a little.
- Three exchanges, each bigger than the last. Between them: the umpire's head whipping side to side.
- He winds up for the winner, a full overhead smash. Cut to her: already there. She sends it past him, low and soft.
- He dives. Slow motion, full stretch. The ball passes a finger's width beyond his strings. He slides to a stop on the blue.
- He lies there looking at the sky. She has already turned her back; a small fist closes at her side. The umpire points to her end.

**Caption:** 1 – 0

*Hand-off: the tennis ball rolls to a stop on the court. Match cut: a golf ball sitting on a tee.*

## Scene 3 — Golf · the volcano, dawn (0:52 – 1:24)

**Caption:** ROUND TWO

- Lava glow and first light. She plays first: one smooth, unhurried swing, the ball lands safely on the green. She steps aside and looks at him. Your turn.
- He looks at her ball, then at the direct line: straight across the lava. Close on his face: he is not grinning now, he is thinking.
- The backswing in slow motion, the club crossing the glow of the crater. Impact.
- The long shot of the film: the camera flies with the ball, high over the lava field, the green small and far away.
- It lands, runs, slows, stops on the lip of the cup. Nobody breathes. It drops.
- He erupts: the full jump for joy. Cut to her: surprise, then the first hint of a smile. A small nod.

**Caption:** 1 – 1

*Hand-off: the ball falls into the dark of the cup. Out of the dark rolls a bowling ball.*

## Scene 4 — Bowling · the neon lanes (1:24 – 1:50)

**Caption:** ROUND THREE

- Neon, a full house, the decider. They stand side by side at the ball return, not looking at each other.
- She bowls. From inside the pin deck, in extreme slow motion: a strike. She turns around with her arms out, and for the first time we see her properly, laughing.
- He steps up. The music drops to a heartbeat. He looks back at her once. She gives him nothing.
- His approach in slow motion, the release, the camera racing down the lane behind the ball. Cut to her leaning forward. Cut to the ball arriving at the pins.
- Cut to black on the sound of the crash.

## Title (1:50 – 1:56)

**MOTIONSPORTS**

## Tag — after the title · rooftop, night (1:56 – 2:06)

- The rooftop again, the crowd gone. The two of them at the net, worn out. He holds up a tennis ball and raises his eyebrows: again?
- She takes it out of his hand and walks to her baseline. He laughs and follows.

**Caption:** PLAY TOGETHER.
**End card:** TENNIS · GOLF · BOWLING / YOUR PHONE IS THE CONTROLLER.

---

## Sound (no voice at all)

- An original score generated in code: near silence in Scene 1, a pulse that grows through the rounds, one full theme on the golf flight, a heartbeat in the decider, a single hit on the title.
- The game's own sounds for the ball, strings, crowd and pins.

## Captions

All captions are entries in `work/trailer-1112/captions.json` (text, start time, duration, style). Edit the file, run `work/trailer-1112/build.sh`, and a new video comes out without re-filming.

## Not yet checked in the game

- Whether the umpire can be made to flinch and point (his head already follows the ball).
- The exact "stops on the lip, then drops" roll in golf: I will animate that ball by hand if the game's own roll will not do it.
- Standing two heroes together at the bowling ball return; the game only shows one bowler at a time.
- Her close-up: under film light her face is the weakest thing in the tests (no hair under the cap, very large eyes). The script keeps her in mid shots and silhouette until Scene 4 for that reason.

## Your calls

- **Names.** Overwatch films lean on named characters. Ours have none. I left them nameless; a name plate each in Scene 1 would be one caption line apiece.
- **Length.** About 2:06 as written. A 60 to 75 second cut would keep Scenes 1, 2 and 4 and shorten golf to the ball flight.
- **Who is the show-off.** As written it is him, because his face holds a close-up better.
