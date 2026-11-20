using System.Collections;
using System.Linq;
using System.Reflection;
using GolfArcade.Game;
using GolfArcade.Shot;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    public class GolfPostShotTests
    {
        const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
        static void Evaluate(GolferView g) => typeof(GolferView).GetMethod("Evaluate", Private).Invoke(g, null);
        static float Field(GolferView g, string name) => (float)typeof(GolferView).GetField(name, Private).GetValue(g);
        IEnumerator Check(bool female, GolfClub club, float load, bool steps)
        {
            var oldBody = GolferStyle.Body; bool? oldOverride = GolferStyle.HeroOverride;
            Time.captureFramerate = 60; GolferStyle.HeroOverride = true;
            GolferStyle.Body = female ? GolferStyle.BodyKind.Female : GolferStyle.BodyKind.Male;
            var root = new GameObject("Post-shot test");
            try
            {
                var g = GolferView.Create(root.transform); g.Stand(Vector3.zero, Vector3.forward); g.SetClub(club, club == GolfClub.Chipper);
                yield return null; Assert.IsTrue(g.IsHero);
                float leftGround=g.Hero.Bones["LeftFoot"].position.y, rightGround=g.Hero.Bones["RightFoot"].position.y;
                for (int i = 0; i < 60; i++) { g.ShowLoad(load * (i + 1) / 60); yield return null; }
                var origin = g.transform.position;
                var bones = g.Hero.Bones;
                var hip = bones["Hips"]; var left = bones["LeftFoot"]; var right = bones["RightFoot"];
                var names = new[] { "Left", "Right" };
                var lengths = names.SelectMany(n => new[] { Vector3.Distance(bones[n+"UpperLeg"].position,bones[n+"LowerLeg"].position), Vector3.Distance(bones[n+"LowerLeg"].position,bones[n+"Foot"].position) }).ToArray();
                float impact = g.Strike(), elapsed = 0, maxHip = 0, maxFoot = 0;
                bool watching = false; Vector3 previous = hip.position;
                Vector3 previousElbowL=bones["LeftLowerArm"].position, previousElbowR=bones["RightLowerArm"].position;
                var turnBones = new[] { "Hips", "Spine", "Chest", "LeftUpperArm", "LeftLowerArm", "RightUpperArm", "RightLowerArm", "LeftHand", "RightHand" }.Where(bones.ContainsKey).Select(n=>bones[n]).ToArray();
                var previousTurns = turnBones.Select(b=>b.rotation).ToArray();
                float maxTurn = 0, heldFinishGap = -1;
                for (int i = 0; i < 300; i++)
                {
                    if (!watching && elapsed >= impact) { g.WatchShot(() => origin + Vector3.forward * 30 + Vector3.up * 6); watching = true; }
                    yield return null; elapsed += 1f / 60;
                    var posedHip = hip.position; var posedL = left.position; var posedR = right.position;
                    if (Field(g,"finishClock") >= 0 && Field(g,"watchClock")-Field(g,"finishClock") > .72f) CheckClubClearance(g, origin, i == 299, ref heldFinishGap);
                    Assert.Less(Vector3.Distance(g.transform.position, origin), .00001f, "gameplay root stays at address");
                    if (i > 140) Assert.Less(Vector3.Distance(posedHip, previous), .025f, "settling hips have no pop");
                    previous = posedHip;
                    for (int joint=0;joint<turnBones.Length;joint++)
                    {
                        float angle=Quaternion.Angle(previousTurns[joint],turnBones[joint].rotation);
                        if (Field(g,"finishClock")>=0 && Field(g,"watchClock")-Field(g,"finishClock")>.9f)
                        {
                            maxTurn=Mathf.Max(maxTurn,angle);
                            Assert.Less(angle,6.5f,$"{turnBones[joint].name}: abrupt post-finish rotation at {elapsed:F3}s");
                        }
                        previousTurns[joint]=turnBones[joint].rotation;
                    }
                    if (Field(g,"finishClock") >= 0 && Field(g,"watchClock")-Field(g,"finishClock") > .72f)
                    {
                        Assert.Less(Vector3.Distance(bones["LeftLowerArm"].position,previousElbowL),.028f,"left lowering elbow has no frame pop");
                        Assert.Less(Vector3.Distance(bones["RightLowerArm"].position,previousElbowR),.028f,"right lowering elbow has no frame pop");
                    }
                    previousElbowL=bones["LeftLowerArm"].position; previousElbowR=bones["RightLowerArm"].position;
                    float handSpan = Vector3.Distance(bones["LeftHand"].position,bones["RightHand"].position);
                    GolferView.MannerismsOff = true; Evaluate(g);
                    // Wrist joint centres are not palm contact points; compare with the approved
                    // grip at this same clip pose rather than assuming an absolute hand size.
                    if (Field(g,"finishClock") >= 0 && Field(g,"watchClock")-Field(g,"finishClock") > .72f)
                        Assert.LessOrEqual(handSpan,Vector3.Distance(bones["LeftHand"].position,bones["RightHand"].position)+.01f,"lowering adds no more than 1 cm wrist separation to the approved grip");
                    float h = Vector3.Distance(posedHip, hip.position), foot = Mathf.Max(Vector3.ProjectOnPlane(posedL-left.position,Vector3.up).magnitude,Vector3.ProjectOnPlane(posedR-right.position,Vector3.up).magnitude);
                    maxHip = Mathf.Max(maxHip,h); maxFoot = Mathf.Max(maxFoot,foot);
                    if (Field(g,"finishClock") < 0 || Field(g,"watchClock")-Field(g,"finishClock") < .69f) Assert.Less(h,.0001f,"no steps before held finish");
                    GolferView.MannerismsOff = false; Evaluate(g);
                    int k = 0;
                    foreach (string n in names) foreach (var pair in new[] { (n+"UpperLeg",n+"LowerLeg"),(n+"LowerLeg",n+"Foot") })
                        Assert.That(Vector3.Distance(bones[pair.Item1].position,bones[pair.Item2].position), Is.EqualTo(lengths[k++]).Within(.001f), "leg length preserved");
                }
                Assert.That(maxHip, steps ? Is.InRange(.10f,.13f) : Is.LessThan(.0001f), "bounded/suppressed body travel");
                Assert.That(maxFoot, steps ? Is.InRange(.14f,.17f) : Is.LessThan(.0001f), "bounded/suppressed foot travel");
                if (steps)
                {
                    foreach (string n in names) Assert.Less(bones[n+"LowerArm"].position.y,bones[n+"UpperArm"].position.y-.05f,"relaxed elbow finishes below its shoulder");
                }
                if (steps)
                {
                    Assert.That(left.position.y, Is.EqualTo(leftGround).Within(.003f), "lead ankle lands at address ground height");
                    Assert.That(right.position.y, Is.EqualTo(rightGround).Within(.003f), "rear ankle lands at address ground height");
                }
                g.Settle(); for (int i=0;i<30;i++) yield return null;
                Assert.IsFalse(g.Watching); var settled=hip.position;
                GolferView.MannerismsOff=true; Evaluate(g); Assert.Less(Vector3.Distance(settled,hip.position),.001f,"no residual post-shot offset");
                Debug.Log($"PostShot {female} {club} load={load}: hips={maxHip:F4}, foot={maxFoot:F4}, maxJointTurn={maxTurn:F3}deg/frame; reset clean");
            }
            finally { GolferView.MannerismsOff=false; Object.Destroy(root); Time.captureFramerate=0; GolferStyle.Body=oldBody; GolferStyle.HeroOverride=oldOverride; }
        }
        // 11-19 review: while the club comes down the shaft stays out of the head envelope (it used to sweep
        // across the face), and at rest the club head is above the turf and clear of both shoes (it sat on the lead foot).
        static void CheckClubClearance(GolferView g, Vector3 origin, bool atRest, ref float heldFinishGap)
        {
            var clearance = typeof(GolferView).GetField("swingClearance", Private).GetValue(g);
            var cf = BindingFlags.Instance | BindingFlags.NonPublic;
            var centre = (Vector3)clearance.GetType().GetField("centre", cf).GetValue(clearance);
            float radius = (float)clearance.GetType().GetField("radius", cf).GetValue(clearance);
            var bones = g.Hero.Bones; var grip = bones["Club"]; var head = bones["Head"];
            var club = g.Hero.Root.GetComponentsInChildren<SkinnedMeshRenderer>(true).FirstOrDefault(r => r.name.StartsWith("CLUB_") && r.gameObject.activeInHierarchy);
            if (!club) return;
            int b = System.Array.FindIndex(club.bones, t => t == grip); Vector3 far = Vector3.zero;
            foreach (var v in club.sharedMesh.vertices) { var q = club.sharedMesh.bindposes[b].MultiplyPoint3x4(v); if (q.sqrMagnitude > far.sqrMagnitude) far = q; }
            Vector3 a = grip.position, tip = grip.TransformPoint(far), c = head.TransformPoint(centre);
            float u = Mathf.Clamp01(Vector3.Dot(c - a, tip - a) / Mathf.Max(1e-6f, (tip - a).sqrMagnitude));
            // The padded envelope (head bounds + 7.5 cm), or the approved held finish's own gap when that is closer
            // (the half-iron finish holds the shaft ~6 cm off the head, inside the padding): never closer than either.
            float gap = Vector3.Distance(c, a + (tip - a) * u), envelope = radius * Mathf.Abs(head.lossyScale.x);
            if (heldFinishGap < 0) heldFinishGap = gap;
            Assert.Greater(gap, Mathf.Min(envelope, heldFinishGap) - .005f, $"lowering shaft stays out of the head envelope (t-finish={Field(g,"watchClock")-Field(g,"finishClock"):F3}s, held gap={heldFinishGap:F4}, grip-head={Vector3.Distance(a,c):F4}, u={u:F2})");
            if (!atRest) return;
            Assert.Greater(tip.y, origin.y - .005f, "resting club head is not under the turf");
            foreach (var n in new[] { "LeftFoot", "RightFoot", "LeftToes", "RightToes" })
                if (bones.TryGetValue(n, out var f)) Assert.Greater(Vector3.ProjectOnPlane(tip - f.position, Vector3.up).magnitude, .15f, $"resting club head clear of {n}");
        }
        static Vector3 ClubTip(GolferView g)
        {
            var grip = g.Hero.Bones["Club"];
            var club = g.Hero.Root.GetComponentsInChildren<SkinnedMeshRenderer>(true).First(r => r.name.StartsWith("CLUB_") && r.gameObject.activeInHierarchy);
            int b = System.Array.FindIndex(club.bones, t => t == grip); Vector3 far = Vector3.zero;
            foreach (var v in club.sharedMesh.vertices) { var q = club.sharedMesh.bindposes[b].MultiplyPoint3x4(v); if (q.sqrMagnitude > far.sqrMagnitude) far = q; }
            return grip.TransformPoint(far);
        }
        // 11-19 review: the next backswing starting mid-lowering fades the post-shot pose out from where the
        // club is; it used to run the lowering arc backwards and whip the club back over the shoulder.
        [UnityTest] public IEnumerator NextAddressMidLoweringDoesNotWhipClubUp()
        {
            var oldBody = GolferStyle.Body; bool? oldOverride = GolferStyle.HeroOverride;
            Time.captureFramerate = 60; GolferStyle.HeroOverride = true; GolferStyle.Body = GolferStyle.BodyKind.Male;
            var root = new GameObject("Post-shot interruption test");
            try
            {
                var g = GolferView.Create(root.transform); g.Stand(Vector3.zero, Vector3.forward); g.SetClub(GolfClub.Driver, false);
                yield return null;
                for (int i = 0; i < 60; i++) { g.ShowLoad((i + 1) / 60f); yield return null; }
                float impact = g.Strike(), elapsed = 0; bool watching = false;
                for (int i = 0; i < 600; i++)
                {
                    if (!watching && elapsed >= impact) { g.WatchShot(() => Vector3.forward * 30 + Vector3.up * 6); watching = true; }
                    yield return null; elapsed += 1f / 60;
                    if (Field(g,"finishClock") >= 0 && Field(g,"watchClock") - Field(g,"finishClock") > 1.8f) break;
                }
                Assert.IsTrue(g.Watching, "still lowering when interrupted");
                float startY = ClubTip(g).y, rise = 0, step = 0; var last = ClubTip(g);
                g.ShowLoad(.01f);
                for (int i = 0; i < 40; i++)
                {
                    yield return null;
                    var tip = ClubTip(g);
                    Assert.Less(tip.y, startY + .30f, $"club head does not swing back up to the finish on the next address (frame {i})");
                    Assert.Less(Vector3.Distance(tip, last), .35f, $"club head has no teleport on the next address (frame {i}; the 0.3 s crossfade itself moves it ~15 cm a frame)");
                    rise = Mathf.Max(rise, tip.y - startY); step = Mathf.Max(step, Vector3.Distance(tip, last)); last = tip;
                }
                Assert.IsFalse(g.Watching);
                Debug.Log($"PostShot interrupt: club head rise={rise:F3} m, max step={step:F3} m/frame");
            }
            finally { Object.Destroy(root); Time.captureFramerate = 0; GolferStyle.Body = oldBody; GolferStyle.HeroOverride = oldOverride; }
        }
        [UnityTest] public IEnumerator MaleDriveSettlesWithSmallSteps() => Check(false,GolfClub.Driver,1,true);
        [UnityTest] public IEnumerator FemaleDriveSettlesWithSmallSteps() => Check(true,GolfClub.Driver,1,true);
        [UnityTest] public IEnumerator HalfIronStaysPlanted() => Check(false,GolfClub.Iron,.5f,false);
        [UnityTest] public IEnumerator ChipStaysPlanted() => Check(true,GolfClub.Chipper,.7f,false);
        [UnityTest] public IEnumerator PuttStaysPlanted() => Check(false,GolfClub.Putter,.7f,false);
    }
}
