# Reference images: manifest

Model: Higgsfield `gpt_image_2_5` (GPT Image 2.5, flare), 16:9, 2k. Quality **high** = 2.75 credits; **medium** = 1 credit (Adnan approved the mixed plan, 10-17).
Each ref is an AI repaint of a real game frame (the source) or of chat 9's approved Majestic target. The prompt is listed or referenced below. Files are JPG q90, ≤2560 px wide.

## Weather
| id | file | source frame (reference) | quality | credits | job |
|---|---|---|---|---:|---|
| W12 | weather/W12_tennis_resort_rain.jpg | chat 9 target `concepts/after/tennis_resort_clear.jpg` | high | 2.75 | be90a9c1 |
| W13 | weather/W13_tennis_resort_seafog.jpg | same | high | 2.75 | e8122647 |
| W14 | weather/W14_tennis_skyscraper_thunderstorm.jpg | chat 9 target `tennis_skyscraper_clear.jpg` | high | 2.75 | f7570c46 |
| W15 | weather/W15_tennis_skyscraper_gusty.jpg | same (note: debris drawn on court; the build keeps it off) | high | 2.75 | c9e19db7 |
| W16 | weather/W16_tennis_volcano_smoke.jpg | chat 9 target `tennis_volcano_storm.jpg` | high | 2.75 | d72343eb |
| W02 | (reused) `../majestic-maps-research/concepts/after/golf_h08_storm.jpg` | chat 9 | — | 0 | — |

## Golf holes
Every hole ref is a repaint of the real in-game frame from `audit/views_clear/hNN_<view>.jpg` (MajesticHoleViews, clear, 10-17, Majestic + rendered sky). The camera pose is in `audit/views_clear/hNN_cameras.json`. Prompts follow `design/HOLE_BRIEFS.md`; the full prompt text is in the Higgsfield job (job id below) and summarized in `refs/prompts/`.

