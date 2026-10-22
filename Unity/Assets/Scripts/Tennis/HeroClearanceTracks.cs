using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

namespace GolfArcade.Tennis
{
    /// HAND CLEARANCE, bake-first (work/hand-clearance). Every authored clip is known ahead of time, so the clearance is solved
    /// offline (AnimationSafetyAudit.Sweep, SWEEP_TRACKS=bake) on every clip x hero x kit, smoothed over time, and stored as a
    /// per-clip correction track: for the few bones the solver moved (clavicles, arm chains, a prop) the local rotation that
    /// takes the game's pose (the clip after the game's own tweaks) to the cleared pose, at 60 Hz.
    ///
    /// At runtime the Player reads which clips the hero's playable graph is playing (weights, times, layer masks), blends their
    /// tracks the same way and applies them; HeroClearance then only solves the residual (blends, transitions, IK aim), which
    /// is clear in almost every frame and exits early. The clips themselves stay untouched (no 3 MB .anim copies), the lobby
    /// export bakes the same track into its keys, and one data file per hero and kit holds them all:
    ///     Resources/HeroClearance/Tracks_<Male|Female>_<Tennis|Golf>.bytes
    public sealed class HeroClearanceTracks
    {
        public sealed class Track
        {
            public string key; public float length, hz; public int frames; public string[] paths; public short[] q;   // frames x bones x (x,y,z,w) * 32767
            /// frames x 2 hands x (x,y,z) in 0.1 mm, hero-root space: where a LOCKED hand (contact, a grip) is meant to be relative
            /// to the game's own hand (a grip slide of up to 1 cm away from the contact instant; 0 at contact). Null: none.
            public short[] slip;
            /// Fingerprint of the clip this track was baked from (curves + keys, Fingerprint()); 0 = unknown (older files). A clip
            /// re-keyed under the same name and length no longer matches: the track is stale and must be re-baked (EditMode test).
            public uint source;
            public Vector3 Slip(int side, float t, bool loop)
            {
                if (slip == null) return Vector3.zero;
                if (loop && length > 0) { t %= length; if (t < 0) t += length; }
                float f = Mathf.Clamp(t * hz, 0, frames - 1); int a = (int)f; int b = Mathf.Min(a + 1, frames - 1); float u = f - a;
                int ia = (a * 2 + side) * 3, ib = (b * 2 + side) * 3; const float m = 1e-4f;
                return Vector3.Lerp(new Vector3(slip[ia], slip[ia + 1], slip[ia + 2]), new Vector3(slip[ib], slip[ib + 1], slip[ib + 2]), u) * m;
            }
            public Quaternion Sample(int bone, float t, bool loop)
            {
                if (loop && length > 0) { t %= length; if (t < 0) t += length; }
                float f = Mathf.Clamp(t * hz, 0, frames - 1); int a = (int)f; int b = Mathf.Min(a + 1, frames - 1); float u = f - a;
                var qa = Read(a, bone); var qb = Read(b, bone);
                if (Quaternion.Dot(qa, qb) < 0) qb = new Quaternion(-qb.x, -qb.y, -qb.z, -qb.w);
                return Quaternion.Normalize(new Quaternion(qa.x + (qb.x - qa.x) * u, qa.y + (qb.y - qa.y) * u, qa.z + (qb.z - qa.z) * u, qa.w + (qb.w - qa.w) * u));
            }
            Quaternion Read(int frame, int bone) { int i = (frame * paths.Length + bone) * 4; const float s = 1f / 32767; return new Quaternion(q[i] * s, q[i + 1] * s, q[i + 2] * s, q[i + 3] * s); }
        }

        /// false: no track is applied anywhere (the sweep's BEFORE / RAW passes, A/B tests)
        public static bool Enabled = true;
        public readonly Dictionary<string, Track> tracks = new Dictionary<string, Track>();
        /// The transform the track paths are relative to (the animator's, as the clips' own paths; the golf rig has no
        /// MatchHeroLook.animator, then the look's own root).
        public static Transform RootOf(MatchHeroLook look) => look.animator ? look.animator.transform : look.transform;
        public static string Key(AnimationClip c) => c.name + "@" + Mathf.RoundToInt(c.length * 1000);
        public static string File(bool female, bool golfKit) => $"Tracks_{(female ? "Female" : "Male")}_{(golfKit ? "Golf" : "Tennis")}";

