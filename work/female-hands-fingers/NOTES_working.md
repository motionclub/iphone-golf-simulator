# working notes (female hands + fingers) — 2026-10-02
- Start blend SHA 573ab443… verified. ArtDir HeroBase_Female.blend = 200dc3b9… (untouched).
- Body_F 22,419 verts, 6,996 tris + 18,883 quads (= 44,762 tris); Hair_F 4,960 tris. All faces smooth, no sharp edges, custom normals INT16_2D, UV flat patch for hands (0.93,0.10), mat Base_Grey_F (idx 0).
- Current hand shells: +x 654 verts / 1332 tris, ring 18 verts (z .8449–.8456, centre (.2320,.0003,.8455), semi a .0286 b .0283);
  -x 672 verts / 1368 tris, ring 18 verts planar z .87258, centre (-.2255,.0003,.8726), semi .0300/.0299.  Side +1 = +x = ANATOMICAL LEFT (limbs chat calls it "R").
- Plate registrations: bald front x_px=440+x/S, back x_px=847-x/S, row=679-z/S, S=0.0025954198; multi sheet S2=1.7039/288.5, left-profile y0 anchor px 791.5, z0 row 338.5.
- Plate profile (left panel, +x hand seen from outside = DORSUM): 4 finger strips spread y≈-6.0..+0.1 cm, vertical; hand band y∈[-6.0,+0.5] at z .80; palm bottom z≈.765; tips z≈.70-.72 (lowest .692). => palm faces MEDIALLY (psi≈0-20, not 55), hand ~2.8 cm forward of our ring.
- Limbs SDF hand: palm rotated psi=55° about vertical, fingers straight capsules (flex 8/20/22), thumb capsule stack.
