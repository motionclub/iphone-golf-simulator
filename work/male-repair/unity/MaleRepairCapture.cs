#if UNITY_EDITOR
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using GolfArcade.Game;
using GolfArcade.Shot;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// 2026-10-19 chat F (male repair): the male hero inside the running game scene (game lights, world, shaders),
    /// front / 3/4 / back / side, face close-ups, shirt close-up and one swing frame (orbit + the game camera's own view).
    /// MR_SPORT=tennis|golf, MR_OUT=<folder>. Proof only; nothing is saved to any asset.
    [InitializeOnLoad]
    public static class MaleRepairCapture
    {
        const string Flag = "MaleRepairCapture";
        const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
        static readonly Stack<IEnumerator> steps = new();
        static bool started; static int warm;
        static string Out => Environment.GetEnvironmentVariable("MR_OUT");
        static string Sport => Environment.GetEnvironmentVariable("MR_SPORT") ?? "tennis";
        static readonly List<string> log = new();
        static MaleRepairCapture() { EditorApplication.update += Tick; }
        public static void Run()
        {
            Directory.CreateDirectory(Out);
            SessionState.SetBool(Flag, true);
            EditorSceneManager.OpenScene(Sport == "golf" ? "Assets/Scenes/Golf.unity" : "Assets/Scenes/Tennis.unity");
            EditorApplication.isPlaying = true;
        }
        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || ++warm < 60) return;
            try
            {
                if (!started)
                {
                    if (Sport == "golf") { var g = Object.FindFirstObjectByType<GolfGame>(); if (!g || !GolfArcade.Course.HoleView.Current) return; steps.Push(Golf(g)); }
                    else { var t = Object.FindFirstObjectByType<TennisGame>(); if (!t || !t.Initialized) return; steps.Push(Tennis(t)); }
                    started = true;
                }
                while (steps.Count > 0)
                {
                    var s = steps.Peek();
                    if (!s.MoveNext()) { steps.Pop(); continue; }
                    if (s.Current is IEnumerator n) { steps.Push(n); continue; }
                    return;
                }
                Finish(0);
            }
            catch (Exception e) { Debug.LogException(e); log.Add("FAIL " + e); Finish(1); }
        }
        static void Finish(int code)
        {
            File.WriteAllLines(Path.Combine(Out, "log.txt"), log);
            SessionState.SetBool(Flag, false); Time.captureFramerate = 0;
            if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false;
        }
        static IEnumerator Frames(int n) { for (int i = 0; i < n; i++) yield return null; }

        static void Shot(Camera cam, string name, Vector3 from, Vector3 target, float fov, int w, int h)
        {
            cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(target - from)); cam.fieldOfView = fov; cam.aspect = w / (float)h;
            var rt = RenderTexture.GetTemporary(w, h, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Default, 8);
            var prev = cam.targetTexture; var act = RenderTexture.active; var tex = new Texture2D(w, h, TextureFormat.RGB24, false);
            try { cam.targetTexture = rt; cam.Render(); RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, w, h), 0, 0); tex.Apply(); File.WriteAllBytes(Path.Combine(Out, name + ".png"), tex.EncodeToPNG()); }
            finally { cam.targetTexture = prev; RenderTexture.active = act; RenderTexture.ReleaseTemporary(rt); Object.DestroyImmediate(tex); }
        }

        /// Facing from the shoulders: right = R - L, forward = right x up.
        static Vector3 Facing(MatchHeroLook look)
        {
            var r = look.Bone(HumanBodyBones.RightUpperArm).position - look.Bone(HumanBodyBones.LeftUpperArm).position; r.y = 0;
            return Vector3.Cross(r.normalized, Vector3.up).normalized;
        }

        /// The standard set around one posed hero. s = world units per metre (golf world is in yards).
        static void Orbit(Camera cam, MatchHeroLook look, string prefix, bool full)
        {
            float s = look.transform.lossyScale.y;
            var fwd = Facing(look);
            var head = look.Bone(HumanBodyBones.Head).position;
            var hips = look.Bone(HumanBodyBones.Hips).position;
            var feet = look.transform.position;
            var centre = new Vector3(hips.x, (feet.y + head.y + .14f * s) * .5f, hips.z);
            float dist = 4.2f * s, half = (head.y + .14f * s - feet.y) * .58f;
            float fov = 2 * Mathf.Atan(half / dist) * Mathf.Rad2Deg;
            Vector3 At(float yaw, float d, Vector3 t, float up = .05f) => t + Quaternion.AngleAxis(yaw, Vector3.up) * fwd * d + Vector3.up * up * s;
            var views = full ? new[] { ("front", 0f), ("tq", 40f), ("side", 90f), ("back", 180f), ("backtq", 220f) } : new[] { ("tq", 40f), ("back", 200f) };
            foreach (var (v, yaw) in views) Shot(cam, prefix + "_" + v, At(yaw, dist, centre, .1f), centre, fov, 900, 1200);
            if (!full) return;
            var face = head + Vector3.up * .07f * s + fwd * .02f * s;
            float fd = 1.6f * s, ffov = 2 * Mathf.Atan(.17f * s / fd) * Mathf.Rad2Deg;
            Shot(cam, prefix + "_face_front", At(0, fd, face, 0), face, ffov, 900, 900);
            Shot(cam, prefix + "_face_tq", At(35, fd, face, 0), face, ffov, 900, 900);
            var chest = Vector3.Lerp(hips, head, .45f);
            float cd = 2.2f * s, cfov = 2 * Mathf.Atan(.42f * s / cd) * Mathf.Rad2Deg;
            Shot(cam, prefix + "_torso_tq", At(30, cd, chest, .05f), chest, cfov, 900, 900);
            Shot(cam, prefix + "_torso_back", At(200, cd, chest, .05f), chest, cfov, 900, 900);
        }


        static void CoverLog(MatchHeroLook look, string tag)
        {
            var cf = typeof(MatchHeroLook).GetField("kitV2CoverSource", BindingFlags.NonPublic | BindingFlags.Instance);
            var src = cf == null ? null : (Mesh)cf.GetValue(look); var cur = look.body.sharedMesh;
            log.Add($"{tag} body now '{cur.name}' v={cur.vertexCount} t={cur.triangles.Length / 3}; cover source '{(src ? src.name : "none")}' v={(src ? src.vertexCount : 0)} t={(src ? src.triangles.Length / 3 : 0)}");
            foreach (var r in look.kit) if (r) log.Add($"  kit {r.name} enabled={r.enabled} mesh '{r.sharedMesh?.name}'");
        }

        static long TriKey(int a, int b, int c) { if (a > b) (a, b) = (b, a); if (b > c) (b, c) = (c, b); if (a > b) (a, b) = (b, a); return ((long)a << 42) | ((long)b << 21) | (long)c; }
        /// MR_HIDE=1 (golf): every runtime-body triangle (bind pose) that sits inside the trousers / belt / socks / shoes, from the floor to
        /// 3 cm above the belt top (the tucked polo), joins the Bottom hide list (union with today's list). Points are compared in the trousers' mesh space (Z-up).
        static void BuildHide(MatchHeroLook look)
        {
            var cf = typeof(MatchHeroLook).GetField("kitV2CoverSource", BindingFlags.NonPublic | BindingFlags.Instance);
            var src = (Mesh)cf.GetValue(look); var bv = src.vertices;
            SkinnedMeshRenderer P(string n) { foreach (var r in look.kit) if (r && r.name == n) return r; return null; }
            var pants = P("Kit_Bottom");
            // a -> b mesh space through any bone both palettes carry (bind pose: bone-from-mesh)
            Matrix4x4 Map(SkinnedMeshRenderer a, SkinnedMeshRenderer b)
            {
                for (int i = 0; i < a.bones.Length; i++) { if (!a.bones[i]) continue; int j = Array.FindIndex(b.bones, x => x && x.name == a.bones[i].name); if (j >= 0) return b.sharedMesh.bindposes[j].inverse * a.sharedMesh.bindposes[i]; }
                throw new InvalidOperationException("no shared bone " + a.name + " / " + b.name);
            }
            var bodyToPants = Map(look.body, pants);
            var cloth = new List<Vector3>(); var clothN = new List<Vector3>(); float beltTop = float.MinValue;
            foreach (var n in new[] { "Kit_Bottom", "Kit_Belt", "Kit_Sock_L", "Kit_Sock_R", "Kit_Shoe_L", "Kit_Shoe_R", "Kit_Top" })
            {
                var r = P(n); if (!r) continue; var m = Map(r, pants);
                var v = r.sharedMesh.vertices; var nn = r.sharedMesh.normals;
                for (int i = 0; i < v.Length; i++) { var p = m.MultiplyPoint3x4(v[i]); if (n == "Kit_Top" && p.z > 1.10f) continue; cloth.Add(p); clothN.Add(m.MultiplyVector(nn[i]).normalized); if (n == "Kit_Belt") beltTop = Mathf.Max(beltTop, p.z); }
            }
            const float cell = .03f; var grid = new Dictionary<Vector3Int, List<int>>();
            Vector3Int C(Vector3 p) => new Vector3Int(Mathf.FloorToInt(p.x / cell), Mathf.FloorToInt(p.y / cell), Mathf.FloorToInt(p.z / cell));
            for (int i = 0; i < cloth.Count; i++) { var c = C(cloth[i]); if (!grid.TryGetValue(c, out var l)) grid[c] = l = new List<int>(); l.Add(i); }
            var bw = src.boneWeights; var bones = look.body.bones;
            bool Torso(int i) { var w = bw[i]; int b = w.boneIndex0; float m = w.weight0; if (w.weight1 > m) { m = w.weight1; b = w.boneIndex1; } if (w.weight2 > m) { m = w.weight2; b = w.boneIndex2; } if (w.weight3 > m) b = w.boneIndex3;
                string n = bones[b] ? bones[b].name : ""; foreach (var a in new[] { "Arm", "Hand", "Shoulder", "Neck", "Head", "Thumb", "Index", "Middle", "Ring", "Little", "Eye", "Jaw" }) if (n.Contains(a)) return false; return true; }
            var inside = new bool[bv.Length]; int nin = 0;
            for (int i = 0; i < bv.Length; i++)
            {
                var p = bodyToPants.MultiplyPoint3x4(bv[i]); if (p.z > beltTop + .05f) continue;
                if (p.z > beltTop - .004f) { if (Torso(i)) { inside[i] = true; nin++; } continue; }   // the tucked polo always covers 5 cm above the belt top (torso skin, not arms)
                var c = C(p); float best = float.MaxValue; int bi = -1;
                for (int dx = -2; dx <= 2; dx++) for (int dy = -2; dy <= 2; dy++) for (int dz = -2; dz <= 2; dz++)
                    if (grid.TryGetValue(c + new Vector3Int(dx, dy, dz), out var l)) foreach (int k in l) { float d = (cloth[k] - p).sqrMagnitude; if (d < best) { best = d; bi = k; } }
                if (bi >= 0 && best < .06f * .06f && Vector3.Dot(clothN[bi], p - cloth[bi]) < .002f) { inside[i] = true; nin++; }
            }
            var ta = Resources.Load<TextAsset>("Golf/KitsV2/Male/KitV2_Golf_Male_Bottom_hide"); var old = ta.bytes;
            var hide = new HashSet<long>(); var list = new List<int>();
            for (int i = 0; i + 12 <= old.Length; i += 12) { int a = BitConverter.ToInt32(old, i), b = BitConverter.ToInt32(old, i + 4), c = BitConverter.ToInt32(old, i + 8); if (hide.Add(TriKey(a, b, c))) list.AddRange(new[] { a, b, c }); }
            int before = hide.Count, added = 0;
            for (int s = 0; s < src.subMeshCount; s++) { var t = src.GetTriangles(s); for (int i = 0; i < t.Length; i += 3) if (inside[t[i]] && inside[t[i + 1]] && inside[t[i + 2]] && hide.Add(TriKey(t[i], t[i + 1], t[i + 2]))) { list.AddRange(new[] { t[i], t[i + 1], t[i + 2] }); added++; } }
            Directory.CreateDirectory(Path.Combine(Out, "hide"));
            using (var w = new BinaryWriter(File.Create(Path.Combine(Out, "hide", "KitV2_Golf_Male_Bottom_hide.bytes")))) foreach (int i in list) w.Write(i);
            log.Add($"hide: beltTop {beltTop:F4}, inside verts {nin}/{bv.Length}, Bottom hide tris {before} -> {hide.Count} (+{added})");
        }
        static IEnumerator Tennis(TennisGame game)
        {
            Time.captureFramerate = 30;
            HeroGarmentLOD.ForceFullDetail = true;
            var pres = game.GetComponent<TennisPresentation>(); if (pres) pres.Finish();
            game.SelectCharacter(false); yield return Frames(4);
            game.ManualSimulation = true; game.enabled = false;
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
            var cam = game.GameplayCamera; var gamePos = cam.transform.position; var gameRot = cam.transform.rotation; float gameFov = cam.fieldOfView;
            cam.nearClipPlane = .02f;
            var actor = game.Player; actor.enabled = false;
            var driver = actor.GetComponentInChildren<HeroTennisDriver>(); driver.enabled = false;
            var look = driver.matchLook;
            if (look.GetComponent<MatchHeroFacePerformance>() is MatchHeroFacePerformance f) f.ForcedBlink = 0;
            var style = HeroKit.Style.From(2, 0, 0, TennisLook.Kit.From("FFFFFF", "10243D", "FFFFFF", "10243D", 2), 0, false);
            style.SkinTint = HeroKit.Hex("C47A4C");
            game.SetPlayerLook(style); yield return Frames(3);
            foreach (var skin in look.GetComponentsInChildren<SkinnedMeshRenderer>()) { skin.updateWhenOffscreen = true; skin.forceMatrixRecalculationPerRender = true; }
            driver.Sample(HeroTennisDriver.Clip.Ready, .5f); yield return Frames(3);
            log.Add("tennis male ready; scale " + look.transform.lossyScale.y); CoverLog(look, "tennis");
            Orbit(cam, look, "tennis", true);
            foreach (var (clip, name) in new[] { (HeroTennisDriver.Clip.Forehand, "forehand"), (HeroTennisDriver.Clip.Serve, "serve") })
            {
                driver.Sample(clip, driver.ContactOf(clip)); yield return Frames(3);
                Orbit(cam, look, "tennis_" + name, false);
                cam.transform.SetPositionAndRotation(gamePos, gameRot); cam.fieldOfView = gameFov;
                Shot(cam, "tennis_" + name + "_gamecam", gamePos, gamePos + gameRot * Vector3.forward, gameFov, 1280, 720);
                log.Add($"{name} contact {driver.ContactOf(clip):F3}");
            }
        }

        static IEnumerator Golf(GolfGame game)
        {
            Time.captureFramerate = 30;
            yield return Frames(30);
            var golfer = (GolferView)typeof(GolfGame).GetField("golfer", Private).GetValue(game);
            var rigField = typeof(GolfGame).GetField("rig", Private);
            var rig = (CameraRig)rigField.GetValue(game);
            var cam = rig.Camera; var gamePos = cam.transform.position; var gameRot = cam.transform.rotation; float gameFov = cam.fieldOfView;
            game.enabled = false; rig.enabled = false;
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
            cam.nearClipPlane = .02f;
            var hl = new HeroLook { Female = false, Skin = HeroKit.Hex("C47A4C"), HairColor = Color.black, Haircut = (int)HeroGolfer.Haircut.Bald, Shirt = HeroKit.Hex("2E5FB8"), Shorts = HeroKit.Hex("2B2F3A"), Shoes = Color.white };
            var own = typeof(GolferView).GetField("own", Private);
            var gl = own.GetValue(golfer) is GolferView.Look cur ? cur : GolferView.Look.Player; gl.Hero = hl; own.SetValue(golfer, gl);
            golfer.ApplyStyle(); yield return Frames(4);
            golfer.enabled = false;
            var look = golfer.Hero.Root.GetComponent<MatchHeroLook>();
            if (look.GetComponent<MatchHeroFacePerformance>() is MatchHeroFacePerformance f) f.ForcedBlink = 0;
            foreach (var skin in look.GetComponentsInChildren<SkinnedMeshRenderer>()) { skin.updateWhenOffscreen = true; skin.forceMatrixRecalculationPerRender = true; }
            if (Environment.GetEnvironmentVariable("MR_DIAG") == "1")
            {   // diagnostic colours: belt magenta, skin green
                look.SetSkin(Color.green);
                foreach (var r in look.kit) if (r && r.name == "Kit_Belt") foreach (var m in r.materials) { if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", Color.magenta); if (m.HasProperty("_TrimColor")) m.SetColor("_TrimColor", Color.magenta); }
            }
            golfer.SetClub(GolfClub.Driver, false);
            typeof(GolferView).GetField("fade", Private).SetValue(golfer, 0f);
            typeof(GolferView).GetMethod("Weigh", Private).Invoke(golfer, null);
            float Read(string k) => (float)typeof(GolferView).GetField(k, Private).GetValue(golfer);
            var show = typeof(GolferView).GetMethod("Show", Private);
            show.Invoke(golfer, new object[] { 0f }); yield return Frames(3);
            Orbit(cam, look, "golf", true);
            cam.fieldOfView = gameFov; Shot(cam, "golf_address_gamecam", gamePos, gamePos + gameRot * Vector3.forward, gameFov, 1280, 720);
            foreach (var (t, name) in new[] { (Read("TopTime"), "top"), (Read("ImpactTime"), "contact"), (Read("EndTime") * .95f, "finish") })
            {
                show.Invoke(golfer, new object[] { t }); yield return Frames(3);
                Orbit(cam, look, "golf_" + name, false);
                Shot(cam, "golf_" + name + "_gamecam", gamePos, gamePos + gameRot * Vector3.forward, gameFov, 1280, 720);
            }
            log.Add("golf male; scale " + look.transform.lossyScale.y); CoverLog(look, "golf"); if (Environment.GetEnvironmentVariable("MR_HIDE") == "1") BuildHide(look);
        }
    }
}
#endif
