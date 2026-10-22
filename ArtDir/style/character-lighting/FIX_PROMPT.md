Stage only, no commit. Tonight's hero-lighting look-dev made heroes brighter but flat and greyer. Keep the brightness, restore shape:
1. _HeroPresentationFill 0.95 -> 0.35, aimed ~35 deg off camera axis (view*.80 + up*.60 - right*.30). Key:fill about 3:1 like the lobby.
2. Shadow floor max(shadow,.4) -> .15. Add a small face-only lift (<=0.2) for the cap brim.
3. Ambient clamp min .25 -> .12, saturation cap .35 -> .60.
4. Skin roll-off (.35,.75) -> (.60,.95).
5. Rim scaled by key direction again (saturate(dot(n,L)*.7+.3)), capped .35. On bright backgrounds let the hero read darker than the background.
Test: re-run CharLightCaptureTests on the same shots into character-lighting/after2/, build before|after|after2|ref sheets. Pass: hero saturation >=0.62, gameplay detail >=6.8, darkest 5% L 3-12, face L 45-65, silhouette >=15 in at least 110/168 gameplay shots, environment unchanged. Adnan's eye decides.