        static readonly Dictionary<string, HeroClearanceTracks> loaded = new Dictionary<string, HeroClearanceTracks>();
        /// The library for a hero and kit (null when none was baked). Tools may Install a freshly baked one.
        public static HeroClearanceTracks For(bool female, bool golfKit)
        {
            string f = File(female, golfKit);
            if (loaded.TryGetValue(f, out var lib)) return lib;
            var ta = Resources.Load<TextAsset>("HeroClearance/" + f);
            lib = ta ? Read(ta.bytes) : null; loaded[f] = lib; return lib;
        }
        public static void Install(bool female, bool golfKit, HeroClearanceTracks lib) => loaded[File(female, golfKit)] = lib;
        public Track Find(AnimationClip c) => c && tracks.TryGetValue(Key(c), out var t) ? t : null;

        // ---------------------------------------------------------------- file
        public static HeroClearanceTracks Read(byte[] bytes)
        {
            var lib = new HeroClearanceTracks();
            using var r = new BinaryReader(new MemoryStream(bytes), Encoding.UTF8);
            string magic = new string(r.ReadChars(4)); if (magic != "HCT1" && magic != "HCT2" && magic != "HCT3") throw new InvalidDataException("not a clearance track file");
            int n = r.ReadInt32();
            for (int i = 0; i < n; i++)
            {
                var t = new Track { key = r.ReadString(), length = r.ReadSingle(), hz = r.ReadSingle(), frames = r.ReadInt32() };
                t.paths = new string[r.ReadInt32()]; for (int b = 0; b < t.paths.Length; b++) t.paths[b] = r.ReadString();
                t.q = new short[t.frames * t.paths.Length * 4]; for (int k = 0; k < t.q.Length; k++) t.q[k] = r.ReadInt16();
                if (magic != "HCT1" && r.ReadBoolean()) { t.slip = new short[t.frames * 6]; for (int k = 0; k < t.slip.Length; k++) t.slip[k] = r.ReadInt16(); }
                if (magic == "HCT3") t.source = r.ReadUInt32();
                lib.tracks[t.key] = t;
            }
            return lib;
        }
        public byte[] Write()
        {
            var ms = new MemoryStream(); using var w = new BinaryWriter(ms, Encoding.UTF8);
            w.Write("HCT3".ToCharArray()); w.Write(tracks.Count);
            foreach (var t in tracks.Values)
            {
                w.Write(t.key); w.Write(t.length); w.Write(t.hz); w.Write(t.frames);
                w.Write(t.paths.Length); foreach (var p in t.paths) w.Write(p);
                foreach (var s in t.q) w.Write(s);
                w.Write(t.slip != null); if (t.slip != null) foreach (var s in t.slip) w.Write(s);
                w.Write(t.source);
            }
            w.Flush(); return ms.ToArray();
        }
        public static short[] Pack(Quaternion[,] q)   // [frame, bone]
        {
            int f = q.GetLength(0), b = q.GetLength(1); var o = new short[f * b * 4];
            for (int k = 0; k < f; k++)
                for (int j = 0; j < b; j++)
                {
                    var x = Quaternion.Normalize(q[k, j]); if (x.w < 0) x = new Quaternion(-x.x, -x.y, -x.z, -x.w);
                    int i = (k * b + j) * 4;
                    o[i] = (short)Mathf.RoundToInt(x.x * 32767); o[i + 1] = (short)Mathf.RoundToInt(x.y * 32767); o[i + 2] = (short)Mathf.RoundToInt(x.z * 32767); o[i + 3] = (short)Mathf.RoundToInt(x.w * 32767);
                }
            return o;
        }
#if UNITY_EDITOR
        /// The clip's content fingerprint (FNV-1a over every curve binding, key time and value): what a track was baked from.
        public static uint Fingerprint(AnimationClip clip)
        {
            uint h = 2166136261;
            void Mix(int x) { unchecked { h ^= (uint)x; h *= 16777619; } }
            foreach (var b in UnityEditor.AnimationUtility.GetCurveBindings(clip).OrderBy(b => b.path + "/" + b.propertyName, StringComparer.Ordinal))
            {
                foreach (char ch in b.path + "/" + b.propertyName) Mix(ch);
                var curve = UnityEditor.AnimationUtility.GetEditorCurve(clip, b); if (curve == null) continue;
                foreach (var k in curve.keys) { Mix(Mathf.RoundToInt(k.time * 1e4f)); Mix(Mathf.RoundToInt(k.value * 1e4f)); }
            }
            return h == 0 ? 1 : h;
        }
#endif
        public static string PathOf(Transform t, Transform root) { var sb = new StringBuilder(t.name); for (var p = t.parent; p && p != root; p = p.parent) sb.Insert(0, p.name + "/"); return sb.ToString(); }

