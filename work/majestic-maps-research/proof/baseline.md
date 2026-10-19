# Baseline per slot (Mac M5, editor, 1920x1080, 4x MSAA)

Counts are single-render (see the docstring of tools/summarize.py for the doubled-read fix).

| slot | tris/frame (M) | draws | SetPass | shadow casters | skinned | particle sys | pixel GPU ms (M5) | sync 1080p ms (M5) | count fix |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| golf_h07_clear | 2.39 | 265 | 97 | 37 | 10 | 4 | 2.56 | 12.56 |  |
| golf_h08_clear | 2.02 | 268 | 87 | 44 | 10 | 0 | 3.36 | 9.25 | /2 vs quiet-run reference |
| golf_h08_fog | 2.02 | 241 | 57 | 44 | 10 | 0 | 6.65 | 13.81 | /2 vs quiet-run reference |
| golf_h08_rain | 2.03 | 289 | 105 | 44 | 10 | 4 | 7.50 | 13.97 | /2 vs quiet-run reference |
| golf_h08_storm | 2.03 | 278 | 94 | 44 | 10 | 4 | 7.37 | 14.98 | /2 vs quiet-run reference |
| golf_h09_clear | 2.46 | 276 | 95 | 40 | 10 | 0 | 3.29 | 10.74 | /2 golf doubled read |
| golf_h10_clear | 1.81 | 246 | 87 | 37 | 10 | 0 | 3.43 | 11.52 | /2 golf doubled read |
| golf_h12_clear | 5.54 | 226 | 111 | 41 | 10 | 0 | 4.27 | 11.58 | /2 vs quiet-run reference |
| golf_h13_clear | 3.28 | 253 | 52 | 66 | 10 | 0 | 3.76 | 13.83 | /2 golf doubled read |
| golf_h13_storm | 3.29 | 263 | 59 | 66 | 10 | 4 | 7.31 | 16.52 | /2 golf doubled read |
| golf_h14_clear | 1.76 | 227 | 90 | 34 | 10 | 0 | 4.48 | 11.51 | /2 golf doubled read |
| golf_h15_clear | 2.26 | 208 | 80 | 31 | 10 | 0 | 3.05 | 13.72 | /2 golf doubled read |
| golf_h16_clear | 2.32 | 263 | 92 | 35 | 10 | 0 | 4.04 | 12.16 | /2 golf doubled read |
| golf_h17_clear | 2.75 | 244 | 92 | 35 | 10 | 0 | 3.75 | 13.24 | /2 golf doubled read |
| golf_h18_clear | 1.41 | 185 | 82 | 34 | 10 | 0 | 3.41 | 10.71 | /2 vs quiet-run reference |
| golf_h19_clear | 2.51 | 270 | 97 | 36 | 10 | 4 | 3.89 | 11.95 | /2 golf doubled read |
| golf_h20_clear | 1.71 | 271 | 103 | 38 | 10 | 4 | 2.45 | 12.80 | /2 golf doubled read |
| golf_h21_clear | 1.73 | 224 | 91 | 29 | 10 | 23 | 3.56 | 12.56 | /2 golf doubled read |
| golf_h21_storm | 1.74 | 236 | 99 | 29 | 10 | 27 | 6.61 | 14.28 | /2 golf doubled read |
| golf_h22_clear | 2.12 | 283 | 115 | 45 | 10 | 23 | 4.28 | 10.13 | /2 golf doubled read |
| golf_h23_clear | 1.75 | 180 | 60 | 25 | 10 | 31 | 3.46 | 12.20 | /2 golf doubled read |
| hub_plaza_clear | 0.97 | 252 | 24 | 134 | 10 | 0 | 2.75 | 7.44 | /2 vs quiet-run reference |
| tennis_resort_clear | 2.53 | 376 | 72 | 85 | 25 | 0 | 2.86 | 12.55 |  |
| tennis_resort_fog | 2.53 | 378 | 75 | 85 | 25 | 0 | 4.29 | 11.55 |  |
| tennis_resort_rain | 2.54 | 392 | 89 | 85 | 25 | 2 | 4.37 | 12.33 |  |
| tennis_resort_storm | 2.54 | 380 | 77 | 85 | 25 | 2 | 4.35 | 10.48 |  |
| tennis_skyscraper_clear | 1.28 | 247 | 44 | 74 | 19 | 0 | 3.80 | 8.14 |  |
| tennis_skyscraper_fog | 1.28 | 249 | 47 | 74 | 19 | 0 | 3.54 | 10.01 |  |
| tennis_skyscraper_rain | 1.28 | 252 | 50 | 74 | 19 | 2 | 3.19 | 10.62 |  |
| tennis_skyscraper_storm | 1.28 | 251 | 49 | 74 | 19 | 2 | 3.72 | 9.83 |  |
| tennis_volcano_clear | 1.34 | 205 | 54 | 57 | 19 | 13 | 3.16 | 9.24 |  |
| tennis_volcano_fog | 1.34 | 217 | 67 | 57 | 19 | 13 | 3.78 | 9.94 |  |
| tennis_volcano_rain | 1.34 | 208 | 58 | 57 | 19 | 15 | 4.12 | 10.13 | /2 vs quiet-run reference |
| tennis_volcano_storm | 1.34 | 220 | 70 | 57 | 19 | 15 | 3.20 | 10.64 |  |

