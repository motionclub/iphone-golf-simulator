# Intuitive tennis aim, calibration removed (2026-11-16 evening)

Adnan: "we will just have intuitive aiming, where when someone swings left it goes left and right it goes right and middle it goes
middle ... a spectrum ... timing determines speed of ball and quality of contact, bad timing should result in lobs or easier to hit
balls" and "remove the calibration from the game now".

Why: the swing-path (acceleration) reading failed on the phone: most of his evening swings read as heading away from the TV, so they
had no direction and every ball went straight, and the lesson kept asking for forehand straight.

Now (`work/aim-swing-direction-1115/patch4.py`, applied to the build clone and the main folder):
- **Aim (Swift, `TennisSwingAim` in SteeringFilter.swift, used in SportsMotion):** half where the racket faces as the shot locks + half how
  it turned over the last 100 ms, relative to the TV, against fixed centres (forehand -13 deg, backhand +1 deg). Within 12 deg is the
  middle, then a straight line to the full side at 45 deg. No calibration or saved profile. On his 121 labelled takes this reading
  picked the asked lane in 71 % of forehands and 89 % of backhands. Every swing logs `aim swing reading=.. aim=.. facing=.. face=..`.
- **Unity:** `SideFromSwing` is a spectrum (no 3-lane snap), the hit badge says LEFT/RIGHT past a third; a swing more than `OutTiming`
  (0.17 s) off is a slow high lob into the middle (`MistimedLob`), never out, local and online. Timing still sets pace and depth.
- **Calibration mode removed** from the TV tennis modes row, the phone Play list and the hub route (code for the lesson is left, unused).

Not done: Unity EditMode tests that assert the 3-lane snap / out balls (TennisFunTests, TennisMatchTests, TennisSpatialContact*) and the
iOS tests for the Calibration rows (MenuBetaTests, HubSessionTests, AimCalibrationTests) need updating; the fixed centres come from
one player's (right-handed) takes.
