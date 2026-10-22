#!/bin/zsh
# Copy this job's files (and only them) from the repo's Unity/ into the private APFS clone.
REPO=${0:A:h:h:h:h}/Unity
CLONE=${CLONE:-$HOME/hand-clearance-work/UnityClone}
for f in Assets/Scripts/Tennis/HeroClearanceProxy.cs Assets/Scripts/Tennis/HeroClearance.cs Assets/Scripts/Tennis/HeroPoseSafety.cs Assets/Scripts/Tennis/HeroClearanceTracks.cs Assets/Scripts/Tennis/HeroTennisDriver.cs Assets/Scripts/Game/GolferView.cs \
         Assets/Scripts/Hub/HubHeroAnimator.cs \
         Assets/Editor/AnimationSafetyAudit.cs Assets/Editor/AnimationSafetyAuditSweep.cs Assets/Editor/AnimationSafetyAuditLegacy.cs \
         Assets/Editor/HeroClearanceBake.cs Assets/Editor/HeroClearanceFilm.cs Assets/Tests/EditMode/HeroClearanceTests.cs; do
  [[ -f $REPO/$f ]] || continue
  cmp -s $REPO/$f $CLONE/$f || { cp $REPO/$f $CLONE/$f; echo "synced $f"; }
done