| file | source view | quality | credits | job |
|---|---|---|---:|---|
| holes/h07_tee.jpg | h07_tee | high | 2.75 | 11899221 |
| holes/h07_flyOpen.jpg | h07_flyOpen | high | 2.75 | 6cd026f3 |
| holes/h08_tee.jpg | h08_tee | high | 2.75 | a1023f24 |
| holes/h08_flyOpen.jpg | h08_flyOpen | high | 2.75 | 100d20f7 |
| holes/h09_tee.jpg | h09_tee | high | 2.75 | f6105e4b |
| holes/h09_flyOpen.jpg | h09_flyOpen | high | 2.75 | eb72d12c |
| holes/h07_approach.jpg | h07_approach + tee ref | medium | 1 | faa7687b |
| holes/h07_greenBack.jpg | h07_greenBack + tee ref | medium | 1 | 39399c25 |
| holes/h07_offR.jpg | h07_offR + tee ref | medium | 1 | 1caadaa5 |
| holes/h08_mid.jpg | h08_mid + tee ref (approach spot was in the water: harness fixed with InPlay()) | medium | 1 | b5c92d67 |
| holes/h08_greenBack.jpg | h08_greenBack + tee ref | medium | 1 | b541dbcb |
| holes/h08_offL.jpg | h08_offL + tee ref | medium | 1 | 934d54b7 |
| holes/h09_mid.jpg | h09_mid + tee ref | medium | 1 | 1e2ddc1c |
| holes/h09_greenBack.jpg | h09_greenBack + tee ref | medium | 1 | 1fa2518e |
| holes/h09_offL.jpg | h09_offL + tee ref | medium | 1 | 5739ef72 |
| holes/h12_tee.jpg | h12_tee + chat 9 `golf_h12_clear.jpg` (note: dropped the hazard boulder; the build keeps it) | high | 2.75 | 09d2750e |
| holes/h12_flyOpen.jpg | h12_flyOpen + chat 9 h12 | high | 2.75 | 3c702e50 |
| ~~holes/h15_tee.jpg v1~~ | h15_tee + h07 tee ref — **layout drift (island tree wall moved, wind ring lost) → regenerated** | high | 2.75 | b1bd0173 |
| holes/h13_tee.jpg | h13_tee | high | 2.75 | aad94211 |
| holes/h13_flyOpen.jpg | h13_flyOpen | high | 2.75 | 4929d6a5 |
| holes/h14_tee.jpg | h14_tee — canopy narrows the fairway: the build keeps the corridor open | high | 2.75 | 7ef42467 |
| holes/h14_flyOpen.jpg | h14_flyOpen | high | 2.75 | 06e2cea0 |
| holes/h17_tee.jpg | h17_tee | high | 2.75 | d5a49951 |
| holes/h17_flyOpen.jpg | h17_flyOpen | high | 2.75 | 5e90e31a |
| holes/h18_tee.jpg | h18_tee | high | 2.75 | cef4ce00 |
| holes/h18_flyOpen.jpg | h18_flyOpen | high | 2.75 | 75f96c3b |
| holes/h19_tee.jpg | h19_tee | high | 2.75 | b695a21e |
| holes/h19_flyOpen.jpg | h19_flyOpen | high | 2.75 | ec61e5fc |
| holes/h20_tee.jpg | h20_tee | high | 2.75 | 9b44611e |
| holes/h20_flyOpen.jpg | h20_flyOpen | high | 2.75 | 40f3e0e9 |
| holes/h10_tee.jpg | h10_tee | high | 2.75 | 58872303 |
| holes/h10_flyOpen.jpg | h10_flyOpen | high | 2.75 | 12308c99 |
| holes/h16_tee.jpg | h16_tee | high | 2.75 | ae8d4434 |
| holes/h16_flyOpen.jpg | h16_flyOpen | high | 2.75 | cb6c21aa |
| holes/h21_tee.jpg | h21_tee | high | 2.75 | 7b9c19c2 |
| holes/h21_flyOpen.jpg | h21_flyOpen | high | 2.75 | db7194d7 |
| holes/h22_tee.jpg | h22_tee | high | 2.75 | 48811fb4 |
| holes/h22_flyOpen.jpg | h22_flyOpen | high | 2.75 | ba922f72 |
| holes/h23_tee.jpg | h23_tee | high | 2.75 | 13d5c9a5 |
| holes/h23_flyOpen.jpg | h23_flyOpen | high | 2.75 | fa2fd5d7 |
| holes/h15_tee.jpg | h15_tee + h07 tee ref (course anchor) — v2: layout held (v1 rejected) | high | 2.75 | 7105687b |
| holes/h15_flyOpen.jpg | h15_flyOpen + h07 tee ref (course anchor) | high | 2.75 | 6e34f699 |
| holes/h13_approach.jpg | h13_approach + tee ref | medium | 1 | ca291095 |
| holes/h13_greenBack.jpg | h13_greenBack + tee ref | medium | 1 | 26bafd31 |
| holes/h13_offR.jpg | h13_offR + tee ref | medium | 1 | 82f932a1 |
| holes/h14_approach.jpg | h14_approach + tee ref | medium | 1 | e9c262b4 |
| holes/h14_greenBack.jpg | h14_greenBack + tee ref | medium | 1 | dd906a64 |
| holes/h14_offL.jpg | h14_offL + tee ref | medium | 1 | 7ce84482 |
| holes/h17_approach.jpg | h17_approach + tee ref | medium | 1 | 9087b3d7 |
| holes/h17_greenBack.jpg | h17_greenBack + tee ref | medium | 1 | 8dcc95e9 |
| holes/h17_offL.jpg | h17_offL + tee ref | medium | 1 | ed82241d |
| holes/h18_greenBack.jpg | h18_greenBack + tee ref — par 3: approach spot was in water | medium | 1 | e981cbc7 |
| holes/h18_offL.jpg | h18_offL + tee ref | medium | 1 | 68288292 |
| holes/h18_offR.jpg | h18_offR + tee ref | medium | 1 | 06ca4cfd |
| holes/h19_approach.jpg | h19_approach + tee ref | medium | 1 | d22948d2 |
| holes/h19_greenBack.jpg | h19_greenBack + tee ref | medium | 1 | fa1f8e8b |
| holes/h19_offR.jpg | h19_offR + tee ref | medium | 1 | f3e87dff |
| holes/h20_approach.jpg | h20_approach + tee ref | medium | 1 | 05350b44 |
| holes/h20_greenBack.jpg | h20_greenBack + tee ref | medium | 1 | cc12fd0e |
| holes/h20_offR.jpg | h20_offR + tee ref | medium | 1 | cfb746b1 |
| holes/h10_mid.jpg | h10_mid + tee ref | medium | 1 | dab39e16 |
| holes/h10_greenBack.jpg | h10_greenBack + tee ref | medium | 1 | c0899d87 |
| holes/h10_offL.jpg | h10_offL + tee ref | medium | 1 | a7774722 |
| holes/h16_approach.jpg | h16_approach + tee ref — used because h16_mid camera sits inside a basalt gate (AUDIT) | medium | 1 | d842661f |
| holes/h16_greenBack.jpg | h16_greenBack + tee ref | medium | 1 | 956e90bd |
| holes/h16_offL.jpg | h16_offL + tee ref | medium | 1 | aef915ab |
| holes/h21_greenBack.jpg | h21_greenBack + tee ref | medium | 1 | a8128414 |
| holes/h21_offL.jpg | h21_offL + tee ref | medium | 1 | 902bfb40 |
| holes/h21_offR.jpg | h21_offR + tee ref | medium | 1 | ce9fa122 |
| holes/h22_mid.jpg | h22_mid + tee ref | medium | 1 | c9ce80da |
| holes/h22_greenBack.jpg | h22_greenBack + tee ref | medium | 1 | eec66122 |
| holes/h22_offL.jpg | h22_offL + tee ref | medium | 1 | 6ee66331 |
| holes/h23_mid.jpg | h23_mid + tee ref | medium | 1 | c8aaa49f |
| holes/h23_greenBack.jpg | h23_greenBack + tee ref | medium | 1 | 5e5df41e |
| holes/h23_offL.jpg | h23_offL + tee ref | medium | 1 | 193872b3 |
| holes/h12_greenBack.jpg | h12_greenBack + tee ref | medium | 1 | 22af7ffe |
| holes/h12_offL.jpg | h12_offL + tee ref | medium | 1 | 73e75907 |
| holes/h12_offR.jpg | h12_offR + tee ref | medium | 1 | e2cca48b |
| holes/h15_approach.jpg | h15_approach + tee ref | medium | 1 | ee5690d4 |
| holes/h15_greenBack.jpg | h15_greenBack + tee ref | medium | 1 | 5378c708 |
| holes/h15_offL.jpg | h15_offL + tee ref | medium | 1 | 5415fa0f |

