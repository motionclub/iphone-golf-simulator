# Follow-ups (not in this pass)
1. Golf belt tears in swings (contact back-right hip, finish buckle chunk, backswing top). Pre-existing. Rebinding the belt to the trousers'
   weights + trousers' correctives (MaleRepairPolo MR_BELT=1) made the top pose worse -> needs the garment pipeline (belt fitted with the trousers).
2. Tennis polo hem balloons/bunches at the back in forehand + serve (no tear, shape only).
3. Shoes still moon-boot + thick socks (audit C1/C2): needs the hidden-foot collapse + shoe4 rebuild.
4. Face: full jaw-corner sculpt (audit F5) and ear shading (F8) — this pass only relaxed the neck side.
5. Lobby/menu (chat G): re-export male heroes with sync_heroes.sh (face mesh changed: neck relax + sclera inset; golf polo mesh; golf hide list)
   and port the male knit switch (_FemaleSurface 1 on male cloth) into MatchHeroSurfaces.swift.
6. Run EditMode tests once all chats are combined.