        // ---------------------------------------------------------------- playback
        /// One per hero: reads the hero's playable graph and applies the blended correction of every clip it is playing.
        public sealed class Player
        {
            readonly Transform root; readonly HeroClearanceTracks lib;
            public PlayableGraph graph;
            /// For a layer mixer (input index, bone): does that layer drive the bone? (the tennis upper-body mask). Null: every layer drives every bone.
            public Func<int, Transform, bool> layerAffects;
            readonly Dictionary<Track, Transform[]> bound = new Dictionary<Track, Transform[]>();
            struct Contribution { public Track track; public float time, weight; public bool loop; public AnimationLayerMixerPlayable layers; public int layer; }
            readonly List<Contribution> active = new List<Contribution>(8);
            readonly Dictionary<Transform, (Vector4 sum, float w)> acc = new Dictionary<Transform, (Vector4, float)>();
            readonly List<Transform> touched = new List<Transform>(32);
            public int Applied { get; private set; }   // bones changed last call (diagnostics)

            public Player(Transform root, HeroClearanceTracks lib) { this.root = root; this.lib = lib; }
            readonly Transform[] arm = new Transform[6];   // L upper, lower, hand, R upper, lower, hand
            /// The arm chains, so a locked hand is held where the game put it (SetArms once; HeroPoseSafety does it).
            public void SetArms(Transform lu, Transform ll, Transform lh, Transform ru, Transform rl, Transform rh) { arm[0] = lu; arm[1] = ll; arm[2] = lh; arm[3] = ru; arm[4] = rl; arm[5] = rh; }
            readonly Vector3[] lockP = new Vector3[2]; readonly Quaternion[] lockR = new Quaternion[2];
            readonly Vector3[] hinge0 = new Vector3[2]; readonly Quaternion[] upper0 = new Quaternion[2], lower0 = new Quaternion[2];
            /// Share of the pose (graph weight on the hand bones) whose clips have a baked track: 1 = a pure baked clip, which is
            /// already cleared and checked against the real meshes, so the residual solve can be skipped (and the result is a
            /// function of time alone, as the lobby bake assumes).
            public float Coverage { get; private set; }
            readonly Vector3[] slipSum = new Vector3[2];
            void Remember()
            {
                for (int s = 0; s < 2; s++)
                {
                    var u = arm[s * 3]; var l = arm[s * 3 + 1]; var h = arm[s * 3 + 2]; if (!u || !l || !h) continue;
                    lockP[s] = h.position; lockR[s] = h.rotation; upper0[s] = u.localRotation; lower0[s] = l.localRotation;
                    hinge0[s] = Vector3.Cross(l.position - u.position, h.position - l.position);
                }
            }
            /// No elbow turns more than 80 degrees about the shoulder-wrist line away from the game's own elbow plane (a flip is
            /// > 90): a continuous clamp, never a switch to the other side.
            const float MaxSwivelFromGame = 80;
            void LimitSwivel()
            {
                for (int s = 0; s < 2; s++)
                {
                    var u = arm[s * 3]; var l = arm[s * 3 + 1]; var h = arm[s * 3 + 2]; if (!u || !l || !h) continue;
                    if (HeroPoseSafety.ClampSwivel(u, l, h, hinge0[s], MaxSwivelFromGame)) FlipsPrevented++;
                }
            }
            public int FlipsPrevented { get; private set; }

