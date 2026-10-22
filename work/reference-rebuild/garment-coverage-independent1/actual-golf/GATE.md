# Actual Golf additional-mask + two-sided original polo review

Scoped coverage improvement accepted by this independent reviewer, pending
root's integration decision. This is not complete clothing-art acceptance.

Compared 60 matched 900x1200 Unity plates from
`proof/reference-rebuild/golf-cloth-control16` and
`proof/reference-rebuild/golf-coverage-two-sided1`: both sexes, Driver / Iron /
PitchingWedge / Wedge / Putter, top / contact / follow, front34 / back34.

Observed:

- Female Driver/Iron/PitchingWedge brown slashes now read as filled shirt.
- No meaningful new backdrop holes, arm detachment, severed cuff/neck or
  broad new shadow artifact was found in these 60 views.
- Same-frame pixel background diagnostic in torso crop x210..710,
  y230..680 finds 56/60 with zero newly exposed backdrop pixels. Four views
  have 1–4 changed backdrop pixels; this is too small to establish a
  meaningful new gap and stays localized at existing boundaries.
- Male shirts retain continuous coverage through all reviewed phases.
- Female Wedge/Putter rear underarm still contains an angular pale fold patch.
  It is filled cloth and already deformed in control16, so the coverage fix
  does not certify that tailoring shape as finished.

The four raw A/B sheets are `male_front34_comparison.jpg`,
`male_back34_comparison.jpg`, `female_front34_comparison.jpg` and
`female_back34_comparison.jpg`. `comparison-index.json` indexes changed
pixels; `actual-background-diagnostic.json` records the backdrop comparison.
These pixel counts support visual review; they are not a substitute for it.

Recommendation: Golf-only original-polo additional Body mask plus two-sided
Top is supported for this bounded coverage repair. Tennis material handling
remains a separate decision. This does not cover unseen intervening frames,
native performance, source topology quality or the full reference-art goal.

No Assets, source garment data or production materials were edited by this
reviewer. Only work evidence and audit tooling were added.
