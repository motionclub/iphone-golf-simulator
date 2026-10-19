# Research: how top sports games built VFX, hit sound, haptics and camera feel

Compiled 2026-10-17 for the party tennis + golf game (phone = motion controller, game AirPlayed to TV, soft-plastic toy look, Unity URP).

**Legend**
- **[S]** sourced fact, URL given.
- **[O]** my own observation or inference. Not a developer statement.
- **[V]** needs checking by frame-stepping the listed footage before we rely on it.

**Source quality.** Nintendo's own interviews ("Ask the Developer", Iwata Asks) are the strongest sources. Reviews and wikis are secondary. Few developers have written publicly about sports-game SFX or VFX in detail. Where nothing primary exists, I say so instead of filling the gap.

**Access note.** The iwataasks.nintendo.com host failed certificate checks from this machine. The nintendo.com/en-gb mirrors of the same interviews load fine, so those are cited where possible.

---

## 1. Wii Sports (2006) and Wii Sports Resort (2009): tennis and golf

**Controller speaker used for hit sounds (the closest match to our phone-as-controller setup)**
- [S] At the 2006 reveal, the tennis demo played a ball "pop" from the controller's new speaker on every hit. Source: Nintendo World Report, 9 May 2006, https://www.nintendoworldreport.com/news/11434
- [S] E3 2006 hands-on: "The remote has a rumble pack built in so you actually *feel* when you've hit the ball." Source: https://hexus.net/gaming/news/wii/5607-e3-2006-live-massive-wii-games-hands-on/?page=2
- [S] **Speaker hardware.** 4-bit Yamaha ADPCM or signed 8-bit PCM at very low sample rates (WiiBrew suggests 8-bit PCM at about 2 kHz). Rumble is a single on/off eccentric motor with no intensity control. So the hit sound in the hand was a short, lo-fi transient, and the "real" sound played on the TV. Source: https://wiibrew.org/wiki/Wiimote
- [S] Player complaint: the tennis hit sound from the remote is identical on every hit, and many players switch the speaker off. Forum anecdote, not a developer statement. Source: https://forums.dolphin-emu.org/Thread-wiimote-sound
- [S] **Nintendo's rule for the speaker (Super Mario Galaxy sound team, Iwata Asks)**
  - The team decided against playing sound through the speaker constantly, because doubling the TV sound in the hand was meaningless.
  - They used it only for the player's own physical actions, such as hitting enemies.
  - Star Bits are the example: a sound plays on the TV, then a delayed second sound plays from the remote, so the bits feel as if they fly into your hand.
  - Iwata said sound coming from your hand adds depth, alongside the rumble.
  - Source: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-Super-Mario-Galaxy/Volume-3-The-Sound-Team/4-Sound-Effects-You-Can-Feel/4-Sound-Effects-You-Can-Feel-205134.html
- [O] **What this means for us.** The phone should play only the player's own contact sound (racket or club impact) plus haptics. It should not mirror the TV mix. A TV echo a few ms later, or a different layer on the TV (crowd, ball flight, bounce), gives the "it came from my hand" spatial split.

**Visual tiers in tennis**
- [S] A Wii Sports serve hit at the top of the toss gives a "power serve": a super-fast ball with a smoke or fire trail. Fan or guide sources only. Source: https://strategywiki.org/wiki/Special:MobileDiff/236121
- [S] Swing timing sets direction: early pulls the ball, late pushes it. Nintendo kept this rule into Switch Sports (see section 2).
- [S] Crowd behaviour (strategy guide)
  - There are two cheer types: plain applause, and a whole-crowd "wow" for comebacks.
  - The crowd grows as your skill rating rises.
  - Source: https://strategywiki.org/wiki/Special:MobileDiff/340933
- [O] That is cheap but effective progression feedback: audience size works as a skill meter.