## Groups (medians across slots)

| group | n | tris median (M) | tris max (M) | draws median | pixel GPU median ms | sync 1080p median ms | shadows Δtris (M) | characters Δtris (M) | shadows Δsync ms | characters Δsync ms | MSAA Δpix ms | post Δsync ms | sky-only sync ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| golf clear | 16 | 2.19 | 5.54 | 250 | 3.51 | 12.06 | 0.40 | 0.54 | 1.49 | 1.08 | 0.78 | 1.30 | 3.49 |
| golf weather | 5 | 2.03 | 3.29 | 263 | 7.31 | 14.28 | 0.49 | 0.54 | 1.91 | 2.01 | 1.09 | 0.92 | 2.97 |
| tennis clear | 3 | 1.34 | 2.53 | 247 | 3.16 | 9.24 | 0.42 | 1.06 | 1.60 | 1.63 | 0.81 | -0.90 | 3.39 |
| tennis weather | 9 | 1.34 | 2.54 | 251 | 3.78 | 10.48 | 0.42 | 1.06 | 1.36 | 2.33 | 0.16 | 0.90 | 3.25 |
| hub | 1 | 0.97 | 0.97 | 252 | 2.75 | 7.44 | 0.35 | 0.76 | 2.13 | 1.38 | 0.80 | -0.81 | 2.30 |

## Weather vs clear, same place

| weather slot | Δtris vs clear (M) | Δdraws | Δpixel GPU ms | Δsync ms | particle systems |
|---|---:|---:|---:|---:|---:|
| golf_h08_fog | +0.00 | -27 | +3.29 | +4.56 | 0 |
| golf_h08_rain | +0.01 | +21 | +4.14 | +4.73 | 4 |
| golf_h08_storm | +0.01 | +10 | +4.01 | +5.74 | 4 |
| golf_h13_storm | +0.01 | +10 | +3.56 | +2.69 | 4 |
| golf_h21_storm | +0.01 | +12 | +3.05 | +1.72 | 27 |
| tennis_resort_fog | +0.00 | +2 | +1.42 | -1.00 | 0 |
| tennis_resort_rain | +0.01 | +16 | +1.51 | -0.22 | 2 |
| tennis_resort_storm | +0.01 | +4 | +1.49 | -2.06 | 2 |
| tennis_skyscraper_fog | +0.00 | +2 | -0.26 | +1.87 | 0 |
| tennis_skyscraper_rain | +0.00 | +5 | -0.61 | +2.48 | 2 |
| tennis_skyscraper_storm | +0.01 | +4 | -0.09 | +1.69 | 2 |
| tennis_volcano_fog | +0.00 | +12 | +0.62 | +0.70 | 13 |
| tennis_volcano_rain | +0.01 | +4 | +0.95 | +0.89 | 15 |
| tennis_volcano_storm | +0.01 | +15 | +0.04 | +1.40 | 15 |
