using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// HAND CLEARANCE offline output (work/hand-clearance). The SceneKit lobby cannot run Unity code, so it gets the clearance
    /// baked into its clips: the runtime HeroClearance.Solve is run frame by frame at `hz` exactly as continuous playback runs it
    /// (same smoothing), and every transform the pass moved (arm chains, clavicles, a prop that is not under a hand) is written
    /// back as keys. Everything else in the clip is copied unchanged.
    ///
    /// For the lobby re-export (chat 6): in MatchHeroLockerExport, before a clip is exported,
    ///     clip = HeroClearanceBake.Corrected(root, clip, SamplePose);
    /// (SamplePose = the exporter's own pose pipeline; the bake runs the solver after it.) Corrected() caches per hero+clip.
    /// Batch: -executeMethod GolfArcade.EditorTools.HeroClearanceBake.Run   BAKE_OUT=<dir for .anim> BAKE_CONTEXTS=tennis_male,...
    ///        BAKE_CLIPS=<substrings>  BAKE_CHECK=1 (the BAKE gate: baked vs runtime between keys, writes bake-check.json)
    public static class HeroClearanceBake
    {
        /// The per-frame request for a clip time (how far each hand may travel). Default: free hands (lobby emotes / idles).
        public delegate HeroClearance.Request RequestFor(float time);

        /// The lobby's key rate: 120 Hz, so SceneKit's linear interpolation between keys follows the corrected motion within the
        /// BAKE gate's 2 mm (checked against the game's pass at the in-between times).
        public const float LobbyHz = 120;
        public sealed class Result { public AnimationClip clip; public int keys; public List<string> moved = new List<string>(); public double solveMs; }

        static readonly Dictionary<(int, int), AnimationClip> corrected = new Dictionary<(int, int), AnimationClip>();
        public static AnimationClip Corrected(GameObject hero, AnimationClip clip, Action<GameObject, AnimationClip, float> pose = null, RequestFor request = null, float hz = LobbyHz)
        {
            var key = (hero.GetInstanceID(), clip.GetInstanceID());
            if (corrected.TryGetValue(key, out var c) && c) return c;
            c = Bake(hero, clip, pose, request, hz).clip; corrected[key] = c; return c;
        }

        public static Result Bake(GameObject hero, AnimationClip clip, Action<GameObject, AnimationClip, float> pose = null, RequestFor request = null, float hz = 60, HeroClearance clearance = null)
        {
            var look = hero.GetComponent<MatchHeroLook>();
            clearance ??= new HeroClearance(look);
            pose ??= (g, a, t) => a.SampleAnimation(g, t);
            // bake-first: the clip's baked correction track (as the game applies it) + the residual solve
            var tracks = Tracks(look); clearance.Residual = tracks != null;
            request ??= _ => HeroClearance.Request.Free;
            int n = Mathf.Max(1, Mathf.CeilToInt(clip.length * hz));
            var all = hero.GetComponentsInChildren<Transform>(true).Where(t => t != hero.transform && !t.name.Contains("ArmBlend_")).ToArray();
            var raw = new (Vector3 p, Quaternion q)[all.Length];
            var frames = new List<(float t, (Vector3 p, Quaternion q)[] f)>(n + 1); var moved = new bool[all.Length];
            var timer = System.Diagnostics.Stopwatch.StartNew(); clearance.Reset();
            bool deterministic = true;
            (Vector3, Quaternion)[] Eval(float t, float dt)
            {
                pose(hero, clip, t);
                for (int i = 0; i < all.Length; i++) raw[i] = (all[i].localPosition, all[i].localRotation);
                tracks?.ApplyClip(clip, t);
                if (tracks == null || tracks.Coverage < .999f) { clearance.Solve(request(t), dt); deterministic = false; }
                var f = new (Vector3, Quaternion)[all.Length];
                for (int i = 0; i < all.Length; i++)
                {
                    f[i] = (all[i].localPosition, all[i].localRotation);
                    if (!moved[i] && ((all[i].localPosition - raw[i].p).sqrMagnitude > 1e-12f || Quaternion.Angle(all[i].localRotation, raw[i].q) > .001f)) moved[i] = true;
                }
                return f;
            }
            for (int k = 0; k <= n; k++) { float t = Mathf.Min(clip.length, k / hz); frames.Add((t, Eval(t, k == 0 ? 0 : 1 / hz))); }
            // A pure baked clip is a function of time alone: where linear interpolation between two keys misses the true pose by more
            // than ~1 mm (the local rotation error over a 0.6 m chain + the position error), a key goes in between (twice at most).
            for (int pass = 0; pass < 2 && deterministic && tracks != null; pass++)
            {
                var add = new List<(float, (Vector3, Quaternion)[])>();
                for (int k = 0; k + 1 < frames.Count; k++)
                {
                    var (ta, fa) = frames[k]; var (tb, fb) = frames[k + 1]; float tm = (ta + tb) * .5f;
                    var fm = Eval(tm, 0); float err = 0;
                    for (int i = 0; i < all.Length; i++)
                    {
                        if (!moved[i]) continue;
                        float ang = Quaternion.Angle(Quaternion.Slerp(fa[i].q, fb[i].q, .5f), fm[i].Item2) * Mathf.Deg2Rad * .6f;
                        float pos = (Vector3.Lerp(fa[i].p, fb[i].p, .5f) - fm[i].Item1).magnitude;
                        err = Mathf.Max(err, ang + pos);
                    }
                    if (err > .001f) add.Add((tm, fm));
                }
                if (add.Count == 0) break;
                frames.AddRange(add); frames.Sort((x, y) => x.t.CompareTo(y.t));
            }
            timer.Stop();
            var res = new Result { solveMs = timer.Elapsed.TotalMilliseconds };
            var outClip = Object.Instantiate(clip); outClip.name = clip.name; res.clip = outClip;
            for (int i = 0; i < all.Length; i++)
            {
                if (!moved[i]) continue;
                string path = AnimationUtility.CalculateTransformPath(all[i], hero.transform);
                res.moved.Add(path);
                var curves = new AnimationCurve[7]; for (int c = 0; c < 7; c++) curves[c] = new AnimationCurve();
                Quaternion prev = frames[0].f[i].q;
                for (int k = 0; k < frames.Count; k++)
                {
                    float t = frames[k].t;
                    var (p, q) = frames[k].f[i];
                    if (Quaternion.Dot(prev, q) < 0) q = new Quaternion(-q.x, -q.y, -q.z, -q.w); prev = q;
                    curves[0].AddKey(t, q.x); curves[1].AddKey(t, q.y); curves[2].AddKey(t, q.z); curves[3].AddKey(t, q.w);
                    curves[4].AddKey(t, p.x); curves[5].AddKey(t, p.y); curves[6].AddKey(t, p.z);
                }
                // linear between the 60 Hz keys: no overshoot between samples
                foreach (var cv in curves) for (int k = 0; k < cv.length; k++) { AnimationUtility.SetKeyLeftTangentMode(cv, k, AnimationUtility.TangentMode.Linear); AnimationUtility.SetKeyRightTangentMode(cv, k, AnimationUtility.TangentMode.Linear); }
                string[] rot = { "m_LocalRotation.x", "m_LocalRotation.y", "m_LocalRotation.z", "m_LocalRotation.w" }, pos = { "m_LocalPosition.x", "m_LocalPosition.y", "m_LocalPosition.z" };
                // drop Euler-hint curves of the same transform so the quaternion keys are the ones played
                foreach (var b in AnimationUtility.GetCurveBindings(outClip).Where(b => b.path == path && b.type == typeof(Transform) && (b.propertyName.StartsWith("localEulerAngles") || b.propertyName.StartsWith("m_LocalEuler"))).ToArray())
                    AnimationUtility.SetEditorCurve(outClip, b, null);
                for (int c = 0; c < 4; c++) AnimationUtility.SetEditorCurve(outClip, EditorCurveBinding.FloatCurve(path, typeof(Transform), rot[c]), curves[c]);
                for (int c = 0; c < 3; c++) AnimationUtility.SetEditorCurve(outClip, EditorCurveBinding.FloatCurve(path, typeof(Transform), pos[c]), curves[4 + c]);
                res.keys += 7 * frames.Count;
            }
            outClip.EnsureQuaternionContinuity();
            return res;
        }

        /// BAKE gate. The bake is the runtime pass recorded at the game's 60 Hz, so: (a) at every 60 Hz frame the baked clip,
        /// played through the same pose pipeline without the solver, must reproduce the runtime result; (b) between frames
        /// (what the SceneKit lobby interpolates) it is compared with the runtime pass stepped at 120 Hz. Hands, elbows,
        /// fingertips and the prop head, mm. Returns (a) and writes (b) to `between`.
        public static float Compare(GameObject hero, AnimationClip source, AnimationClip baked, Action<GameObject, AnimationClip, float> pose, RequestFor request, float hz, HeroClearance clearance, out string where, out float between)
        {
            var look = hero.GetComponent<MatchHeroLook>();
            var tracks = Tracks(look); clearance.Residual = tracks != null;
            var probes = new[] { HumanBodyBones.LeftHand, HumanBodyBones.RightHand, HumanBodyBones.LeftLowerArm, HumanBodyBones.RightLowerArm, HumanBodyBones.LeftMiddleDistal, HumanBodyBones.RightMiddleDistal }.Select(look.Bone).Where(b => b).ToArray();
            Vector3[] Probe() => probes.Select(b => b.position).Concat(Head(clearance)).ToArray();
            float Diff(Vector3[] x, Vector3[] y, ref string w, float t) { float m = 0; for (int i = 0; i < x.Length && i < y.Length; i++) { float d = Vector3.Distance(x[i], y[i]) * 1000; if (d > m) { m = d; w = $"t={t:0.000} probe {i}"; } } return m; }
            int n = Mathf.Max(1, Mathf.CeilToInt(source.length * hz));
            float atKeys = 0; where = ""; between = 0; string wb = "";
            for (int pass = 0; pass < 2; pass++)
            {
                int sub = pass == 0 ? 1 : 2; clearance.Reset();
                for (int k = 0; k <= n * sub; k++)
                {
                    float t = Mathf.Min(source.length, k / (hz * sub));
                    pose(hero, source, t); tracks?.ApplyClip(source, t); if (tracks == null || tracks.Coverage < .999f) clearance.Solve(request(t), k == 0 ? 0 : 1 / (hz * sub)); var rt = Probe();
                    if (pass == 1 && k % 2 == 0) continue;   // pass (b): only the in-between times
                    pose(hero, baked, t); var bk = Probe();
                    if (pass == 0) atKeys = Mathf.Max(atKeys, Diff(rt, bk, ref where, t)); else between = Mathf.Max(between, Diff(rt, bk, ref wb, t));
                    // (the solver re-reads the clip's pose on every call, so sampling the baked clip in between leaves its state alone)
                }
            }
            where += " | between " + wb;
            return atKeys;
        }
        static HeroClearanceTracks.Player Tracks(MatchHeroLook look)
        {
            var lib = look ? HeroClearanceTracks.For(look.female, look.golfKit) : null;
            if (lib == null) return null;
            var p = new HeroClearanceTracks.Player(HeroClearanceTracks.RootOf(look), lib);
            p.SetArms(look.Bone(HumanBodyBones.LeftUpperArm), look.Bone(HumanBodyBones.LeftLowerArm), look.Bone(HumanBodyBones.LeftHand), look.Bone(HumanBodyBones.RightUpperArm), look.Bone(HumanBodyBones.RightLowerArm), look.Bone(HumanBodyBones.RightHand));
            return p;
        }
        static IEnumerable<Vector3> Head(HeroClearance c)
        {
            var p = c.HeldPropAny(); if (p == null) yield break;
            Vector3 far = p.local[0]; foreach (var l in p.local) if (Vector3.Dot(l, p.axisLocal) > Vector3.Dot(far, p.axisLocal)) far = l;
            yield return p.grip.TransformPoint(far);
        }

        // ---------------------------------------------------------------- batch
        public static void Run()
        {
            EditorUtility.audioMasterMute = true;
            try { Execute(); EditorApplication.Exit(0); }
            catch (Exception e) { Debug.LogException(e); EditorApplication.Exit(1); }
        }
        static string Env(string k, string d) { var v = Environment.GetEnvironmentVariable(k); return string.IsNullOrEmpty(v) ? d : v; }
        static void Execute() => Check(Env("BAKE_OUT", Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "hand-clearance-work/bake")), Env("BAKE_CHECK", "0") == "1");
        /// Bakes the clips (BAKE_CONTEXTS / BAKE_CLIPS) and, with check, compares each baked clip to the runtime pass between keys.
        public static void Check(string outDir, bool check)
        {
            Directory.CreateDirectory(outDir); float hz = LobbyHz;
            var report = new StringBuilder("[\n");
            foreach (var ctx in Env("BAKE_CONTEXTS", "tennis_male,tennis_female").Split(','))
            {
                bool female = ctx.EndsWith("female");
                // the lobby heroes are the tennis prefabs (MatchHeroLockerExport) in edit mode
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Resources/Tennis/Customization/Player" + (female ? "Female" : "Male") + ".prefab");
                var hero = (GameObject)Object.Instantiate(prefab); hero.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
                try
                {
                    var driver = hero.GetComponent<HeroTennisDriver>(); driver.ResolvePerformanceClips();
                    var look = hero.GetComponent<MatchHeroLook>();
                    var clearance = new HeroClearance(look);
                    var clips = driver.slots.Where(s => s.clip).GroupBy(s => s.clip).Select(g => g.First()).ToList();
                    string filter = Env("BAKE_CLIPS", "Ready,IntroWave,EmoteSlump");
                    clips = clips.Where(s => filter.Split(',').Any(f => s.id.ToString().IndexOf(f, StringComparison.OrdinalIgnoreCase) >= 0 || s.clip.name.IndexOf(f, StringComparison.OrdinalIgnoreCase) >= 0)).ToList();
                    foreach (var s in clips)
                    {
                        RequestFor req = HeroTennisDriver.IsEmote(s.id) ? (RequestFor)(_ => HeroClearance.Request.Free) : (_ => HeroClearance.Request.Free);
                        Action<GameObject, AnimationClip, float> pose = (g, a, t) => { a.SampleAnimation(g, t); HeroGripPolish.ApplyGrip(look); };
                        var r = Bake(hero, s.clip, pose, req, hz, clearance);
                        string file = Path.Combine(outDir, $"{(female ? "Female" : "Male")}_{s.id}_clearance.anim");
                        if (file.StartsWith("Assets/")) AssetDatabase.CreateAsset(r.clip, file);
                        float diff = -1, between = -1; string where = "";
                        if (check) diff = Compare(hero, s.clip, r.clip, pose, req, hz, clearance, out where, out between);
                        report.Append($"{{\"ctx\":\"{ctx}\",\"clip\":\"{s.id}\",\"length\":{s.clip.length.ToString("0.###", CultureInfo.InvariantCulture)},\"keys\":{r.keys},\"moved\":{r.moved.Count},\"bakeMs\":{r.solveMs.ToString("0.#", CultureInfo.InvariantCulture)},\"bakedVsRuntimeAtFramesMm\":{diff.ToString("0.###", CultureInfo.InvariantCulture)},\"bakedVsRuntimeBetweenFramesMm\":{between.ToString("0.###", CultureInfo.InvariantCulture)},\"where\":\"{where}\"}},\n");
                        Debug.Log($"[HeroClearanceBake] {ctx} {s.id}: {r.moved.Count} transforms, {r.keys} keys, {r.solveMs:0} ms; baked vs runtime {diff:0.000} mm at frames, {between:0.000} mm between, {where}");
                    }
                }
                finally { Object.DestroyImmediate(hero); }
            }
            File.WriteAllText(Path.Combine(outDir, "bake-check.json"), report.ToString().TrimEnd(',', '\n') + "\n]\n");
            AssetDatabase.SaveAssets();
        }
    }
}
