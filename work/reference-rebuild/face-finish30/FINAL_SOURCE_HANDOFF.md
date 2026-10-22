# Head forms final source handoff

**Use `ears/{Male,Female}_OriginalFaceFinish30Ears.blend` and `.fbx` for the complete broad-head finishing lane.** Export hashes are in `ears/STAGED_EXPORT.json`. They include broad cheek/jaw cleanup, female smooth round scalp, local subnasal/philtrum continuity, and reviewed ear cartilage polish. They do not include the held eye operation.

Visual source review PASS by geometry Astra and independently by material Astra. Actual broad cheek/chin improvement was reviewed and accepted by root in face-finish30-broad1. Root also reviewed female cap and male philtrum improvement in composed1. Ear actual integration is pending; compact source before/after crops are `ears/{male,female}_ear_{before,after}.png`.

Reproduce in sequence:
1. `build-face30.py`: frozen Smooth1 → main broad sources.
2. `final/finish-surfaces.py`: broad → clean subnasal surface + fitted female scalp.
3. `ears/finish-ears.py`: final → gentle cartilage/rim/lobe finish.
4. `ears/export.py`: export original-name Body/ReferenceFeatures plus53-bone rig.

All original vertex prefixes retained (Male33472 /Female22891); final Body counts43900 /34366. All weights and topology remain unchanged from broad30 during final and ear passes. All original blink shape deltas remain exact. All rigs/rest/bind transforms and feature mesh remain unchanged. Broad source originalparent map is recursive: appended parents may refer to earlier appended vertices. Later final and ear phases add a common positional delta to all shape states.

Eye lane status updated: root isolated the severe female brown-block artifact to imported blendshape normal deltas; disabling those deltas removed it without a geometry change. At root's request, the unchanged READY female operation (`c5f92baf…`) is now composed on final Ears source in `composed-ears/{Male,Female}_OriginalFaceFinish30ComposedEars.{blend,fbx}`. That folder's STAGED_EXPORT.json is the current normal-helper integration candidate. Female active prefix conflict is exactly0; male uses accepted original eye geometry pending its own READY operation. The earlier `composed-female/` artifact is superseded. `COMPOSITION_DIAGNOSTIC.json` established exact female source/composition parity (max0.000119mm float precision). Eye lane reports tiny corner holes remain a separate source residual. Root owns the coherent runtime normal helper and actual validation.

Source actual normals: default continuous remains preferred. Global source-normal A/B made socket/browbridge shading worse. The female smooth cap makes original and appended scalp points follow one fitted continuous surface, replacing long flat sections while keeping original dimensions. Ear first trial acquired ridges; final trial fixed attachment within2mm/fade11mm and uses smooth authored-normal frames, retaining helix/concha.

No production Assets writes by this lane. Root owns serial Unity/GPU, native adoption and final game/lobby proof.
