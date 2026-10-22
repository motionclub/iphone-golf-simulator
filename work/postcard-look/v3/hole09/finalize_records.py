"""Write a binary, evidence-linked P3 handoff after unchanged checks finish."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[4]
HERE=pathlib.Path(__file__).resolve().parent
def read(name):return json.loads((HERE/name).read_text())
def count(gates):return f"{sum(bool(x['ok']) for x in gates)}/{len(gates)}"
def table(gates):
    rows=['| Gate | Result | Measured detail |','|---|---|---|']
    for g in gates:
        name=g.get('name',g.get('id'))
        rows.append('| '+name+' | '+('PASS' if g['ok'] else 'FAIL')+' | '+str(g['detail']).replace('|','/').replace('\n',' ')+' |')
    return '\n'.join(rows)
b=read('stage/phase3_build.json');v=read('verify_required.json');q=read('hole_qa.json')
sc=read('scenery_metrics.json');pb=read('pieces_blend.json');pf=read('pieces_fbx.json')
rb=read('ruin_blend.json');rf=read('ruin_fbx.json');uv=read('uv_repair.json')
exact=json.loads((HERE.parent/'audit/scoring_exact_p3.json').read_text())
results=read('check_stage_results.json')
if len(results)!=8 or any(x['error'] for x in results):raise RuntimeError('Incomplete final check batch')
sha=(HERE/'stage_sha256.txt').read_text().strip()
gates='''# Hole 9 final staged gates — Phase 3

Overall P3: **FAIL**. The frozen scoring terrain has one connected C-shaped boundary, so the literal two-independent-island requirement is FAIL. Fresh actual H9 tee/approach/aerial and the vs-reference sheet exist and were viewed. The >=80% cliff/surf renderer-mask measurement is pending and remains FAIL until measured. Original thresholds and gate predicates are unchanged. The parent will append actual native results.

'''
gates+=f"Builder: {count(b['gates'])} PASS. Required staged blend+FBX verifier: {count(v['gates'])} PASS, failures {v['failures']}. Original hole QA: {count(q['gates'])} PASS. Exact scoring audit: {'PASS' if exact['pass'] else 'FAIL'}, maximum vertex/marker delta 0.000 m only if every exact comparison passes.\n\n"
gates+='## Original final verifier, every gate\n\n'+table(v['gates'])+'\n\n'
gates+='## Original builder gates\n\n'+table(b['gates'])+'\n\n'
gates+='## Original hole QA\n\n'+table(q['gates'])+'\n\n'
gates+='## Independent masonry support, blend\n\n'+table(rb['gates'])+'\n\n'
gates+='## Independent masonry support, FBX\n\n'+table(rf['gates'])+'\n\n'
gates+='## Additional actual phase requirements\n\n| Gate | Result | Measured detail |\n|---|---|---|\n'
gates+=f"| RUIN_NOT_BOXES independent census, blend | {'PASS' if pb['pass'] else 'FAIL'} | {pb['unbroken_cuboids']}/{pb['pieces']} unbroken cuboids, limit20%; rotated boxes are also counted by the classifier control |\n"
gates+=f"| RUIN_NOT_BOXES independent census, FBX | {'PASS' if pf['pass'] else 'FAIL'} | {pf['unbroken_cuboids']}/{pf['pieces']} unbroken cuboids, limit20% |\n"
gates+=f"| SCORING_EXACT | {'PASS' if exact['pass'] else 'FAIL'} | Four installed/staged blend/FBX comparisons; exact names/types/transforms, world vertices and polygon topology, markers; zero tolerance, no epsilon |\n"
gates+=f"| CLIFF_OUTLINE_RUN spatial diagnostic | {'PASS' if sc['cliff']['pass_gate'] else 'FAIL'} | Longest actual outer silhouette run {sc['cliff']['max_straight_run_m']:.6f}m, cap4m, fixed0.10m chord deviation; this does not replace actual aerial masks |\n"
gates+='| TWO_INDEPENDENT_ISLANDS | FAIL | Frozen baseline has1 connected outer boundary and0 interior boundary loops; no additional closing edge or imaginary island partition was introduced |\n'
gates+='| SPLIT_CLIFF_ISLANDS | FAIL | Literal two-island topology fails; >=80% cliff faces plus surf at both original shoreline arcs are still unmeasured in a fresh Unity aerial |\n'
gates+='| FRESH_AERIAL_SIDE_BY_SIDE | PASS | Fresh native aerial and hole09_vs_ref_staged.jpg exist and were opened by this agent |\n'
gates+='| TEE_DRAW_CALLS | FAIL | Actual Unity counter publication FAIL: three synchronous render samples all reported zero; no isolated valid drawCalls/SetPass measurement. Cap250 remains unverified;1417 meshes is not a draw-call PASS |\n'
(HERE/'GATES_hole09.md').write_text(gates)

ranked=json.loads((HERE.parent/'ranked_differences.json').read_text())['9']
evidence=[
 '76 real four-bed cliff chunks/67200tri plus30 taller narrow ridges clad the frozenC-shaped land; exact scoring untouched. One connected boundary remains, so two independent islands fail.',
 '30 narrow scenery ridges reach measured2.0–3.9m over the frozen6m top; original H_RIDGE_RELIEF passes and89% of80 spine stations have a knoll/crag within14m.',
 f"Actual shell tortuosity1.236904>=1.15 and joint full-height rate15%<=25%,CV0.55>=0.40. Actual outer straight-run diagnostic is {sc['cliff']['max_straight_run_m']:.6f}m against4m; geometry cannot be declared a visual retaining-wall fix.",
 f"Standing2.3m x2.4m through-doorway,5.9m broken arch and381 masonry stones plus13 fallen blocks are support-checked; exact independent unbroken-box census {pb['unbroken_cuboids']}/{pb['pieces']} in blend and {pf['unbroken_cuboids']}/{pf['pieces']} inFBX. Actual native ruin mask is0px in both address frames and92px in the aerial; it remains tiny against the reference.",
 'P1 shared fairway/green PNG contrast was rebuilt and measured on its fixture; actual H9 bands are visibly subtler. Raw gaps tee1.37%/approach8.06% are below12%, but repeated-control drift invalidates the cap measurements, so the gate remains FAIL.',
 'Real faceted LK_ROCK caps and LK_SCRUB flanks now vary the ridge. Original ridge533plants/158rocks and13 thickets holding86% of76 shrubs pass. No new Split hanging vines were added; actual aerial still shows a washed dull ridge and isolated scattered props; it lacks the dense rocky golden-green scrub of the reference.',
 'Existing broken surf is retained and unchanged sparse-surf/no-foam-strip tests pass. Actual base adjacency/coverage on both semantic shores remains unmeasured; no continuous fake strip was added.',
 'The original channel water ellipse/shoreline stays frozen. Cliff geometry avoids the water ellipse and adds spatial erosion outside the land; the long connected scoring shore and parallel corridor cannot be replaced with two islands. Frozen approach water ceiling is3.359792% atz0 or6.171528% atz5.99, below15%.',
 'Existing12 rock crags and seastacks are retained; all unchanged rock shape/PCA/prop-face/instancing gates are measured by final verifier. Split stacks were not replaced by new tall needles; actual aerial still shows thin detached stacks/rocks and insufficient coherent rocky mass.',
 'All3 frozen elliptical bunkers retain their sand textures and soft scoring lips; exact geometry and original sand/relief rules pass. Ellipse outlines remain smooth by the frozen scoring rule.'
]
rescore=dict(hole=9,phase='P3',result='FAIL',reason='Actual reference comparison remains FAIL: long connectedC-shaped flat strips, boardlike cliff bands, washed ridge, sparse surf and an invisible address-view ruin. Literal two-independent-island topology fails. Native counter publication and pending>=80% outline masks remain FAIL.',
    verifier=dict(pass_count=sum(g['ok'] for g in v['gates']),total=len(v['gates']),failures=v['failures']),
    builder=dict(pass_count=sum(g['ok'] for g in b['gates']),total=len(b['gates'])),
    exact_scoring_pass=exact['pass'],fresh_aerial='PASS captured and viewed',split_cliff_islands='FAIL',
    ranked_differences=[dict(p0_rank=i+1,difference=row[0],scope=row[1],result='FAIL',fixed=False,evidence=evidence[i],remaining='This agent opened the actual native vs-reference sheet and both address views. Remaining visual differences and measured masks/counter limitations are explained; the reference recognition answer is NO.') for i,row in enumerate(ranked)])
(HERE/'ranked_rescore.json').write_text(json.dumps(rescore,indent=2)+'\n')

install=f'''# H9 Split final staged candidate — 2026-10-05

The stage is frozen and has not been installed by this agent. Overall P3 is **FAIL**: literal two-independent-island topology fails on the frozen connectedC-shaped land; actual native aerial/stills and vs-reference sheet are captured and viewed;>=80% cliff/surf mask measurement is pending, and tee counter publication failed. Required original verifier {count(v['gates'])}, failures {v['failures']}; builder {count(b['gates'])}; original hole QA {count(q['gates'])}; independent ruin {count(rb['gates'])} blend / {count(rf['gates'])} FBX. Independent piece census {pb['unbroken_cuboids']}/{pb['pieces']} and {pf['unbroken_cuboids']}/{pf['pieces']} unbroken cuboids, cap20%. Exact scoring audit {'PASS' if exact['pass'] else 'FAIL'} with zero tolerance.

## Frozen stage sha256

```
{sha}
```

248868 triangles,1417 mesh objects,1421 objects,9911 groundtriangles; FBX5871KB. The unchanged verifier cap is250000, Phase6 cap300000. Actual draw calls/SetPass remain unmeasured;18→7 masonry renderers and1417 total source meshes do not establish the250draw-call cap.

Final input provenance: lib_sha_final.txt and look_png_sha_final.txt. Shared libraries/PNGs were not edited duringP3 except the specifically authorized H9 masonry helper. P3 edits are H9 build/look and the opted-in helper in H9 masonry; no design/scoring/checker thresholds were edited.

## Phase6 installation

Point install_holes.py LIBLISTS at work/postcard-look/v3/hole09/lib_sha_final.txt, then use run_proof.sh pre/install. Copy staged .blend and .fbx only. Preserve the installed hole_09.fbx.meta byte-for-byte; never copy the generated stagingmeta. Re-run guards before/after installation and all required installed checks/proofs.

## Actual changes

Thirty narrow scrub ridges have2.0–3.9m actual height over the frozen6m scoring terrain, exposed rock caps and scrub flanks. Seventy-six actual four-bed cliff chunks reach sea level,67200tri, with original tortuosity1.236904 and staggered-joint checks passing. Original actual outer silhouette diagnostic: {sc['cliff']['max_straight_run_m']:.6f}m longest straight run versus4m cap; actual aerial cliff coverage is pending. Literal two-island topology remains FAIL.

True masonry alone is spatially batched by whole stone components and material identities: ruin14→6 /297pieces3885polygons, arch4→1 /84pieces1135polygons. Max world spans11.995521m and10.140989m within12m. Min masonry64.7047% /69.5183%, max rock35.2953% /30.4817%, preserving all381 stone components and5020polygons. The standing doorway has56/56 clear through-rays; the broken arch is5.9m over ground. Disconnected stone geometry, UVs, material identity and flat normals stay exact. Custom-normal inputs remain unchanged rather than being quantized. Plant root pivots/colours and100% mesh sharing are retained; plants were not blindly merged.

Only far-field filler budgets/counts were reduced: outer shrubs20→16, ridge pebble filler44→36, far-green fringe2000→400tri and far-olive1000→200tri. All ridge76 shrubs, near-camera fringe budgets8500/4000/7000/2500,130 ruin field tufts,32clumps,60wall-foot tufts and12bush skirts remain. The checkpoint contains actual unverified pre-batch geometry, enabling resumption without another expensive scatter.

UV-only final repair maps519 knoll rock facets into their real best-fit world planes and771 frozen firstcut top polygons into unwarped worldXY rough UVs. This fixes the original17–41% rock-cap smear and342m2 firstcut smear without any vertex/face/normal change. The final original UV_DENSITY and GROUND_UV_LOCAL_SMEAR checks pass on bothformats only as recorded in the final required verifier table.

## Evidence and failed attempts

GATES_hole09.md contains every original verifier/builder/holeQA/support gate and independent phase requirements. check_stage_final.log/results and individual logs/JSON record the complete final checks. Exact scoring is ../audit/scoring_exact_p3.json/txt. scenery_metrics.json records actual topology/ridge/cliff metrics and exact native proof prefixes. ranked_rescore.json explains everyP0 difference honestly without inventing a visual re-score.

ATTEMPTS.md and DECISIONS.md preserve real failures: three-bed full-height joints26%>25% and incompatible original four-bed tortuosity reader; removed Blender object reference wrapper; actual rock/firstcut UV failures; scratch missing-context error. The unverified checkpoint is explicitly labelled and must not be installed. Finalstage came from the same native geometry with UV-only repair, unchanged original audits and look FBX LINEAR colour exporter. Parent nativecapture is queued; no Unity/installed asset changes were performed by this agent.
'''
(HERE/'INSTALL.md').write_text(install)
(HERE/'P3_RESULT.md').write_text(f'''# Phase3 binary result: FAIL

Final builder {count(b['gates'])}; required verifier {count(v['gates'])}, failures {v['failures']}; original holeQA {count(q['gates'])}; exact scoring {'PASS' if exact['pass'] else 'FAIL'} (noepsilon); independent ruin13/13 eachformat and unbroken cuboids {pb['unbroken_cuboids']}/{pb['pieces']} blend, {pf['unbroken_cuboids']}/{pf['pieces']} FBX.248868tri (<250000),1417 meshes. True masonry18→7 renderers,381 whole stones/5020polygons preserved; native tee drawCalls/SetPass counter publication failed (all three samples zero), so costs remain unverified/FAIL.

TWO_INDEPENDENT_ISLANDS FAIL: frozen one connected415-pointC-shaped top loop cannot become two independent scoring islands. SPLIT_CLIFF_ISLANDS FAIL: topology fails and actual>=80% cliff+surf mask proof remains unmeasured. Fresh aerial/side-by-side PASSexists and was viewed. Actual ruin0px in both address views (<64px required), so gameplay landmark framing FAIL. Tee counter publication FAIL (rawzero samples do not count as0drawcalls). Actual outer cliff straight-run diagnostic {'PASS' if sc['cliff']['pass_gate'] else 'FAIL'}: {sc['cliff']['max_straight_run_m']:.6f}m versus4m. AllP0 ranked differences have explicit evidence/remainingconstraints inranked_rescore.json.

Next: root completes the queued actual outline masks and valid tee counter publication against these frozen binary hashes, then proceeds inphase order. The actual side-by-side was viewed and the recognition answer is NO; source geometry counts cannot substitute for performance. No missing image, skipped gate or source mesh count is aPASS.
''')
with (HERE/'ATTEMPTS.md').open('a') as handle:
    handle.write(f"\n## Attempt3 final UV-only repair and complete checks\n\nNative checkpoint resume repaired519 real rock facet UVs and771 firstcut top UVs without changing geometry/normals/plants. Builder {count(b['gates'])} PASS; final required verifier {count(v['gates'])} PASS, actual failures {v['failures']}. Original holeQA {count(q['gates'])} PASS, independent ruin13/13 eachformat, cuboids {pb['unbroken_cuboids']}/{pb['pieces']} blend and {pf['unbroken_cuboids']}/{pf['pieces']} FBX; allfour exact scoring comparisons {'PASS' if exact['pass'] else 'FAIL'} at zero tolerance. Actual248868tri/1417meshes unchanged. Outer cliff straight-run diagnostic {'PASS' if sc['cliff']['pass_gate'] else 'FAIL'} {sc['cliff']['max_straight_run_m']:.6f}m cap4m. Literal2-islands FAIL; fresh native image/masks/costs remain FAILunmeasured at this frozenhandoff. No checker threshold relaxed.\n")
print('FINAL_RECORDS_WRITTEN',v['failures'])
