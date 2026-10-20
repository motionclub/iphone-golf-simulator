# Resort architectural relief1 actual gate

GATE: Root installation, Unity compile and shader PASS. Three matched views exist and were visually compared with TENNIS_RESORT_RELIEF_OFF=1 controls: reference16, clubhouse17 and terrace12.

GATE: Bounded bright-architecture clipping correction PASS. Terrace paving is now warm cream rather than clipped white/red; its measured patch has66.55% clipped pixels in control and0% in candidate. White clubhouse trim72.18%→0%, canvas36.99%→0.37%. The warm hue survives and gradients remain below the display ceiling.

GATE: Effect isolation PASS. Court patch is exactly pixel-identical. The water sample differs by less than0.042/255 per channel, consistent with animated-wave timing, with no material change. No geometry/light/post/renderer/AO change occurred.

GATE: Broad architectural relief/reference quality PARTIAL. Shaded facade and foundation patches remain pixel-identical. Correction: active URP17.3 mode1 is PerPixel (PerVertex=2), so the proposed vertex-fill scaling never affected the production lighting path. Root removed that unused scaling/comment and retained the accepted shoulder only. The observable gain is localized highlight rolloff. Flat facade forms and coarse vegetation remain far from the premium target.

No further tennis source changes. Iterations stopped at root instruction; current installed hashes are preserved in manifest.json.
