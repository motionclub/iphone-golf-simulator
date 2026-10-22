using System.Linq;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Playables;
using GolfArcade.Tennis;

namespace GolfArcade.Tests
{
    /// HAND CLEARANCE (work/hand-clearance): the proxy is fitted from the body and the garments, the solver takes buried hands
    /// out without changing bone lengths, grips or locked contacts, and a bigger garment grows the proxy with no tuning.
    public class HeroClearanceTests
    {
        static GameObject Hero(bool female) { var go = Object.Instantiate(TennisCustomization.HeroBase(female)); go.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity); return go; }
        static AnimationClip Move(bool female, string name) => Resources.LoadAll<AnimationClip>("HeroMoves/" + (female ? "Female" : "Male")).First(c => c.name == name);

        [Test]
        public void ProxyIsFittedForEveryBodyPartAndEnclosesItsOwnSkin([Values(false, true)] bool female)
        {
            var go = Hero(female);
            try
            {
                var look = go.GetComponent<MatchHeroLook>(); var clr = new HeroClearance(look);
                foreach (var part in new[] { HeroClearanceProxy.Part.Pelvis, HeroClearanceProxy.Part.Torso, HeroClearanceProxy.Part.Head, HeroClearanceProxy.Part.Thigh, HeroClearanceProxy.Part.Shin, HeroClearanceProxy.Part.UpperArm, HeroClearanceProxy.Part.Hand, HeroClearanceProxy.Part.Finger })
                    Assert.That(clr.proxy.capsules.Any(c => c != null && c.part == part), part + " proxy");
                Move(female, "Emote_Slump").SampleAnimation(go, .5f);
                clr.proxy.Refresh();
                var baked = new Mesh(); look.body.BakeMesh(baked, true); var v = baked.vertices; var m = Matrix4x4.TRS(look.body.transform.position, look.body.transform.rotation, Vector3.one);
                var src = clr.proxy.sources[0]; int inside = 0, total = 0;
                for (int i = 0; i < v.Length; i += 7)
                {
                    int d = src.dominant[i]; if (d < 0) continue; var c = clr.proxy.capsules[d]; if (c == null || c.part == HeroClearanceProxy.Part.Finger) continue;
                    total++; if (HeroClearanceProxy.Depth(c, m.MultiplyPoint3x4(v[i]), false, out _) > -.004f) inside++;
                }
                // rigid per-bone proxies: skin blended between two bones (hip crease, shoulder) bulges past either in deep poses
                Assert.That(inside / (float)total, Is.GreaterThan(.85f), $"skin within 4 mm of its own proxy: {inside}/{total}");
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void BuriedHandsComeOutWithLengthsAndGripKept([Values(false, true)] bool female)
        {
            var go = Hero(female);
            try
            {
                var look = go.GetComponent<MatchHeroLook>(); var clr = new HeroClearance(look) { Diagnostics = true };
                var clip = Move(female, "Emote_Slump");
                // played as the game plays it: 60 Hz, the solver carrying its state from frame to frame
                float worstBefore = 0, worstAfter = 0; int n = Mathf.CeilToInt(clip.length * 60), clear = 0;
                for (int k = 0; k <= n; k++)
                {
                    clip.SampleAnimation(go, Mathf.Min(clip.length, k / 60f)); clr.proxy.Refresh();
                    var u = look.Bone(HumanBodyBones.RightUpperArm); var l = look.Bone(HumanBodyBones.RightLowerArm); var h = look.Bone(HumanBodyBones.RightHand);
                    float a = Vector3.Distance(u.position, l.position), b = Vector3.Distance(l.position, h.position);
                    worstBefore = Mathf.Max(worstBefore, clr.Measure(false));
                    clr.Solve(HeroClearance.Request.Free, k == 0 ? 0 : 1 / 60f);
                    worstAfter = Mathf.Max(worstAfter, clr.ResidualDepth); if (clr.ResidualDepth < .002f) clear++;
                    Assert.That(Vector3.Distance(u.position, l.position), Is.EqualTo(a).Within(.00002f));
                    Assert.That(Vector3.Distance(l.position, h.position), Is.EqualTo(b).Within(.00002f));
                }
                Assert.That(worstBefore, Is.GreaterThan(.004f), "the slump buries the hands (test premise)");
                Assert.That(worstAfter, Is.LessThan(worstBefore * .25f), "the deepest intrusion at least 4x shallower");
                Assert.That(clear / (float)(n + 1), Is.GreaterThan(.8f), "most frames fully outside the body and clothes proxy");
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void LockedHandsAtContactDoNotMove()
        {
            var go = Hero(false);
            try
            {
                var look = go.GetComponent<MatchHeroLook>(); var driver = go.GetComponent<HeroTennisDriver>(); driver.ResolvePerformanceClips();
                var clr = new HeroClearance(look);
                foreach (var id in new[] { HeroTennisDriver.Clip.Forehand, HeroTennisDriver.Clip.Backhand, HeroTennisDriver.Clip.Serve })
                {
                    var s = driver.slots.First(x => x.id == id); s.clip.SampleAnimation(go, s.contact);
                    var r = look.Bone(HumanBodyBones.RightHand); var lh = look.Bone(HumanBodyBones.LeftHand); var p = r.position; var q = r.rotation; var lp = lh.position;
                    clr.Reset(); clr.Solve(new HeroClearance.Request { travelLeft = 0, travelRight = 0, twoHanded = id == HeroTennisDriver.Clip.Backhand }, 0);
                    Assert.That(Vector3.Distance(p, r.position), Is.LessThan(.00001f), id + " racket hand");
                    Assert.That(Quaternion.Angle(q, r.rotation), Is.LessThan(.05f), id + " racket face");
                    Assert.That(Vector3.Distance(lp, lh.position), Is.LessThan(.00001f), id + " off hand");
                }
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void BakedTrackRoundTripsAndPlaysByTheGraphsWeights()
        {
            var go = Hero(false);
            var graph = UnityEngine.Playables.PlayableGraph.Create("track test");
            try
            {
                var look = go.GetComponent<MatchHeroLook>(); var root = look.animator.transform;
                var clip = Move(false, "Emote_Slump"); var upper = look.Bone(HumanBodyBones.RightUpperArm);
                // a track that turns the right upper arm 10 degrees for the whole clip, written and read back
                var d = Quaternion.AngleAxis(10, Vector3.forward); var q = new Quaternion[3, 1]; for (int f = 0; f < 3; f++) q[f, 0] = d;
                var lib = new HeroClearanceTracks();
                lib.tracks[HeroClearanceTracks.Key(clip)] = new HeroClearanceTracks.Track { key = HeroClearanceTracks.Key(clip), length = clip.length, hz = 2 / clip.length, frames = 3, paths = new[] { HeroClearanceTracks.PathOf(upper, root) }, q = HeroClearanceTracks.Pack(q) };
                var back = HeroClearanceTracks.Read(lib.Write());
                Assert.That(back.Find(clip), Is.Not.Null, "found by clip after the round trip");
                // played at half weight against an untracked pose: half the correction
                var mixer = UnityEngine.Animations.AnimationMixerPlayable.Create(graph, 2);
                var a = UnityEngine.Animations.AnimationClipPlayable.Create(graph, clip); var b = UnityEngine.Animations.AnimationClipPlayable.Create(graph, clip);
                graph.Connect(a, 0, mixer, 0); graph.Connect(b, 0, mixer, 1); mixer.SetInputWeight(0, 1); mixer.SetInputWeight(1, 0);
                UnityEngine.Animations.AnimationPlayableOutput.Create(graph, "pose", look.animator).SetSourcePlayable(mixer);
                graph.SetTimeUpdateMode(UnityEngine.Playables.DirectorUpdateMode.Manual);
                a.SetTime(.5); b.SetTime(.5); graph.Evaluate(0);
                var before = upper.localRotation;
                var player = new HeroClearanceTracks.Player(root, back) { graph = graph };
                player.Apply();
                Assert.That(Quaternion.Angle(before * d, upper.localRotation), Is.LessThan(.05f), "full weight: the whole correction");
                upper.localRotation = before;
                var half = UnityEngine.Animations.AnimationClipPlayable.Create(graph, Move(false, "Emote_Shock"));   // an untracked clip sharing the weight
                graph.Disconnect(mixer, 1); graph.Connect(half, 0, mixer, 1); mixer.SetInputWeight(0, .5f); mixer.SetInputWeight(1, .5f);
                player.Apply();
                Assert.That(Quaternion.Angle(before * Quaternion.Slerp(Quaternion.identity, d, .5f), upper.localRotation), Is.LessThan(.1f), "half weight: half the correction");
                HeroClearanceTracks.Enabled = false; upper.localRotation = before; player.Apply();
                Assert.That(Quaternion.Angle(before, upper.localRotation), Is.LessThan(.001f), "switched off: nothing");
            }
            finally { HeroClearanceTracks.Enabled = true; if (graph.IsValid()) graph.Destroy(); Object.DestroyImmediate(go); }
        }

        [Test]
        public void InstalledTracksMatchTheClipsTheyWereBakedFrom()
        {
            // a clip re-keyed under the same name and length would get the old clip's corrections (10-18: a lifted racket in the
            // locker on a combined build): every installed track carries its clip's fingerprint, and it must still match
            int checkedTracks = 0; var stale = new System.Collections.Generic.List<string>();
            foreach (bool female in new[] { false, true })
                foreach (bool golf in new[] { false, true })
                {
                    var lib = HeroClearanceTracks.For(female, golf); if (lib == null) continue;
                    string sex = female ? "Female" : "Male";
                    var clips = Resources.LoadAll<AnimationClip>("HeroMoves/" + sex).Concat(Resources.LoadAll<AnimationClip>("Tennis/Performance"))
                        .Concat(Resources.LoadAll<AnimationClip>(GolfArcade.Game.HeroGolfer.PathFor(female)));
                    var go = Hero(female);
                    try
                    {
                        var driver = go.GetComponent<HeroTennisDriver>(); if (driver) { driver.ResolvePerformanceClips(); clips = clips.Concat(driver.slots.Where(x => x.clip).Select(x => x.clip)); }
                    }
                    finally { Object.DestroyImmediate(go); }
                    foreach (var c in clips.Distinct())
                    {
                        var t = lib.Find(c); if (t == null || t.source == 0) continue;
                        checkedTracks++;
                        if (HeroClearanceTracks.Fingerprint(c) != t.source) stale.Add($"{HeroClearanceTracks.File(female, golf)}: {t.key}");
                    }
                }
            Assert.That(stale, Is.Empty, "stale clearance tracks (re-bake: work/hand-clearance/tools/full_bake.sh): " + string.Join(", ", stale.Distinct()));
            if (checkedTracks == 0) Assert.Ignore("no fingerprinted tracks installed yet (HCT3)");
        }

        [Test]
        public void ABiggerShirtGrowsTheTorsoProxyWithNoTuning()
        {
            var go = Hero(false);
            try
            {
                var look = go.GetComponent<MatchHeroLook>();
                var clr = new HeroClearance(look);
                var chest = clr.proxy.capsules.First(c => c != null && c.name == "Chest");
                Assert.That(chest.garmentNodes, Is.GreaterThan(0), "the shirt is measured into the chest proxy");
                var top = look.kit.First(k => k && k.name == "Kit_Top"); var mesh = top.sharedMesh;
                var grown = Object.Instantiate(mesh); var v = grown.vertices; var n = grown.normals;
                var bodyV = look.body.sharedMesh.vertices; var rel = look.body.transform.worldToLocalMatrix * top.transform.localToWorldMatrix; var inv = rel.inverse;
                for (int i = 0; i < v.Length; i++)
                {
                    var p = rel.MultiplyPoint3x4(v[i]); int best = 0; float bd = float.MaxValue;
                    for (int j = 0; j < bodyV.Length; j += 3) { float d = (bodyV[j] - p).sqrMagnitude; if (d < bd) { bd = d; best = j; } }
                    v[i] = inv.MultiplyPoint3x4(p + (p - bodyV[best]).normalized * .01f);
                }
                grown.vertices = v; top.sharedMesh = grown;
                var clr2 = new HeroClearance(look);
                var chest2 = clr2.proxy.capsules.First(c => c != null && c.name == "Chest");
                var grew = Enumerable.Range(0, chest.R.Length).Where(i => chest.offset[i] > .002f).Select(i => chest2.R[i] - chest.R[i]).OrderBy(x => x).ToArray();
                float median = grew[grew.Length / 2];
                Assert.That(median, Is.InRange(.006f, .014f), "median growth where the shirt is");
                for (int i = 0; i < chest.Rb.Length; i++) Assert.That(chest2.Rb[i], Is.EqualTo(chest.Rb[i]).Within(1e-6f), "the bare body table is untouched");
                top.sharedMesh = mesh;
            }
            finally { Object.DestroyImmediate(go); }
        }
    }
}