            /// Apply the blended correction for what the graph is playing now (after the graph has been evaluated and the game's
            /// own pose tweaks have run; before the residual solve). travel 0..1 per hand as the caller gives the solver: a hand
            /// with travel 0 (racket / club contact, a grip) is put where the game's pose has it plus the track's baked slip (0 at
            /// the contact instant, up to 1 cm in a grip away from it), at every time, between the track's keys too; in between
            /// it is blended. The track's elbow, clavicle and body changes stay; the elbow keeps the game's side.
            public void Apply(float travelLeft = 1, float travelRight = 1)
            {
                Applied = 0;
                Remember();
                Correct();
                if (Applied > 0) { Relock(travelLeft, travelRight); LimitSwivel(); }
            }
            void Relock(float travelLeft, float travelRight)
            {
                for (int s = 0; s < 2; s++)
                {
                    float travel = Mathf.Clamp01(s == 0 ? travelLeft : travelRight); if (travel >= 1) continue;
                    var u = arm[s * 3]; var l = arm[s * 3 + 1]; var h = arm[s * 3 + 2]; if (!u || !l || !h) continue;
                    var locked = lockP[s] + root.TransformVector(Vector3.ClampMagnitude(slipSum[s], .015f));
                    var p = Vector3.Lerp(locked, h.position, travel); var r = Quaternion.Slerp(lockR[s], h.rotation, travel);
                    HeroPoseSafety.Solve(u, l, h, p, hinge0[s]); h.rotation = r;
                }
            }
            void Correct()
            {
                Coverage = 0; slipSum[0] = slipSum[1] = Vector3.zero;
                if (!Enabled || lib == null || !graph.IsValid() || graph.GetOutputCount() == 0) return;
                active.Clear(); bool any = false;
                for (int o = 0; o < graph.GetOutputCount(); o++)
                {
                    var output = graph.GetOutput(o); if (!output.IsOutputValid()) continue;
                    var src = output.GetSourcePlayable(); if (!src.IsValid()) continue;
                    Walk(src, output.GetWeight(), default, -1, ref any);
                }
                if (!any) return;
                // coverage and the locked hands' slip, by the weight the graph gives the hand bones
                float covered = 0, all = 0;
                for (int s = 0; s < 2; s++)
                {
                    var hb = arm[s * 3 + 2]; if (!hb) continue;
                    foreach (var c in active)
                    {
                        float w = c.weight * LayerFactor(c, hb); if (w <= 1e-5f) continue;
                        all += w; if (c.track == null) continue;
                        covered += w; slipSum[s] += c.track.Slip(s, c.time, c.loop) * w;
                    }
                }
                Coverage = all > 1e-5f ? covered / all : 0;
                // the clips this bone's weight comes from (with no track: an identity correction of that weight)
                acc.Clear(); touched.Clear();
                foreach (var c in active)
                {
                    if (c.track == null) continue;
                    var bones = Bind(c.track);
                    for (int b = 0; b < bones.Length; b++)
                    {
                        var t = bones[b]; if (!t || acc.ContainsKey(t)) continue;
                        acc[t] = (Vector4.zero, 0); touched.Add(t);
                    }
                }
                foreach (var t in touched)
                {
                    Vector4 sum = Vector4.zero; float total = 0;
                    foreach (var c in active)
                    {
                        float w = c.weight * LayerFactor(c, t); if (w <= 1e-5f) continue;
                        total += w;
                        int bi = c.track != null ? Array.IndexOf(Bind(c.track), t) : -1;
                        var q = bi >= 0 ? c.track.Sample(bi, c.time, c.loop) : Quaternion.identity;
                        if (q.w < 0) q = new Quaternion(-q.x, -q.y, -q.z, -q.w);
                        sum += new Vector4(q.x, q.y, q.z, q.w) * w;
                    }
                    if (total <= 1e-5f) continue;
                    sum += new Vector4(0, 0, 0, 1) * Mathf.Max(0, 1 - total);   // any weight the graph leaves to the bind pose
                    if (sum.sqrMagnitude < 1e-10f) continue;
                    var d = Quaternion.Normalize(new Quaternion(sum.x, sum.y, sum.z, sum.w));
                    if (Quaternion.Angle(d, Quaternion.identity) < .01f) continue;
                    t.localRotation = t.localRotation * d; Applied++;
                }
            }

