#!/bin/bash
# r5: tennis (A/B + bake) -> golf (tee-group tris on 16 holes + identity/pop/film/perf/gpu + bake merged with tennis) -> EditMode tests.
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
P=work/character-lod/proof
rm -f work/character-lod/install/HeroLodCache.bytes          # v3 cache is stale for v4: start the merge from tennis
CLOD_METHOD=CharacterLodTennisProbe work/character-lod/tools/run_probe.sh $P/r5t > $P/r5t_run.out 2>&1
[ -f $P/r5t/HeroLodCache_tennis.bytes ] && cp $P/r5t/HeroLodCache_tennis.bytes work/character-lod/install/HeroLodCache.bytes
CLOD_VIEWS=tee,drive work/character-lod/tools/run_probe.sh $P/r5 > $P/r5_run.out 2>&1
[ -f $P/r5/HeroLodCache.bytes ] && cp $P/r5/HeroLodCache.bytes work/character-lod/install/HeroLodCache.bytes
work/character-lod/tools/run_tests.sh $P/r5tests > $P/r5tests_run.out 2>&1
echo "r5 chain done"
