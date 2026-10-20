# Finger weights candidate held

Paused for user face priority before actual. No Assets, Unity or GPU writes.

Active original female finger mesh has Hand leakage at PIP: index vertex3280 near/beyond PIP carries46.56% Hand; neighboring vertices are100% Intermediate. Source8.05mm edge stretches30.85mm under exact input clip (3.83x). Aliased position weights are consistent. Runtime HeroHandWeights touches thumbs only; head/axilla modifiers do not cause these four-digit wedges.

One staged candidate finger-weights.patch adds HeroGolfFingerWeights and one MatchHeroLook hook. Opt-in VISUAL_GOLF_FINGER_WEIGHTS=1, independent of wrist-roll flag; female golf only. Rest vertices/normals/topology/UVs/morphs/palette/rig/clip TRS exact. Smooth chain field applies beyond45-90% of proximal segment; palm/wrist/thumb remain outside.363 skin vertices change; affected max edge stretch4.42x->2.97x,99percentile3.93x->2.58x across current poses. Some individual affected triangles worsen; actual required. Male probe held due max edge regression4.93x->5.23x despite improved99percentile.

Source repro test-distal-chain.py and distal-chain-source-proof.json. finger-source-analysis.json gives exact bad triangles. tiny-queue.HELD.json pins continuous3 wrist/authored flags and adds only finger-weight flag; compare exact continuous3 baseline at female Driver top/Putter address. Male remains unchanged control. No queue launched, no shipping claim.
