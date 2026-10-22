# Compact basalt prototype handoff

Source is scratch-only compact_columns.py. Production integration belongs to the hole agent. Shared scripts, textures, design, verifier, scoring and installed assets remain unchanged by this work.

Use compact_ring_tile(D,path,top_z,bottom_z=-1.6,rows=3,seed=0,width_m=(1.68,1.78),pitch_m=1.875,depth_pitch_m=3.25,name="ROCK_WALL_...",max_faces=490,max_span_m=20,clip=None,bottoms=None). A ~9.375m tile has3actual depth rows×5columns. Each real5/6-sided column is one connected closed stone with one genuine top corner fracture. It returns object,columns (width,sides,bottom,top,grid_index,vertex/face ranges),horizontal_span,path_length,rows,columns_per_row and triangle_projection_per_m. The left of the path has ~8m actual backing depth; account for this in off-play clearance.

For supported upper far-sector bands, retain identical path/grid/seed/width/clip and pass bottoms=[s['top'] for s in lower['columns']]. Scalar previous nominal top would create gaps because actual tops vary; never use it. Near returned objects must all still reach12..60m;70m bands belong only to genuine far sectors. Full skyline variance, ring angular coverage, near object count, crust minimum, full budget and UV/color/window gates are the original whole-hole tests.

Attempt5 all9local checks PASS at14.2/18.2/26.2m and a30.2m curved world-position tile: rock_shape,PCA,count_columns,side area,faces,actual width,side count,span,near tops. Each tile15actual shafts/124polygons/316triangles;15detected caps;PCA .3522/.2824/.1984/.17188;95.61–97.77%side area;width1.602–1.7669m;span12.80–15.39m. Cost33.69–33.71tri/m;3200m projected walls107.8–107.9k triangles. Projection is not a fullhole budget PASS.

Support fixture:20.2/44.2/70.2m three-band far sector. Each band passes unchanged shape/PCA/count/face/width/span;PCA .25195/.22567/.20829;total948tri. All30interfaces have exact0m gap;98.5634–99.5476% cap/base bearing. Extra strict cap-vertex containment diagnostic FAILs at tiny world-float cut points and remains FAIL in support/measurements.json. Do not report all-support PASS. The first harness serializationFAIL is preserved separately.

Failed alternatives remain in attempts1–4 and DECISIONS.md. Low5.5m bands fail near tops; thin row generators fail PCA; all-pentagon tall tiles fail facet orientations; four-row26m tile fails PCA. No repeated failed idea was fixed by names or changed thresholds. Clay previews show a real column cluster but are not reference-match or Game view PASS evidence. Current ordinary world-box UV remains incompatible with the frozen shared Basalt tile's zone/component gates; retain those FAILs.

Final source SHA is in source_sha.json. The existing hole09_stone halfspace solver is imported read-only. No Unity or installs were run.
