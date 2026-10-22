# Left-handed serve visual gap

Run 28b deliberately leaves left-handed mirroring out of its pass matrix. Existing LH films remain available as unsupported examples; their requested and actual handedness is recorded separately.

`HeroTennisDriver.TossArm` selects LeftUpperArm, LeftLowerArm, LeftHand and left finger bones for every Match hero. `VisualTossPoint` samples the same Serve clip. `TennisServeRoutine.Side` already switches the fallback sign, but Match visual callbacks override those fallback points. `TennisActor.ApplyTossReach` selects the actor model's off-hand and needs its visual-driver contract verified. `TennisGame.ConfigureMatch` configures the opponent from profile handedness, so requesting an LH opponent in this recorder does not make it LH.

A separate implementation should define a handedness-aware visual arm and finger mapping, mirror serve-point sampling, pole direction and racket/contact geometry consistently, and supply or mirror the Serve animation while preserving contact and toss timing. It must cover `HeroTennisDriver.cs`, `TennisActor.cs`, `TennisServeRoutine.cs`, opponent configuration in `TennisGame.cs`, and the serve animation/import ownership held by run 26b. Changes to the skeleton or run 29 garments are unnecessary unless testing demonstrates otherwise.

Risk is moderate to high: mirroring only the hand target leaves the racket, animation and contact geometry inconsistent; opponent configuration also has gameplay effects. Estimate: roughly 200–400 lines plus a 32-case visual/timing matrix, about 2–4 focused implementation days and separate art review. This is a planning estimate, not measured work. Keep it out of the carry penetration correction.
