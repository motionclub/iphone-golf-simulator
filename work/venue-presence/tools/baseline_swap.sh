#!/bin/bash
# One-off: measure the ORIGINAL builder's triangle counts and build time with the same dump tool, then restore the new files.
#   1. parks TennisVenueBuilder.{Mesh,Skyscraper,Volcano}.cs (+ .meta) outside Assets
#   2. puts the original TennisVenueBuilder.cs (before_code/) back, adding only a build stopwatch log
#   3. captures both venues with HERO_VENUE_DUMP=1
#   4. ALWAYS restores the new files and verifies them against after_code/SHA256.txt
ROOT=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
SC=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/77154239-0257-4f5d-b25c-11ae6b66b84a/scratchpad
T=$ROOT/Unity/Assets/Scripts/Tennis
VP=$ROOT/work/venue-presence
mkdir -p "$SC/parked"
cd "$ROOT" || exit 1

restore() {
  for f in Mesh Skyscraper Volcano; do
    [ -f "$SC/parked/TennisVenueBuilder.$f.cs" ] && mv "$SC/parked/TennisVenueBuilder.$f.cs" "$T/"
    [ -f "$SC/parked/TennisVenueBuilder.$f.cs.meta" ] && mv "$SC/parked/TennisVenueBuilder.$f.cs.meta" "$T/"
  done
  cp "$VP/after_code/TennisVenueBuilder.cs" "$T/TennisVenueBuilder.cs"
  echo "== restored; verifying against after_code/SHA256.txt"
  ( cd "$T" && for f in TennisVenueBuilder.cs TennisVenueBuilder.Mesh.cs TennisVenueBuilder.Skyscraper.cs TennisVenueBuilder.Volcano.cs TennisVenueFx.cs; do
      want=$(grep " $f\$" "$VP/after_code/SHA256.txt" | cut -d' ' -f1); have=$(shasum -a 256 "$f" | cut -d' ' -f1)
      [ "$want" = "$have" ] && echo "   OK   $f" || echo "   DIFF $f" ; done )
  ( cd "$ROOT/Unity/Assets/Editor" && want=$(grep " TennisVenueCapture.cs\$" "$VP/after_code/SHA256.txt" | cut -d' ' -f1); have=$(shasum -a 256 TennisVenueCapture.cs | cut -d' ' -f1); [ "$want" = "$have" ] && echo "   OK   TennisVenueCapture.cs" || echo "   DIFF TennisVenueCapture.cs" )
}
trap restore EXIT

for f in Mesh Skyscraper Volcano; do mv "$T/TennisVenueBuilder.$f.cs" "$SC/parked/"; mv "$T/TennisVenueBuilder.$f.cs.meta" "$SC/parked/"; done
cp "$VP/before_code/TennisVenueBuilder.cs.before" "$T/TennisVenueBuilder.cs"
python3 - <<'EOF'
p='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Scripts/Tennis/TennisVenueBuilder.cs'
s=open(p).read()
old="""            var root = new GameObject(kind + " venue").transform;
            switch (kind)
            {
                case TennisVenueKind.Skyscraper: Skyscraper.Build(root); break;
                case TennisVenueKind.Volcano: Volcano.Build(root); break;
            }"""
new="""            var root = new GameObject(kind + " venue").transform;
            var clock = System.Diagnostics.Stopwatch.StartNew();
            switch (kind)
            {
                case TennisVenueKind.Skyscraper: Skyscraper.Build(root); break;
                case TennisVenueKind.Volcano: Volcano.Build(root); break;
            }
            Debug.Log("[VenueBuild] " + kind + " venue built in " + clock.ElapsedMilliseconds + " ms (ORIGINAL builder)");"""
assert old in s
open(p,'w').write(s.replace(old,new,1))
EOF
HERO_VENUE_DUMP=1 HERO_VENUE_ONLY=none "$VP/tools/capture.sh" "$VP/proof/baseline_dump" skyscraper volcano > "$VP/logs/baseline_swap_run.txt" 2>&1
cp "$VP/logs/capture_skyscraper.log" "$VP/logs/before_capture_skyscraper.log"
cp "$VP/logs/capture_volcano.log" "$VP/logs/before_capture_volcano.log"
echo "== measured:"
grep -h "VenueBuild\] .*ORIGINAL\|VenueDump\] \(skyscraper\|volcano\)" "$VP/logs/before_capture_skyscraper.log" "$VP/logs/before_capture_volcano.log" | grep -v "^GolfArcade\|Filename" | sort -u
grep -h "VenueDump\] venue group" "$VP/logs/before_capture_volcano.log" | sort -u > "$VP/logs/before_volcano_groups.txt"
grep -h "VenueDump\] venue group" "$VP/logs/before_capture_skyscraper.log" | sort -u > "$VP/logs/before_skyscraper_groups.txt"
