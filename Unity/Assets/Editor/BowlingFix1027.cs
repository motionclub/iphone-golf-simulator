#if UNITY_EDITOR
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using GolfArcade.Bowling;
using GolfArcade.Game;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// Proof captures for the 10-27 bowling fixes (Adnan: hands, two-hand carry, walking through furniture, flicker, skip):
    ///   -executeMethod GolfArcade.EditorTools.BowlingFix1027.Run   BFIX_OUT=<dir>  BFIX=geo,hands  (FILM_NO_HUD=1 recommended)
    /// geo, per venue: meshes.bin (world triangles of every visible mesh, for coplanar.py), topdown.png (everything between 5 cm and
    /// 1.6 m above the floors, seen from above: the furniture a walker could hit), walks.csv (each hero's path lounge -> stance -> lounge),
    /// static_/pan_ frame sequences for flicker.py (heroes and crowd hidden).
    /// hands: Club Lanes, a male and a female hero through two frames of autoplay, close front views of both every 4th frame (hands.csv).
    [InitializeOnLoad]
    public static class BowlingFix1027
    {
        const string Flag = "BowlingFix1027";
        static IEnumerator script;
        static int lastFrame = -1;
        static string output;
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
        static string F(float v) => v.ToString("0.###", Inv);
        const BindingFlags Any = BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.Instance;

        static BowlingFix1027() { EditorApplication.update += Tick; }

        public static void Run()
        {
            script = null; lastFrame = -1;
            if (!File.Exists(BowlingFilm.ScenePath)) BowlingFilm.EnsureScene();
            EditorSceneManager.OpenScene(BowlingFilm.ScenePath);
            EditorUtility.audioMasterMute = true;
            BowlingVenue.Selected = BowlingVenueKind.ClubLanes;
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return;
            lastFrame = Time.frameCount;
            try { if (script == null) script = Record(); if (!script.MoveNext()) Finish(0); }
            catch (Exception e)
            {
                Debug.LogException(e);
                if (!string.IsNullOrEmpty(output)) File.WriteAllText(Path.Combine(output, "error.txt"), e.ToString());
                Finish(1);
            }
        }

        static void Finish(int code)
        {
            SessionState.SetBool(Flag, false); Time.captureFramerate = 0;
            if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false;
        }

        static IEnumerator WaitGame(Action<BowlingGame> got)
        {
            for (int i = 0; i < 600; i++)
            {
                var g = Object.FindFirstObjectByType<BowlingGame>();
                if (g && g.Initialized) { got(g); yield break; }
                yield return null;
            }
            throw new Exception("no BowlingGame");
        }

        static IEnumerator Record()
        {
            output = Path.GetFullPath(Environment.GetEnvironmentVariable("BFIX_OUT") ?? "../work/bowling/proof/fix-1027");
            Directory.CreateDirectory(output);
            var stages = (Environment.GetEnvironmentVariable("BFIX") ?? "geo,hands").Split(',');
            Time.captureFramerate = 30;
            if (Array.IndexOf(stages, "geo") >= 0)
            {
                var only = Environment.GetEnvironmentVariable("BFIX_VENUES");
                foreach (BowlingVenueKind v in Enum.GetValues(typeof(BowlingVenueKind)))
                {
                    if (!string.IsNullOrEmpty(only) && !only.Contains(v.ToString())) continue;
                    BowlingVenue.Selected = v;
                    EditorSceneManager.LoadSceneInPlayMode(BowlingFilm.ScenePath, new LoadSceneParameters(LoadSceneMode.Single));
                    yield return null; yield return null;
                    BowlingGame game = null;
                    var w = WaitGame(g => game = g); while (w.MoveNext()) yield return w.Current;
                    var e = Geo(game, v.ToString()); while (e.MoveNext()) yield return e.Current;
                }
            }
            if (Array.IndexOf(stages, "probe") >= 0)
            {
                BowlingGame game = null;
                var w = WaitGame(g => game = g); while (w.MoveNext()) yield return w.Current;
                var e = Probe(game); while (e.MoveNext()) yield return e.Current;
            }
            if (Array.IndexOf(stages, "walk") >= 0)
            {
                BowlingVenue.Selected = BowlingVenueKind.ClubLanes;
                EditorSceneManager.LoadSceneInPlayMode(BowlingFilm.ScenePath, new LoadSceneParameters(LoadSceneMode.Single));
                yield return null; yield return null;
                BowlingGame game = null;
                var w = WaitGame(g => game = g); while (w.MoveNext()) yield return w.Current;
                var e = WalkProbe(game); while (e.MoveNext()) yield return e.Current;
            }
            if (Array.IndexOf(stages, "film") >= 0)
            {
                BowlingVenue.Selected = BowlingVenueKind.ClubLanes;
                EditorSceneManager.LoadSceneInPlayMode(BowlingFilm.ScenePath, new LoadSceneParameters(LoadSceneMode.Single));
                yield return null; yield return null;
                BowlingGame game = null;
                var w = WaitGame(g => game = g); while (w.MoveNext()) yield return w.Current;
                var e = Film(game); while (e.MoveNext()) yield return e.Current;
            }
            foreach (var (stage, legacy) in new[] { ("handsbefore", true), ("hands", false) })
            {
                if (Array.IndexOf(stages, stage) < 0) continue;
                BowlingHero.LegacyHands = legacy;
                BowlingVenue.Selected = BowlingVenueKind.ClubLanes;
                EditorSceneManager.LoadSceneInPlayMode(BowlingFilm.ScenePath, new LoadSceneParameters(LoadSceneMode.Single));
                yield return null; yield return null;
                BowlingGame game = null;
                var w = WaitGame(g => game = g); while (w.MoveNext()) yield return w.Current;
                var e = Hands(game, stage); while (e.MoveNext()) yield return e.Current;
                BowlingHero.LegacyHands = false;
            }
        }

        static List<BowlingHero> Heroes(BowlingGame g) => (List<BowlingHero>)typeof(BowlingGame).GetField("heroes", Any).GetValue(g);
        static Vector3 Spot(BowlingGame g, string name, object arg) => (Vector3)typeof(BowlingGame).GetMethod(name, Any).Invoke(g, new[] { arg });
        static void Send(BowlingGame g, BowlingHero h, Vector3 to, float yaw, bool sit) =>
            typeof(BowlingGame).GetMethod("Send", Any).Invoke(g, new object[] { h, to, yaw, sit });

        static void SetVisible(BowlingGame g, bool heroes, bool crowd)
        {
            foreach (var h in Heroes(g)) if (h) foreach (var r in h.GetComponentsInChildren<Renderer>(true)) r.forceRenderingOff = !heroes;
            foreach (var c in Object.FindObjectsByType<GolfArcade.Majestic.MajesticCrowd>(FindObjectsSortMode.None)) c.gameObject.SetActive(crowd);
            if (g.BallView) foreach (var r in g.BallView.GetComponentsInChildren<Renderer>(true)) r.forceRenderingOff = !heroes;
        }

        // ------------------------------------------------------------------ geometry: z-fight dump, furniture map, walks, flicker frames

        static IEnumerator Geo(BowlingGame game, string venue)
        {
            string dir = Path.Combine(output, venue); Directory.CreateDirectory(dir);
            game.KeyboardEnabled = false;
            game.NewGame(new[] { "A", "B", "C", "D" });
            for (int i = 0; i < 20; i++) yield return null;
            DumpMeshes(Path.Combine(dir, "meshes.bin"));

            var cam = Camera.main;
            var keep = (cam.transform.position, cam.transform.rotation, cam.orthographic, cam.orthographicSize, cam.nearClipPlane, cam.farClipPlane, cam.clearFlags, cam.backgroundColor, cam.fieldOfView);
            // the furniture map: x -3.2..3.2, z -12.5..-3.5 at 100 px/m, everything 5 cm .. 1.6 m above the approach (the lounge floor is .18 lower)
            SetVisible(game, false, true);
            game.enabled = false;
            var canvases = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None);
            foreach (var c in canvases) c.enabled = false;
            cam.orthographic = true; cam.orthographicSize = 4.5f; cam.nearClipPlane = .1f; cam.farClipPlane = 1.65f;
            cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = Color.black;
            cam.transform.SetPositionAndRotation(new Vector3(0, 1.7f, -8f), Quaternion.Euler(90, 0, 0));
            yield return null;
            cam.aspect = 640f / 900;
            cam.transform.SetPositionAndRotation(new Vector3(0, 1.7f, -8f), Quaternion.Euler(90, 0, 0));
            GameCapture.Save(Path.Combine(dir, "topdown.png"), 640, 900);
            cam.ResetAspect();
            foreach (var c in canvases) c.enabled = true;
            game.enabled = true;
            cam.orthographic = keep.orthographic; cam.orthographicSize = keep.orthographicSize; cam.nearClipPlane = keep.nearClipPlane; cam.farClipPlane = keep.farClipPlane;
            cam.clearFlags = keep.clearFlags; cam.backgroundColor = keep.backgroundColor;
            SetVisible(game, true, true);

            // walks: every hero from the lounge to the stance, back to its seat, and the bowler from the end of a shot to the lounge
            var heroes = Heroes(game);
            game.enabled = false;   // (the game would keep sending the bowler to the stance)
            void Put(BowlingHero h, Vector3 p) { h.Snap(); h.transform.position = p; h.WalkTo(p, 0); }
            var csv = new StringBuilder("venue,leg,hero,frame,x,y,z,remaining\n");
            for (int leg = 0; leg < 3; leg++)
            {
                for (int i = 0; i < heroes.Count; i++)
                {
                    var h = heroes[i]; if (!h) continue;
                    if (leg == 0) { Put(h, Spot(game, "WaitSpot", i)); Send(game, h, Spot(game, "StartSpot", 12f + 6 * i), 0, false); }
                    else if (leg == 1) Send(game, h, Spot(game, "WaitSpot", i), 0, true);
                    else { Put(h, new Vector3(-.3f + .2f * i, 0, -.8f)); Send(game, h, Spot(game, "WaitSpot", i), 0, true); }
                }
                for (int f = 0; f < 400; f++)
                {
                    bool any = false;
                    for (int i = 0; i < heroes.Count; i++)
                    {
                        var h = heroes[i]; if (!h) continue;
                        var p = h.Position; any |= !h.Arrived;
                        csv.Append(string.Join(",", venue, leg, i, f, F(p.x), F(p.y), F(p.z), F(h.Remaining))).Append('\n');
                    }
                    if (!any) break;
                    yield return null;
                }
            }
            File.WriteAllText(Path.Combine(dir, "walks.csv"), csv.ToString());
            game.enabled = true;
            if (Environment.GetEnvironmentVariable("BFIX_WALKONLY") == "1") { Debug.Log($"[BowlingFix1027] geo {venue} done (walks only)"); yield break; }

            // flicker frames (no people): the setup view held still, then the ball's camera dollying down the lane
            SetVisible(game, false, false);
            game.enabled = false;   // the game's camera moves no more; the frames below place it
            var hud = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None);
            foreach (var c in hud) c.enabled = false;
            var seq = Path.Combine(dir, "static"); Directory.CreateDirectory(seq);
            var setupPos = new Vector3(0, 2.4f, BowlingApproach.StartZ - 4.8f); var setupLook = new Vector3(0, .2f, 12);
            cam.fieldOfView = 38;
            for (int f = 0; f < 12; f++)
            {
                cam.transform.SetPositionAndRotation(setupPos, Quaternion.LookRotation(setupLook - setupPos));
                BowlingLaneMirror.RenderNow();
                GameCapture.Save(Path.Combine(seq, $"f{f:000}.png"), 960, 540);
                yield return null;
            }
            // z-fight: each game view held still while the camera wiggles 1 mm (a real z-fight blinks, the rest moves < 1 px), with the
            // 10-27 floor fixes and with the old floor heights put back (Tiki DeckEdge top in the deck plane, Club AisleEdge top in the aisle carpet)
            var views = new (string name, Vector3 pos, Vector3 look)[]
            {
                ("setup", setupPos, setupLook),
                ("lounge", new Vector3(.6f, 1.4f, -1f), new Vector3(0, 1.05f, -7.5f)),
                ("pins", new Vector3(0, .95f, 14.8f), new Vector3(0, .12f, 18.7f)),
            };
            // the shadow reach the alley is drawn with (the shared pipeline asset; the clone's copy is put back after)
            var urp = UnityEngine.Rendering.GraphicsSettings.defaultRenderPipeline as UnityEngine.Rendering.Universal.UniversalRenderPipelineAsset;
            var keepShadow = urp ? (urp.shadowDistance, urp.shadowCascadeCount, urp.cascade2Split, urp.cascade4Split) : default;
            var conditions = Environment.GetEnvironmentVariable("BFIX_SHADOWS") == "1"
                ? new (string name, float dist, int cascades)[] { ("authored", keepShadow.Item1, keepShadow.Item2), ("golf320", 320, 4), ("alley34", 34, 2) }
                : new (string name, float dist, int cascades)[] { ("now", keepShadow.Item1, keepShadow.Item2) };
            Debug.Log($"[BowlingFix1027] authored shadows {keepShadow.Item1} m x{keepShadow.Item2}");
            if (Environment.GetEnvironmentVariable("BFIX_ISOLATE") == "1")
            {
                // what makes the lounge strip blink: each suspect switched off in turn (lounge view only)
                var vol = Object.FindObjectsByType<UnityEngine.Rendering.Volume>(FindObjectsSortMode.None);
                var lights = Object.FindObjectsByType<Light>(FindObjectsSortMode.None);
                var probes = Object.FindObjectsByType<ReflectionProbe>(FindObjectsSortMode.None);
                var camData = cam.GetComponent<UnityEngine.Rendering.Universal.UniversalAdditionalCameraData>();
                var suspects = new (string name, Action on, Action off)[]
                {
                    ("base", () => { }, () => { }),
                    ("nomirror", () => BowlingLaneMirror.Enabled = false, () => BowlingLaneMirror.Enabled = true),
                    ("nopost", () => { if (camData) camData.renderPostProcessing = false; foreach (var v in vol) v.enabled = false; }, () => { if (camData) camData.renderPostProcessing = true; foreach (var v in vol) v.enabled = true; }),
                    ("noaddlights", () => { foreach (var l in lights) if (l.type != LightType.Directional) l.enabled = false; }, () => { foreach (var l in lights) l.enabled = true; }),
                    ("noprobe", () => { foreach (var r in probes) r.enabled = false; }, () => { foreach (var r in probes) r.enabled = true; }),
                    ("noshadow", () => { foreach (var l in lights) l.shadows = LightShadows.None; }, () => { }),
                    ("nocarpet", () => { foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None)) if (r.name == "Carpet" || r.name == "Deck" || r.name.StartsWith("Floor")) r.forceRenderingOff = true; }, () => { }),
                };
                var lounge = views[1];
                var only = Environment.GetEnvironmentVariable("BFIX_SUSPECTS");
                foreach (var (sn, on, off) in suspects)
                {
                    if (!string.IsNullOrEmpty(only) && !only.Contains(sn)) continue;
                    on();
                    seq = Path.Combine(dir, $"iso_{sn}"); Directory.CreateDirectory(seq);
                    for (int f = 0; f < 16; f++)
                    {
                        var p = lounge.pos + new Vector3((f % 2) * .001f, ((f / 2) % 2) * .001f, 0);
                        cam.transform.SetPositionAndRotation(p, Quaternion.LookRotation(lounge.look - p));
                        BowlingLaneMirror.RenderNow();
                        GameCapture.Save(Path.Combine(seq, $"f{f:000}.png"), 960, 540);
                        yield return null;
                    }
                    off();
                }
                conditions = new (string name, float dist, int cascades)[0];
            }
            foreach (var (when, dist, cascades) in conditions)
            {
                if (urp) { urp.shadowDistance = dist; urp.shadowCascadeCount = cascades; if (when == "alley34") urp.cascade2Split = .3f; if (when == "golf320") { urp.cascade2Split = .18f; urp.cascade4Split = new Vector3(.05f, .14f, .38f); } }
                foreach (var (vn, vp, vl) in views)
                {
                    seq = Path.Combine(dir, $"jit_{vn}_{when}"); Directory.CreateDirectory(seq);
                    for (int f = 0; f < 24; f++)
                    {
                        var p = vp + new Vector3((f % 2) * .001f, ((f / 2) % 2) * .001f, 0);
                        cam.transform.SetPositionAndRotation(p, Quaternion.LookRotation(vl - p));
                        BowlingLaneMirror.RenderNow();
                        GameCapture.Save(Path.Combine(seq, $"f{f:000}.png"), 960, 540);
                        yield return null;
                    }
                }
            }
            if (urp) { urp.shadowDistance = keepShadow.Item1; urp.shadowCascadeCount = keepShadow.Item2; urp.cascade2Split = keepShadow.Item3; urp.cascade4Split = keepShadow.Item4; }
            game.enabled = true;
            foreach (var c in hud) c.enabled = true;
            cam.transform.SetPositionAndRotation(keep.position, keep.rotation); cam.fieldOfView = keep.fieldOfView;
            SetVisible(game, true, true);
            Debug.Log($"[BowlingFix1027] geo {venue} done");
        }

        /// World triangles of every visible MeshRenderer (coplanar.py's meshes.bin): name, vertices, then per submesh its material and indices.
        static void DumpMeshes(string path)
        {
            using var w = new BinaryWriter(File.Create(path));
            var list = new List<MeshRenderer>();
            foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            {
                if (!r.enabled || !r.gameObject.activeInHierarchy || r.forceRenderingOff) continue;
                var mf = r.GetComponent<MeshFilter>(); if (!mf || !mf.sharedMesh) continue;
                if (r.GetComponentInParent<BowlingHero>()) continue;
                list.Add(r);
            }
            int failed = 0;
            var ok = new List<(MeshRenderer r, Vector3[] v, int[][] sub)>();
            foreach (var r in list)
            {
                var m = r.GetComponent<MeshFilter>().sharedMesh;
                try
                {
                    var v = m.vertices; var l2w = r.transform.localToWorldMatrix;
                    for (int i = 0; i < v.Length; i++) v[i] = l2w.MultiplyPoint3x4(v[i]);
                    var sub = new int[m.subMeshCount][];
                    for (int s = 0; s < m.subMeshCount; s++) sub[s] = m.GetTopology(s) == MeshTopology.Triangles ? m.GetTriangles(s) : new int[0];
                    ok.Add((r, v, sub));
                }
                catch (Exception) { failed++; }
            }
            w.Write(ok.Count);
            foreach (var (r, v, sub) in ok)
            {
                string Path_(Transform t) => t.parent ? Path_(t.parent) + "/" + t.name : t.name;
                var name = Encoding.UTF8.GetBytes(Path_(r.transform)); w.Write(name.Length); w.Write(name);
                w.Write(v.Length); foreach (var p in v) { w.Write(p.x); w.Write(p.y); w.Write(p.z); }
                w.Write(sub.Length);
                var mats = r.sharedMaterials;
                for (int s = 0; s < sub.Length; s++)
                {
                    var mn = Encoding.UTF8.GetBytes(s < mats.Length && mats[s] ? mats[s].name : "-"); w.Write(mn.Length); w.Write(mn);
                    w.Write(sub[s].Length); foreach (int i in sub[s]) w.Write(i);
                }
            }
            Debug.Log($"[BowlingFix1027] meshes {ok.Count} (unreadable {failed}) -> {path}");
        }

        // ------------------------------------------------------------------ hands: both heroes through two frames of autoplay

        /// Offscreen renders here do not re-skin: a SkinnedMeshRenderer draws its last skinning pass, not the bones as they are now (a forearm
        /// turned 90 deg just before the render did not show, probe 10-27; bowling2/film.sh hit the same). So the heroes are drawn from
        /// BakeMesh copies of their skinned meshes, made from the live bones, for the length of one capture.
        internal static void SaveBaked(IEnumerable<BowlingHero> heroes, string path, int w, int h)
        {
            var made = new List<(SkinnedMeshRenderer smr, GameObject copy)>();
            foreach (var hero in heroes)
            {
                if (!hero) continue;
                foreach (var smr in hero.GetComponentsInChildren<SkinnedMeshRenderer>())
                {
                    if (!smr.enabled || smr.forceRenderingOff || !smr.sharedMesh) continue;
                    var mesh = new Mesh(); smr.BakeMesh(mesh, true);
                    var go = new GameObject(smr.name + " (baked)");
                    go.transform.SetPositionAndRotation(smr.transform.position, smr.transform.rotation);
                    go.AddComponent<MeshFilter>().sharedMesh = mesh;
                    var mr = go.AddComponent<MeshRenderer>(); mr.sharedMaterials = smr.sharedMaterials;
                    smr.forceRenderingOff = true;
                    made.Add((smr, go));
                }
            }
            try { GameCapture.Save(path, w, h); }
            finally
            {
                foreach (var (smr, go) in made) { smr.forceRenderingOff = false; Object.DestroyImmediate(go.GetComponent<MeshFilter>().sharedMesh); Object.DestroyImmediate(go); }
            }
        }

        /// Degrees between where a hand's palm faces and the thigh beside it (0 = palm in, 180 = palm out), about the hand's own axis.
        static float Palm(BowlingHero h, bool left)
        {
            if (!h.Look) return -1;
            Transform B(HumanBodyBones b) => h.Look.Bone(b);
            var hd = B(left ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand); var mid = B(left ? HumanBodyBones.LeftMiddleProximal : HumanBodyBones.RightMiddleProximal);
            var idx = B(left ? HumanBodyBones.LeftIndexProximal : HumanBodyBones.RightIndexProximal); var lit = B(left ? HumanBodyBones.LeftLittleProximal : HumanBodyBones.RightLittleProximal);
            if (!hd || !mid || !idx || !lit) return -1;
            var axis = (mid.position - hd.position).normalized;
            var across = Vector3.ProjectOnPlane(idx.position - lit.position, axis).normalized;
            var palm = left ? Vector3.Cross(across, axis) : Vector3.Cross(axis, across);
            var t = h.transform; var want = (left ? t.right : -t.right) - t.forward * .35f;
            if (h.Anim && h.Anim.SeatWeight > .5f) want = -t.up;
            return Vector3.Angle(Vector3.ProjectOnPlane(palm, axis), Vector3.ProjectOnPlane(want, axis));
        }

        /// What draws the hero: every renderer under it, which bones the body is skinned to, and where the drawn hand really is.
        static IEnumerator Probe(BowlingGame game)
        {
            game.KeyboardEnabled = false;
            game.PlayerFemale.Clear(); game.PlayerFemale.Add(false); game.PlayerFemale.Add(true);
            game.NewGame(new[] { "Male", "Female" });
            var heroes = Heroes(game);
            for (int f = 0; f < 90; f++) yield return null;
            var log = new StringBuilder();
            foreach (var h in heroes)
            {
                var hand = h.Look.Bone(HumanBodyBones.RightHand);
                log.Append($"HERO {h.name} look={h.Look.name} body={(h.Look.body ? h.Look.body.name : "-")} hand={Path_(hand)}\n");
                foreach (var c in h.GetComponentsInChildren<MonoBehaviour>(true)) log.Append($"  comp {c.GetType().Name} on {c.name} enabled={c.enabled}\n");
                foreach (var r in h.GetComponentsInChildren<Renderer>(true))
                {
                    var smr = r as SkinnedMeshRenderer;
                    string bones = "";
                    if (smr && smr.bones != null)
                    {
                        int k = Array.IndexOf(smr.bones, hand);
                        Transform same = null; foreach (var b in smr.bones) if (b && b.name == hand.name) { same = b; break; }
                        bones = $" bones={smr.bones.Length} hasLookHand={k >= 0} sameNameHand={(same ? Path_(same) : "-")} root={(smr.rootBone ? Path_(smr.rootBone) : "-")}";
                    }
                    log.Append($"  R {Path_(r.transform)} {r.GetType().Name} on={r.enabled && r.gameObject.activeInHierarchy} off={r.forceRenderingOff} vis={r.isVisible}{bones}\n");
                }
                // move the right hand bone 30 cm up and see whether the baked body follows it
                if (h.Look.body)
                {
                    var m0 = new Mesh(); h.Look.body.BakeMesh(m0, true);
                    var keep = hand.position; hand.position += Vector3.up * .3f;
                    var m1 = new Mesh(); h.Look.body.BakeMesh(m1, true);
                    hand.position = keep;
                    var a = m0.vertices; var b = m1.vertices; float moved = 0; int n = 0;
                    for (int i = 0; i < a.Length; i++) { float d = (a[i] - b[i]).magnitude; if (d > .1f) n++; moved = Mathf.Max(moved, d); }
                    log.Append($"  bake: verts {a.Length} moved>{0.1f}m {n} max {moved:0.000}\n");
                }
            }
            // render test: wait for the male to carry the ball up from the lounge, then the same view three ways
            var m = heroes[0];
            game.Autoplay.Enqueue(new BowlingGame.Shot(17, 8.5f, 300, 35, 0));
            for (int f = 0; f < 30 * 30; f++)
            {
                if (m.Ball && !m.Arrived && !m.ClipPlaying) break;
                // force a lounge walk: the male goes to sit, then is sent back up with the ball
                if (f == 0) { m.WalkTo(m.Position, 0); }
                yield return null;
                if (f == 1) typeof(BowlingGame).GetMethod("Send", Any).Invoke(game, new object[] { m, Spot(game, "WaitSpot", 0), 0f, true });
                if (f == 1) for (int k = 0; k < 200 && !m.Arrived; k++) yield return null;
                if (f == 1) { m.Anim.Seated = false; typeof(BowlingGame).GetMethod("Send", Any).Invoke(game, new object[] { m, Spot(game, "StartSpot", 20f), 0f, false }); }
            }
            for (int f = 0; f < 20; f++) yield return null;
            var cam = Camera.main; var hud = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None); foreach (var c in hud) c.enabled = false;
            var tr = m.transform; var hp = m.Position;
            var pos = hp + tr.forward * 1.45f + tr.right * .55f + Vector3.up * 1.15f; var at = hp + Vector3.up * .9f;
            void Shoot(string name) { cam.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(at - pos)); GameCapture.Save(Path.Combine(output, name), 640, 720); }
            var cw = typeof(BowlingHero).GetField("carryW", Any);
            var rh = m.Look.Bone(HumanBodyBones.RightHand);
            log.Append($"render test: ball={(bool)m.Ball} walking={!m.Arrived} clip={m.Anim.Playing} carryW={cw.GetValue(m)} dR={Vector3.Distance(rh.position, game.BallView.transform.position):0.000}\n");
            Shoot("A_asis.jpg");
            var keepHand = rh.position; m.Look.Bone(HumanBodyBones.RightLowerArm).rotation = Quaternion.AngleAxis(90, tr.right) * m.Look.Bone(HumanBodyBones.RightLowerArm).rotation;
            Shoot("B_forearm_moved_now.jpg");
            yield return null;
            Shoot("C_next_frame.jpg");
            log.Append($"next frame: carryW={cw.GetValue(m)} dR={Vector3.Distance(rh.position, game.BallView.transform.position):0.000}\n");
            File.WriteAllText(Path.Combine(output, "probe.txt"), log.ToString());
            Debug.Log("[BowlingFix1027] probe written");
        }
        static string Path_(Transform t) => !t ? "-" : t.parent ? Path_(t.parent) + "/" + t.name : t.name;

        /// Walk smoothness at 60 fps: each hero walks lounge -> stance -> lounge; per frame its root position, yaw, ground speed, the
        /// walk/run/idle blend, the planted toe's slip and the hips' / hands' angular speed (walk.csv), plus every clip's key rate (clips.csv).
        /// Also frames of the male walking (walkframes/, BakeMesh), every 2nd frame.
        static IEnumerator WalkProbe(BowlingGame game)
        {
            string dir = Path.Combine(output, "walk"); Directory.CreateDirectory(Path.Combine(dir, "frames"));
            Time.captureFramerate = 60;
            game.KeyboardEnabled = false;
            game.PlayerFemale.Clear(); game.PlayerFemale.Add(false); game.PlayerFemale.Add(true);
            game.NewGame(new[] { "M", "F" });
            var heroes = Heroes(game);
            var clips = new StringBuilder("hero,clip,length,frameRate,maxKeysPerSecond,curves\n");
            foreach (var h in heroes)
            {
                var a = h.GetComponentInChildren<Animator>();
                foreach (var c in Resources.LoadAll<AnimationClip>("HeroMoves/" + (h.Female ? "Female" : "Male")))
                {
                    if (c.name.StartsWith("__preview__")) continue;
                    var b = AnimationUtility.GetCurveBindings(c); float maxKps = 0;
                    foreach (var bind in b) { var cv = AnimationUtility.GetEditorCurve(c, bind); if (cv != null && c.length > 0) maxKps = Mathf.Max(maxKps, cv.length / c.length); }
                    clips.Append(string.Join(",", h.Female ? "F" : "M", c.name, F(c.length), F(c.frameRate), F(maxKps), b.Length)).Append('\n');
                }
            }
            File.WriteAllText(Path.Combine(dir, "clips.csv"), clips.ToString());
            game.enabled = false;
            var csv = new StringBuilder("hero,leg,frame,x,y,z,yaw,speed,wIdle,wWalk,wRun,toeSlip,hipsDeg,handRDeg,handLDeg\n");
            var cam = Camera.main;
            for (int leg = 0; leg < 2; leg++)
            {
                for (int i = 0; i < heroes.Count; i++)
                {
                    var h = heroes[i];
                    if (leg == 0) { h.Snap(); h.transform.position = Spot(game, "WaitSpot", i); h.WalkTo(h.Position, 0); h.Anim.Seated = false; Send(game, h, Spot(game, "StartSpot", 14f + 10 * i), 0, false); }
                    else Send(game, h, Spot(game, "WaitSpot", i), 0, true);
                }
                var last = new Dictionary<Transform, Quaternion>();
                for (int f = 0; f < 60 * 14; f++)
                {
                    bool any = false;
                    for (int i = 0; i < heroes.Count; i++)
                    {
                        var h = heroes[i]; any |= !h.Arrived;
                        float D(HumanBodyBones bb) { var t = h.Look.Bone(bb); if (!t) return 0; float d = last.TryGetValue(t, out var q) ? Quaternion.Angle(q, t.rotation) : 0; last[t] = t.rotation; return d * 60; }
                        var wgt = h.Anim.Weights;
                        csv.Append(string.Join(",", i, leg, f, F(h.Position.x), F(h.Position.y), F(h.Position.z), F(h.transform.eulerAngles.y), F(h.Anim.Speed),
                            F(wgt.x), F(wgt.y), F(wgt.z), F(h.Anim.PlantedToeSpeed), F(D(HumanBodyBones.Hips)), F(D(HumanBodyBones.RightHand)), F(D(HumanBodyBones.LeftHand)))).Append('\n');
                    }
                    if (leg == 0 && f % 2 == 0 && f < 60 * 9)
                    {
                        var m = heroes[0]; var hp = m.Position;
                        var pos = hp + new Vector3(2.2f, 1.3f, .4f); var at = hp + Vector3.up * .9f;
                        cam.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(at - pos));
                        var hud = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None); foreach (var c in hud) c.enabled = false;
                        BowlingLaneMirror.RenderNow();
                        SaveBaked(heroes, Path.Combine(dir, "frames", $"f_{f / 2:00000}.jpg"), 960, 540);
                        foreach (var c in hud) c.enabled = true;
                    }
                    if (!any && f > 30) break;
                    yield return null;
                }
            }
            File.WriteAllText(Path.Combine(dir, "walk.csv"), csv.ToString());
            game.enabled = true; Time.captureFramerate = 30;
            Debug.Log("[BowlingFix1027] walk probe done");
        }

        /// A quick gameplay clip (male then female, one frame each, autoplay): frames/ = the game's own view with its HUD, close/ = the
        /// bowler up close; both drawn from BakeMesh copies so the live pose shows. 20 fps.
        static IEnumerator Film(BowlingGame game)
        {
            string dir = Path.Combine(output, "film"); Directory.CreateDirectory(Path.Combine(dir, "frames")); Directory.CreateDirectory(Path.Combine(dir, "close"));
            int fps = int.TryParse(Environment.GetEnvironmentVariable("BFIX_FILM_FPS"), out int ff) ? ff : 20;
            float from = float.TryParse(Environment.GetEnvironmentVariable("BFIX_FILM_FROM"), NumberStyles.Float, Inv, out float fr) ? fr : 0;
            float to = float.TryParse(Environment.GetEnvironmentVariable("BFIX_FILM_TO"), NumberStyles.Float, Inv, out float tt) ? tt : 75;
            Time.captureFramerate = fps;
            game.KeyboardEnabled = false;
            game.PlayerFemale.Clear(); game.PlayerFemale.Add(false); game.PlayerFemale.Add(true);
            game.NewGame(new[] { "Adnan", "Sam" });
            game.Autoplay.Enqueue(new BowlingGame.Shot(14, 8.6f, 300, 35, 0));      // male: 9 or so
            game.Autoplay.Enqueue(new BowlingGame.Shot(8, 8.2f, 220, 20, .02f));    // male: the spare ball
            game.Autoplay.Enqueue(new BowlingGame.Shot(16, 8.8f, 320, 40, 0));      // female
            game.Autoplay.Enqueue(new BowlingGame.Shot(30, 8.2f, 220, 15, 0));      // female: the spare ball
            var cam = Camera.main; var heroes = Heroes(game);
            int frame = 0; float start = Time.time;
            while (Time.time - start < to && (game.Autoplay.Count > 0 || game.Flow != BowlingGame.Phase.Setup))
            {
                if (Time.time - start < from) { yield return null; continue; }
                SaveBaked(heroes, Path.Combine(dir, "frames", $"f_{frame:00000}.jpg"), 960, 540);
                // the close view: the hero who is moving (a walker), else the bowler
                BowlingHero h = heroes.Count > game.Current ? heroes[game.Current] : null;
                foreach (var x in heroes) if (x && !x.Arrived && x.Remaining > .9f) { h = x; break; }
                if (h)
                {
                    var (was, wasRot, fov) = (cam.transform.position, cam.transform.rotation, cam.fieldOfView);
                    var hud = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None); foreach (var c in hud) c.enabled = false;
                    var t = h.transform; var hp = h.Position;
                    var pos = hp + t.forward * 2.3f + t.right * 1.1f + Vector3.up * 1.35f; var at = hp + Vector3.up * .95f;
                    cam.fieldOfView = 38;
                    cam.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(at - pos));
                    BowlingLaneMirror.RenderNow();
                    SaveBaked(heroes, Path.Combine(dir, "close", $"f_{frame:00000}.jpg"), 960, 540);
                    foreach (var c in hud) c.enabled = true;
                    cam.transform.SetPositionAndRotation(was, wasRot); cam.fieldOfView = fov;
                    BowlingLaneMirror.RenderNow();
                }
                frame++;
                yield return null;
            }
            Time.captureFramerate = 30;
            Debug.Log($"[BowlingFix1027] film {frame} frames");
        }

        static IEnumerator Hands(BowlingGame game, string name)
        {
            string dir = Path.Combine(output, name); Directory.CreateDirectory(dir);
            game.KeyboardEnabled = false;
            game.PlayerFemale.Clear(); game.PlayerFemale.Add(false); game.PlayerFemale.Add(true);
            game.NewGame(new[] { "Male", "Female" });
            // a strike, then two-ball frames: the walk to the lounge, the walk back up the approach, the seated wait
            game.Autoplay.Enqueue(new BowlingGame.Shot(17, 8.5f, 300, 35, 0));
            game.Autoplay.Enqueue(new BowlingGame.Shot(25, 7.5f, 200, 10, .03f));
            game.Autoplay.Enqueue(new BowlingGame.Shot(10, 7.5f, 200, 10, 0));
            game.Autoplay.Enqueue(new BowlingGame.Shot(25, 8f, 250, 30, -.06f));
            game.Autoplay.Enqueue(new BowlingGame.Shot(15, 8f, 250, 30, 0));
            var cam = Camera.main; var heroes = Heroes(game);
            var csv = new StringBuilder("frame,flow,current,hero,clip,ball,seated,walking,image,dR,dL,ballUp,palmR,palmL\n");
            int frame = 0, shot = 0;
            while (frame < 30 * 75 && game.Autoplay.Count > 0)
            {
                if (frame % 4 == 0)
                {
                    var (was, wasRot) = (cam.transform.position, cam.transform.rotation);
                    var hud = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None);
                    foreach (var c in hud) c.enabled = false;
                    for (int i = 0; i < heroes.Count; i++)
                    {
                        var h = heroes[i]; if (!h) continue;
                        var t = h.transform; var hp = h.Position;
                        // a close front three-quarter view of the arms and hands (chest to knees)
                        var pos = hp + t.forward * 1.45f + t.right * .55f + Vector3.up * 1.15f; var at = hp + Vector3.up * .9f;
                        cam.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(at - pos));
                        BowlingLaneMirror.RenderNow();
                        string img = $"h{i}_{shot:00000}.jpg";
                        SaveBaked(heroes, Path.Combine(dir, img), 640, 720);
                        var ball = game.BallView.transform.position;
                        Transform B(HumanBodyBones b) => h.Look ? h.Look.Bone(b) : null;
                        float dR = h.Ball && B(HumanBodyBones.RightHand) ? Vector3.Distance(B(HumanBodyBones.RightHand).position, ball) : -1;
                        float dL = h.Ball && B(HumanBodyBones.LeftHand) ? Vector3.Distance(B(HumanBodyBones.LeftHand).position, ball) : -1;
                        csv.Append(string.Join(",", frame, game.Flow, game.Current, i, h.Anim ? h.Anim.Playing : "", h.Ball ? 1 : 0,
                            h.Anim && h.Anim.Seated ? 1 : 0, h.Arrived ? 0 : 1, img, F(dR), F(dL), F(h.Ball ? ball.y - hp.y : -1),
                            F(Palm(h, false)), F(Palm(h, true)))).Append('\n');
                    }
                    shot++;
                    foreach (var c in hud) c.enabled = true;
                    cam.transform.SetPositionAndRotation(was, wasRot);
                }
                frame++;
                yield return null;
            }
            File.WriteAllText(Path.Combine(dir, "hands.csv"), csv.ToString());
            Debug.Log($"[BowlingFix1027] hands {shot} samples");
        }
    }
}
#endif
