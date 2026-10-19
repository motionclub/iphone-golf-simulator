# Make the Party Sports heroes feel alive

Our heroes look fine, but they feel fake and lifeless, and their clothes look painted on. Nintendo characters (Switch Sports, Mario, Splatoon) are very simple, yet they feel alive and full of soul. We are NOT copying their look. We are copying the principles that make them feel alive, and applying them to our existing heroes.

Keep the existing body, rig, proportions, face identity, outfits and camera. Garments stay socket items. Stage only: no commits, pushes, stashes or checkouts.

## Scope: quick pass, FEMALE HERO ONLY

This is a quick pass on the female hero only, in tennis and golf. Don't touch the male hero. If this works, we repeat it for the male later.

**Step 1: quick audit (short).** Record short muted clips of the female hero in a tennis rally, on a golf hole, in idle and in a few emotes. Write a short `ArtDir/style/alive/AUDIT.md` that scores her against the 10 principles below (alive / weak / missing) with timestamps, and pick the 3–4 changes that will add the most life fastest.

**Step 2: do those changes** on the female hero only. Keep it small and cheap.

## What makes a character feel alive (copy these)

1. **Never fully still.** Breathing in the chest and shoulders, small weight shifts, a little sway, fidgets every few seconds. A frozen pose looks dead.
2. **Eyes are the soul.** Blinking at natural, irregular times. Eyes and head look at what matters: the ball, the opponent, the hole, the camera after a big moment. Eyes move first, then the head, then the body.
3. **Faces react to everything.** Simple expressions such as focused, happy, shocked, annoyed and proud. Brows and mouth change for every hit, miss, point and putt. Keep it simple and readable from the gameplay camera.
4. **Overlap and follow-through.** Body parts don't all stop together. The head, hands, hair, cap brim, shirt tails, skirt and sleeves lag and settle a beat after the body. This is the biggest reason Nintendo characters feel soft and alive.
5. **Anticipation and settle.** A small wind-up before every action and a small overshoot after it, then a settle back into idle. Nothing snaps; everything blends.
6. **Personality in timing.** Give her her own rhythm, posture and attitude in idle, walk, celebrations and reactions.
7. **Reactions fit the moment.** A quick, honest reaction to every outcome (good shot, bad shot, won point, lost point, holed putt, miss) before the game moves on. Short, but never skipped.

## Clothes that look real, not painted on

8. **Fabric moves.** Hems, sleeves, skirt and shirt tails swing, lag and settle with motion (simple bone or spring jiggle, cheap on mobile). They should never move rigidly as if glued to the skin.
9. **Clothes have thickness.** A visible edge and gap at hems, cuffs, collars and armholes. Garments sit slightly off the body, never flush on it.
10. **Soft fabric shading.** Gentle fold and crease shading, soft ambient occlusion where cloth meets skin and under collars and hems, and a slightly different light response from skin (cloth soft and matte, skin warmer). No clipping through the body in normal play.

## Light check (keep it simple)

- Record short muted before/after clips of the female hero: tennis rally, golf hole, idle and emotes.
- Save before/after side-by-side sheets and clips in `ArtDir/style/alive/after/`.
- The idle never fully freezes. Blinks happen. Eyes and head track the ball. Hems and sleeves visibly lag. No new clipping.
- Keep 60 fps on the phone.

Stop and show Adnan if the hero's identity or silhouette starts to drift.
