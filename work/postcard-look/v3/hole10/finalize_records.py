"""Summarize frozen P4 evidence; never edits sources or binaries."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[3]
V=json.loads((H/'verify_required.json').read_text());S=json.loads((H/'stage_gates.json').read_text());B=json.loads((H/'stage/build_gates.json').read_text());I=json.loads((H/'stage/build_inventory.json').read_text());M=json.loads((H/'geometry_metrics.json').read_text());E=json.loads((H.parent/'audit/scoring_exact_p4.json').read_text())
def count(g):return f"{sum(x['ok'] for x in g)}/{len(g)}"
def clean(s):return str(s).replace('|','/').replace('\n',' ')
def rows(g):return '\n'.join(f"| {x['name']} | {'PASS' if x['ok'] else 'FAIL'} | {clean(x['detail'])} |" for x in g)
sha=(H/'capture_sha256.txt').read_text().strip()
summary='''GATE P4 FAIL. The production source and stage are frozen until Phase 7. Geometry checks and exact scoring pass; shared basalt texture/window checks and tee smoke fail. Required fresh Unity stills/aerial, BASALT_JOINTS, native lava/smoke and actual render costs remain unmeasured FAIL until the parent captures them. Missing evidence is not a PASS.\n'''
g='# Hole10 Phase4 full binary gate table\n\n'+summary+f"\nBuilder {count(B)}; required verifier {count(V['gates'])}; original stage gates {count(S)}. Every predicate and threshold is retained.\n\n| Gate | Result | Evidence |\n|---|---|---|\n"
g+=rows(B)+'\n'+rows(V['gates'])+'\n'+rows(S)+'\n'
g+='| SCORING_EXACT | PASS | All4 installed/staged blend/FBX comparisons against their matching baselines; max vertex/marker delta exactly0m, no rounding or epsilon. |\n'
g+=f"| WORLD_COLUMNS_WIDTH | {'PASS' if M['width_gate_pass'] else 'FAIL'} | {M['actual_shafts']} whole shafts in {M['objects']} actual compact bodies; across-corner world diameter {M['world_width_min']:.9f}..{M['world_width_max']:.9f}m against0.6..1.8m. |\n"
g+=f"| BODY_FACE_SPAN_SHAPE | {'PASS' if M['faces_gate_pass'] and M['span_gate_pass'] and M['shape_gate_pass'] else 'FAIL'} | Max{M['faces_max']} faces, horizontal AABB diagonal{M['horizontal_span_max']:.9f}m; all{M['objects']} original rock_shape checks pass. Min measured PCA r3{min(r['shape'].get('r3',1) for r in M['objects_measured']):.9f}. |\n"
g+='| EXTRA_STRICT_SUPPORT_CONTAINMENT | FAIL | Scratch three-band support diagnostic found a few micrometres of world-float corner-point containment error; retained prototypes/support/measurements.json. All30 interfaces have exact0m specified vertical gap and98.5634..99.5476% actual bearing. No containment threshold softened. |\n'
for n in ('FRESH_AERIAL_SIDE_BY_SIDE','GAME_BASALT_JOINTS','GAME_LAVA_ORANGE','GAME_SMOKE_SOFT','GAME_SMOKE_VISIBLE','TEE_DRAW_CALLS','NATIVE_INSTANCING','ACTUAL_REFERENCE_RECOGNITION'):
 g+=f'| {n} | FAIL | Required actual native measurement pending; source geometry is not a substitute. |\n'
(H/'GATES_hole10.md').write_text(g)
result='# Phase4 Crater result — frozen candidate\n\n'+summary+f'''
Final build: {I['stats']['tris']} triangles, {I['stats']['meshes']} meshes, {I['stats']['objects']} objects. Original total cap250000, leaving1686 triangles. Near wall148 full-height tiles covers100% of360deg, tops13.4..25.5m; far255 real tiles/bands covers100%, tops16.7..69.2m. The72-bin skyline has p10~20.2/p90~69.2m, amplitude48.9m>=40, mean adjacent step8.11m>=4. Seven real high ridge sectors receive supported upper geological bands rather than a full-height thin scaled ring.

There are{M['actual_shafts']} whole connected5/6-sided shafts in the403 wall tiles,11 lava stacks and1 tee body. World widths{M['world_width_min']:.9f}..{M['world_width_max']:.9f}m, max380polygons/body and18.429022m actual horizontal span. All inherited rock classifiers pass, minimum PCA r3{min(r['shape'].get('r3',1) for r in M['objects_measured']):.9f}. The skins are genuinely open terrain-backed column cladding,131pieces with the original pillar undercut. CRATER_WALL_COVERED measures2/4944 rays exposed, largest patch1m²; pillar648m² sides100%basalt reachingz=-6,678m² basalt underside, pin hits originalGREEN at play height.

The tee is a real closed body of34 perimeter columns plus12 buried interior supports,576vertices/380polygons/968triangles. FrozenTEE_BOX grass remains exact. Top caps are11.5mm over the grass, inside its hull by0.147m and1.669m clear of markers;74%of622 down-ray samples emerge>=3mm. Physical placement passes; its actual cap glow2.537%>0.5% makes original stage H_TEE_RIM FAIL. Actual cap luminance0.163<=0.17. build_inventory.json's legacy win_lum_mean0.1473 is the global Basalt_C decoded mean, not the independently sampled cap mean; use stage_gates.json for the cap measurement. A visible raised-platform reference likeness is not inferred from its buried stone depth.

FIRSTCUT now usesLK_ROUGH with its4m actual tile;14UV slivers in9clusters were re-authored without changing geometry, resulting in0m² own-surface badUV area. GREEN_APRON retainsLK_FAIRWAY. Plants retain565objects/7shared meshes and100%mesh sharing, original pivots/colors/height/lean. Fringe525tufts/123clumps/19singles,30987triangles, original FR_BUDGET45000 unchanged. Crust714actual whole plates in23chunks retains all clearance/500plate/20chunk predicates.

The volcano is static with5lava flows,15%LK_LAVA area and a connected molten body spanning>=60%height. Exactly3soft smoke groups/9cards remain. Decoded SMOKE_SOFT passes, but geometric proof tee0.82%<1.5% fails; approach1.66% and lava-rim2.84% pass. After two measured placement failures, this idea is stopped and the honest remaining tee failure retained. Native coverage/shape/color are pending.

Final required verifier {count(V['gates'])}: missing LOOK_STILLS_TEXTURED and SMOKE_VISIBLE_STILLS; BASALT_PRISMS both formats; SMOKE_IN_FRAME both formats. Original stage gates {count(S)}: H_GLOW_JOINTS and cap-glow H_TEE_RIM fail both formats. Builder {count(B)}: H_UV_WINDOWS fails because actual decoded pixels, not intended window labels, drive counters. Known texture defects remain for authorizedPhase7; no PNG/library/design/checker/gate-predicate edits occurred.

The exact scoring audit is PASS at0.000m across all4 comparisons. Blend checks every ordered local/world vertex and polygon list; FBX compares exact canonical spatial triangles/unique positions permitting only UV splits/reordering. Names/types/marker matrices are exact.

Final binary hashes:

```
{sha}
```

All complete gates are inGATES_hole10.md and rawJSON/logs. Native capture is ready through the parent; no Unity or installed asset was edited by this agent. Source/stage are frozen untilPhase7.
'''
(H/'P4_RESULT.md').write_text(result)
install='# Crater staged Phase4 candidate — INSTALL\n\n'+summary+f'''
Only hole10_build.py and hole10_look.py were changed; hole10_design.py is frozen. Input provenance is lib_sha_final.txt and look_png_sha_final.txt. Stage binaries/capture are exact lines in stage_sha256.txt and capture_sha256.txt; every entry points to a real file belowv3/hole10/stage. The generated staging.meta must never replace installedUnity hole_10.fbx.meta.

```
{sha}
```

Installation is owned by the parent Phase6 through the authorized installer/proof flow and guards7/7. Use lib_sha_final.txt for the installer input list, install only blend/FBX and preserve installed.meta bytes. This agent performed no install/Unity write. Exact scoring0m alreadypasses; rerun required original verifier and native proofs after any authorized later texture repair or install.

Budget248314triangles/1191meshes/1200objects; builder{count(B)}, required verifier{count(V['gates'])}, original stage gates{count(S)}. Geometry/PCA/shaft widths/spans/ring/skyline/pillar/sightlines/UVrepair/plantcounts pass. Basalt masks/windows, tee smoke and fresh native evidence fail. All failure logs/attempts are retained, not selected away.

Unverified checkpoints are never install candidates. Actual appearance,>=15%sea-or-lava,64px landmark, mowing/instancing/GPUcost and<=250drawCalls await native proof. Horizontal lava plane atz0 alone can cover at most~2.2615%of frozen tee view; this is not a ceiling on elevated genuine volcano lava streams, which may also count asLK_LAVA in the actual mask. No fakewater/lava sheet or gameplay camera edits were used.

The full measurement/limitations are P4_RESULT.md, GATES_hole10.md, geometry_metrics.json, stage_gates.json, verify_required.json, and ../audit/scoring_exact_p4.json. Fresh aerial+reference comparison and ranked re-score will be appended after the parent's actual capture, without source/binary mutation.
'''
(H/'INSTALL.md').write_text(install)
(H/'ATTEMPTS.md').write_text('''# P4 attempts\n\n1. Prototype thin closed rows: all18PCA FAIL and16/18regular-solid FAIL. Compact reconstruction changed actual geology; no renaming exemption. Heavy four-cut prototypecost was rejected for full-ringbudget, lighter one-cut real5/6-sided shafts passed unchanged checks.\n2. Tee perimeter prototype FAIL radiusCV0.1016<0.15. Real12buried interior supports changed physical structure; filledbody radiusCV0.197851/PCA0.868673 PASS.\n3. Fullintegrationattempt1 stopped before export on unused D.look_objects wrapper AttributeError; log retained, wrapper corrected.\n4. First complete attempt2:255038triangles FAIL; smoke tee1.15%,approach1.66%,lava-rim0% FAIL overall. All original geometry classifiers passed and exact scoring0m. Complete binaries/source/checks archived underattempt2/.\n5. Finalattempt3:248314triangles PASS after actual far-field crust930→714plates and fringe558→525tufts. All mandatory minima retained. Smoke tee0.82% FAIL,approach1.66%/rim2.84% PASS. After two measured smoke failures, stopped before a third placement attempt; no softened threshold. Current source/stage frozen.\n6. Extra strict stacked-cap vertex containment remainsFAIL for micrometre world-float corners. Physical bearing98.5634..99.5476%,specified interfaces0gap; every inherited shape/support check passes. Both facts retained.\n\nAll immutablePNG texture FAILs remain. Native required evidence is pendingFAIL; no estimated performancePASS.\n''')
old=json.loads((H.parent/'ranked_differences.json').read_text())['10']
notes=[
'Replaced scaled giant wall segments with403 complete compact5/6-sided tiles, actual widths<=1.779925m and every shape/PCA passes. Fresh native no-plank/reference judgement remains unmeasured.',
'Current Basalt_E malformed component area46.670589%>10%; H_GLOW_JOINTS cap2.70%>.5%,side3.94%>2.94%,lit-side93%>50%. Shared topology repair waitsPhase7.',
'P1library mowing fixture passed but does not certify fullCrater. FIRSTCUT darkerLK_ROUGH; actualCrater frame bands unmeasured.',
'Original pillar top staysfrozen; new narrow open column cladding preserves realbottom/support. CRATER_PILLAR PASS; apparentdepth at frozenframe unmeasured.',
'Near/far real height/ridge/shaft width architecture passes all oldgates; cutcorner silhouette+naturalbroken-rim recognition await native.',
'Kept real135mvolcano/5flows and genuine lowproofwindow; no cameraedit. Peakframing/referenceaerial unmeasured.',
'Real46columnstonebody geometry passes; capglowFAIL and bodymostlyburiedbyfrozengrass/terrain. Raisedstonevisibility unmeasured, no visualPASS inferred.',
'Staticlava/5lights/sourcecolor unchanged; texture patterns/nativeLAVA_ORANGE mustbe measured.',
'Three groups/9softcards; decodedSMOKE_SOFT PASS but geometrictee .82%<1.5%. Actualaerialsilhouettes/readability unmeasured.',
'Frozen scoringbunkerellipse unchanged. Existingsoft lips retained; new marginstyle/referencefit unmeasured, no falsehazard patches.'
]
rank=[dict(rank=i+1,difference=d[0],phase=d[1],result='FAIL',reason=notes[i],basis='Initial frozen-source geometry plus original gates; required fresh native re-score pending') for i,d in enumerate(old)]
json.dump(rank,open(H/'ranked_rescore.json','w'),indent=2)
(H/'ranked_rescore.md').write_text('# Crater initial P0-difference re-score\n\nEvery visual item remains binaryFAIL until fresh native evidence resolves it. Geometric fixes are recorded separately; no numerical visual score is invented.\n\n'+ '\n'.join(f"{r['rank']}. FAIL — {r['difference']} {r['reason']}" for r in rank)+'\n')
print('P4_RECORDS_WRITTEN source/stage unchanged')