            /// Applies one clip's track at a time directly (no graph): the sweep without a graph, the lobby bake.
            public void ApplyClip(AnimationClip clip, float time, float travelLeft = 1, float travelRight = 1)
            {
                Applied = 0; Coverage = 0; slipSum[0] = slipSum[1] = Vector3.zero;
                if (!Enabled || lib == null) return;
                var track = lib.Find(clip); if (track == null) return;
                Coverage = 1; for (int s = 0; s < 2; s++) slipSum[s] = track.Slip(s, time, clip.isLooping);
                Remember();
                var bones = Bind(track);
                for (int b = 0; b < bones.Length; b++) if (bones[b]) { bones[b].localRotation = bones[b].localRotation * track.Sample(b, time, clip.isLooping); Applied++; }
                if (Applied > 0) { Relock(travelLeft, travelRight); LimitSwivel(); }
            }

            float LayerFactor(in Contribution c, Transform bone)
            {
                if (!c.layers.IsValid()) return 1;
                int n = c.layers.GetInputCount(); float f = 1;
                if (c.layer > 0 && layerAffects != null && !layerAffects(c.layer, bone)) return 0;
                if (c.layer > 0) f *= c.layers.GetInputWeight(c.layer);
                for (int l = Mathf.Max(1, c.layer + 1); l < n; l++)
                {
                    if (layerAffects != null && !layerAffects(l, bone)) continue;
                    f *= 1 - Mathf.Clamp01(c.layers.GetInputWeight(l));
                }
                return f;
            }

            void Walk(Playable p, float weight, AnimationLayerMixerPlayable layers, int layer, ref bool any)
            {
                if (weight <= 1e-4f || !p.IsValid()) return;
                var type = p.GetPlayableType();
                if (type == typeof(AnimationClipPlayable))
                {
                    var cp = (AnimationClipPlayable)p; var clip = cp.GetAnimationClip(); if (!clip) return;
                    var track = lib.Find(clip); if (track != null) any = true;
                    active.Add(new Contribution { track = track, time = (float)cp.GetTime(), weight = weight, loop = clip.isLooping, layers = layers, layer = layer });
                    return;
                }
                if (type == typeof(AnimationLayerMixerPlayable))
                {
                    var lm = (AnimationLayerMixerPlayable)p;
                    // a layer's own weight is applied in LayerFactor (it depends on the bone's mask)
                    for (int i = 0; i < p.GetInputCount(); i++) Walk(p.GetInput(i), weight, lm, i, ref any);
                    return;
                }
                if (type == typeof(AnimationMixerPlayable))
                {
                    for (int i = 0; i < p.GetInputCount(); i++) Walk(p.GetInput(i), weight * p.GetInputWeight(i), layers, layer, ref any);
                    return;
                }
                for (int i = 0; i < p.GetInputCount(); i++) Walk(p.GetInput(i), weight * p.GetInputWeight(i), layers, layer, ref any);
            }

            Transform[] Bind(Track t)
            {
                if (bound.TryGetValue(t, out var b)) return b;
                b = new Transform[t.paths.Length]; for (int i = 0; i < b.Length; i++) b[i] = root.Find(t.paths[i]);
                bound[t] = b; return b;
            }
        }
    }
}
