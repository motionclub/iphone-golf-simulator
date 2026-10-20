# GATE EMOTES - definitions, written 2026-10-04 BEFORE any gate was run (clips solved and exported, nothing measured yet). Not edited after a run.

Measured on the exported FBX files re-imported into Blender (bone matrices, objects) + the numpy skinned body (EmoHero.mesh) + the in-game trace of the Unity film run.
World = Blender world: the hero faces -Y, its right is -X, up is +Z. Authoring forward = -Y. Thresholds are in the lines; a line is PASS only if every number on it passes, for BOTH heroes.
Interpretation notes (mine, stated up front): "same size as the run" is read as "at least as big as the run": the run clips' pelvis moves 0.05 m (vertical) / 0.03 m (lateral) with <6 deg of pitch and
the arms swing +-0.19 m with the elbows at 95-120 deg; the thrust must exceed the pelvis numbers and keep the run's arm posture. "Aggressive and angry" (Adnan, mid-job) is gated through body measures only (the faces
are painted, no expression bones exist): fold >= 40 deg, peak wrist speed, stamp, head shake.

| id | line | definition |
|---|---|---|
| N1 | the six names exist | `Male_/Female_` x {Emote_Scuba, Emote_Thrust, Emote_Spike, Intro_Wave, Intro_BringIt, Intro_Pushups}.fbx: 12 files in work/emotes/export/fbx AND byte-identical copies in Unity/Assets/Characters/MatchHeroes/<Hero>/; Unity imports one AnimationClip per file named <Hero>_<Name> (Unity log) |
| N2 | no other new clip | files added under Unity/Assets since the job baseline (data/unity_files_before.txt) that are *.fbx / *.anim / *.controller / *.overrideController / *.playable = exactly those 12 FBX; none removed |
| L1 | length | clip length within 0.35 s of 2.0 (Scuba, Thrust, Spike, Wave) / 3.0 (BringIt, Pushups); both heroes have equal frame counts and equal key times |
| P1 | in place | Rig object transform and Root bone constant (<=1e-6); frame 0 and the last frame match ReadyIdle frame 0 (mean armature-space bone rotation difference of non-finger bones <= 4 deg, max <= 12 deg); a foot counts as planted while its toe joint is <= 0.04 m above its READY height: its toe joint moves <= 0.02 m horizontally from the READY spot while planted, and at the end each toe joint is within 0.03 m of the READY spot |
| B1 | no new bones | each FBX armature has exactly the 53 bone names and the same parents as the ReadyIdle FBX; the FBX object set equals the ReadyIdle FBX's (rig, body, face, hair (female), Hand_Racket, Racket_Classic, Grip, ButtCap, StringBed) |
| R1 | racket stays on Hand_Racket | in Scuba, Thrust, Wave, BringIt: Racket_Classic world matrix = Hand_Racket world matrix (<=1e-4 m, <=0.01 deg) every frame; Hand_Racket is constant relative to the RightHand bone (<=1e-5) in all clips |
| S1 | Scuba: pinch | the hand whose pad (mean of Index / Middle distal tips) is nearer the nose: <= 0.03 m from the nose tip for >= 1.0 s continuous |
| S2 | Scuba: the other hand waves in front of the face | its wrist within 0.30 m of the nose for >= 80 % of the pinch window, at least 0.0 m in front of the face plane, and its wrist's lateral position crosses its window mean >= 4 times (2 cycles) with peak-to-peak >= 0.04 m |
| S3 | Scuba: knees open and close twice | knee-to-knee distance (LowerLeg heads) has exactly 2 maxima with prominence >= 0.04 m |
| S4 | Scuba: hold, then Ready | after the last knee maximum the pinch stays <= 0.03 m for >= 0.15 s, then P1 end match |
| T1 | Thrust: two big thrusts | Hips head forward position has exactly 2 maxima with prominence >= 0.12 m, peak-to-peak >= 0.15 m (the run's pelvis bob is 0.05 m) |
| T2 | Thrust: size | pelvis pitch swing >= 20 deg; hips p-p exceeds the run's pelvis p-p by >= 2x |
| T3 | Thrust: fists up | for >= 80 % of the thrust window both wrists are >= 0.02 m below-or-above their elbow height, i.e. wrist z >= elbow z - 0.02, within 0.45 m of the shoulder, both fists closed: the free (left) hand's mean proximal finger angle (Index..Little) >= 60 deg above the relaxed hand, the racket (right) hand >= 25 deg above relaxed (it is closed on the racket grip, the engine's own grip pose, which is the most it can close) |
| T4 | Thrust: not a grab | each wrist >= 0.22 m from the Hips head in every frame |
| K1 | Spike: one downward hit | the right wrist descends >= 0.6 m within <= 0.25 s ending no later than the release, from a start with the wrist >= head top - 0.15 m |
| K2 | Spike: aggressive | peak wrist speed >= 6 m/s with a downward component >= 5 m/s; pelvis pitch >= 40 deg at the deepest fold; the left foot stamps (its toe joint rises >= 0.04 m then returns to <= 0.02 m above READY within 0.15 s of the release) |
| K3 | Spike: the racket leaves the hand once and comes back | the distance Racket_Classic - Hand_Racket origins exceeds 0.02 m in exactly one contiguous interval of 0.6 - 1.4 s, and is <= 1 mm for every later frame (>= 0.5 s attached at the end) |
| K4 | Spike: bounces once | the racket's lowest vertex (racket points at the game's 1.3x) touches the court (z <= 0.01 m) in exactly one contiguous event, and its origin then rises >= 0.25 m above the contact height before the return |
| K5 | Spike: hands on hips, then Ready | after the return both wrists are within 0.14 m of their hip landmark (Hips head +-0.19 m lateral, +0.08 m up) for >= 0.3 s continuous; a head shake (Head yaw p-p >= 25 deg, >= 2 reversals) while they are there; then P1 end match |
| W1 | Wave: waves twice, palm forward | the waving hand (wrist above the shoulder >= 0.6 s) has >= 4 crossings of its finger-direction lateral angle with p-p >= 40 deg; palm normal . forward >= 0.5 for >= 80 % of the wave window |
| W2 | Wave: the other hand holds the racket still | in the wave window the right wrist stays within 0.03 m of its mean and the shaft direction changes <= 8 deg |
| C1 | BringIt: a beckon, not a swing | the free hand's palm normal points to the chest centre (dot >= 0.35) for >= 70 % of the beckon window; the mean proximal finger angle of that hand has >= 3 peaks with p-p >= 35 deg; its wrist stays within 0.12 m of its window mean; the racket head never exceeds 2.0 m/s |
| C2 | BringIt: racket points at the other player | in the beckon window the shaft (Hand_Racket local Y) is within 25 deg of forward in azimuth and within +-35 deg of horizontal |
| C3 | BringIt: two steps in place | exactly 2 foot-lift events (toe joint >= 0.03 m above READY), each returning within 0.03 m of its start |
| U1 | Pushups: drop to the floor | both Hand bone heads <= 0.12 m high for >= 0.8 s while the UpperChest <= 0.65 m |
| U2 | Pushups: two pushups | UpperChest z in that window has exactly 2 minima with depth >= 0.15 m; elbow flexion range >= 60 deg in each rep |
| U3 | Pushups: stand, Ready | Hips z >= 0.80 m at the end; P1 end match |
| U4 | Pushups: racket set down and picked up | one leave, one return (distance rule of K3); while off the hand >= 1.2 s, lying with its lowest vertex <= 0.03 m, its origin moving <= 0.02 m; racket points vs body vertices >= 0.01 m apart while it lies |
| F1 | floor | the body mesh never goes below z = -0.03 m, all 12 clips |
| G1 | in-game: plays | for each of the 12 the Unity film trace shows the driver playing that clip (PlayingClip name) for >= 90 % of the frames of its length, never another emote clip, and returns to Ready afterwards; film file work/emotes/film/<Name>_<male|female>.mp4 exists for each of the 12 |
| G2 | in-game racket | in the Unity trace the racket stays on Hand_Racket (<= 1 mm) in the four non-racket clips; Spike and Pushups obey K3 / U4 on the world positions of the game (1.3x racket) |
| G3 | triggers | after a won game (not a point) the winner plays exactly one taunt; a plain point plays none; PlayTaunt(name) plays that taunt; the intro hook plays one intro when the match presentation asks for the intro emote |
| X1 | no footage in the repo | no media file (mp4 mov m4v webm mkv avi mp3 wav m4a aac flac ogg) created since the job baseline outside work/emotes/film; no script in work/emotes/scripts contains a URL or a downloader name (http, yt-dlp, youtube-dl, wget, curl, pytube) |
| X2 | untouched | `scripts/protected.py verify`: Serve, Walk, the three runs (Unity FBX + meta), the golf course scripts / resources, every shader, the locker files are not on this job's write list and not written inside its run windows |

## Corrections made BEFORE the first gate run (nothing has been measured yet; each is a mistake in this file, not a response to a result)
* 2026-10-04 15:21 T3: the right hand holds the racket, so a "60 deg" fist was impossible by construction (the racket grip pose closes the proximal joints about 30 deg on average). The line now asks 60 deg for the free hand and 25 deg for the racket hand.
* Everything else above is exactly as first written. After the first run this file is not edited again; a FAIL is fixed in the clip, never in the definition.
