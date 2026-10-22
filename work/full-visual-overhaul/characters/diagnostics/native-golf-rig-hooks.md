# Native actual golf rig integration

`MatchHeroLockerExport.RunGolf` now exports actual `HeroGolfer.Build` with **54 named bones (original golf rest + Club), one rigid Face track, and all four skinned equipment parts**. Geometry/clip coordinates remain the existing Unity-metres z reflection. Full tennis remains 53 named bones plus rigid face/racket tracks. The unified loader requires no second skeleton or external prop.

Equipment part names: `Club_Driver`, `Club_Iron`, `Club_Wedge`, `Club_Putter`. All use their original live Club binding. `buildHero` hides all but `Club_Iron`. Remove/skip the separate static `NativeGolfEquipment.make` attachment when any `Club_*` part exists. Every clip has optional `equipment` lower-case driver/iron/wedge/putter from original landmarks, with iron as menu fallback.

Golf clips: `ready` and `idle` = actual Idle, `serve` and `golfDrive` = actual Drive, `golfIron`, `golfHalf`, `golfChip`, `golfPutt`, `wave`, `cheer`, `matchWin` = Cheer, `hitPerfect` and `celebratePoint` = FistPump. All actual authored resource clips, no guessed retargets. Original contact times come from golfer_<sex>_clips JSON.

## HeroRig hook points (root-owned MatchHeroMotion.swift)

In attach(), after constructing every skinner:

```swift
data.attachMorphers(to: root)
```

When applying the first ready pose, also:

```swift
data.applyMorphWeights(ready.morphWeights(at: 0, loop: true), to: root)
```

In detach(), for every skinned node before restoring static geometry:

```swift
node.morpher = nil
```

In apply(_ motion: MenuMotion, at time: Double), immediately after applying bone pose:

```swift
data.applyMorphWeights(motion.morphWeights(data, at: time), to: root)
```

The data helpers are installed in MatchHeroData.swift. Morph targets include positions and normals in original bind space. SceneKit `SCNMorpher.calculationMode=.additive` applies the weighted target differences before skinning; `unifiesNormals=false` preserves source custom normals. Weights are normalized to the authored source frame's weight (Unity 100 = native 1), not clamped or normalized again. Both exporters and native samples use the same 60Hz + adaptive-cut times. `MenuMotion.morphWeights` follows the exact same idle offset, fade-in, full clip, fade-out, and settle-to-ready semantics as MenuMotion.pose. This avoids fit popping during menu transitions.

The exporter self-check explicitly adds the exported corrective deltas using the exported weights **before** multiplying the exported bone/bind matrices. It rejects >0.5mm deviation and writes independent golden weighted-vertex samples if MH_LOCKER_GOLDEN is set. These numerical gates are unverified until the actual fresh export runs.
