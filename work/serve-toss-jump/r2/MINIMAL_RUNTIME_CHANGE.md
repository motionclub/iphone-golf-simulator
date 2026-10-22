Prompt 28 owns `Unity/Assets/Scripts/Tennis/HeroTennisDriver.cs`. This change is a proposal only; it has **not** been applied or tested.

The live trace identifies `LockFeet`, specifically line 708's 65 mm step arc and lines 716–720's drift-triggered step creation. At clip 1.510118, the base layer is 100% Serve and the upper layer is 0%; adding the arc raises the male left heel by 64.012497 mm and the female right heel by 64.012211 mm. Neither clip import nor the upper/lower layer split causes that difference.

The smallest targeted change is to stop procedural replant steps while the match Serve clip owns the pose, including a step left over from walking in. Keep the existing planted-foot lock and all other clips' steps.

Inside `LockFeet`'s foot loop, immediately before the existing line 703:

```csharp
bool authoredServe = Match && actionActive && action == Clip.Serve;
if (authoredServe) stepping[f] = false;
```

Add `!authoredServe &&` to the condition at existing line 716:

```csharp
if (!authoredServe && !FluidOff && locked[f] && plantedNow && lockW[f] > .9f
    && drift > StepDrift && !stepping[1 - f] && dt > 0
    && Vector3.Distance(upper.position, foot.position) < legLen * .985f)
```

The clear is necessary: guarding only new step creation would still let an already-running walk-in step apply line 708 during Serve. This proposed guard preserves the rest of the leg lock; it does not address the separate clip landing, contact knee, clearance or wrist problems.

After the owner integrates a suitable fix, rerun the unchanged-candidate trace first. Then resume the clip work from prompt 26's existing rekey scripts and candidate FBXs. Do not install until every gate passes.
