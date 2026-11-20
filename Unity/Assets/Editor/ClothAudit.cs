#if UNITY_EDITOR
using System; using System.Collections; using System.Collections.Generic; using System.IO; using System.Linq;
using UnityEditor; using UnityEditor.SceneManagement; using UnityEngine;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;
namespace GolfArcade.EditorTools
{
    /// CLOTH AUDIT (work/cloth-rip-1120): films the player's hero during real gameplay from 4 directions and writes a flat
    /// ID pass (skin green, top red, bottom blue, shoes yellow, socks cyan, other kit grey, rest dark, background magenta)
    /// so skin showing through a garment can be counted (audit.py). Works as a passive hook under any film when CA_OUT is set
    /// (golf: CurrentGolfSwingFilm, bowling: BowlingFilm) and has its own tennis driver:
    ///   Unity -batchmode -executeMethod GolfArcade.EditorTools.ClothAudit.RunTennis   env CA_OUT, CA_FEMALE=1, CA_FRAMES (game frames), CA_EVERY
    [InitializeOnLoad] public static class ClothAudit
    {
        const string Flag = "ClothAudit.Tennis";
        static string Out => Environment.GetEnvironmentVariable("CA_OUT");
        static int Every => int.TryParse(Environment.GetEnvironmentVariable("CA_EVERY"), out int e) ? e : 3;
        static int lastFrame = -1, shots; static IEnumerator script; static Camera cam; static RenderTexture idRt, lookRt; static Texture2D tex, lookTex;
static StreamWriter log;
        static ClothAudit() { EditorApplication.update += Tick; }

        public static void RunTennis()
        {
            SessionState.SetBool(Flag, true); EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity"); EditorApplication.isPlaying = true;
        }
        static void Tick()
        {
            if (string.IsNullOrEmpty(Out) || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return;
            lastFrame = Time.frameCount;
            try
            {
                if (SessionState.GetBool(Flag, false))
                {
                    if (script == null) { var g = Object.FindFirstObjectByType<GolfArcade.Tennis.TennisGame>(); if (!g || !g.Initialized) return; script = Tennis(g); }
                    if (!script.MoveNext()) { Finish(0); return; }
                }
                if (Time.frameCount % Every == 0 && Time.frameCount > 20) Capture();
            }
            catch (Exception e) { Debug.LogException(e); if (SessionState.GetBool(Flag, false)) Finish(1); }
        }
        static void Finish(int code)
        {
            SessionState.SetBool(Flag, false); log?.Flush(); Time.captureFramerate = 0; Debug.Log($"[ClothAudit] complete {shots} shots -> {Out}");
            if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false;
        }
        static IEnumerator Tennis(GolfArcade.Tennis.TennisGame game)
        {
            int frames = int.TryParse(Environment.GetEnvironmentVariable("CA_FRAMES"), out int f) ? f : 1800;
            Time.captureFramerate = 60;
            var pres = game.GetComponent<GolfArcade.Tennis.TennisPresentation>(); if (pres) pres.Finish();
            game.SelectCharacter(Environment.GetEnvironmentVariable("CA_FEMALE") == "1"); game.ConfigureMatch(GolfArcade.Tennis.TennisGame.Mode.Campaign, "Nadia", "Nadia", "ROUND"); if (pres) pres.Finish();
            for (int n = 0; n < 30; n++) yield return null;
            game.AutoPlay = true; game.AutoPlayLean = true;
            for (int n = 0; n < frames; n++) yield return null;
        }

        static Material unlitMat, vcolMat;
        static float Depth => float.TryParse(Environment.GetEnvironmentVariable("CA_DEPTH"), out float d) ? d : .02f;
        static Material Unlit() => unlitMat ? unlitMat : unlitMat = new Material(Shader.Find("Universal Render Pipeline/Unlit"));
        static readonly Color Skin = new(0, 1, 0), Top = new(1, 0, 0), Bottom = new(0, 0, 1), Shoe = new(1, 1, 0), Sock = new(0, 1, 1), Kit = new(.6f, .6f, .6f), Rest = new(.25f, .25f, .25f);
        static Color RoleOf(Renderer r)
        {
            string n = r.name.StartsWith("HeroLod ") ? r.name.Substring(8) : r.name;
            if (n == "OriginalSeamFeatures") return Rest;
            if (n.StartsWith("Kit_Top") || n == "Kit_Shirt") return Top;
            if (n.StartsWith("Kit_Bottom") || n == "Kit_Shorts" || n.Contains("Skirt")) return Bottom;
            if (n.StartsWith("Kit_Shoe")) return Shoe;
            if (n.StartsWith("Kit_Sock")) return Sock;
            if (n.StartsWith("Kit_") || n.StartsWith("Acc_")) return Kit;
            string l = n.ToLowerInvariant();
            if (l.Contains("hair") || l.Contains("eye") || l.Contains("iris") || l.Contains("sclera") || l.Contains("pupil") || l.Contains("brow") || l.Contains("lash") || l.Contains("racket") || l.Contains("ball") || l.Contains("club") || l.Contains("catch") || l.Contains("teeth") || l.Contains("tongue")) return Rest;
            return r is SkinnedMeshRenderer ? Skin : Rest;
        }
        static Transform HeroRoot(Renderer top)
        {
            for (var t = top.transform; t; t = t.parent) if (t.GetComponent<Animator>()) return t;
            return top.transform;
        }
        static SkinnedMeshRenderer FindTop()
        {
            var main = Camera.main; var at = main ? main.transform.position : Vector3.zero;
            SkinnedMeshRenderer best = null; float bd = 1e9f;
            foreach (var r in Object.FindObjectsByType<SkinnedMeshRenderer>(FindObjectsSortMode.None))
            {
                if (!r || !r.enabled || !r.gameObject.activeInHierarchy || !r.name.StartsWith("Kit_Top")) continue;
                float d = (r.bounds.center - at).sqrMagnitude; if (d < bd) { bd = d; best = r; }
            }
            return best;
        }
        static readonly Dictionary<int, Mesh> covered = new();
        static Material VCol() { if (vcolMat) return vcolMat; vcolMat = new Material(Shader.Find("Hidden/ClothAuditVCol")); return vcolMat; }
        /// Body copy whose vertex colours say which garment should cover it (measured once, in the hero's current pose):
        /// green = free skin, orange = under the top, purple = under the bottom, azure = under sock/shoe.
        static Mesh CoveredMesh(SkinnedMeshRenderer body, Renderer[] mine)
        {
            int key = body.GetInstanceID();
            if (covered.TryGetValue(key, out var m) && m && body.sharedMesh && m.vertexCount == body.sharedMesh.vertexCount) return m;
            // rest (bind) shape of every mesh in the hero root's space: renderer transforms do not animate, bones do
            var root = body.transform.root; var bw = root.worldToLocalMatrix * body.transform.localToWorldMatrix;
            var bv = body.sharedMesh.vertices; for (int i = 0; i < bv.Length; i++) bv[i] = bw.MultiplyPoint3x4(bv[i]);
            var tris = body.sharedMesh.triangles;
            var bnA = body.sharedMesh.normals; for (int i = 0; i < bnA.Length; i++) bnA[i] = bw.MultiplyVector(bnA[i]).normalized;
            var cols = Enumerable.Repeat(new Color(0, 1, .2f, 1), bv.Length).ToArray();
            var best = Enumerable.Repeat(-1f, bv.Length).ToArray();
            foreach (var g in mine.OfType<SkinnedMeshRenderer>())
            {
                if (g.name.StartsWith("HeroLod") || !g.sharedMesh || !g.sharedMesh.isReadable) continue;
                var role = RoleOf(g); Color tag;
                if (role == Top) tag = new Color(1, .5f, 0); else if (role == Bottom) tag = new Color(.5f, 0, 1); else if (role == Shoe || role == Sock) tag = new Color(0, .5f, 1); else continue;
                var gw = root.worldToLocalMatrix * g.transform.localToWorldMatrix;
                var gv = g.sharedMesh.vertices; var gn = g.sharedMesh.normals;
                for (int i = 0; i < gv.Length; i++) { gv[i] = gw.MultiplyPoint3x4(gv[i]); gn[i] = gw.MultiplyVector(gn[i]).normalized; }
                var depth = GolfArcade.Tennis.KitTuck.Depth(bv, tris, gv, gn, g.sharedMesh.triangles, bnA);
                for (int i = 0; i < bv.Length; i++)
                    if (!float.IsNaN(depth[i]) && depth[i] >= 0 && depth[i] > best[i]) { best[i] = depth[i]; cols[i] = depth[i] >= Depth ? tag : Color.white; }
            }
            m = Object.Instantiate(body.sharedMesh); m.name = body.sharedMesh.name + " (cloth audit)"; m.hideFlags = HideFlags.HideAndDontSave; m.colors = cols;
            covered[key] = m;
            Debug.Log($"[ClothAudit] coverage {body.name}: shallow {cols.Count(c => c.g > .9f && c.r > .9f)} top {cols.Count(c => c.r > .9f && c.g < .9f)} bottom {cols.Count(c => c.b > .9f && c.r > .3f && c.r < .9f)} feet {cols.Count(c => c.b > .9f && c.g > .3f && c.g < .9f)} of {cols.Length}");
            return m;
        }
        static readonly HashSet<int> baked = new();
        /// CA_TUCK_OUT: write KitTuck depth data for this hero's worn kit from its runtime rest meshes (once per hero).
        static void BakeTuck(Transform root)
        {
            string dir = Environment.GetEnvironmentVariable("CA_TUCK_OUT"); if (string.IsNullOrEmpty(dir)) return;
            var look = root.GetComponentInParent<GolfArcade.Tennis.MatchHeroLook>() ?? root.GetComponentInChildren<GolfArcade.Tennis.MatchHeroLook>();
            if (!look || !look.body || look.kit == null || !baked.Add(look.GetInstanceID())) return;
            var src = typeof(GolfArcade.Tennis.MatchHeroLook).GetField("kitV2CoverSource", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic)?.GetValue(look) as Mesh;
            if (!src) src = look.body.sharedMesh;
            var rw = look.transform.worldToLocalMatrix; var bm = rw * look.body.transform.localToWorldMatrix;
            var bv = src.vertices; for (int i = 0; i < bv.Length; i++) bv[i] = bm.MultiplyPoint3x4(bv[i]);
            var bnrm = src.normals; for (int i = 0; i < bnrm.Length; i++) bnrm[i] = bm.MultiplyVector(bnrm[i]).normalized;
            var tris = src.triangles; string sport = look.KitSportFolder, sex = look.female ? "Female" : "Male";
            Directory.CreateDirectory(Path.Combine(dir, sport, sex));
            foreach (var g in look.kit)
            {
                if (!g || !g.enabled || !g.sharedMesh || !g.sharedMesh.isReadable) continue;
                string tag = g.name.Substring(4).Replace("_", ""); if (GolfArcade.Tennis.KitTuck.Cap(tag) <= 0) continue;
                var gm = rw * g.transform.localToWorldMatrix; var gv = g.sharedMesh.vertices; var gn = g.sharedMesh.normals;
                for (int i = 0; i < gv.Length; i++) { gv[i] = gm.MultiplyPoint3x4(gv[i]); gn[i] = gm.MultiplyVector(gn[i]).normalized; }
                var t0 = DateTime.Now; var depth = GolfArcade.Tennis.KitTuck.Depth(bv, tris, gv, gn, g.sharedMesh.triangles, bnrm);
                var file = Path.Combine(dir, sport, sex, $"KitV2_{sport}_{sex}_{tag}_tuck.bytes"); File.WriteAllBytes(file, GolfArcade.Tennis.KitTuck.Encode(depth));
                Debug.Log($"[ClothAudit] tuck {sport} {sex} {tag}: {depth.Count(d => d > 0)} covered, {depth.Count(d => d > .02f)} deep, {(DateTime.Now - t0).TotalMilliseconds:0} ms -> {file}");
            }
        }
        static void Capture()
        {
            var top = FindTop(); if (!top) return;
            var root = HeroRoot(top);
            BakeTuck(root);
            var mine = root.GetComponentsInChildren<Renderer>(false).Where(r => r.enabled && !(r is ParticleSystemRenderer) && !(r is TrailRenderer) && !(r is LineRenderer)).ToArray();
            var mineSet = new HashSet<Renderer>(mine);
            var bottom = mine.FirstOrDefault(r => r.name.StartsWith("Kit_Bottom"));
            var centre = (bottom ? bottom.bounds.center : top.bounds.center - Vector3.up * .35f) + Vector3.up * .12f;
            var main = Camera.main;
            var bearing = main ? Vector3.ProjectOnPlane(main.transform.position - centre, Vector3.up) : -root.forward;
            if (bearing.sqrMagnitude < .01f) bearing = -root.forward; bearing.Normalize();
            if (!cam)
            {
                cam = new GameObject("ClothAudit cam") { hideFlags = HideFlags.HideAndDontSave }.AddComponent<Camera>(); cam.enabled = false;
                var data = cam.gameObject.AddComponent<UniversalAdditionalCameraData>(); data.renderPostProcessing = false; data.antialiasing = AntialiasingMode.None;
                cam.allowMSAA = false; cam.nearClipPlane = .05f; cam.farClipPlane = 50;
                idRt = new RenderTexture(512, 512, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB) { antiAliasing = 1 };
                lookRt = new RenderTexture(640, 640, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB) { antiAliasing = 4 };
                tex = new Texture2D(512, 512, TextureFormat.RGB24, false); lookTex = new Texture2D(640, 640, TextureFormat.RGB24, false);
                Directory.CreateDirectory(Out); log = new StreamWriter(Path.Combine(Out, "shots.csv")) { AutoFlush = false };
                log.WriteLine("shot,frame,time,hero,state");
                foreach (var v in new[] { "back", "front", "left", "right", "look_back", "look_front" }) Directory.CreateDirectory(Path.Combine(Out, v));
            }
            string id = shots.ToString("00000");
            if (shots % 200 == 0) Debug.Log("[ClothAudit] renderers: " + string.Join(" | ", mine.Select(r => $"{r.name}={RoleOf(r)}:{r.GetType().Name}:{string.Join("+", r.sharedMaterials.Select(m => m ? m.shader.name : "null"))}")));
            var views = new (string name, float yaw, float up, float dist)[] { ("back", 0, .75f, 3.1f), ("front", 180, .35f, 3.1f), ("left", 90, .35f, 3.1f), ("right", -90, .35f, 3.1f) };
            bool noId = Environment.GetEnvironmentVariable("CA_NOID") == "1";
            if (Environment.GetEnvironmentVariable("CA_ZERO_SHAPES") == "1")   // debug: garment pose correctives off for this capture
                foreach (var g in mine.OfType<SkinnedMeshRenderer>()) if (g.name.Contains("Kit_Top") && g.sharedMesh) for (int k = 0; k < g.sharedMesh.blendShapeCount; k++) g.SetBlendShapeWeight(k, 0);
            // ID pass
            // other renderers are kept out by the layer mask below; never toggle their enabled flag (re-enabling a body
            // SkinnedMeshRenderer breaks its skin shading in Unity 6000.3: dark streaks, see HeroLod notes)
            var saved = new Dictionary<Renderer, Material[]>(); var blocks = new Dictionary<Renderer, MaterialPropertyBlock>(); var meshes = new Dictionary<SkinnedMeshRenderer, Mesh>();
            foreach (var body in mine.OfType<SkinnedMeshRenderer>().Where(r => !noId && (r.name.StartsWith("Body") || r.name.StartsWith("HeroLod Body"))))
            {
                var cm = CoveredMesh(body, mine); meshes[body] = body.sharedMesh; saved[body] = body.sharedMaterials;
                body.sharedMesh = cm; body.sharedMaterials = Enumerable.Repeat(VCol(), body.sharedMaterials.Length).ToArray();
                if (shots % 200 == 0) Debug.Log($"[ClothAudit] body swap {body.name} mesh={body.sharedMesh.name} subs={cm.subMeshCount} mats={body.sharedMaterials.Length} shader={VCol().shader.name} supported={VCol().shader.isSupported} colors={cm.colors.Length}");
            }
            foreach (var r in mine)
            {
                if (r is SkinnedMeshRenderer sr && meshes.ContainsKey(sr)) continue;
                var c = RoleOf(r); var mats = r.sharedMaterials;
                bool cloth = mats.Length > 0 && mats.All(m => m && m.HasProperty("_ClothAuditColor"));
                if (!cloth) { saved[r] = mats; r.sharedMaterials = Enumerable.Repeat(Unlit(), mats.Length).ToArray(); }
                var orig = new MaterialPropertyBlock(); r.GetPropertyBlock(orig); blocks[r] = orig;
                var work = new MaterialPropertyBlock(); r.GetPropertyBlock(work); work.SetColor("_ClothAuditColor", c); work.SetColor("_BaseColor", c); r.SetPropertyBlock(work);
            }
            var layers = mine.ToDictionary(r => r, r => r.gameObject.layer); foreach (var r in mine) r.gameObject.layer = 31; cam.cullingMask = 1 << 31;
            Shader.SetGlobalFloat("_ClothAuditMode", 1);
            var fog = RenderSettings.fog; RenderSettings.fog = false;
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(1, 0, 1, 1); cam.fieldOfView = 36;
            if (!noId) foreach (var v in views) Render(v, bearing, centre, idRt, tex, Path.Combine(Out, v.name, id + ".png"), true);
            Shader.SetGlobalFloat("_ClothAuditMode", 0); RenderSettings.fog = fog;
            foreach (var kv in layers) kv.Key.gameObject.layer = kv.Value; cam.cullingMask = main ? main.cullingMask : ~0;
            foreach (var kv in saved) kv.Key.sharedMaterials = kv.Value;
            foreach (var kv in meshes) kv.Key.sharedMesh = kv.Value;
            foreach (var kv in blocks) kv.Key.SetPropertyBlock(kv.Value.isEmpty ? null : kv.Value);
            // look pass (what the player sees, same framing)
            if (main) { cam.clearFlags = main.clearFlags; cam.backgroundColor = main.backgroundColor; }
            Render(views[0], bearing, centre, lookRt, lookTex, Path.Combine(Out, "look_back", id + ".jpg"), false);
            Render(views[1], bearing, centre, lookRt, lookTex, Path.Combine(Out, "look_front", id + ".jpg"), false);
            string state = "";
            var anim = root.GetComponentInChildren<Animator>();
            if (anim && anim.runtimeAnimatorController) { var ci = anim.GetCurrentAnimatorClipInfo(0); if (ci.Length > 0) state = ci.OrderByDescending(c => c.weight).First().clip.name; }
            foreach (var p in root.GetComponentsInChildren<Animation>()) foreach (AnimationState s in p) if (p.IsPlaying(s.name) && s.weight > .5f) state = s.name;
            log.WriteLine($"{id},{Time.frameCount},{Time.time:0.000},{root.name},{state}");
            if (++shots % 50 == 0) log.Flush();
        }
        static void Render((string name, float yaw, float up, float dist) v, Vector3 bearing, Vector3 centre, RenderTexture rt, Texture2D t, string file, bool png)
        {
            var dir = Quaternion.AngleAxis(v.yaw, Vector3.up) * bearing;
            var from = centre + dir * v.dist + Vector3.up * v.up;
            cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(centre - from, Vector3.up)); cam.aspect = 1;
            cam.targetTexture = rt; cam.Render(); cam.targetTexture = null;
            var a = RenderTexture.active; RenderTexture.active = rt; t.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0); t.Apply(); RenderTexture.active = a;
            File.WriteAllBytes(file, png ? t.EncodeToPNG() : t.EncodeToJPG(85));
        }
    }
}
#endif
