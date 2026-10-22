# Fixed fold AO measurement protocol

Use the final ClothProofRig fold cameras for both AO=1 and AO=0. Lighting, cavity, normal maps, exposure, pose and post processing remain identical. Rear armpit and waist cameras avoid the Ready pose arms/racket; crotch is front. Screenshots are linearized from sRGB. Rec.709 luma darkening is 100*(Y_noAO-Y_AO)/Y_noAO.

Within a fixed named feature crop, measure white cloth crease texels whose authored AO is <=0.85, excluding trim and boundary antialiasing. This reports the actual crease, rather than diluting it with unrelated smooth cloth. Include crop rectangles, selected pixel count and an overlay of the selected pixels. Do not select based on observed darkening. Inspect every selected crop for skin/body occlusion. Report maximum darkening over all visible main garment texels and reject >30%. Female skort covers the crotch; crotch uses male shorts.

Candidate ROI definitions will be written before computing lit luma darkening, based only on feature location and AO data images.
