#if UNITY_EDITOR
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// TRAILER film server (private clone only). Stays in play mode and executes shot files dropped into TR_DIR:
    ///   Unity -batchmode -projectPath <clone> -executeMethod GolfArcade.EditorTools.TrailerFilm.Run   TR_SCENE=Tennis TR_DIR=<dir>
    /// <dir>/cmd.json = one Cmd; when it is done the server writes <dir>/done.txt ("ok" or the exception) and waits for the next.
    /// Between takes game time stands still (timeScale 0). A take steps the game `frames` times at 1/fps and renders the listed
    /// cameras through the game's own camera with a film volume (depth of field, bloom, grade) and extra lights.
    [InitializeOnLoad]
    public static class TrailerFilm
    {
        const string Flag = "TrailerFilm";
        const BindingFlags BF = BindingFlags.Instance | BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.FlattenHierarchy;
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

        [Serializable] public class Cmd { public string op = "take"; public string scene; public string path; public string filter; public int depth = 3; public Take take; }
        [Serializable] public class Take
        {
            public string name = "take", outDir; public int frames = 1, warm = 0, fps = 120, every = 1, w = 1920, h = 1080, quality = 95, seed = -1;
            public float ss = 1.5f, timeScale = 1; public int[] only; public Ev[] events; public Cam[] cams; public Lit[] lights; public bool keepLights;
            public Post post; public Env env; public string[] hide, show, trace;
        }
        [Serializable] public class Ev { public int f; public string @do = "call"; public string on = "game", m; public string[] a; public float[] v; public string s; public int until = -100000; }
        [Serializable] public class Cam
        {
            public string name = "a", posAnchor = "world", lookAnchor = "world"; public float posSmooth, lookSmooth; public Key[] keys;
            public float shake, shakeFreq = .6f, aperture = 2.8f, focal = 60, near = .05f, far = -1; public bool dof = true, ease = true; public string focusAnchor; public int from = -100000, to = 100000, every = 0, sub = 1;
        }
        [Serializable] public class Key { public float f; public float[] pos, look; public float fov = 35, roll, focusOffset; }
        [Serializable] public class Lit
        {
            public string name = "L", type = "spot", anchor = "world", lookAnchor; public float[] pos, look, color;
            public float intensity = 1, range = 20, angle = 40, inner = -1, smooth; public bool shadows; public float shadowStrength = 1; public int on = -100000, off = 100000; public float fade = 1;
        }
        [Serializable] public class Post
        {
            public float exposure = 0, contrast = 0, saturation = 0, temperature = 0, tint = 0, bloom = .25f, bloomThreshold = .9f, bloomScatter = .7f, vignette = .25f, ca = 0;
            public float[] filter, lift, gamma, gain, shadows, midtones, highlights; public string tonemap = "aces"; public bool exclusive = true;
        }
        [Serializable] public class Env
        {
            public float mainLight = -1, ambient = -1, shadowDistance = -1, fogDensity = -1, shadowStrength = -1; public float[] mainColor, mainEuler, fogColor, ambientColor;
        }

        static IEnumerator script; static int lastFrame = -1; static string dir; static StringBuilder log = new StringBuilder();
        static Volume volume; static readonly List<Light> filmLights = new List<Light>(); static readonly List<Lit> filmLightSpecs = new List<Lit>();
        static readonly Dictionary<string, string> alias = new Dictionary<string, string>();
        static readonly Dictionary<Light, (float i, Color c, Quaternion r, float s)> lightOrig = new Dictionary<Light, (float, Color, Quaternion, float)>();
        static readonly Dictionary<string, Vector3> smoothed = new Dictionary<string, Vector3>();
        static readonly List<Renderer> hidden = new List<Renderer>(); static readonly List<Behaviour> hiddenB = new List<Behaviour>();
        static UniversalRenderPipelineAsset hq; static bool envSaved; static float ambI; static Color ambC, ambSky, ambEq, ambGr; static bool fog0; static float fogD0; static Color fogC0;
        static readonly List<(Volume v, float w)> otherVolumes = new List<(Volume, float)>();

        static TrailerFilm() { EditorApplication.update += Tick; }
        static string Env_(string k, string d) => Environment.GetEnvironmentVariable(k) ?? d;

        public static void Run()
        {
            script = null; lastFrame = -1;
            string scene = Env_("TR_SCENE", "Tennis");
            EditorSceneManager.OpenScene("Assets/Scenes/" + scene + ".unity");
            EditorUtility.audioMasterMute = true;
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return;
            lastFrame = Time.frameCount;
            if (script == null) { if (!Ready()) return; script = Serve(); }
            try { if (!script.MoveNext()) Quit(0); }
            catch (Exception e) { Debug.LogException(e); Fail(e); script = Serve(); }
        }
        static void Quit(int c) { SessionState.SetBool(Flag, false); Time.captureFramerate = 0; Time.timeScale = 1; if (Application.isBatchMode) EditorApplication.Exit(c); else EditorApplication.isPlaying = false; }
        static void Fail(Exception e) { Time.timeScale = 0; File.WriteAllText(Path.Combine(dir, "log.txt"), log.ToString()); File.WriteAllText(Path.Combine(dir, "done.txt"), "ERROR " + e); }

        // ---------------------------------------------------------------- the game in the scene
        static readonly Dictionary<string, Type> typeCache = new Dictionary<string, Type>(); static Object gameCache;
        static Type FindType(string n)
        {
            if (typeCache.TryGetValue(n, out var hit)) return hit;
            var found = FindTypeSlow(n); typeCache[n] = found; return found;
        }
        static Type FindTypeSlow(string n)
        {
            foreach (var a in AppDomain.CurrentDomain.GetAssemblies())
            {
                Type[] ts; try { ts = a.GetTypes(); } catch (ReflectionTypeLoadException e) { ts = e.Types; }
                foreach (var t in ts) if (t != null && (t.Name == n || t.FullName == n)) return t;
            }
            return null;
        }
        static Object Game()
        {
            if (gameCache) return gameCache;
            foreach (var n in new[] { "TennisGame", "GolfGame", "BowlingGame" }) { var t = FindType(n); if (t == null) continue; var o = Object.FindFirstObjectByType(t); if (o) return gameCache = o; }
            return null;
        }
        static bool Ready()
        {
            var g = Game(); if (!g) return false;
            var init = g.GetType().GetProperty("Initialized", BF); if (init != null) return (bool)init.GetValue(g);
            var swing = g.GetType().GetProperty("Swing", BF); return swing == null || swing.GetValue(g) != null;
        }
        static Camera Cam0()
        {
            var g = Game(); if (g) { var p = g.GetType().GetProperty("GameplayCamera", BF); var c = p?.GetValue(g) as Camera; if (c) return c; }
            return Camera.main;
        }

        // ---------------------------------------------------------------- expressions: game.Player.<HeroTennisDriver>  type:TennisFx  static:TennisVenue  find:Name
        static object Root(string head)
        {
            if (alias.TryGetValue(head, out var ex)) return Eval(ex);
            if (head == "game") return Game();
            if (head == "cam") return Cam0();
            if (head.StartsWith("type:")) { var t = FindType(head.Substring(5)); return t == null ? null : Object.FindFirstObjectByType(t); }
            if (head.StartsWith("static:")) return FindType(head.Substring(7));
            if (head.StartsWith("find:")) return GameObject.Find(head.Substring(5));
            return null;
        }
        static object Eval(string expr)
        {
            var parts = expr.Split('.'); object o = Root(parts[0]);
            for (int i = 1; i < parts.Length && o != null; i++) o = Member(o, parts[i]);
            return o;
        }
        static object Member(object o, string name)
        {
            if (name.StartsWith("<") && name.EndsWith(">"))
            {
                var t = FindType(name.Substring(1, name.Length - 2)); var go = o as GameObject ?? (o as Component)?.gameObject;
                return go && t != null ? go.GetComponentInChildren(t, true) : null;
            }
            if (name.StartsWith("/")) { var tr = o as Transform ?? (o as Component)?.transform ?? (o as GameObject)?.transform; return tr ? Child(tr, name.Substring(1)) : null; }
            bool isType = o is Type; var type = isType ? (Type)o : o.GetType(); object self = isType ? null : o;
            for (var t = type; t != null; t = t.BaseType)
            {
                var f = t.GetField(name, BF | BindingFlags.DeclaredOnly); if (f != null) return f.GetValue(self);
                var p = t.GetProperty(name, BF | BindingFlags.DeclaredOnly); if (p != null) return p.GetValue(self);
                var m = t.GetMethods(BF | BindingFlags.DeclaredOnly).FirstOrDefault(x => x.Name == name && x.GetParameters().Length == 0); if (m != null) return m.Invoke(self, null);
            }
            throw new Exception("no member " + name + " on " + type.Name);
        }
        static Transform Child(Transform t, string contains)
        {
            foreach (var c in t.GetComponentsInChildren<Transform>(true)) if (c.name.IndexOf(contains, StringComparison.OrdinalIgnoreCase) >= 0) return c;
            return null;
        }
        static Transform Bone(Transform root, string bone)
        {
            if (Enum.TryParse<HumanBodyBones>(bone, out var hb))
                foreach (var an in root.GetComponentsInChildren<Animator>()) if (an.isHuman && an.gameObject.activeInHierarchy) { var b = an.GetBoneTransform(hb); if (b) return b; }
            return Child(root, bone);
        }
        static Transform AsTransform(object o) => o as Transform ?? (o as Component)?.transform ?? (o as GameObject)?.transform;

        /// anchor = expr[:Bone][~]   ("~": offsets turn with the transform's yaw).  "world" = origin.
        static Vector3 Point(string anchor, float[] off, out Quaternion frame)
        {
            frame = Quaternion.identity; Vector3 o = off != null && off.Length >= 3 ? new Vector3(off[0], off[1], off[2]) : Vector3.zero;
            if (string.IsNullOrEmpty(anchor) || anchor == "world") return o;
            bool local = anchor.EndsWith("~"); if (local) anchor = anchor.Substring(0, anchor.Length - 1);
            string bone = null; int k = anchor.LastIndexOf(':'); if (k > 0 && !anchor.Substring(0, k).EndsWith("type") && !anchor.Substring(0, k).EndsWith("find") && !anchor.Substring(0, k).EndsWith("static")) { bone = anchor.Substring(k + 1); anchor = anchor.Substring(0, k); }
            object v = Eval(anchor); if (v == null) throw new Exception("anchor not found: " + anchor);
            if (v is Vector3 p) return p + o;
            var t = AsTransform(v); if (!t) throw new Exception("anchor is not a transform: " + anchor);
            Transform b = bone != null ? Bone(t, bone) : t; if (!b) throw new Exception("bone not found: " + bone);
            if (local) { frame = Quaternion.Euler(0, t.eulerAngles.y, 0); return b.position + frame * o; }
            return b.position + o;
        }
        static Vector3 Smooth(string key, Vector3 target, float frames, bool reset)
        {
            if (frames <= 0 || reset || !smoothed.TryGetValue(key, out var s)) { smoothed[key] = target; return target; }
            s = Vector3.Lerp(s, target, 1 - Mathf.Exp(-1f / frames)); smoothed[key] = s; return s;
        }

        // ---------------------------------------------------------------- calls
        static object Convert_(string s, Type t)
        {
            if (t == typeof(string)) return s;
            var nt = Nullable.GetUnderlyingType(t); if (nt != null) return s == "null" ? null : Convert_(s, nt);
            if (s == "null") return null;
            if (t == typeof(float)) return float.Parse(s, Inv);
            if (t == typeof(double)) return double.Parse(s, Inv);
            if (t == typeof(int)) return int.Parse(s, Inv);
            if (t == typeof(bool)) return s == "true" || s == "1";
            if (t.IsEnum) return Enum.Parse(t, s, true);
            if (t == typeof(Vector3))
            {
                if (s.StartsWith("@")) { int plus = s.IndexOf('+'); string an = plus > 0 ? s.Substring(1, plus - 1) : s.Substring(1); var off = plus > 0 ? Floats(s.Substring(plus + 1)) : null; return Point(an, off, out _); }
                var f = Floats(s); return new Vector3(f[0], f[1], f[2]);
            }
            if (t == typeof(Vector2)) { var f = Floats(s); return new Vector2(f[0], f[1]); }
            if (t == typeof(Color)) { var f = Floats(s); return new Color(f[0], f[1], f[2], f.Length > 3 ? f[3] : 1); }
            if (s.StartsWith("=")) return Eval(s.Substring(1));
            if (t.IsArray && t.GetElementType() == typeof(string)) return s.Split('|');
            // a struct / class built from numbers: "6,20" -> new Wind(6,20)
            var nums = s.Split(',');
            foreach (var c in t.GetConstructors(BF)) { var ps = c.GetParameters(); if (ps.Length != nums.Length) continue; try { return c.Invoke(ps.Select((p, i) => Convert_(nums[i], p.ParameterType)).ToArray()); } catch { } }
            throw new Exception("cannot convert '" + s + "' to " + t.Name);
        }
        static float[] Floats(string s) => s.Split(',').Select(x => float.Parse(x, Inv)).ToArray();
        static object Call(string on, string m, string[] a)
        {
            object o = Eval(on); if (o == null) throw new Exception("target not found: " + on);
            a = a ?? new string[0]; bool isType = o is Type; var type = isType ? (Type)o : o.GetType(); object self = isType ? null : o;
            for (var t = type; t != null; t = t.BaseType)
            {
                foreach (var mi in t.GetMethods(BF | BindingFlags.DeclaredOnly).Where(x => x.Name == m))
                {
                    var ps = mi.GetParameters(); if (ps.Length < a.Length || ps.Skip(a.Length).Any(p => !p.HasDefaultValue)) continue;
                    object[] args; try { args = ps.Select((p, i) => i < a.Length ? Convert_(a[i], p.ParameterType) : p.DefaultValue).ToArray(); } catch { continue; }
                    return mi.Invoke(self, args);
                }
                if (a.Length == 1)
                {
                    var f = t.GetField(m, BF | BindingFlags.DeclaredOnly); if (f != null) { f.SetValue(self, Convert_(a[0], f.FieldType)); return null; }
                    var p = t.GetProperty(m, BF | BindingFlags.DeclaredOnly); if (p != null && p.GetSetMethod(true) != null) { p.GetSetMethod(true).Invoke(self, new[] { Convert_(a[0], p.PropertyType) }); return null; }
                }
            }
            if (a.Length == 0) return Member(o, m);
            throw new Exception("no callable " + m + "(" + a.Length + ") on " + type.Name);
        }

        // ---------------------------------------------------------------- the picture
        static void Hq()
        {
            if (hq) return;
            var src = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset; if (!src) return;
            hq = Object.Instantiate(src); hq.name = "TrailerURP";
            var so = new SerializedObject(hq);
            void I(string n, int v) { var p = so.FindProperty(n); if (p != null) p.intValue = v; else log.AppendLine("hq: no " + n); }
            void B(string n, bool v) { var p = so.FindProperty(n); if (p != null) p.boolValue = v; else log.AppendLine("hq: no " + n); }
            I("m_AdditionalLightsPerObjectLimit", 8); B("m_AdditionalLightShadowsSupported", true); I("m_AdditionalLightsShadowmapResolution", 4096);
            I("m_MainLightShadowmapResolution", 4096); I("m_SoftShadowQuality", 3); I("m_HDRColorBufferPrecision", 1); I("m_MSAA", 4); B("m_SupportsHDR", true);
            I("m_ColorGradingLutSize", 32);
            so.ApplyModifiedPropertiesWithoutUndo();
            QualitySettings.renderPipeline = hq; GraphicsSettings.defaultRenderPipeline = hq;
        }
        static void EnsureVolume()
        {
            if (volume) return;
            var go = new GameObject("TrailerVolume"); Object.DontDestroyOnLoad(go);
            volume = go.AddComponent<Volume>(); volume.isGlobal = true; volume.priority = 1000; volume.profile = ScriptableObject.CreateInstance<VolumeProfile>();
            foreach (var t in new[] { typeof(Bloom), typeof(DepthOfField), typeof(Vignette), typeof(ColorAdjustments), typeof(Tonemapping), typeof(WhiteBalance), typeof(ChromaticAberration), typeof(LiftGammaGain), typeof(ShadowsMidtonesHighlights) })
                volume.profile.Add(t, true);
        }
        static Vector4 V4(float[] f, float w) => f != null && f.Length >= 3 ? new Vector4(f[0], f[1], f[2], f.Length > 3 ? f[3] : w) : new Vector4(1, 1, 1, w);
        static Color Col(float[] f, Color d) => f != null && f.Length >= 3 ? new Color(f[0], f[1], f[2], 1) : d;
        static void ApplyPost(Post p)
        {
            EnsureVolume(); if (p == null) p = new Post(); var pr = volume.profile;
            // the scene's own volumes: with `exclusive` only the film volume grades the picture
            if (otherVolumes.Count == 0) foreach (var v in Object.FindObjectsByType<Volume>(FindObjectsSortMode.None)) if (v != volume) otherVolumes.Add((v, v.weight));
            foreach (var (v, w) in otherVolumes) if (v) v.weight = p.exclusive ? 0 : w;
            pr.TryGet(out Bloom bloom); bloom.active = p.bloom > 0; bloom.intensity.Override(p.bloom); bloom.threshold.Override(p.bloomThreshold); bloom.scatter.Override(p.bloomScatter); bloom.highQualityFiltering.Override(true);
            pr.TryGet(out Vignette vig); vig.active = p.vignette > 0; vig.intensity.Override(p.vignette); vig.smoothness.Override(.45f);
            pr.TryGet(out ColorAdjustments ca); ca.postExposure.Override(p.exposure); ca.contrast.Override(p.contrast); ca.saturation.Override(p.saturation); ca.colorFilter.Override(Col(p.filter, Color.white));
            pr.TryGet(out Tonemapping tm); tm.mode.Override(p.tonemap == "aces" ? TonemappingMode.ACES : p.tonemap == "neutral" ? TonemappingMode.Neutral : TonemappingMode.None);
            pr.TryGet(out WhiteBalance wb); wb.temperature.Override(p.temperature); wb.tint.Override(p.tint);
            pr.TryGet(out ChromaticAberration chr); chr.active = p.ca > 0; chr.intensity.Override(p.ca);
            pr.TryGet(out LiftGammaGain lgg); lgg.active = p.lift != null || p.gamma != null || p.gain != null; lgg.lift.Override(V4(p.lift, 0)); lgg.gamma.Override(V4(p.gamma, 0)); lgg.gain.Override(V4(p.gain, 0));
            pr.TryGet(out ShadowsMidtonesHighlights smh); smh.active = p.shadows != null || p.midtones != null || p.highlights != null; smh.shadows.Override(V4(p.shadows, 0)); smh.midtones.Override(V4(p.midtones, 0)); smh.highlights.Override(V4(p.highlights, 0));
        }
        static void ApplyEnv(Env e)
        {
            if (!envSaved) { envSaved = true; ambI = RenderSettings.ambientIntensity; ambC = RenderSettings.ambientLight; ambSky = RenderSettings.ambientSkyColor; ambEq = RenderSettings.ambientEquatorColor; ambGr = RenderSettings.ambientGroundColor; fog0 = RenderSettings.fog; fogD0 = RenderSettings.fogDensity; fogC0 = RenderSettings.fogColor; }
            foreach (var l in Object.FindObjectsByType<Light>(FindObjectsSortMode.None))
            {
                if (filmLights.Contains(l) || l.type != LightType.Directional) continue;
                if (!lightOrig.ContainsKey(l)) lightOrig[l] = (l.intensity, l.color, l.transform.rotation, l.shadowStrength);
                var o = lightOrig[l];
                l.intensity = e != null && e.mainLight >= 0 ? o.i * e.mainLight : o.i;
                l.color = e != null && e.mainColor != null ? Col(e.mainColor, o.c) : o.c;
                l.transform.rotation = e != null && e.mainEuler != null && e.mainEuler.Length >= 3 ? Quaternion.Euler(e.mainEuler[0], e.mainEuler[1], e.mainEuler[2]) : o.r;
                l.shadowStrength = e != null && e.shadowStrength >= 0 ? e.shadowStrength : o.s;
            }
            float k = e != null && e.ambient >= 0 ? e.ambient : 1;
            RenderSettings.ambientIntensity = ambI * k; RenderSettings.ambientLight = (e != null && e.ambientColor != null ? Col(e.ambientColor, ambC) : ambC) * k;
            RenderSettings.ambientSkyColor = ambSky * k; RenderSettings.ambientEquatorColor = ambEq * k; RenderSettings.ambientGroundColor = ambGr * k;
            if (e != null && e.fogDensity >= 0) { RenderSettings.fog = e.fogDensity > 0; RenderSettings.fogMode = FogMode.ExponentialSquared; RenderSettings.fogDensity = e.fogDensity; RenderSettings.fogColor = Col(e.fogColor, fogC0); }
            else { RenderSettings.fog = fog0; RenderSettings.fogDensity = fogD0; RenderSettings.fogColor = fogC0; }
            if (hq) hq.shadowDistance = e != null && e.shadowDistance > 0 ? e.shadowDistance : 60;
        }
        static void BuildLights(Take t)
        {
            if (t.keepLights) return;
            foreach (var l in filmLights) if (l) Object.Destroy(l.gameObject); filmLights.Clear(); filmLightSpecs.Clear();
            if (t.lights == null) return;
            foreach (var s in t.lights)
            {
                var go = new GameObject("TrailerLight " + s.name); var l = go.AddComponent<Light>();
                l.type = s.type == "point" ? LightType.Point : s.type == "dir" ? LightType.Directional : LightType.Spot;
                l.color = Col(s.color, Color.white); l.intensity = s.intensity; l.range = s.range; l.spotAngle = s.angle; l.innerSpotAngle = s.inner >= 0 ? s.inner : s.angle * .6f;
                l.shadows = s.shadows ? LightShadows.Soft : LightShadows.None; l.shadowStrength = s.shadowStrength; l.shadowBias = .02f; l.shadowNormalBias = .3f; l.renderMode = LightRenderMode.ForcePixel;
                var d = go.AddComponent<UniversalAdditionalLightData>(); d.softShadowQuality = SoftShadowQuality.High;
                filmLights.Add(l); filmLightSpecs.Add(s);
            }
        }
        static void PlaceLights(bool reset)
        {
            for (int i = 0; i < filmLights.Count; i++)
            {
                var s = filmLightSpecs[i]; var l = filmLights[i]; if (!l) continue;
                l.intensity = s.intensity * Mathf.Clamp01((curFrame - s.on + 1) / Mathf.Max(1f, s.fade)) * Mathf.Clamp01((s.off - curFrame) / Mathf.Max(1f, s.fade));
                var p = Smooth("L" + i, Point(s.anchor, s.pos, out _), s.smooth, reset); l.transform.position = p;
                if (l.type != LightType.Point) { var at = Smooth("LL" + i, Point(s.lookAnchor ?? s.anchor, s.look, out _), s.smooth, reset); if ((at - p).sqrMagnitude > 1e-6f) l.transform.rotation = Quaternion.LookRotation(at - p); }
            }
        }
        static void Hide(Take t)
        {
            if (t.show != null && t.show.Contains("*")) { foreach (var r in hidden) if (r) r.enabled = true; hidden.Clear(); foreach (var b in hiddenB) if (b) b.enabled = true; hiddenB.Clear(); }
            if (t.hide == null) return;
            bool Match(Transform tr) { for (var x = tr; x; x = x.parent) foreach (var h in t.hide) if (x.name.IndexOf(h, StringComparison.OrdinalIgnoreCase) >= 0) return true; return false; }
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include, FindObjectsSortMode.None)) if (r.enabled && Match(r.transform)) { r.enabled = false; hidden.Add(r); }
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) if (c.enabled && Match(c.transform)) { c.enabled = false; hiddenB.Add(c); }
        }

        static float Hermite(float a, float b, float c, float d, float t) { float t2 = t * t, t3 = t2 * t; return .5f * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3); }
        static Vector3 V(float[] f) => f != null && f.Length >= 3 ? new Vector3(f[0], f[1], f[2]) : Vector3.zero;
        static void EvalKeys(Cam c, float f, out float[] pos, out float[] look, out float fov, out float roll, out float focus)
        {
            var k = c.keys; int n = k.Length;
            if (n == 1 || f <= k[0].f) { pos = k[0].pos; look = k[0].look; fov = k[0].fov; roll = k[0].roll; focus = k[0].focusOffset; return; }
            if (f >= k[n - 1].f) { pos = k[n - 1].pos; look = k[n - 1].look; fov = k[n - 1].fov; roll = k[n - 1].roll; focus = k[n - 1].focusOffset; return; }
            int i = 0; while (i < n - 2 && f > k[i + 1].f) i++;
            float u = Mathf.InverseLerp(k[i].f, k[i + 1].f, f); if (n == 2 && c.ease) u = u * u * (3 - 2 * u);
            Key a = k[Mathf.Max(i - 1, 0)], b = k[i], d = k[i + 1], e = k[Mathf.Min(i + 2, n - 1)];
            float[] H(Func<Key, float[]> g) { var r = new float[3]; for (int j = 0; j < 3; j++) r[j] = n == 2 ? Mathf.Lerp(V(g(b))[j], V(g(d))[j], u) : Hermite(V(g(a))[j], V(g(b))[j], V(g(d))[j], V(g(e))[j], u); return r; }
            pos = H(x => x.pos); look = H(x => x.look); fov = Mathf.Lerp(b.fov, d.fov, u); roll = Mathf.Lerp(b.roll, d.roll, u); focus = Mathf.Lerp(b.focusOffset, d.focusOffset, u);
        }

        static RenderTexture big, small; static Texture2D tex; static int curFrame; static float curDt = 1f / 120;
        static void Render(Camera cam, Take t, Cam c, int frame, string file, bool reset)
        {
            EvalKeys(c, frame, out var kp, out var kl, out float fov, out float roll, out float focusOff);
            var pos = Smooth("P" + c.name, Point(c.posAnchor, kp, out _), c.posSmooth, reset);
            var look = Smooth("K" + c.name, Point(c.lookAnchor, kl, out _), c.lookSmooth, reset);
            var rot = Quaternion.LookRotation(look - pos) * Quaternion.Euler(0, 0, roll);
            if (c.shake > 0)
            {
                float tt = frame / (float)t.fps * c.shakeFreq * 6f;
                rot *= Quaternion.Euler((Mathf.PerlinNoise(tt, 3.1f) - .5f) * 2 * c.shake, (Mathf.PerlinNoise(7.7f, tt) - .5f) * 2 * c.shake, (Mathf.PerlinNoise(tt, 19.3f) - .5f) * c.shake);
                pos += new Vector3(Mathf.PerlinNoise(tt * .7f, 41f) - .5f, Mathf.PerlinNoise(53f, tt * .7f) - .5f, 0) * (c.shake * .02f);
            }
            volume.profile.TryGet(out DepthOfField dof); dof.active = c.dof;
            if (c.dof)
            {
                var fp = string.IsNullOrEmpty(c.focusAnchor) ? look : Point(c.focusAnchor, null, out _);
                dof.mode.Override(DepthOfFieldMode.Bokeh); dof.focusDistance.Override(Mathf.Max(.1f, Vector3.Dot(fp - pos, rot * Vector3.forward) + focusOff));
                dof.aperture.Override(c.aperture); dof.focalLength.Override(c.focal); dof.bladeCount.Override(7); dof.bladeCurvature.Override(1f);
            }
            var tp = cam.transform.position; var tr = cam.transform.rotation; float tf = cam.fieldOfView, ta = cam.aspect, tn = cam.nearClipPlane, tfar = cam.farClipPlane; var tt0 = cam.targetTexture;
            var data = cam.GetUniversalAdditionalCameraData(); bool pp0 = data.renderPostProcessing; var aa0 = data.antialiasing; data.renderPostProcessing = true; data.antialiasing = AntialiasingMode.None;
            int bw = Mathf.RoundToInt(t.w * t.ss), bh = Mathf.RoundToInt(t.h * t.ss);
            if (!big || big.width != bw || big.height != bh) { if (big) big.Release(); big = new RenderTexture(bw, bh, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Default) { antiAliasing = 4, filterMode = FilterMode.Bilinear }; big.Create(); }
            if (!small || small.width != t.w || small.height != t.h) { if (small) small.Release(); small = new RenderTexture(t.w, t.h, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Default); small.Create(); if (tex) Object.DestroyImmediate(tex); tex = new Texture2D(t.w, t.h, TextureFormat.RGB24, false); }
            cam.transform.SetPositionAndRotation(pos, rot); cam.fieldOfView = fov; cam.aspect = t.w / (float)t.h; cam.nearClipPlane = c.near; if (c.far > 0) cam.farClipPlane = c.far;
            var mirror = FindType("BowlingLaneMirror"); mirror?.GetMethod("RenderNow", BF)?.Invoke(null, null);
            cam.targetTexture = big; cam.Render(); cam.targetTexture = tt0;
            Graphics.Blit(big, small);
            var act = RenderTexture.active; RenderTexture.active = small; tex.ReadPixels(new Rect(0, 0, t.w, t.h), 0, 0); tex.Apply(false); RenderTexture.active = act;
            File.WriteAllBytes(file, file.EndsWith(".png") ? tex.EncodeToPNG() : tex.EncodeToJPG(t.quality));
            cam.transform.SetPositionAndRotation(tp, tr); cam.fieldOfView = tf; cam.aspect = ta; cam.nearClipPlane = tn; cam.farClipPlane = tfar; data.renderPostProcessing = pp0; data.antialiasing = aa0;
        }

        static MethodInfo Meth(object o, string n, int args) { for (var t = o.GetType(); t != null; t = t.BaseType) foreach (var m in t.GetMethods(BF | BindingFlags.DeclaredOnly)) if (m.Name == n && m.GetParameters().Length == args) return m; return null; }
        static float Ease(string s, float u) => s == "linear" ? u : s == "in" ? u * u : s == "out" ? 1 - (1 - u) * (1 - u) : u * u * (3 - 2 * u);
        static void RunEvent(Ev e, int f)
        {
            float u = e.until > e.f ? Mathf.Clamp01((f - e.f) / (float)(e.until - e.f)) : 1;
            switch (e.@do)
            {
                case "call": { var r = Call(e.on, e.m, e.a); if (r != null && !(r is IEnumerator)) log.AppendLine("call " + e.on + "." + e.m + " -> " + r); break; }
                case "get": log.AppendLine("get " + e.on + (e.m != null ? "." + e.m : "") + " = " + Describe(e.m != null ? Member(Eval(e.on), e.m) : Eval(e.on))); break;
                case "alias": { int k = e.s.IndexOf('='); alias[e.s.Substring(0, k)] = e.s.Substring(k + 1); break; }
                case "timescale": Time.timeScale = e.v[0]; break;
                case "place": { var tr = AsTransform(Eval(e.on)); if (!tr) throw new Exception("place: " + e.on); if (e.v.Length >= 3) tr.position = new Vector3(e.v[0], e.v[1], e.v[2]); if (e.v.Length >= 4) tr.rotation = Quaternion.Euler(0, e.v[3], 0); break; }
                case "active": { var go = Eval(e.on) as GameObject ?? (Eval(e.on) as Component)?.gameObject; if (go) go.SetActive(e.s != "0"); break; }
                case "enable": { if (Eval(e.on) is Behaviour b) b.enabled = e.s != "0"; break; }
                case "move":
                {   // v = from xyz, to xyz, [arc height]; s = ease
                    var tr = AsTransform(Eval(e.on)); if (!tr) throw new Exception("move: " + e.on); float k = Ease(e.s, u);
                    var p = Vector3.Lerp(new Vector3(e.v[0], e.v[1], e.v[2]), new Vector3(e.v[3], e.v[4], e.v[5]), k); if (e.v.Length > 6) p.y += e.v[6] * 4 * k * (1 - k);
                    tr.position = p; break;
                }
                case "drive":
                {   // an actor walked by hand: v = from xyz, to xyz; its own Advance/Pose run with the speed it really has
                    var o = Eval(e.on); var tr = AsTransform(o); if (!tr) throw new Exception("drive: " + e.on); float k = Ease(e.s ?? "linear", u);
                    var p = Vector3.Lerp(new Vector3(e.v[0], e.v[1], e.v[2]), new Vector3(e.v[3], e.v[4], e.v[5]), k); var vel = (p - tr.position) / curDt; if (f == e.f) vel = Vector3.zero;
                    tr.position = p;
                    Meth(o, "Advance", 3)?.Invoke(o, new object[] { curDt, Vector3.Dot(vel, tr.right), Vector3.Dot(vel, tr.forward) }); Meth(o, "Pose", 0)?.Invoke(o, null); break;
                }
                case "tick": { var o = Eval(e.on); Meth(o, "Advance", 3)?.Invoke(o, new object[] { curDt, 0f, 0f }); Meth(o, "Pose", 0)?.Invoke(o, null); break; }
                case "yaw": { var tr = AsTransform(Eval(e.on)); float a = e.v.Length > 1 ? Mathf.LerpAngle(e.v[0], e.v[1], Ease(e.s, u)) : e.v[0]; tr.rotation = Quaternion.Euler(0, a, 0); break; }
                case "seed": UnityEngine.Random.InitState((int)e.v[0]); break;
                case "gameclock": { var g = Game(); var fld = g.GetType().GetField("Clock", BF); if (fld != null) fld.SetValue(g, (Func<double>)(() => Time.timeAsDouble)); break; }
                default: throw new Exception("unknown event " + e.@do);
            }
        }
        static string Describe(object o)
        {
            if (o == null) return "null";
            if (o is string s) return s;
            if (o is Transform t) return t.name + " pos=" + t.position.ToString("F3") + " rot=" + t.eulerAngles.ToString("F1");
            if (o is Component c) return c.GetType().Name + " on " + c.name + " pos=" + c.transform.position.ToString("F3") + " rot=" + c.transform.eulerAngles.ToString("F1");
            if (o is IEnumerable en) { var sb = new StringBuilder("["); int n = 0; foreach (var x in en) { if (n++ > 60) { sb.Append("…"); break; } sb.Append(x).Append(", "); } return sb.Append("]").ToString(); }
            if (o is Vector3 v) return v.ToString("F3");
            return o.ToString();
        }

        static IEnumerator DoTake(Take t)
        {
            Hq(); EnsureVolume(); ApplyPost(t.post); ApplyEnv(t.env); BuildLights(t); Hide(t);
            if (t.seed >= 0) UnityEngine.Random.InitState(t.seed);
            string root = string.IsNullOrEmpty(t.outDir) ? Path.Combine(dir, "takes", t.name) : t.outDir;
            if (t.cams != null) foreach (var c in t.cams) Directory.CreateDirectory(Path.Combine(root, c.name));
            Time.captureFramerate = t.fps; Time.timeScale = t.timeScale; curDt = t.timeScale / t.fps;
            foreach (var smr in Object.FindObjectsByType<SkinnedMeshRenderer>(FindObjectsSortMode.None)) smr.updateWhenOffscreen = true;
            var trace = new StringBuilder(); if (t.trace != null) trace.AppendLine("f;" + string.Join(";", t.trace)); int total = t.warm + t.frames; bool first = true;
            for (int n = 0; n < total; n++)
            {
                int f = n - t.warm; curFrame = f;
                if (t.events != null) foreach (var e in t.events) if (e.f == f || (e.until > e.f && f > e.f && f <= e.until)) RunEvent(e, f);
                yield return null;
                if (t.trace != null) { trace.Append(f); foreach (var x in t.trace) { string val; try { val = Describe(Eval(x)); } catch (Exception ex) { val = "ERR " + ex.Message; } trace.Append(';').Append(val); } trace.AppendLine(); }
                if (f < 0 || t.cams == null) continue;
                bool save = t.only != null && t.only.Length > 0 ? Array.IndexOf(t.only, f) >= 0 : f % Mathf.Max(1, t.every) == 0;
                PlaceLights(first);
                var cam = Cam0(); if (!cam) throw new Exception("no camera");
                foreach (var c in t.cams)
                {
                    // smoothing follows every frame; pictures only for the frames asked for
                    bool mine = save;
                    if (f < c.from || f > c.to) mine = false; else if (c.every > 0 && (t.only == null || t.only.Length == 0)) mine = (f - Mathf.Max(c.from, 0)) % c.every < Mathf.Max(1, c.sub);
                    if (!mine) { EvalKeys(c, f, out var kp, out var kl, out _, out _, out _); Smooth("P" + c.name, Point(c.posAnchor, kp, out _), c.posSmooth, first); Smooth("K" + c.name, Point(c.lookAnchor, kl, out _), c.lookSmooth, first); continue; }
                    Render(cam, t, c, f, Path.Combine(root, c.name, "f_" + f.ToString("00000") + ".jpg"), first);
                }
                first = false;
            }
            Time.timeScale = 0;
            Directory.CreateDirectory(root); File.WriteAllText(Path.Combine(root, "take.json"), JsonUtility.ToJson(t, true));
            if (t.trace != null) File.WriteAllText(Path.Combine(root, "trace.csv"), trace.ToString());
        }

        static void Dump(Cmd c)
        {
            var sb = new StringBuilder();
            void Walk(Transform t, int d)
            {
                if (!string.IsNullOrEmpty(c.filter) && d == 0 && t.GetComponentsInChildren<Transform>(true).All(x => x.name.IndexOf(c.filter, StringComparison.OrdinalIgnoreCase) < 0)) return;
                sb.Append(' ', d * 2).Append(t.name).Append(t.gameObject.activeInHierarchy ? "" : " (off)").Append("  [").Append(string.Join(",", t.GetComponents<Component>().Where(x => x && !(x is Transform)).Select(x => x.GetType().Name))).Append("] ").Append(t.position.ToString("F2")).Append(" kids=").Append(t.childCount).AppendLine();
                if (d < c.depth) foreach (Transform k in t) Walk(k, d + 1);
            }
            var roots = new HashSet<Transform>(); foreach (var t in Object.FindObjectsByType<Transform>(FindObjectsInactive.Include, FindObjectsSortMode.None)) roots.Add(t.root);
            foreach (var r in roots.OrderBy(x => x.name)) Walk(r, 0);
            sb.AppendLine("---- lights");
            foreach (var l in Object.FindObjectsByType<Light>(FindObjectsSortMode.None)) sb.AppendLine($"{l.name} {l.type} i={l.intensity} c={l.color} rot={l.transform.eulerAngles} pos={l.transform.position} shadows={l.shadows} range={l.range}");
            sb.AppendLine("---- volumes");
            foreach (var v in Object.FindObjectsByType<Volume>(FindObjectsSortMode.None)) sb.AppendLine($"{v.name} global={v.isGlobal} prio={v.priority} w={v.weight} comps={(v.profile ? string.Join(",", v.profile.components.Select(x => x.GetType().Name + (x.active ? "" : "(off)"))) : "none")}");
            sb.AppendLine("---- cameras");
            foreach (var cm in Object.FindObjectsByType<Camera>(FindObjectsSortMode.None)) sb.AppendLine($"{cm.name} en={cm.enabled} pos={cm.transform.position} rot={cm.transform.eulerAngles} fov={cm.fieldOfView} near={cm.nearClipPlane} far={cm.farClipPlane} depth={cm.depth} comps={string.Join(",", cm.GetComponents<Component>().Select(x => x.GetType().Name))}");
            sb.AppendLine($"---- ambient mode={RenderSettings.ambientMode} i={RenderSettings.ambientIntensity} c={RenderSettings.ambientLight} sky={RenderSettings.ambientSkyColor} fog={RenderSettings.fog} {RenderSettings.fogDensity} {RenderSettings.fogColor} skybox={(RenderSettings.skybox ? RenderSettings.skybox.shader.name : "none")}");
            File.WriteAllText(c.path ?? Path.Combine(dir, "dump.txt"), sb.ToString());
        }

        static IEnumerator Serve()
        {
            dir = Path.GetFullPath(Env_("TR_DIR", "../trailer")); Directory.CreateDirectory(dir);
            Time.captureFramerate = 120; Time.timeScale = 0;
            string cmdPath = Path.Combine(dir, "cmd.json"), donePath = Path.Combine(dir, "done.txt");
            File.WriteAllText(Path.Combine(dir, "ready.txt"), "ready " + DateTime.Now);
            while (true)
            {
                if (!File.Exists(cmdPath)) { yield return null; continue; }
                string json = File.ReadAllText(cmdPath); File.Delete(cmdPath); log.Length = 0;
                var cmd = JsonUtility.FromJson<Cmd>(json);
                if (cmd.op == "quit") { File.WriteAllText(donePath, "ok quit"); yield break; }
                if (cmd.op == "dump") Dump(cmd);
                else if (cmd.op == "scene")
                {
                    otherVolumes.Clear(); lightOrig.Clear(); envSaved = false; hidden.Clear(); hiddenB.Clear(); filmLights.Clear(); filmLightSpecs.Clear(); Time.timeScale = 1;
                    UnityEngine.SceneManagement.SceneManager.LoadScene(cmd.scene);
                    for (int i = 0; i < 20; i++) yield return null;
                    for (int i = 0; i < 6000 && !Ready(); i++) yield return null;
                    Time.timeScale = 0;
                }
                else if (cmd.op == "take") { var e = DoTake(cmd.take); while (e.MoveNext()) yield return e.Current; }
                else throw new Exception("unknown op " + cmd.op);
                File.WriteAllText(Path.Combine(dir, "log.txt"), log.ToString());
                File.WriteAllText(donePath, "ok");
            }
        }
    }
}
#endif
