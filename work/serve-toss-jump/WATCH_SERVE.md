# Watched serve references — event order only

Read and watched on 2026-10-05. These are playback timestamps in slow-motion videos, not physical elapsed seconds. Event frames have uncertainty when the ball is cropped or between frames. No motion was copied from a particular player.

| Reference | View | Release | Trophy / deepest load | Contact | Front-foot landing | Release → trophy | Trophy → contact |
|---|---|---:|---:|---:|---:|---:|---:|
| [Alcaraz — original reference](https://www.youtube.com/watch?v=rxo1uEdLouY&t=178s) | rear oblique | ~179.30–179.45 s (selected release-phase frame 179.446 s) | 179.696 s | ~180.180 s | 180.496 s | ~0.246–0.396 s | ~0.483 s |
| [Federer — SlowMotionTennis](https://www.youtube.com/watch?v=WWC1hcKBh4g) | side | ~4.30 s (4.1–4.4 bracket) | 5.680 s | ~7.373 s (ball above crop; extended-arm contact inferred) | 8.520 s | ~1.380 s | ~1.693 s |
| [Djokovic — Essential Tennis, BNP 2013](https://www.youtube.com/watch?v=I3WKDjMrp64) | back | ~4.68 s (4.4–4.7 bracket) | 10.887 s | ~14.55 s (14.387–14.687 bracket) | 17.720 s | ~6.208 s | ~3.663 s |

In all three observations: both feet support the toss; the toss hand rises above the head; the knees load into the trophy; the racket descends behind the shoulder before acceleration; leg drive precedes airborne extended-arm contact; the front (left) foot lands while the right leg remains behind and above the court. The bottom/load, takeoff, contact, and landing are distinct events. The original installed pre-release jump contradicts this order.

Saved browser captures in `refs/`: each reference has release, trophy, contact and landing JPGs. Alcaraz release is bracketed because the ball has already left the crop in the selected release-phase frame. Federer contact is inferred from the arm/racket position because the ball is cropped; Djokovic contact is bracketed. These uncertainties are not used to relax the task's numeric gates.

The authored clip uses the game's existing stance 0.20, release 0.70, trophy 1.3333 and contact 1.70 seconds. Its timing is independent of these videos' slow-motion playback rate.