**Golf**
- [S] The power meter shows a thin white line for the live backswing. Swinging past blue into red makes the ball drift off line, so overswing is shown as a colour change, not a fail screen. Source: Nintendo UK "On target with Wii Sports golf", https://www.nintendo.co.uk/en-gb/News/2008/On-target-with-Wii-Sports-golf-250745.html
- [S] Wii Sports Resort golf grew from 9 to 18 holes late in development.
- [S] Table tennis replaced tennis so the original game would keep being played. Kenta Sato (tennis programmer on the original) said MotionPlus responsiveness made table tennis possible, because tennis's slower rallies had hidden input delay. Source: Iwata Asks Wii Sports Resort, https://www.nintendo.com/fr-fr/Iwata-demande/Iwata-demande-Wii-Sports-Resort/Iwata-Asks-Wii-Sports-Resort/5-Le-tennis-passe-a-table/5-Le-tennis-passe-a-table-220402.html
- [O] **What this means for us.** A slower ball hides latency. Our AirPlay path adds TV latency, so the phone-side hit sound and haptic, which have near-zero latency, carry the "contact" moment. The TV visual can trail by about 100 ms without breaking the feel.

**Wii Sports Club (Wii U, 2013): Iwata Asks**
- [S] **Opponent reactions are feedback.**
  - Shimamura: smash into the opponent's corner and you can tell your opponent is frustrated. Iwata adds that you see them stomping and swinging the racket.
  - The developers were "always grinning" while testing this.
  - Source: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-in-Motion-Wii-Sports-Club/Wii-Sports-Club/3-When-Mii-Characters-Get-Frustrated/3-When-Mii-Characters-Get-Frustrated-823820.html
- [S] **Lie shown on the second screen.** In golf, the GamePad on the floor shows the ball at your feet. Iwata notes you can tell at a glance whether it sits in the rough or a bunker. Source: https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-in-Motion-Wii-Sports-Club/Wii-Sports-Club/4-More-Realistic-Tennis/4-More-Realistic-Tennis-823870.html
- [O] **What this means for us.** The phone screen could show the lie (grass blades, sand, ball sitting down) as the second-screen equivalent.

**Footage to frame-step**
- `OsnNlg_Sask`, "Wii Sports 2006 full gameplay (ALL 5 SPORTS)": tennis starts at 0:00:14. Look at the serve trail on a well-timed serve, the ball contact flash or lack of one, and crowd reactions after the point. [V]
- `bMnN3m_5X-A`, "Wii Sports - Tennis". [V]
- `1hEVZTld8u4`, "Every Hole in One in Wii Sports Resort Golf": hole-in-one celebration, camera and crowd. [V]

---

## 2. Nintendo Switch Sports (2022; golf added Nov 2022)

Primary source: Ask the Developer Vol. 5, https://www.nintendo.com/sg/interview/as8s/ (parts 01–04). Summary page: https://www.nintendo.com/au/news-and-articles/ask-the-developer-vol-5-nintendo-switch-sports/

- [S] **Sound priorities (Sound director Natsuko Yokoyama, part 3)**
  - Motion-control sound effects come first.
  - Earlier games had no music during matches, which built tension and made the swing sounds stand out.
  - Switch Sports added music, but placed it as if it plays from speakers inside the venue, and mixed it so it never covers the swing sounds.
  - Yokoyama said that layering more sound makes repeated solo play more enjoyable.
  - The team also tuned how sound resonates in each facility (part 4).
  - Source: https://www.nintendo.com/sg/interview/as8s/03.html
- [S] **Concepts dropped for the sound's sake**
  - A robot-athlete concept was rejected partly because it implied mechanical "clunk" sounds that would compete with the motion sounds.
  - A pro stadium with a big crowd was prototyped and dropped as not casual enough.
  - Source: part 3, same URL.
- [S] **Latency versus accuracy trade-off (programmer Shinji Okane, part 2)**
  - Waiting for the whole swing gives accurate detection, but players feel the game is "one step behind".
  - Responding early gives a fast reaction with less data.
  - Early detection was right only about 80–90% of the time, and they pushed past 90% using deep learning.
  - Source: https://www.nintendo.com/sg/interview/as8s/02.html
- [S] **Timing sets direction (director Yoshikazu Yamashita, part 2)**
  - Direction comes from swing timing, not swing direction. Reading swing direction made the controls unstable.
  - Local tennis also reads a racket twist after the swing; online play cannot, because of lag (part 4).
