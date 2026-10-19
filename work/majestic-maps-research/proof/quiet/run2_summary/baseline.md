# Baseline per slot (Mac M5, editor, 1920x1080, 4x MSAA)

Counts are single-render (see the docstring of tools/summarize.py for the doubled-read fix).

| slot | tris/frame (M) | draws | SetPass | shadow casters | skinned | particle sys | pixel GPU ms (M5) | sync 1080p ms (M5) | count fix |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| golf_h08_clear | 2.02 | 268 | 86 | 44 | 10 | 4 | 2.42 | 12.08 |  |
| golf_h08_storm | 2.03 | 299 | 114 | 44 | 10 | 4 | 7.39 | 12.25 |  |
| golf_h12_clear | 5.53 | 221 | 106 | 40 | 10 | 0 | 3.07 | 11.78 |  |
| golf_h18_clear | 1.41 | 185 | 80 | 34 | 10 | 0 | 1.64 | 11.64 |  |
| hub_plaza_clear | 0.97 | 252 | 24 | 134 | 10 | 0 | 2.36 | 5.87 |  |
| tennis_resort_clear | 2.53 | 374 | 34 | 85 | 25 | 0 | 3.04 | 11.16 |  |
| tennis_resort_storm | 2.54 | 390 | 51 | 85 | 25 | 2 | 4.08 | 11.37 |  |
| tennis_skyscraper_clear | 1.28 | 245 | 33 | 74 | 19 | 0 | 2.92 | 10.04 |  |
| tennis_skyscraper_storm | 1.28 | 250 | 39 | 74 | 19 | 2 | 3.98 | 9.72 |  |
| tennis_volcano_clear | 1.34 | 203 | 39 | 57 | 19 | 13 | 2.78 | 12.66 |  |
| tennis_volcano_storm | 1.34 | 208 | 45 | 57 | 19 | 15 | 4.60 | 8.60 |  |

## Groups (medians across slots)

| group | n | tris median (M) | tris max (M) | draws median | pixel GPU median ms | sync 1080p median ms | shadows Δtris (M) | characters Δtris (M) | shadows Δsync ms | characters Δsync ms | MSAA Δpix ms | post Δsync ms | sky-only sync ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| golf clear | 3 | 2.02 | 5.53 | 221 | 2.42 | 11.78 | 0.49 | 0.54 | 3.14 | 1.55 | -0.10 | 1.87 | 3.05 |
| golf weather | 1 | 2.03 | 2.03 | 299 | 7.39 | 12.25 | 0.49 | 0.54 | 0.71 | 0.02 | 1.77 | -0.05 | 2.61 |
| tennis clear | 3 | 1.34 | 2.53 | 245 | 2.92 | 11.16 | 0.42 | 1.06 | 2.37 | 2.84 | -0.43 | 1.78 | 3.51 |
| tennis weather | 3 | 1.34 | 2.54 | 250 | 4.08 | 9.72 | 0.42 | 1.06 | 0.55 | 1.82 | 0.28 | 0.33 | 3.08 |
| hub | 1 | 0.97 | 0.97 | 252 | 2.36 | 5.87 | 0.35 | 0.76 | 0.04 | 1.36 | 0.97 | -0.59 | 2.05 |

## Weather vs clear, same place

| weather slot | Δtris vs clear (M) | Δdraws | Δpixel GPU ms | Δsync ms | particle systems |
|---|---:|---:|---:|---:|---:|
| golf_h08_storm | +0.01 | +31 | +4.97 | +0.17 | 4 |
| tennis_resort_storm | +0.01 | +16 | +1.05 | +0.21 | 2 |
| tennis_skyscraper_storm | +0.01 | +5 | +1.06 | -0.32 | 2 |
| tennis_volcano_storm | +0.01 | +5 | +1.82 | -4.06 | 15 |