## Golf weather
| id | file | source | quality | credits | job |
|---|---|---|---|---:|---|
| W01 | weather/W01_golf_h07_rain.jpg | h07_tee + h07 tee ref | high | 2.75 | 052974a7 |
| W03 | weather/W03_golf_h13_thunderstorm.jpg | h13_tee + h13 tee ref | high | 2.75 | 456b7dbe |
| W04 | weather/W04_golf_h15_seafog.jpg | h15_tee + h15 tee ref | high | 2.75 | 313609d4 |
| W05 | weather/W05_golf_h20_gusty.jpg | h20_tee + h20 tee ref | high | 2.75 | fbcea3ea |
| W06 | weather/W06_golf_h17_snow.jpg | h17_tee + h17 tee ref | high | 2.75 | b44180f3 |
| W07 | weather/W07_golf_h17_blizzard.jpg | h17_tee + h17 tee ref | high | 2.75 | 27bd7a46 |
| W08 | weather/W08_golf_h17_freezingfog.jpg | h17_tee + h17 tee ref | high | 2.75 | aeb90657 |
| W09 | weather/W09_golf_h22_ashfall.jpg | h22_tee + h22 tee ref | high | 2.75 | 8969a75f |
| W10 | weather/W10_golf_h23_eruption.jpg | h23_tee + h23 tee ref | high | 2.75 | c2f412d0 |
| W11 | weather/W11_golf_h21_smoke.jpg | h21_tee + h21 tee ref | high | 2.75 | 02651b94 |
| W02 | weather/W02_golf_h08_rain_clearing_chat9.jpg | copy of chat 9 `concepts/after/golf_h08_storm.jpg` | — | 0 | — |

## Totals
- **Images:** 96 generated.
  - Golf holes: 80 kept = 32 high (tee + flyover × 16 holes) + 48 medium (3 more views × 16). Plus 1 rejected high (h15 tee v1).
  - Weather: 15 high (5 tennis + 10 golf). W02 reuses chat 9's image.
- **Credits:** 180.0 spent (balance 282.4 → 102.4); estimate approved by Adnan: ~180.
- **Higgsfield source uploads:** media ids are in `media_ids.tsv` (they expire after Higgsfield's retention; re-upload from `audit/views_clear/`).
