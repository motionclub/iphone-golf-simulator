#!/bin/zsh
# male-garments: copy the OWNED garment files from ~/male-garments-UnityClone into Unity/ and stage them by explicit path.
# Shared files (the two male prefabs, MatchHeroLook.cs) are NOT copied: patches/ + patches/INSTALL.md for the integration chat.
#   install_to_repo.sh [--dry]
set -e; setopt null_glob
ME=${0:A:h:h}; REPO=${ME:h:h}; CL=$HOME/male-garments-UnityClone; DRY=0; [[ $1 == --dry ]] && DRY=1
files=()
for d in Assets/Characters/KitsV2/MatchHero_Male Assets/Characters/KitsV2/GolfKitHero_Male Assets/Resources/Tennis/KitsV2/Male Assets/Resources/Golf/KitsV2/Male; do
  for f in $CL/$d/*(.); do r=${f#$CL/}; cmp -s $f $REPO/Unity/$r || files+=$r; done
done
print -l $files > $ME/patches/installed_files.txt
echo "${#files} owned files differ"
(( DRY )) && { print -l $files; exit 0; }
for r in $files; do mkdir -p ${REPO}/Unity/${r:h}; cp $CL/$r $REPO/Unity/$r; done
cd $REPO && git add -- ${files/#/Unity/} && echo staged ${#files}