- [S] **Perfect serve feedback:** hitting the serve at the top of the toss turns the ball trail red and gives a faster ball. Source: https://www.touchtapplay.com/how-to-do-rocket-serves-in-nintendo-switch-sports-tennis/
- [S] **Golf update:** 21 holes from the Wii Sports series, plus online Survival Golf where the worst player each hole is eliminated. Sources: https://www.nme.com/news/nintendo-switch-sports-is-getting-a-free-golf-update-next-week-3353736 and https://www.pockettactics.com/nintendo-switch-sports/golf
- [O] I found no source on Switch Sports HD Rumble on hit. Frame-stepping cannot show rumble, so this stays unknown.
- [O] **What this means for us**
  - Mix the swing and hit sounds above everything else.
  - Diegetic venue music, ducked under hits, is the Nintendo answer to "music or no music".
  - Hit detection should fire on the earliest confident sample. Our phone sound and haptic must not wait for the full swing.

**Footage to frame-step**
- `T9MhqWwhsIA`, "Nintendo Switch Sports - Official Gameplay Trailer". [V]
- `MbHumqb00Yg`, "Casual Sport Series: Tennis - Official Gameplay Trailer": look for the red perfect-serve trail, the contact frame, and any flash. [V]
- `LivrZI3_TPc`, "Nintendo Switch Sports Golf Update and Overview Trailer". Also `NDLfV1dhiok`, "Official Golf Update Trailer". Look at ball flight trail, cup-in celebration and Survival elimination UI. [V]

---

## 3. Mario Tennis Aces (Switch 2018, Camelot) and Mario Tennis Fever (Switch 2, Feb 2026)

