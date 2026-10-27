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
    /// The walk-up check (approach-1027, "they glide instead of walking up"): the male then the female bowl one ball each in Club Lanes on
    /// autoplay; for every frame of their approach (the shot clip, root at the stance) feet.csv logs both feet (ankle, ball of the foot), the
    /// hips and the neck in world space, and side/ gets a 60 fps side view of the whole approach (heroes drawn from BakeMesh copies: offscreen
    /// renders do not re-skin, see BowlingFix1027.SaveBaked). Whatever stands between the camera and the bowler (ball returns, the next lane's
    /// furniture) is hidden for the film.
    ///   -executeMethod GolfArcade.EditorTools.BowlingApproach1027.Run   BAPP_OUT=<dir>  [BAPP_TIMING=<s> autoplay release offset]  FILM_NO_HUD=1
    [InitializeOnLoad]
    public static class BowlingApproach1027
    {
        const string Flag = "BowlingApproach1027";
        static IEnumerator script;
        static int lastFrame = -1;
        static string output;
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
        static string F(float v) => v.ToString("0.####", Inv);
        const BindingFlags Any = BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.Instance;

        static BowlingApproach1027() { EditorApplication.update += Tick; }

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

        static List<BowlingHero> Heroes(BowlingGame g) => (List<BowlingHero>)typeof(BowlingGame).GetField("heroes", Any).GetValue(g);
        static float ApproachT(BowlingGame g) => (float)typeof(BowlingGame).GetField("approachT", Any).GetValue(g);

        static IEnumerator Record()
        {
            output = Path.GetFullPath(Environment.GetEnvironmentVariable("BAPP_OUT") ?? "../work/bowling/proof/approach-1027/unity");
            Directory.CreateDirectory(output);
            float timing = float.TryParse(Environment.GetEnvironmentVariable("BAPP_TIMING"), NumberStyles.Float, Inv, out float tm) ? tm : 0;
            Time.captureFramerate = 60;
            EditorSceneManager.LoadSceneInPlayMode(BowlingFilm.ScenePath, new LoadSceneParameters(LoadSceneMode.Single));
            yield return null; yield return null;
            BowlingGame game = null;
            for (int i = 0; i < 600 && !game; i++)
            {
                var g = Object.FindFirstObjectByType<BowlingGame>();
                if (g && g.Initialized) game = g; else yield return null;
            }
            if (!game) throw new Exception("no BowlingGame");
            game.KeyboardEnabled = false;
            game.PlayerFemale.Clear(); game.PlayerFemale.Add(false); game.PlayerFemale.Add(true);
            game.NewGame(new[] { "Adnan", "Sam" });
            for (int k = 0; k < 4; k++) game.Autoplay.Enqueue(new BowlingGame.Shot(14 + k, 8.6f, 300, 35, timing));
            var heroes = Heroes(game);
            var cam = Camera.main;
            var csv = new StringBuilder("hero,frame,t,clip,clipTime,lAnkX,lAnkY,lAnkZ,lBallX,lBallY,lBallZ,rAnkX,rAnkY,rAnkZ,rBallX,rBallY,rBallZ,hipsX,hipsY,hipsZ,neckX,neckY,neckZ\n");
            var done = new HashSet<int>();
            int guard = 0;
            while (done.Count < 2 && guard++ < 60 * 240)
            {
                if (game.Flow != BowlingGame.Phase.Approach) { yield return null; continue; }
                int who = game.Current; var h = heroes[who];
                if (done.Contains(who)) { yield return null; continue; }
                string dir = Path.Combine(output, "side_" + (h.Female ? "female" : "male")); Directory.CreateDirectory(dir);
                // the camera: square to the lane on the bowler's right, the whole approach in frame; hide what stands in between
                var stance = h.Position; float zc = stance.z + 1.95f;
                var camPos = new Vector3(stance.x + 7f, 1.0f, zc);
                var hidden = new List<Renderer>();
                var mine = new HashSet<Renderer>(); foreach (var x in heroes) if (x) foreach (var r in x.GetComponentsInChildren<Renderer>(true)) mine.Add(r);
                foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                {
                    if (!r.enabled || mine.Contains(r)) continue;
                    var b = r.bounds;
                    if (b.max.y < .04f || b.min.x > camPos.x || b.max.x < stance.x + .45f) continue;
                    if (b.max.z < stance.z - 1.5f || b.min.z > stance.z + 5.5f) continue;
                    if (b.size.x > 30 || b.size.z > 60) continue;     // the hall itself
                    r.enabled = false; hidden.Add(r);
                }
                int frame = 0;
                while (game.Flow == BowlingGame.Phase.Approach || (game.Flow == BowlingGame.Phase.Rolling && ApproachT(game) < 3.4f))
                {
                    float t = ApproachT(game);
                    Transform B(HumanBodyBones bb) => h.Look ? h.Look.Bone(bb) : null;
                    Vector3 P(HumanBodyBones bb) { var tr = B(bb); return tr ? tr.position : Vector3.zero; }
                    string V(Vector3 v) => $"{F(v.x)},{F(v.y)},{F(v.z)}";
                    csv.Append(string.Join(",", h.Female ? "female" : "male", frame, F(t), h.Anim ? h.Anim.Playing : "", F(h.ClipTime),
                        V(P(HumanBodyBones.LeftFoot)), V(P(HumanBodyBones.LeftToes)), V(P(HumanBodyBones.RightFoot)), V(P(HumanBodyBones.RightToes)),
                        V(P(HumanBodyBones.Hips)), V(P(HumanBodyBones.Neck)))).Append('\n');
                    var (was, wasRot, fov) = (cam.transform.position, cam.transform.rotation, cam.fieldOfView);
                    var hud = Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None); foreach (var c in hud) c.enabled = false;
                    cam.fieldOfView = 24;
                    cam.transform.SetPositionAndRotation(camPos, Quaternion.LookRotation(new Vector3(stance.x, 1.0f, zc) - camPos));
                    SaveBaked(heroes, Path.Combine(dir, $"f_{frame:00000}.jpg"), 1280, 720);
                    foreach (var c in hud) c.enabled = true;
                    cam.transform.SetPositionAndRotation(was, wasRot); cam.fieldOfView = fov;
                    frame++;
                    yield return null;
                }
                foreach (var r in hidden) if (r) r.enabled = true;
                done.Add(who);
                Debug.Log($"[BowlingApproach1027] {(h.Female ? "female" : "male")} approach {frame} frames");
            }
            File.WriteAllText(Path.Combine(output, "feet.csv"), csv.ToString());
            Time.captureFramerate = 30;
            Debug.Log($"[BowlingApproach1027] done {done.Count} approaches -> {output}");
        }

        static void SaveBaked(IEnumerable<BowlingHero> heroes, string path, int w, int h)
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
    }
}
#endif
