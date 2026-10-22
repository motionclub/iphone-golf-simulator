#if UNITY_EDITOR
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// CLIPPING AUDIT of the emote set (work/emote-standard/CLIPPING_AUDIT.md). Extra modes of AnimationAudit (this file is a partial of it):
    ///   AA_MODE=emote    per clip, 15 fps: four full-body views + ID passes + both hands + face (as the breakdown), plus
    ///                    hints.json  = hand in body / under cloth, racket in body / under cloth, garment through garment (world + per view pixels)
    ///                    feet.json   = 30 fps shoe contact data (lowest point, verts below the floor, contact-point travel between samples)
    ///   AA_MODE=closeup  AA_JOBS=<jobs.json>: re-render single frames zoomed on a problem (pixel or world point)
    ///   AA_MODE=face     face sweep (moods x blink x gaze x views) per context
    /// Env: AA_OUT AA_CONTEXTS AA_CLIPS (substring list) AA_BD_FPS (15)
    public static partial class AnimationAudit
    {
        // ---------------------------------------------------------------- face
        [DefaultExecutionOrder(1151)]
        public sealed class FaceDrive : MonoBehaviour
        {
            public MatchHeroLook look; public float blink, brow; public Vector2 gaze;
            void LateUpdate() { if (!look) return; look.SetFacePerformance(blink, gaze, brow); HeroFaceReferenceFit.ApplyExpression(look, blink, gaze, brow); }
        }
        static (float blink, float brow) Mood(string bare)
        {
            string n = bare.ToLowerInvariant();
            if (n.Contains("jumpjoy") || n.Contains("fistpump") || n.Contains("victory")) return (.16f, .00065f);
            if (n.Contains("slump") || n.Contains("defeat")) return (.1f, -.0006f);
            if (n.Contains("stomp")) return (.24f, -.0009f);
            if (n.Contains("shock")) return (0, .0011f);
            return (0, 0);
        }
        static string MoodName(string bare)
        {
            string n = bare.ToLowerInvariant();
            if (n.Contains("jumpjoy") || n.Contains("fistpump") || n.Contains("victory")) return "happy";
            if (n.Contains("slump") || n.Contains("defeat")) return "sad";
            if (n.Contains("stomp")) return "angry";
            if (n.Contains("shock")) return "shock";
            return "neutral";
        }

        // head-local camera frame, captured in the reference pose
        sealed class HeadRig { public Transform head; public Vector3 fwdL, upL, centerL; }
        static HeadRig MakeHeadRig(MatchHeroLook look, GameObject root)
        {
            var h = look.Bone(HumanBodyBones.Head); var inv = Quaternion.Inverse(h.rotation);
            var c = look.face ? look.face.bounds.center : h.position + Vector3.up * .08f;
            return new HeadRig { head = h, fwdL = inv * root.transform.forward, upL = inv * Vector3.up, centerL = inv * (c - h.position) };
        }
        static void HeadCam(Camera cam, HeadRig r, float yawDeg, float dist, float fov, int W, int H)
        {
            var target = r.head.position + r.head.rotation * r.centerL;
            var fwd = r.head.rotation * r.fwdL; var up = r.head.rotation * r.upL;
            var dir = Quaternion.AngleAxis(yawDeg, up) * fwd;
            var from = target + dir * dist;
            cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(target - from, up)); cam.fieldOfView = fov; cam.aspect = (float)W / H;
        }

        static void Snap(Camera cam, string path, int W, int H, int q = 92)
        {
            var rt = RenderTexture.GetTemporary(W, H, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Default, 4);
            cam.targetTexture = rt; cam.Render(); cam.targetTexture = null;
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false); var act = RenderTexture.active;
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = act; RenderTexture.ReleaseTemporary(rt);
            File.WriteAllBytes(path, tex.EncodeToJPG(q)); Object.DestroyImmediate(tex);
        }

        // ---------------------------------------------------------------- checks added to the hand check
        sealed class Hint { public string kind, side; public Vector3 c; public float depth; public int n; }
        static string HintJson(Hint h, Camera cam, int W, int H, string key)
        {
            var sp = cam.WorldToViewportPoint(h.c); if (sp.z <= 0) return null;
            return $"{{\"img\":\"{key}\",\"kind\":\"{h.kind}\",\"side\":\"{h.side}\",\"x\":{F(sp.x * W)},\"y\":{F(H - sp.y * H)},\"depth\":{F(h.depth)},\"n\":{h.n},\"wx\":{F(h.c.x)},\"wy\":{F(h.c.y)},\"wz\":{F(h.c.z)}}}";
        }

        /// the racket against the torso / legs / head skin (6 mm) and the garments (10 mm); both arms are excluded (the hands hold it)
        static List<Hint> RacketCheck(Subject s)
        {
            var res = new List<Hint>(); if (s.racketMeshes == null || s.racket == null) return res;
            var inB = new List<(Vector3 p, float d)>(); var inC = new List<(Vector3 p, float d)>();
            foreach (var mf in s.racketMeshes)
            {
                var M = mf.transform.localToWorldMatrix; var vs = mf.sharedMesh.vertices;
                for (int i = 0; i < vs.Length; i += 2)
                {
                    var p = M.MultiplyPoint3x4(vs[i]);
                    int f = s.full.Nearest(p, .04f, t => s.exclTri[0][t] || s.exclTri[1][t], out var q, out var bc);
                    if (f >= 0)
                    {
                        var n = s.bn[s.fullTris[f * 3]] * bc.x + s.bn[s.fullTris[f * 3 + 1]] * bc.y + s.bn[s.fullTris[f * 3 + 2]] * bc.z;
                        float d = Vector3.Dot(p - q, n.normalized); if (d < -.006f) inB.Add((p, -d));
                    }
                    int f2 = s.outerGrid.Nearest(p, .04f, out var q2, out var bc2);
                    if (f2 >= 0)
                    {
                        var n2 = s.clothN[s.clothT[f2 * 3]] * bc2.x + s.clothN[s.clothT[f2 * 3 + 1]] * bc2.y + s.clothN[s.clothT[f2 * 3 + 2]] * bc2.z;
                        if (s.outFlip[f2]) n2 = -n2;
                        float d2 = Vector3.Dot(p - q2, n2.normalized); if (d2 < -.010f) inC.Add((p, -d2));
                    }
                }
            }
            if (inB.Count >= 3) res.Add(new Hint { kind = "racket in body", side = "R", c = inB.Aggregate(Vector3.zero, (a, x) => a + x.p) / inB.Count, depth = inB.Max(x => x.d) * 1000, n = inB.Count });
            if (inC.Count >= 3) res.Add(new Hint { kind = "racket under cloth", side = "R", c = inC.Aggregate(Vector3.zero, (a, x) => a + x.p) / inC.Count, depth = inC.Max(x => x.d) * 1000, n = inC.Count });
            return res;
        }

        /// garment against garment: A's outer-surface edges crossing B's outer surface (each pair once). A hem lying on a waistband always crosses a
        /// little (the reference pose has the same); a pair is flagged when its crossings are far more numerous or deeper than in the reference pose.
        /// depth = the shorter side of the crossing edge (how far a vertex is behind the other surface). Baseline: pair -> (count, max depth).
        static bool Related(string x, string y)
        {
            x = x.Replace("Kit_", ""); y = y.Replace("Kit_", "");
            bool top = x == "Top" && y == "Bottom" || x == "Bottom" && y == "Top";
            bool foot = x.StartsWith("Sock_") && y == "Shoe_" + x.Substring(5) || x.StartsWith("Shoe_") && y == "Sock_" + x.Substring(5);
            return top || foot;
        }
        static List<Hint> PairCheck(Subject s, ref Dictionary<int, (int n, float d)> baseline)
        {
            var res = new List<Hint>(); int K = s.kit.Length;
            var tg = new Grid[K]; var ids = new int[K][];
            for (int k = 0; k < K; k++)
            {
                var tris = s.kitTris[k]; var l = new List<int>();
                for (int f = 0; f < tris.Length / 3; f++) if (s.kitOuterTri[k][f]) l.Add(f);
                tg[k] = new Grid(.03f); tg[k].Build(s.kv[k], tris, l); ids[k] = l.ToArray();
            }
            var now = new Dictionary<int, (int n, float d)>(); var pts = new Dictionary<int, List<Vector3>>();
            for (int a = 0; a < K; a++)
                for (int b = 0; b < K; b++)
                {
                    if (a == b || !Related(s.kit[a].name, s.kit[b].name)) continue;
                    int key = Mathf.Min(a, b) * 16 + Mathf.Max(a, b);
                    var tris = s.kitTris[a]; var kv = s.kv[a]; int n = 0; float md = 0;
                    for (int ii = 0; ii < ids[a].Length; ii += 2)
                    {
                        int f = ids[a][ii];
                        for (int e = 0; e < 2; e++)
                        {
                            var p0 = kv[tris[f * 3 + e]]; var p1 = kv[tris[f * 3 + e + 1]]; var dv = p1 - p0; float len = dv.magnitude; if (len < 1e-5f) continue; dv /= len;
                            float t = tg[b].Ray(p0, dv, len); if (t < 0) continue;
                            n++; md = Mathf.Max(md, Mathf.Min(t, len - t));
                            if (!pts.TryGetValue(key, out var l)) pts[key] = l = new List<Vector3>(); if (l.Count < 400) l.Add(p0 + dv * t);
                        }
                    }
                    now[key] = now.TryGetValue(key, out var o0) ? (o0.n + n, Mathf.Max(o0.d, md)) : (n, md);
                }
            if (baseline == null) { baseline = now; return res; }
            foreach (var kv in now)
            {
                (int n, float d) b0 = baseline.TryGetValue(kv.Key, out var o) ? o : (0, 0f);
                if (kv.Value.n >= 6 && (kv.Value.n > b0.n * 1.8f + 15 || kv.Value.d > b0.d + .006f))
                {
                    int a = kv.Key / 16, b = kv.Key % 16; var l = pts[kv.Key];
                    res.Add(new Hint { kind = $"{s.kit[a].name.Replace("Kit_", "")} intersects {s.kit[b].name.Replace("Kit_", "")}", side = "-", c = l.Aggregate(Vector3.zero, (x, y) => x + y) / l.Count, depth = kv.Value.d * 1000, n = kv.Value.n });
                }
            }
            return res;
        }

        // ---------------------------------------------------------------- feet
        static readonly Mesh[] footMesh = { new Mesh(), new Mesh() };
        static string FootSample(Subject s, Vector3[][] prev, float t, GameObject root, float groundY)
        {
            var parts = new List<string>(); var fwd = root.transform.forward; var right = root.transform.right;
            for (int f = 0; f < 2; f++)
            {
                int k = Array.FindIndex(s.kit, r => r.name.EndsWith(f == 0 ? "Shoe_L" : "Shoe_R"));
                if (k < 0) { parts.Add("null"); continue; }
                Bake(s.kit[k], footMesh[f], out var v, out _);
                float ymin = float.MaxValue; int below = 0; Vector3 cp = Vector3.zero; int nlow = 0;
                foreach (var p in v) if (p.y < ymin) ymin = p.y;
                foreach (var p in v) { if (p.y < groundY - .003f) below++; if (p.y < ymin + .012f) { cp += p; nlow++; } }
                cp /= Mathf.Max(1, nlow);
                float mag = -1, dfw = 0, drt = 0; int nc = 0;
                if (prev[f] != null && prev[f].Length == v.Length)
                {
                    var d = new List<float>(); Vector3 sum = Vector3.zero;
                    for (int i = 0; i < v.Length; i++)
                        if (prev[f][i].y < groundY + .010f && v[i].y < groundY + .014f) { var a = v[i] - prev[f][i]; a.y = 0; d.Add(a.magnitude); sum += a; }
                    nc = d.Count; if (nc >= 8) { d.Sort(); mag = d[nc / 2]; sum /= nc; dfw = Vector3.Dot(sum, fwd); drt = Vector3.Dot(sum, right); }
                }
                prev[f] = v;
                parts.Add($"{{\"ymin\":{F((ymin - groundY) * 1000)},\"below\":{below},\"nc\":{nc},\"mag\":{F(mag * 1000)},\"dfwd\":{F(dfw * 1000)},\"dright\":{F(drt * 1000)},\"cx\":{F(cp.x)},\"cy\":{F(cp.y)},\"cz\":{F(cp.z)}}}");
            }
            return $"{{\"t\":{F(t)},\"L\":{parts[0]},\"R\":{parts[1]}}}";
        }

        // ---------------------------------------------------------------- the emote pass
        static IEnumerator EmoteAudit(string outDir, Camera cam)
        {
            var floor = GameObject.CreatePrimitive(PrimitiveType.Quad); floor.transform.rotation = Quaternion.Euler(90, 0, 0); floor.transform.localScale = Vector3.one * 6;
            var fm = new Material(Shader.Find("Universal Render Pipeline/Lit")); fm.SetColor("_BaseColor", new Color(.30f, .45f, .36f)); floor.GetComponent<Renderer>().sharedMaterial = fm;
            float fps = float.Parse(Env("AA_BD_FPS", "15"), CultureInfo.InvariantCulture);
            foreach (var context in Env("AA_CONTEXTS", "tennis_male,tennis_female,golf_male,golf_female").Split(','))
            {
                bool female = context.EndsWith("female"), golf = context.StartsWith("golf");
                var root = golf ? BuildGolf(female) : BuildTennis(female);
                for (int i = 0; i < 6; i++) yield return null;
                var look = root.GetComponent<MatchHeroLook>();
                foreach (var fp in root.GetComponentsInChildren<MatchHeroFacePerformance>(true)) fp.enabled = false;
                var fd = root.AddComponent<FaceDrive>(); fd.look = look;
                var poser = root.AddComponent<Poser>(); poser.root = root; poser.look = look;
                if (golf) poser.golfClear = new GolfSwingClearance(lastGolfer);
                var probe = root.AddComponent<Probe>();
                var clips = ClipsFor(context, root, female);
                var clubs = root.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("CLUB_")).ToArray();
                string filt = Env("AA_CLIPS", ""); Environment.SetEnvironmentVariable("AA_CLIPS", "");
                var allClips = ClipsFor(context, root, female); Environment.SetEnvironmentVariable("AA_CLIPS", filt);
                var refClip = allClips.FirstOrDefault(c => c.name.Contains("Ready") || c.name.Contains("Idle")).clip ?? allClips[0].clip;
                foreach (var c in clubs) c.gameObject.SetActive(false);
                // the reference pose = the clip list's Ready / Idle when it is in the filtered set, else the first clip's frame 0
                poser.clip = refClip; poser.time = 0; yield return null; yield return null;
                Subject s = null; probe.measure = () => { if (s == null) s = Prepare(context, root); }; yield return null; yield return null;
                if (Env("AA_NATURAL", "1") == "1") NaturalInside(s, cam, floor);
                // baselines of the garment layering, in the reference pose
                Dictionary<int, (int n, float d)> pairBase = null; probe.measure = () => { Bake(s.body, s.bakedBody, out s.bv, out s.bn); for (int k = 0; k < s.kit.Length; k++) Bake(s.kit[k], s.bakedKit[k], out s.kv[k], out s.kn[k]); BuildCloth(s); s.full.Build(s.bv, s.fullTris, Enumerable.Range(0, s.fullTris.Length / 3).ToList()); PairCheck(s, ref pairBase); };
                yield return null; probe.measure = null;
                var headRig = MakeHeadRig(look, root);
                string cdir = Path.Combine(outDir, context); Directory.CreateDirectory(cdir);
                // the ground = the lowest sole point of both shoes in the reference pose
                float groundY = float.MaxValue; probe.measure = () => { for (int f = 0; f < 2; f++) { int kk = Array.FindIndex(s.kit, r => r.name.EndsWith(f == 0 ? "Shoe_L" : "Shoe_R")); if (kk < 0) continue; Bake(s.kit[kk], footMesh[f], out var vv, out _); foreach (var pp in vv) groundY = Mathf.Min(groundY, pp.y); } };
                yield return null; probe.measure = null; if (groundY > 1) groundY = 0;
                File.WriteAllText(Path.Combine(cdir, "ground.json"), "{\"groundY\":" + F(groundY * 1000) + "}\n");
                var index = new List<string>();
                foreach (var (name, clip, racket) in clips)
                {
                    string bare = name.Substring(name.IndexOf(':') + 1);
                    if (s.racket) foreach (var mr in s.racket.GetComponentsInChildren<Renderer>(true)) mr.enabled = racket;
                    foreach (var c in clubs) c.gameObject.SetActive(false);
                    poser.golfSwing = false; poser.golfDrive = false;
                    var (mb, mbr) = Mood(bare); fd.blink = mb; fd.brow = mbr; fd.gaze = Vector2.zero;
                    string safe = name.Replace(":", "_").Replace("/", "_").Replace(" ", "_");
                    string ddir = Path.Combine(cdir, safe); Directory.CreateDirectory(ddir);
                    // ---- feet at 30 fps
                    int nf = Mathf.Max(3, Mathf.CeilToInt(clip.length * 30) + 1); var feet = new List<string>(); var prev = new Vector3[2][];
                    for (int i = 0; i < nf; i++)
                    {
                        float t = clip.length * i / (nf - 1); poser.clip = clip; poser.time = t; string js = null;
                        probe.measure = () => js = FootSample(s, prev, t, root, groundY);
                        yield return null; if (js != null) feet.Add(js);
                    }
                    probe.measure = null;
                    File.WriteAllText(Path.Combine(ddir, "feet.json"), "[\n" + string.Join(",\n", feet) + "\n]\n");
                    // ---- frames at fps
                    int K = Mathf.Clamp(Mathf.RoundToInt(clip.length * fps) + 1, 6, 64); var hints = new List<string>(); var times = new List<string>();
                    for (int k = 0; k < K; k++)
                    {
                        float t = clip.length * k / (K - 1); poser.clip = clip; poser.time = t; times.Add(F(t));
                        yield return null; yield return null;
                        var hk = HandCheck(s);
                        var extra = new List<Hint>();
                        extra.AddRange(hk.Select(x => new Hint { kind = x.kind, side = x.side == 0 ? "L" : "R", c = x.c, depth = x.depth, n = x.n }));
                        if (racket) extra.AddRange(RacketCheck(s));
                        extra.AddRange(PairCheck(s, ref pairBase));
                        var hips = look.Bone(HumanBodyBones.Hips).position; var center = new Vector3(hips.x, .98f, hips.z);
                        var fwd = root.transform.forward; var right = root.transform.right;
                        foreach (var (v, dv) in new[] { ("front", fwd), ("back", -fwd), ("left", -right), ("right", right) })
                        {
                            var from = center + dv * 3.6f + Vector3.up * .25f;
                            cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(center - from)); cam.fieldOfView = 34; cam.aspect = 400f / 560f;
                            Snap(cam, Path.Combine(ddir, $"f{k:00}_{v}.jpg"), 400, 560);
                            IdPass(s, cam, floor, Path.Combine(ddir, $"f{k:00}_{v}_id.png"));
                            foreach (var h in extra) { var js = HintJson(h, cam, 400, 560, $"f{k:00}_{v}"); if (js != null) hints.Add(js); }
                        }
                        foreach (var (hn, hb, sgn) in new[] { ("handL", HumanBodyBones.LeftHand, -1f), ("handR", HumanBodyBones.RightHand, 1f) })
                        {
                            var hand = look.Bone(hb); if (!hand) continue;
                            var mid = hand.position + (hand.position - look.Bone(sgn < 0 ? HumanBodyBones.LeftLowerArm : HumanBodyBones.RightLowerArm).position).normalized * .06f;
                            var chestP = look.Bone(HumanBodyBones.Chest).position;
                            var away = Vector3.ProjectOnPlane(mid - chestP, Vector3.up); if (away.sqrMagnitude < 1e-4f) away = root.transform.right * sgn;
                            var dirv = (away.normalized * .6f + root.transform.forward * .7f + Vector3.up * .25f).normalized;
                            var from = mid + dirv * .85f;
                            cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(mid - from)); cam.fieldOfView = 30; cam.aspect = 240f / 280f;
                            Snap(cam, Path.Combine(ddir, $"f{k:00}_{hn}.jpg"), 240, 280);
                            foreach (var h in extra.Where(x => x.side == (sgn < 0 ? "L" : "R") || x.side == "-")) { var js = HintJson(h, cam, 240, 280, $"f{k:00}_{hn}"); if (js != null) hints.Add(js); }
                        }
                        HeadCam(cam, headRig, 0, .75f, 20, 256, 256); Snap(cam, Path.Combine(ddir, $"f{k:00}_face.jpg"), 256, 256);
                    }
                    File.WriteAllText(Path.Combine(ddir, "hands.json"), "[\n" + string.Join(",\n", hints) + "\n]\n");
                    index.Add($"{{\"clip\":\"{name}\",\"dir\":\"{safe}\",\"frames\":{K},\"length\":{F(clip.length)},\"racket\":{(racket ? "true" : "false")},\"mood\":\"{MoodName(bare)}\",\"times\":[{string.Join(",", times)}]}}");
                    Debug.Log($"[EmoteAudit] {context} {name} frames={K} feet={nf}");
                }
                File.WriteAllText(Path.Combine(cdir, "index.json"), "[\n" + string.Join(",\n", index) + "\n]\n");
                File.WriteAllText(Path.Combine(cdir, "legend.json"), "{\"1\":\"body\"," + string.Join(",", s.kit.Select((r, k) => $"\"{k + 2}\":\"kit:{r.name}\"")) + ",\"9\":\"head\",\"10\":\"prop\"}\n");
                foreach (var b in idCodes.Values) b?.Release(); idCodes.Clear();
                Object.Destroy(root); yield return null;
            }
        }

        static readonly (HumanBodyBones a, HumanBodyBones b)[] AreaSegs = {
            (HumanBodyBones.Hips, HumanBodyBones.Spine), (HumanBodyBones.Spine, HumanBodyBones.Chest), (HumanBodyBones.Chest, HumanBodyBones.Neck), (HumanBodyBones.Neck, HumanBodyBones.Head),
            (HumanBodyBones.LeftShoulder, HumanBodyBones.LeftUpperArm), (HumanBodyBones.RightShoulder, HumanBodyBones.RightUpperArm),
            (HumanBodyBones.LeftUpperArm, HumanBodyBones.LeftLowerArm), (HumanBodyBones.RightUpperArm, HumanBodyBones.RightLowerArm),
            (HumanBodyBones.LeftLowerArm, HumanBodyBones.LeftHand), (HumanBodyBones.RightLowerArm, HumanBodyBones.RightHand),
            (HumanBodyBones.Hips, HumanBodyBones.LeftUpperLeg), (HumanBodyBones.Hips, HumanBodyBones.RightUpperLeg),
            (HumanBodyBones.LeftUpperLeg, HumanBodyBones.LeftLowerLeg), (HumanBodyBones.RightUpperLeg, HumanBodyBones.RightLowerLeg),
            (HumanBodyBones.LeftLowerLeg, HumanBodyBones.LeftFoot), (HumanBodyBones.RightLowerLeg, HumanBodyBones.RightFoot),
            (HumanBodyBones.LeftFoot, HumanBodyBones.LeftToes), (HumanBodyBones.RightFoot, HumanBodyBones.RightToes) };
        static readonly float[] AreaRadius = { .16f, .15f, .17f, .10f, .06f, .06f, .05f, .05f, .04f, .04f, .10f, .10f, .08f, .08f, .05f, .05f, .05f, .05f };
        static readonly string[] AreaNames = { "hips", "waist", "chest", "neckhead", "LShoulder", "RShoulder", "LUpperArm", "RUpperArm", "LForearm", "RForearm", "Lpelvis", "Rpelvis", "LThigh", "RThigh", "LShin", "RShin", "LFoot", "RFoot" };
        /// the body segment nearest the point (or ray): name + distance (m)
        static string Area(MatchHeroLook look, Vector3 pt, Ray? ray, Vector3 around, string skip = "")
        {
            string best = "?"; float bd = 1e9f;
            for (int i = 0; i < AreaSegs.Length; i++)
            {
                var ta = look.Bone(AreaSegs[i].a); var tb = look.Bone(AreaSegs[i].b); if (!ta || !tb) continue;
                string nm = AreaNames[i]; if (skip.Length > 0 && (nm.Contains("Shoulder") || nm.Contains("UpperArm") || nm.Contains("Forearm")) && skip.IndexOf(nm[0]) >= 0) continue;
                Vector3 A = ta.position, B = tb.position; if (i == 3) B = A + (B - A).normalized * .22f;
                float d;
                if (ray.HasValue)
                {
                    // closest approach of the ray to the segment, the ray restricted to within 0.7 m of `around`
                    var o = ray.Value.origin; var u = ray.Value.direction; var v = B - A; var w0 = o - A;
                    float a = Vector3.Dot(u, u), b = Vector3.Dot(u, v), c = Vector3.Dot(v, v), dd = Vector3.Dot(u, w0), e = Vector3.Dot(v, w0);
                    float den = a * c - b * b; float sc = den > 1e-9f ? (b * e - c * dd) / den : 0, tc = den > 1e-9f ? (a * e - b * dd) / den : 0;
                    tc = Mathf.Clamp01(tc); sc = Vector3.Dot(A + v * tc - o, u);
                    float s0 = Vector3.Dot(around - o, u); sc = Mathf.Clamp(sc, s0 - .3f, s0 + .3f);
                    d = (o + u * sc - (A + v * tc)).magnitude - AreaRadius[i];
                }
                else { var v = B - A; float tc = Mathf.Clamp01(Vector3.Dot(pt - A, v) / Mathf.Max(1e-6f, v.sqrMagnitude)); d = (pt - (A + v * tc)).magnitude - AreaRadius[i]; }
                if (d < bd) { bd = d; best = AreaNames[i]; }
            }
            return best + ":" + F((bd + .2f) * 1000);
        }

        // ---------------------------------------------------------------- closeups: jobs.json = [{ctx, clip, t, view, mode:"px"|"world", x, y, wx, wy, wz, fov, w, h, out, face}]
        [Serializable] public sealed class Job { public string ctx, clip, view, mode, @out, skip; public float t, x, y, wx, wy, wz, fov; public int w, h; }
        [Serializable] public sealed class Jobs { public Job[] jobs; }
        static IEnumerator Closeups(string outDir, Camera cam)
        {
            var jobs = JsonUtility.FromJson<Jobs>(File.ReadAllText(Env("AA_JOBS", "jobs.json"))).jobs;
            var floor = GameObject.CreatePrimitive(PrimitiveType.Quad); floor.transform.rotation = Quaternion.Euler(90, 0, 0); floor.transform.localScale = Vector3.one * 6;
            var fm = new Material(Shader.Find("Universal Render Pipeline/Lit")); fm.SetColor("_BaseColor", new Color(.30f, .45f, .36f)); floor.GetComponent<Renderer>().sharedMaterial = fm;
            var areas = new List<string>();
            foreach (var grp in jobs.GroupBy(j => j.ctx))
            {
                string context = grp.Key; bool female = context.EndsWith("female"), golf = context.StartsWith("golf");
                var root = golf ? BuildGolf(female) : BuildTennis(female);
                for (int i = 0; i < 6; i++) yield return null;
                var look = root.GetComponent<MatchHeroLook>();
                foreach (var fp in root.GetComponentsInChildren<MatchHeroFacePerformance>(true)) fp.enabled = false;
                var fd = root.AddComponent<FaceDrive>(); fd.look = look;
                var poser = root.AddComponent<Poser>(); poser.root = root; poser.look = look;
                if (golf) poser.golfClear = new GolfSwingClearance(lastGolfer);
                var clips = ClipsFor(context, root, female);
                var clubs = root.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("CLUB_")).ToArray(); foreach (var c in clubs) c.gameObject.SetActive(false);
                poser.clip = clips[0].clip; poser.time = 0; yield return null; yield return null;
                foreach (var j in grp)
                {
                    var hit = clips.FirstOrDefault(c => c.name == j.clip); if (hit.clip == null) { Debug.LogWarning("[Closeup] no clip " + j.clip); continue; }
                    if (look.racketGrip) foreach (var mr in look.racketGrip.GetComponentsInChildren<Renderer>(true)) mr.enabled = hit.racket;
                    string bare = j.clip.Substring(j.clip.IndexOf(':') + 1); var (mb, mbr) = Mood(bare); fd.blink = mb; fd.brow = mbr;
                    poser.clip = hit.clip; poser.time = j.t; yield return null; yield return null;
                    var hips = look.Bone(HumanBodyBones.Hips).position; var center = new Vector3(hips.x, .98f, hips.z);
                    var fwd = root.transform.forward; var right = root.transform.right;
                    Vector3 dv = j.view == "front" ? fwd : j.view == "back" ? -fwd : j.view == "left" ? -right : right;
                    int W = j.w > 0 ? j.w : 720, H = j.h > 0 ? j.h : 720; float fov = j.fov > 0 ? j.fov : 7f;
                    var from = center + dv * 3.6f + Vector3.up * .25f;
                    if (j.mode == "px")
                    {
                        cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(center - from)); cam.fieldOfView = 34; cam.aspect = 400f / 560f;
                        var ray = cam.ViewportPointToRay(new Vector3(j.x / 400f, 1 - j.y / 560f, 0));
                        areas.Add($"{{\"out\":\"{j.@out}\",\"area\":\"{Area(look, Vector3.zero, ray, center, j.skip ?? "")}\"}}");
                        cam.transform.rotation = Quaternion.LookRotation(ray.direction, Vector3.up); cam.fieldOfView = fov; cam.aspect = (float)W / H;
                    }
                    else
                    {
                        var target = new Vector3(j.wx, j.wy, j.wz);
                        areas.Add($"{{\"out\":\"{j.@out}\",\"area\":\"{Area(look, target, null, center, j.skip ?? "")}\"}}");
                        var f2 = target + dv * 1.2f + Vector3.up * .15f;
                        cam.transform.SetPositionAndRotation(f2, Quaternion.LookRotation(target - f2)); cam.fieldOfView = j.fov > 0 ? j.fov : 24f; cam.aspect = (float)W / H;
                    }
                    Directory.CreateDirectory(Path.GetDirectoryName(Path.Combine(outDir, j.@out)));
                    Snap(cam, Path.Combine(outDir, j.@out), W, H, 94);
                }
                Object.Destroy(root); yield return null;
            }
            File.WriteAllText(Path.Combine(outDir, "areas_" + Env("AA_TAG", "x") + ".json"), "[\n" + string.Join(",\n", areas) + "\n]\n");
        }


        // ---------------------------------------------------------------- loaded assets + rest-pose stills (AA_MODE=loaded)
        static string Jq(string x) => (x ?? "").Replace("\\", "/").Replace("\"", "'");
        static string SrcPath(Mesh m)
        {
            if (!m) return "";
            string p = AssetDatabase.GetAssetPath(m); if (!string.IsNullOrEmpty(p)) return p;
            string n = m.name.Replace(" (cover)", "").Replace("(Clone)", "").Trim();
            var g = AssetDatabase.FindAssets("t:Mesh " + n); return g.Length > 0 ? "~" + AssetDatabase.GUIDToAssetPath(g[0]) : "(runtime mesh, no asset)";
        }
        static IEnumerator Loaded(string outDir, Camera cam)
        {
            var floor = GameObject.CreatePrimitive(PrimitiveType.Quad); floor.transform.rotation = Quaternion.Euler(90, 0, 0); floor.transform.localScale = Vector3.one * 6;
            var fm = new Material(Shader.Find("Universal Render Pipeline/Lit")); fm.SetColor("_BaseColor", new Color(.30f, .45f, .36f)); floor.GetComponent<Renderer>().sharedMaterial = fm;
            var all = new List<string>(); Directory.CreateDirectory(Path.Combine(outDir, "stills"));
            foreach (var context in new[] { "tennis_male", "tennis_female", "golf_male", "golf_female" })
            {
                bool female = context.EndsWith("female"), golf = context.StartsWith("golf");
                var root = golf ? BuildGolf(female) : BuildTennis(female);
                for (int i = 0; i < 6; i++) yield return null;
                var look = root.GetComponent<MatchHeroLook>();
                foreach (var fp in root.GetComponentsInChildren<MatchHeroFacePerformance>(true)) fp.enabled = false;
                var poser = root.AddComponent<Poser>(); poser.root = root; poser.look = look;
                string filt = Env("AA_CLIPS", ""); Environment.SetEnvironmentVariable("AA_CLIPS", "");
                var clips = ClipsFor(context, root, female); Environment.SetEnvironmentVariable("AA_CLIPS", filt);
                var rc = clips.FirstOrDefault(c => c.name.Contains("Ready") || c.name.Contains("Idle")); poser.clip = rc.clip ?? clips[0].clip; poser.time = 0;
                var clubs = root.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("CLUB_")); foreach (var c in clubs) c.gameObject.SetActive(false);
                yield return null; yield return null; yield return null;
                // what is loaded
                string prefabPath = golf ? "(HeroGolfer.Build: " + HeroGolfer.PathFor(female) + ")" : "Assets/Resources/Tennis/Customization/Player" + (female ? "Female" : "Male") + ".prefab";
                all.Add($"{{\"ctx\":\"{context}\",\"role\":\"prefab\",\"name\":\"{Jq(root.name)}\",\"path\":\"{Jq(prefabPath)}\"}}");
                foreach (var r in root.GetComponentsInChildren<Renderer>(true))
                {
                    if (!r.enabled && !(r is SkinnedMeshRenderer)) continue;
                    Mesh m = r is SkinnedMeshRenderer sr ? sr.sharedMesh : (r.GetComponent<MeshFilter>() ? r.GetComponent<MeshFilter>().sharedMesh : null); if (!m) continue;
                    string role = r == look.body ? "body" : r == look.face ? "face" : r.name.StartsWith("Kit_") ? "garment" : "other";
                    var mats = string.Join(";", r.sharedMaterials.Where(x => x).Select(x => x.name + "=" + AssetDatabase.GetAssetPath(x)));
                    all.Add($"{{\"ctx\":\"{context}\",\"role\":\"{role}\",\"name\":\"{Jq(r.name)}\",\"active\":{(r.gameObject.activeInHierarchy && r.enabled ? "true" : "false")},\"mesh\":\"{Jq(m.name)}\",\"verts\":{m.vertexCount},\"path\":\"{Jq(SrcPath(m))}\",\"mats\":\"{Jq(mats)}\"}}");
                }
                foreach (var c in root.GetComponents<MonoBehaviour>()) if (c && (c.GetType().Name.Contains("Polo") || c.GetType().Name.Contains("KitV2") || c.GetType().Name.Contains("Garment") || c.GetType().Name.Contains("SkinNormals")))
                    all.Add($"{{\"ctx\":\"{context}\",\"role\":\"component\",\"name\":\"{c.GetType().Name}\"}}");
                // the same hero as stored on disk: the prefab asset's own renderers and the asset files behind their meshes / materials
                {
                    GameObject src = golf ? Resources.Load<GameObject>(HeroGolfer.PathFor(female)) : AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
                    if (src == null) { string[] rp = { "Hero/golfer_" + (female ? "f" : "m"), HeroGolfer.PathFor(female) }; foreach (var q in rp) { src = Resources.Load<GameObject>(q); if (src) break; } }
                    if (src != null)
                    {
                        all.Add($"{{\"ctx\":\"{context}\",\"role\":\"source\",\"name\":\"{Jq(src.name)}\",\"path\":\"{Jq(AssetDatabase.GetAssetPath(src))}\"}}");
                        foreach (var r in src.GetComponentsInChildren<Renderer>(true))
                        {
                            Mesh m = r is SkinnedMeshRenderer sr2 ? sr2.sharedMesh : (r.GetComponent<MeshFilter>() ? r.GetComponent<MeshFilter>().sharedMesh : null);
                            all.Add($"{{\"ctx\":\"{context}\",\"role\":\"src-renderer\",\"name\":\"{Jq(r.name)}\",\"active\":{(r.gameObject.activeSelf && r.enabled ? "true" : "false")},\"mesh\":\"{Jq(m ? m.name : "")}\",\"path\":\"{Jq(m ? AssetDatabase.GetAssetPath(m) : "")}\",\"mats\":\"{Jq(string.Join(";", r.sharedMaterials.Where(x => x).Select(x => AssetDatabase.GetAssetPath(x))))}\"}}");
                        }
                    }
                }
                // rest-pose stills: full body 3/4 and head front
                var hips = look.Bone(HumanBodyBones.Hips).position; var center = new Vector3(hips.x, .95f, hips.z);
                var fwd = root.transform.forward; var right = root.transform.right;
                var dirv = (fwd * .85f + right * .5f).normalized; var from = center + dirv * 3.4f + Vector3.up * .2f;
                cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(center - from)); cam.fieldOfView = 34; cam.aspect = 640f / 800f;
                Snap(cam, Path.Combine(outDir, "stills", $"rest_{context}_body.jpg"), 640, 800);
                var rig = MakeHeadRig(look, root); HeadCam(cam, rig, 20, .75f, 20, 640, 640); Snap(cam, Path.Combine(outDir, "stills", $"rest_{context}_head.jpg"), 640, 640);
                Object.Destroy(root); yield return null;
            }
            File.WriteAllText(Path.Combine(outDir, "loaded.json"), "[\n" + string.Join(",\n", all) + "\n]\n");
        }

        // ---------------------------------------------------------------- face sweep
        static IEnumerator FaceSweep(string outDir, Camera cam)
        {
            var states = new List<(string name, float blink, float brow, Vector2 gaze)> {
                ("neutral", 0, 0, Vector2.zero), ("happy", .16f, .00065f, Vector2.zero), ("sad", .1f, -.0006f, Vector2.zero), ("angry", .24f, -.0009f, Vector2.zero), ("shock", 0, .0011f, Vector2.zero),
                ("blinkhalf", .5f, 0, Vector2.zero), ("blinkfull", 1, 0, Vector2.zero), ("happy_blink", 1, .00065f, Vector2.zero), ("sad_blink", 1, -.0006f, Vector2.zero), ("angry_blink", 1, -.0009f, Vector2.zero), ("shock_browmax", .3f, .001f, Vector2.zero),
                ("gaze_left", 0, 0, new Vector2(-.0018f, 0)), ("gaze_right", 0, 0, new Vector2(.0018f, 0)), ("gaze_up", 0, 0, new Vector2(0, .0018f)), ("gaze_down", 0, 0, new Vector2(0, -.0018f)),
                ("angry_gaze_down", .24f, -.0009f, new Vector2(0, -.0018f)), ("shock_gaze_up", 0, .0011f, new Vector2(0, .0018f)) };
            foreach (var context in Env("AA_CONTEXTS", "tennis_male,tennis_female,golf_male,golf_female").Split(','))
            {
                bool female = context.EndsWith("female"), golf = context.StartsWith("golf");
                var root = golf ? BuildGolf(female) : BuildTennis(female);
                for (int i = 0; i < 6; i++) yield return null;
                var look = root.GetComponent<MatchHeroLook>();
                foreach (var fp in root.GetComponentsInChildren<MatchHeroFacePerformance>(true)) fp.enabled = false;
                var fd = root.AddComponent<FaceDrive>(); fd.look = look;
                var poser = root.AddComponent<Poser>(); poser.root = root; poser.look = look;
                var clips = ClipsFor(context, root, female);
                poser.clip = clips[0].clip; poser.time = 0; yield return null; yield return null;
                var rig = MakeHeadRig(look, root); string cdir = Path.Combine(outDir, "face_" + context); Directory.CreateDirectory(cdir);
                foreach (var st in states)
                {
                    fd.blink = st.blink; fd.brow = st.brow; fd.gaze = st.gaze; yield return null; yield return null;
                    foreach (var (vn, yaw) in new[] { ("front", 0f), ("l45", -45f), ("r45", 45f), ("side", 90f) })
                    {
                        HeadCam(cam, rig, yaw, .6f, 18, 384, 384); Snap(cam, Path.Combine(cdir, $"{st.name}_{vn}.jpg"), 384, 384);
                    }
                }
                Object.Destroy(root); yield return null;
            }
        }
    }
}
#endif