**Aces mechanics with built-in VFX tiers** (source: Mario Wiki, https://www.mariowiki.com/Mario_Tennis_Aces)
- [S] **Shot-type trails are colour-coded:** red for topspin, blue for slice, purple for flat, orange for lob, white for drop shot. The colour tells the opponent what is coming.
- [S] **Energy gauge**
  - It fills from rallying, charging shots and well-timed Trick Shots.
  - It turns yellow when a Zone Shot is available.
  - A rotating Star Point appears on the court where a Zone Shot can be taken. Since v3.0.0 it turns turquoise when you stand in it.
- [S] **Zone Shot**
  - Time slows, the camera moves to first person, and you aim a reticle with gyro or stick.
  - Aiming drains energy. If energy runs out, the shot fails and pops up high.
- [S] **Zone Speed** slows time with a trigger hold.
- [S] **Special Shot** plays a short character-pose animation, then a first-person aim.
- [S] **Camera zoom** is used for Zone aiming and for challenge (line-call) moments.
- [S] **Racket damage:** a badly timed block of a Zone or Special Shot damages the racket. Three Zone hits or one Special breaks it. Results screens show coloured X marks.
- [S] **Charge shot:** hold the button early to charge. A max charge pushes the opponent back.
- [S] **Swing Mode** (one Joy-Con, motion): early swing gives a pull shot, late gives a push shot, and a badly timed hit gives a slow, attackable ball.
- [S] **Rumble as tension.** In the tournament demo, the Joy-Con pulsed like a heartbeat before match-point serves. Source: Nintendo Wire impressions, https://nintendowire.com/features/impressions-mario-tennis-aces-set-to-serve-up-some-fun-this-summer/
- [S] **Serve grades** (Nintendo's official tips): a near-peak serve is rated "GOOD" and is faster than normal; a peak serve is "NICE". Source: https://play.nintendo.com/news-tips/tips-tricks/mario-tennis-aces-tips-tricks/ (via search summary)
- [S] **Design intent:** Camelot wanted to "reset" the series and make it more competitive, eSports-like. Source: Nintendo Dream interview via Nintendo Everything, https://nintendoeverything.com/mario-tennis-aces-devs-on-the-games-mechanics-story-mode-how-new-characters-were-decided-name-more/
- [S] Music is by Motoi Sakuraba (Camelot's long-time composer). I found no public sound-designer credit or interview. Source: https://en.wikipedia.org/wiki/Motoi_Sakuraba
- [O] **Aces' tier ladder** (normal → charged → Trick → Zone → Special) escalates each step by adding:
  - a time slowdown,
  - a camera change (third person → first person → cutscene),
  - a stronger trail,
  - a consequence (racket damage).
  - This is the clearest "hit-strength tier" design in the genre.

**Mario Tennis Fever (Switch 2, 12 Feb 2026)**
- [S] Over 30 "Fever Rackets". A Fever Shot is a powerful smash whose racket effect triggers where the ball lands.
- [S] Example effects: Flame (small fires that stun), Ice (slippery sheet), Fire Bar, Freezing (icicles), Volcano, Spiny, Magic (swaps the opponent's racket for a frying pan).
- [S] Effect sources: https://www.videogameschronicle.com/guide/mario-tennis-fever-the-best-and-worst-fever-rackets/ and https://www.shacknews.com/article/147805/mario-tennis-fever-review-score
- [S] The Talking Flower introduces players and commentates. There are instant replays after scores.
- [S] Criticism: in long rallies, Fever Shots happen on both sides every point, which reviewers found tiresome. Source: https://www.dexerto.com/gaming/mario-tennis-fever-review-3315802/
- [O] **Lesson.** If the top tier fires too often it stops being special. Gate big VFX by rarity.

**Footage to frame-step**
- `0lPJCJqpcK8`, "Mario Tennis Aces - Nintendo Direct Trailer".
- `J7NG82-2iXs`, "Mario Tennis Aces - All Zone Shots Animations (All Characters)".
- `A5BUIycx8iE`, "All 9 Special Shots in Mario Tennis Aces Demo".
- Look at: slowdown onset frames, screen tint or vignette, trail width at each tier, contact flash shape, and camera cut timing. [V]
- Mario Tennis Fever: `0qlPHM5wQyY` ("Mario Tennis Fever - Trailer") and `iP5MGnurtLQ` (overview trailer). Look at court-hazard decals and spawn FX on landing. [V]

---

## 4. Mario Golf: Super Rush (Switch 2021, Camelot)

- [S] **Special shots (Nintendo Everything interview)**
  - The team considered a tennis-style Zone Shot but rejected it as against the spirit of golf (Yamamura).
  - Because golf is solo, they wanted a special shot that affects other players' balls, which is why it makes shockwaves.
  - H. Takahashi pictured a spinning Donkey Kong landing on the green with a huge shockwave.
  - Source: https://nintendoeverything.com/mario-golf-super-rush-interview-opening-swing-mode-more/
- [S] **The Impact timing click was removed**, and that held up in prototyping. The vertical shot gauge bends to show how slopes curve a shot (S. Takahashi). Reviewers called the bending gauge an effective visual hint. Sources: same interview, and https://thesixthaxis.com/2021/06/24/mario-golf-super-rush-review-nintendo-switch
- [S] **Swing Mode was tuned to the very end.** The hard part was not the code but making it feel like real golf. When a player misses, the game tries to show what caused it (S. Takahashi). Same interview.
- [S] **Power gauge shift zones:** red zones either side of the gauge, sized by club and lie. Swinging into them can shift the ball sideways at random. Overhead view shows carry and a thick white roll ring. Source: https://nintendo.com/us/whatsnew/planning-your-shot-in-mario-golf-super-rush
- [S] **Nice Shot across the Mario Golf series** (source: https://www.mariowiki.com/Nice_Shot)
  - It is a well-timed, well-powered swing.
  - In Super Rush, confetti launches on a Nice Shot.
  - In World Tour, a confirm sound plays and the ball leaves gold and rainbow streaks.
  - In Mario Golf 64, no Nice Shot is called if the ball is heading for a hazard. No Nice or Good Shot is called if the ball doesn't end on the green, fringe or fairway.
  - So the celebration is gated by outcome, not just input.
- [S] **Special shot effects:** Luigi's freezes the green; Wario's Lightning Blast drives the ball straight down from a thundercloud; others push opponents' balls. Sources: Looper, https://www.looper.com/467417/mario-golf-super-rush-special-shots-explained, and Mario Wiki.

**Footage to frame-step**
- `g__umJvdlh4` and `ds-0l01i2hs`, "All Special Shots": look at the shockwave ring on the green, ground decal and camera shake. [V]

---

## 5. Everybody's Golf / Hot Shots Golf (Clap Hanz; PS4 2017, VR 2019)

- [S] Classic three-press swing: start, set power, then hit the impact window. The perfect-impact window changes size with club and lie. Super Backspin requires perfect impact. Source: Push Square guide, https://www.pushsquare.com/news/2017/08/guide_how_to_play_like_a_pro_in_everybodys_golf_on_ps4
- [S] PS4 review: "Plenty of visual effects" fire on a perfect shot or a chipped-in eagle. A complete miscue also gets its own comic effect, which is the series' trademark charm. The reviewer found the on-screen graphics a little busy. Source: https://press-start.com.au/reviews/playstation4-reviews/2017/08/29/everybodys-golf-review-old-friend-returns/
- [S] Clap Hanz was founded by former Camelot staff, which explains why the systems are shared with Mario Golf (Push Square company page).
- [O] **Comic failure feedback.** The series gives failures their own funny effect. A miscue is a moment, not a void. That suits party play.

**Footage to frame-step**
- `bwMnPKKf5uo`, "Everybody's Golf E3 2017 Gameplay Trailer" (PlayStation AU).
- `_K5R5fkh6po`, "'Complete Guide' Gameplay Trailer".
- Look at the perfect-impact sparkle, the miscue effect, and chip-in fireworks. [V]

---

## 6. Golf Story (Sidebar Games, Switch 2017) and Sports Story (2022)

- [S] Designer Andrew Newey said he wanted to capture golf's vibe (the sounds, sights and characters) more than anything. The game began as a two-person Wii U project and was influenced by Mario Golf on Game Boy Color. Sources: https://nintendoeverything.com/interview-golf-story-dev-on-wii-u-origins-cut-ideas-and-more/ and https://en.wikipedia.org/wiki/Golf_Story
- [O] I found no detailed public material on Golf Story's hit SFX or VFX.

**Footage to frame-step**
- `YyjTzc7EH4I`, "Golf Story Reveal Trailer": 2D shot meter and impact pop. [V]
- `geq1XrcqgHM`, "Sports Story Trailer". [V]

---

## 7. TopSpin 2K25 (Hangar 13 / 2K, 2024)

- [S] **Timing Meter (official 2K "Centre Court Report")**
  - Minimal design for readability, with a green zone. Releasing in green gives a "perfect shot"; early or late risks the net or out.
  - On clay, sliding kicks up dust and leaves scuff marks, and the court is swept between sets.
  - On grass, the area behind the baseline wears from grass to dirt over a tournament.
  - Source: https://2k.com/games/topspin-2k/topspin-2k25/centre-court-report/gameplay/
- [S] **Post-shot label and meter speed (Shacknews)**
  - After each shot a label reads perfect, good, too soon or too late. The reviewer says this shows why a shot was mishit, so the timing doesn't feel like cheating.
  - The meter line moves faster on difficult returns and slower on easy ones in good position.
  - Low stats can still send a perfect-timed ball into the net.
  - Source: https://shacknews.com/article/139582/topspin-2k25-review-top-spin
- [S] **Pre-release preview:** the meter appears above the player's head, with a red circle near the legs. Source: Sports Gamers Online, https://www.sportsgamersonline.com/games/2k-reveals-topspin-2k25-official-gameplay/amp/
- [S] **Audio:** there is no commentary, only the court PA announcer. A grunt-frequency slider is in the character creator. Reviewers called the crowd NPCs lacklustre. Sources: MP1st preview, https://mp1st.com/?p=254835, and Shacknews.
- [O] **Lessons for us**
  - The grade label explains the outcome, which keeps the player trusting the system.
  - Persistent surface marks (scuffs, worn baseline) are cheap and very readable.
  - Our soft-plastic courts could take toy-like scuff decals.

**Footage to frame-step**
- `7eNj6n6WUmQ`, "TopSpin 2K25 - Official Gameplay Showcase Trailer".
- `3a3Er6BhL24`, "How to turn on and off Timing Feedback in TopSpin 2K25": shows the feedback label UI.
- `r_nLe9Ek9Oc`, timing-meter toggle.
- Look at the label pop animation, colour per grade, and the clay dust puff. [V]

---

## 8. PGA Tour 2K21 / 2K23 / 2K25 (HB Studios) and The Golf Club

- [S] **Commentary (PocketGamer.biz interview with lead audio designer John McCarthy)**
  - McCarthy, the in-house audio designer, voices the casual commentary.
  - It began as placeholder lines, because a computer voice could not give the right tone.
  - The target was a weekend round with friends: second person, talking *to* you, not *about* you.
  - For new lines, voice talent gets a situation and at most one example line, then records many variations.
  - Source: https://www.pocketgamer.biz/interview/73766/pga-tour-2k21-john-mccarthy-interview/
- [S] **Impact sound tells you strike quality (2K23 reviews)**
  - "Various sounds at impact" reward a pure strike, and a poor strike is audible at contact. Source: Sports Gamers Online, https://www.sportsgamersonline.com/games/pga-tour-2k23-review/
  - Another review calls the sounds "very crisp", giving feedback on how well you hit. Source: https://www.thumbculture.co.uk/pga-tour-2k23-pc-review
- [S] After each shot, a feedback graphic shows swing path and tempo. Source: GamesRadar, https://www.gamesradar.com/pga-tour-2k23-review
- [S] The PS5 version supports DualSense vibration and trigger effects (PlayStation store listing). No source details how they map to the swing. Source: https://playstation.com/en-us/games/pga-tour-2k23
- [S] PGA Tour 2K21 main-menu music is by Christopher Tin (first hired composer). Tournament music copies TV golf broadcasts.
- [O] Search summaries claim McCarthy field-recorded swings and putts at local courses for The Golf Club, but I could not confirm this in any source. Treat it as unverified.

**Footage to frame-step**
- `9okRdqlh3_Q`, "PGA TOUR 2K25 Official Gameplay Trailer" (2K): look at the shot tracer, the post-shot tempo graphic, and the camera after impact. [V]

---

## 9. EA Sports PGA Tour (2023)

- [S] The Pure Strike system is built on ShotLink and TrackMan data (ball speed, launch angle), plus motion capture of real players. The Frostbite engine and LiDAR or drone course capture give photoreal courses. Sources: https://mp1st.com/news/ea-sports-pga-tour-introduces-shotlink-system-to-the-game and https://www.gamerbraves.com/?p=140325
- [O] I found no public audio or VFX write-up. The game's shot feedback presumably flows from simulation data, but I have no source for that.

**Footage to frame-step**
- `0ZCOFsKQuGI`, "EA Sports PGA Tour - Official Gameplay Overview (4K)", narrated by commentator Iona Stephen. [V]
- `VUGvJ3WPDUk`, "Launch Trailer". [V]

---

## 10. Golf Clash (Playdemic / EA, mobile) and Tennis Clash (Wildlife, mobile)

**Golf Clash**
- [S] **Slingshot swing (Game Developer UX review, Om Tandon, March 2018)**
  - Pull the ball back and release when the moving needle lines up. Results are graded Great, Perfect or Sliced.
  - The timing borrows CSR2's colour-zone alignment.
  - A perfect release does not guarantee a good result: wind, lie, ball and club still matter.
  - Both players see the same camera, so watching the opponent works as a tutorial.
  - Large bold fonts are used for readability.
  - Source: https://www.gamedeveloper.com/design/ux-review-golfclash-s-swing-to-success-
- [S] Putting swaps the bullseye for a light path, plus a second needle alignment. Source: guide, https://www.levelwinner.com/golf-clash-ultimate-guide-13-tips-tricks-become-best-player/
- [S] Golf Clash was deconstructed at GDC 2018 (Deconstructor of Fun) on audience and skill-versus-luck. Players who lose feel they could have played better, not that stats beat them. Source: https://mobilefreetoplay.com/gdc-2018-deconstructing-golf-clash-and-rules-of-survival/
- [O] I found no public material on Golf Clash's perfect-shot SFX or haptics.

**Tennis Clash**
- [S] Swipe to hit, tap to move. Swipe length sets power; swipe direction sets direction. Matches are shortened to first to seven points. Satisfaction comes from placing the ball where you planned. Source: GameAnalytics (Sarah Impey), https://www.gameanalytics.com/blog/how-tennis-clash-scored-a-golden-set

**Footage to frame-step**
- `CeOY62p0Tmo`, "How to hit the PERFECT shot! Needle Trainer Tutorial": look at the needle, the bullseye, and the Perfect label animation. [V]
- `5JvngTcVAVo`, Tennis Clash gameplay: look at the swipe trail and the hit spark. [V]

---

## 11. AO Tennis 2 (Big Ant) and Matchpoint Tennis Championships (Torus)

- [S] **AO Tennis 2 reviews**
  - Crowd reactions are exaggerated or mistimed enough to notice. Source: https://www.gamingnexus.com/Article/6068/AO-Tennis-2/
  - The crowd "couldn't care less" during long rallies. Source: Sports Gamers Online.
  - Ball hits and grunts were praised. Source: Thumbculture.
- [S] **Matchpoint review:** shot power audibly changes the strike sound. Grunts and strikes sound right; commentary is weak. Source: https://www.theouterhaven.net/2022/07/matchpoint-tennis-championships-solid-fundamentals-lots-to-learn/
- [S] **Matchpoint development:** the hardest problems were animation responsiveness and matching ball physics to the animations. The first prototype was scrapped. Source: Impulse Gamer interview with David McIntosh, https://www.impulsegamer.com/torus-interview-with-david-mcintosh-matchpoint-tennis-championships
- [O] **Lessons**
  - Crowd audio must track rally length and tension. A crowd that ignores a long rally reads as broken.
  - Shot power should change the hit sound (pitch, gain, layer), not only its volume.

---

## 12. Adjacent references (non-sports, directly reusable)

- [S] **Sakurai on hitstop (Famitsu column; Source Gaming fan translation)**
  - Attacker and victim freeze for the same time, and stronger hits freeze longer up to a cap.
  - Marth's sword **tip (sweet spot) gets more hitstop than the edge**.
  - During the freeze, the victim shakes side to side on the ground and up and down in the air. The shake decays and scales with camera distance.
  - Hitstop is kept short in multiplayer, because a freeze opens a window for third parties.
  - Source: https://sourcegaming.info/2015/11/11/thoughts-on-hitstop-sakurais-famitsu-column-vol-490-1/
- [S] **Sakurai video "Eight Hit Stop Techniques"** (`tycbMSjDDLg`)
  - shake the hit object more;
  - keep the hitbox still;
  - shake horizontally on the ground, vertically in the air;
  - decay the shake;
  - control the amount;
  - interpolate into the damage pose;
  - keep the attacker moving slightly;
  - scale shake with camera distance.
  - Source: https://nintendowire.com/news/2022/12/12/this-week-in-sakurai-12-5-12-11-fine-tuning-hit-stop-and-cheating-the-system/
  - The companion video "Stop for Big Moments!" is `OdVkEOzdCPw`.
- [S] **Loughborough sports-engineering research on golf feel** (Roberts, Jones, Rothberg et al.)
  - Golfers' ratings of a shot's pleasantness tracked impact-sound loudness and sharpness.
  - Sound correlated with perceived feel more strongly than hand vibration did.
  - In putting, the louder and sharper sound was judged the "harder, faster" ball, with spectral peaks around 2–4 kHz.
  - Lower vibration at the hands was described as "pleasant" and "solid".
  - Sources: https://dspace.lboro.ac.uk/2134/11475, https://repository.lboro.ac.uk/articles/journal_contribution/Assessment_of_the_impact_sound_in_golf_putting/9564332, https://dspace.lboro.ac.uk/2134/11474
- [S] **Loughborough tennis-racket impact thesis (Banwell 2013):** the racket sound has two parts, an initial impulsive crack and a quieter, longer ring. Source: https://dspace.lboro.ac.uk/dspace-jspui/handle/2134/13678
- [S] **Apple WWDC19 "Designing Audio-Haptic Experiences" (session 810)**
  - Three principles: Causality, Harmony, Utility.
  - Sound and haptic are two instruments in the same tempo. Latency between them breaks the illusion.
  - Transient haptics suit impacts. Modulate intensity by impact velocity.
  - Pair a sharp-attack sound with a sharp transient.
  - Source: https://developer.apple.com/videos/play/wwdc2019/810 (implementation: session 223, https://developer.apple.com/videos/play/wwdc2019/223)

---

## Cross-game patterns

1. **The controller plays only the player's own contact, never a TV duplicate.** Hand-side sound and rumble mark "I hit it", and the TV carries the world. *(Wii Sports tennis speaker pop, Super Mario Galaxy speaker rule, Wii E3 rumble on hit; Apple Causality principle)*
2. **Timing is the main quality input, and its grade drives direction or power.** Early pulls, late pushes. *(Wii Sports, Switch Sports, Mario Tennis Aces Swing Mode, TopSpin 2K25, Golf Clash, Everybody's Golf, Mario Golf)*
3. **Every shot gets a named grade label** (Nice/Good, Perfect/Great/Sliced, perfect/good/too soon/too late). It explains the result and keeps trust. *(TopSpin 2K25, Golf Clash, Mario Tennis Aces serves, Mario Golf Nice Shot, OlliOlli Perfect/Sloppy)*
4. **The trail colour or style encodes shot type or quality.** *(Aces colour-coded trails, Switch Sports red perfect-serve trail, Wii Sports power-serve smoke trail, Mario Golf World Tour gold/rainbow streak)*
5. **A tier ladder adds a channel at each step:** trail, then flash, then slowdown, then camera change, then cutscene. *(Mario Tennis Aces charge → Trick → Zone → Special; Mario Golf Super Rush special shots; Fever Shots)*
6. **Slow-motion or time-stretch belongs to the top tier and costs a resource.** *(Aces Zone Speed and Zone Shot drain energy; Fever Shots gated by a meter)*
7. **The biggest VFX must stay rare**, or it becomes noise. *(Fever criticised for Fever Shots every point; Everybody's Golf "a little busy"; Sakurai keeps hitstop short in multiplayer)*
8. **Sweet spot gets more impact time and a crisper sound than an edge hit.** *(Sakurai: Marth tip vs edge; PGA 2K23 impact sounds reveal strike quality; Loughborough: louder, sharper reads as "solid")*
9. **Shot power changes the timbre, not just the volume.** *(Matchpoint, PGA 2K23, Loughborough putting study)*
10. **Celebrations are gated by outcome, not just input.** No "Nice Shot" when the ball is heading into a hazard. *(Mario Golf 64 / Nice Shot rules, Golf Clash perfect-but-in-the-rough)*
11. **Failure gets its own comic moment** instead of silence. *(Everybody's Golf miscue effects, Mii frustration in Wii Sports Club, Aces racket-break)*
12. **Opponent and crowd reactions are feedback channels.** *(Wii Sports two crowd cheer types and growing crowd; Wii Sports Club stomping Miis; Fever reaction animations; AO Tennis 2 as the negative example)*
13. **Crowd audio must follow rally length and tension**; a flat crowd reads as broken. *(AO Tennis 2 criticism; Wii Sports "wow" on comebacks)*
14. **Music never masks hit sounds.** Use none in matches, or diegetic venue music ducked under SFX. *(Wii Sports, Switch Sports Yokoyama interview)*
15. **Tension haptics are separate from hit haptics.** A heartbeat pulse before a match point builds anticipation. *(Mario Tennis Aces demo; Apple's alarm ramp before the sound)*
16. **Respond on the earliest confident sample.** Latency kills motion feel, and slower balls hide residual delay. *(Switch Sports latency-vs-accuracy trade-off; Wii Sports Resort table tennis needed MotionPlus)*
17. **Surface feedback persists:** dust puffs, scuffs, worn baselines, lie shown at the player's feet. *(TopSpin 2K25 clay and grass wear; Wii Sports Club GamePad lie view; Super Rush gauge bent by lie and slope)*
18. **Shot-aid UI shows physics before the swing** (bent gauge, roll ring, risk zones), and mistakes are shown after it. *(Mario Golf Super Rush, Wii Sports golf red overswing, PGA 2K tempo or path graphic)*
19. **Commentary is personal and second person**, from a cheap in-house voice or a mascot. *(PGA 2K McCarthy, Mario Tennis Fever Talking Flower, Aces Toad commentary)*
20. **Big-moment camera grammar:** zoom on aim and line calls, and cut to first person or a cutscene for the top tier. *(Mario Tennis Aces Zone/Special/challenge zooms; Super Rush special shots — to verify by frame-stepping)*
