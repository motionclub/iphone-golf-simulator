using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;
using GolfArcade.Game;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    /// Avatar audit (2026-11-10, user: "polish the avatars across the different sports, right now a lot looks wonky"): both heroes in
    /// each sport's real scene while they play, shot close from the front, the side and behind, plus the face and the hands, a few
    /// times a second. Runs only with AVATAR_AUDIT=<out dir> (and AVATAR_AUDIT_ONLY=tennis|golf|bowling to do one sport).
    public class AvatarAuditCapture
    {
        Camera cam; RenderTexture rt; Texture2D tex; string dir;
        void Begin(string sport)
        {
            dir = Path.Combine(Path.GetFullPath(System.Environment.GetEnvironmentVariable("AVATAR_AUDIT")), sport); Directory.CreateDirectory(dir);
            cam = new GameObject("Avatar audit cam").AddComponent<Camera>(); cam.enabled = false; cam.nearClipPlane = .05f;
            rt = new RenderTexture(540, 720, 24) { antiAliasing = 4 }; tex = new Texture2D(540, 720, TextureFormat.RGB24, false); cam.targetTexture = rt;
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
        }
        void Shot(string name, Vector3 from, Vector3 at, float fov)
        {
            cam.transform.position = from; cam.transform.rotation = Quaternion.LookRotation(at - from); cam.fieldOfView = fov;
            cam.Render(); RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, 540, 720), 0, 0); tex.Apply(); RenderTexture.active = null;
            File.WriteAllBytes(Path.Combine(dir, name + ".jpg"), tex.EncodeToJPG(88));
        }
        static Transform Bone(Transform root, string name) => root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name);
        void Around(string tag, Transform hero)
        {
            // what the player sees: the game's own camera, heroes at the detail level their distance gives them
            if (System.Environment.GetEnvironmentVariable("AVATAR_AUDIT_GAME") == "1") { GameCapture.Save(Path.Combine(dir, tag + "_0game.jpg"), 1280, 720); return; }
            var hips = Bone(hero, "Hips"); var head = Bone(hero, "Head"); var hand = Bone(hero, "RightHand"); var left = Bone(hero, "LeftHand");
            Vector3 feet = hero.position, mid = (hips ? hips.position : feet + Vector3.up * .9f); mid.y = feet.y + .9f;
            Vector3 f = hero.forward, r = hero.right;
            Shot(tag + "_1front", mid + f * 3.3f + Vector3.up * .15f, mid, 34);
            Shot(tag + "_2side", mid + r * 3.3f + Vector3.up * .15f, mid, 34);
            Shot(tag + "_3back", mid - f * 3.1f + r * .9f + Vector3.up * .3f, mid, 34);
            if (head) Shot(tag + "_4face", head.position + f * .95f + r * .25f + Vector3.up * .05f, head.position + Vector3.up * .03f, 30);
            if (hand) Shot(tag + "_5handR", hand.position + f * .5f + r * .3f + Vector3.up * .2f, hand.position, 30);
            if (left) Shot(tag + "_6handL", left.position + f * .5f - r * .3f + Vector3.up * .2f, left.position, 30);
        }
        static bool Wants(string sport)
        {
            if (string.IsNullOrEmpty(System.Environment.GetEnvironmentVariable("AVATAR_AUDIT"))) return false;
            var only = System.Environment.GetEnvironmentVariable("AVATAR_AUDIT_ONLY");
            return string.IsNullOrEmpty(only) || only == sport;
        }

        [UnityTest, Timeout(900000)] public IEnumerator Tennis()
        {
            Assume.That(Wants("tennis"), "set AVATAR_AUDIT to capture");
            foreach (bool female in new[] { false, true })
            {
                yield return SceneManager.LoadSceneAsync("Tennis"); yield return null;
                var game = Object.FindFirstObjectByType<TennisGame>();
                while (!game.Initialized) yield return null;
                game.SelectCharacter(female);
                // the look as a real launch applies it (NativeSportsSession): the locker's kit colours on the worn kit
                var kit = TennisLook.Kit.From("E8505B", "24345E", "FFFFFF", "", 2);
                game.ApplyOutfit(kit); game.SetPlayerLook(HeroKit.Style.From(2, 1, 1, kit, female ? 1 : 0, female));
                game.ConfigureMatch(TennisGame.Mode.Training, "", "", "", 1, 3);
                yield return null; yield return null;
                Begin("tennis");
                Time.captureFramerate = 60; game.AutoPlay = true;
                try
                {
                    for (int frame = 0; frame < 720; frame++)
                    {
                        yield return null;
                        if (frame % 36 == 18) Around($"{(female ? "f" : "m")}_{frame:0000}", game.Player.transform);
                        if (frame == 400) Around($"{(female ? "f" : "m")}_rival", game.Opponent.transform);
                        if (frame == 306 && !female && System.Environment.GetEnvironmentVariable("AVATAR_AUDIT_THUMB") == "1")
                        {
                            // thumb diagnosis: the right thumb's joints as posed, and the same frame with each hand pass switched off in turn
                            var root = game.Player.transform; var log = new System.Text.StringBuilder();
                            void Dump(string tag) { foreach (var n in new[] { "RightHand", "RightThumbProximal", "RightThumbIntermediate", "RightThumbDistal", "RightIndexProximal" }) { var t = Bone(root, n); if (t) log.AppendLine($"{tag} {n} localEuler={t.localEulerAngles} localScale={t.localScale} lossy={t.lossyScale} pos={root.InverseTransformPoint(t.position)}"); } }
                            Dump("as-played");
                            foreach (var mb in root.GetComponentsInChildren<MonoBehaviour>(true)) log.AppendLine("component " + mb.GetType().Name + " enabled=" + mb.enabled + " on " + mb.name);
                            var body = root.GetComponentsInChildren<SkinnedMeshRenderer>(true).FirstOrDefault(r => r.name.StartsWith("Body"));
                            if (body) log.AppendLine("body mesh " + body.sharedMesh.name + " verts=" + body.sharedMesh.vertexCount);
                            File.WriteAllText(Path.Combine(dir, "thumb.txt"), log.ToString());
                            foreach (var type in new[] { "HeroGripPolish", "HeroThumbRigMigration", "HeroPoseSafety", "HeroAuthoredHandPose" })
                            {
                                var comps = root.GetComponentsInChildren<MonoBehaviour>(true).Where(m => m.GetType().Name == type).ToArray();
                                if (comps.Length == 0) continue;
                                foreach (var c in comps) c.enabled = false;
                                yield return null; yield return null;
                                var hand = Bone(root, "RightHand");
                                Shot("thumb_without_" + type, hand.position + root.forward * .5f + root.right * .3f + Vector3.up * .2f, hand.position, 30);
                                foreach (var c in comps) c.enabled = true;
                            }
                        }
                    }
                }
                finally { Time.captureFramerate = 0; game.AutoPlay = false; }
            }
        }

        [UnityTest, Timeout(900000)] public IEnumerator Golf()
        {
            Assume.That(Wants("golf"), "set AVATAR_AUDIT to capture");
            var original = GolferStyle.Current.Clone(); var oldOverride = GolferStyle.HeroOverride;
            try
            {
                Time.timeScale = 1; Time.captureFramerate = 60; GolferStyle.HeroOverride = true;
                foreach (var body in new[] { GolferStyle.BodyKind.Male, GolferStyle.BodyKind.Female })
                {
                    GolferStyle.Body = body;
                    yield return SceneManager.LoadSceneAsync("Golf", LoadSceneMode.Single);
                    var game = Object.FindFirstObjectByType<GolfGame>();
                    yield return null; game.Play();
                    game.Swing.Synthetic.FixedStepSeconds = 1.0 / 60.0;
                    for (int i = 0; i < 900 && (game.Current != GolfGame.State.Aim || game.Swing.Phase != Swing.SwingPhase.Address); i++) yield return null;
                    var golfer = (GolferView)typeof(GolfGame).GetField("golfer", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(game);
                    Begin("golf");
                    string who = body == GolferStyle.BodyKind.Female ? "f" : "m";
                    for (int frame = 0; frame < 420; frame++)
                    {
                        if (frame == 60) game.Swing.Synthetic.Backswing(true);
                        if (frame == 138) game.Swing.Synthetic.Backswing(false);
                        yield return null;
                        if (frame % 20 == 10 && golfer && golfer.Hero.Root) Around($"{who}_{frame:0000}", golfer.Hero.Root.transform);
                    }
                }
            }
            finally { GolferStyle.SaveDevice(original); GolferStyle.Unwear(); GolferStyle.HeroOverride = oldOverride; Time.captureFramerate = 0; }
        }

        [UnityTest, Timeout(900000)] public IEnumerator Bowling()
        {
            Assume.That(Wants("bowling"), "set AVATAR_AUDIT to capture");
            foreach (bool female in new[] { false, true })
            {
                yield return SceneManager.LoadSceneAsync("Bowling"); yield return null; yield return null;
                var game = Object.FindFirstObjectByType<GolfArcade.Bowling.BowlingGame>();
                Time.captureFramerate = 60;
                try
                {
                    game.PlayerFemale.Clear(); game.PlayerFemale.Add(female); game.Autoplay.Clear();
                    game.PlayerLook.Clear(); game.PlayerLook.Add(("", "E8505B", "24345E", "FFFFFF"));   // as a real launch does
                    game.NewGame(new[] { "You" });
                    Begin("bowling");
                    for (int frame = 0; frame < 600; frame++)
                    {
                        if (frame == 120) game.Autoplay.Enqueue(new GolfArcade.Bowling.BowlingGame.Shot(20, 7.2f, 260, 35, 0f));
                        yield return null;
                        var hero = Object.FindObjectsByType<MatchHeroLook>(FindObjectsSortMode.None).FirstOrDefault(h => h.isActiveAndEnabled);
                        if (frame % 30 == 15 && hero) Around($"{(female ? "f" : "m")}_{frame:0000}", hero.transform);
                    }
                }
                finally { Time.captureFramerate = 0; }
            }
        }
    }
}
