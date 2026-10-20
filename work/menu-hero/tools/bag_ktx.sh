#!/bin/zsh
# chat G: lobby .ktx copies of the golf bag maps the exporter installed (2048 halves, MatchHeroLockerExport.LobbyHalf); same TextureConverter
# settings as work/accessories/lobby/compress_maps.py (ASTC 8x8, linear, flipped, clamp). Run after sync_heroes.sh.
A=${0:A:h:h:h:h}/GolfArcade/Unity/CharacterAssets
for p in $A/MatchHero_Acc_*_golf_bag_Bag_[MN].png; do
  out=${p:r}.ktx
  [[ -f $out && $out -nt $p ]] && { echo "up to date ${out:t}"; continue; }
  /Applications/Xcode.app/Contents/Developer/usr/bin/TextureConverter --compression_format=ASTC8x8 --compression_quality=Highest --alpha_mode=Preserve --channel_weighting=Linear \
    --gamma_in=1 --gamma_out=1 --flip_y --wrap_mode=Clamp --file_format=KTX --output=$out $p || exit 1
  echo "${out:t} $(stat -f %z $out)"
done
