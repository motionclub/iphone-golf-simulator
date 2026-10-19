# Quiet-machine run 1 (2026-10-17 09:30, load ~4), recovered from the session log
The machine rebooted before the JSON files were copied out of /tmp; these lines are the harness's own log output.
Sky-only = 18 draws and empty = 6 draws here (single render), vs 36/12 in the loaded sweep (double-counted).

golf_h08_clear: pixelGPU1080=1.25ms sync q/1/2=3.94/9.38/13.13 tris=2015793 draws=279 setpass=97 casters=44
  variants (tris/draws/casters): noShadows 1.52M/235/0, noPost 2.02M/268/44, noMSAA 2.02M/279/44, noHeroes 1.47M/217/28, skyOnly 0/18, empty 0/6
  pixel/sync1x: noShadows 2.28/5.39, noPost 2.31/5.49, noMSAA 1.70/4.11, noHeroes 2.49/5.51, skyOnly 0.93/1.57, empty 1.21/1.60
golf_h12_clear: pixelGPU1080=2.10ms sync q/1/2=5.07/9.91/16.20 tris=5536339 draws=229 setpass=112 casters=41
  variants: noShadows 3.66M/188/0, noPost 5.54M/218/41, noMSAA 5.54M/229/41, noHeroes 4.99M/167/25, skyOnly 0/18, empty 0/6
  pixel/sync1x: noShadows 2.40/5.84, noPost 2.42/6.50, noMSAA 1.81/5.06, noHeroes 2.47/6.21, skyOnly 0.88/1.54, empty 1.12/1.49
golf_h18_clear: tris=1.41M draws=196 casters=34 | noShadows 1.06M/162, noHeroes 0.87M/140, skyOnly 0/18, empty 0/6
