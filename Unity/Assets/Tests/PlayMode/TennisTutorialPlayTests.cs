using System.Collections;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    public class TennisTutorialPlayTests
    {
        const float Dt = 1f / 120;
        static void Simulate(TennisGame game, float seconds)
        { for (int i = 0; i < seconds * 120; i++) game.Step(Dt); }

        static void Serve(TennisGame game, bool good)
        {
            // (TOSS only counts once the player has walked to the serve spot: the lesson's serve now comes first, straight after setup)
            for (int i = 0; i < 600 && !game.ServeReady; i++) game.Step(Dt);
            game.Toss(good ? 1 : 0);
            for (int i = 0; i < 300 && game.Flow != TennisGame.Phase.PlayerServeToss; i++) game.Step(Dt);
            if (good) Simulate(game, TennisRules.ServeApex + TennisRules.ServeLatency);
            game.RequestSwing(.7f);
            Simulate(game, 6);
        }

        [UnityTest, Timeout(120000)] public IEnumerator CustomizedCharacterKeepsRigAndRacket()
        {
            yield return SceneManager.LoadSceneAsync("Tennis", LoadSceneMode.Single); yield return null;
            var game=Object.FindFirstObjectByType<TennisGame>();
            game.ManualSimulation=true;
            game.ApplyOutfit(TennisLook.Kit.From("E0243C","1E2A6E","9EE63A","8A4FFF",4));
            game.Player.Customize(4,2,1,1,3,3);
            Assert.IsNotNull(game.Player.GetComponent<TennisCustomization>());
            Assert.AreEqual(Vector3.one,game.Player.transform.localScale, "Cosmetics must not change gameplay reach");
            var head=System.Array.Find(game.Player.GetComponentsInChildren<Transform>(),t=>t.name.EndsWith("Curls"));
            Assert.IsNotNull(head);
            var camera=new GameObject("Customization review camera").AddComponent<Camera>();
            camera.transform.position=game.Player.transform.position+new Vector3(0,1.1f,3.3f);
            camera.transform.LookAt(game.Player.transform.position+Vector3.up*.95f);
            camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.05f,.08f,.13f);
            var target=new RenderTexture(600,800,24);camera.targetTexture=target;
            yield return null;camera.Render();RenderTexture.active=target;
            var image=new Texture2D(600,800,TextureFormat.RGB24,false);image.ReadPixels(new Rect(0,0,600,800),0,0);image.Apply();
            System.IO.File.WriteAllBytes("/tmp/customization-unity-player.png",image.EncodeToPNG());
            RenderTexture.active=null;camera.targetTexture=null;Object.Destroy(target);Object.Destroy(image);Object.Destroy(camera.gameObject);
            var position=game.Player.SweetSpot.position;
            Assert.IsFalse(float.IsNaN(position.x));
            game.RequestSwing(.6f);
        }

        [UnityTest, Timeout(180000)] public IEnumerator CompleteTheWholeLessonWithRealShotsAndNoSkipping()
        {
            yield return SceneManager.LoadSceneAsync("Tennis", LoadSceneMode.Single); yield return null;
            var game = Object.FindFirstObjectByType<TennisGame>();
            game.ManualSimulation = true; game.NativeControlled = true;
            game.ConfigureMatch(TennisGame.Mode.Tutorial, "", "Ray", "TUTORIAL");
            game.BeginLesson(1);
            var tutorial = game.GetComponent<TennisTutorial>();
            int finished = 0;
            float began = Time.realtimeSinceStartup, firstContact = -1;
            System.Action<Vector2, Timing, bool> contact = (face, grade, super) => { if (firstContact < 0) firstContact = Time.realtimeSinceStartup - began; };
            TennisGame.ContactMade += contact;
            System.Action onFinished = () => finished++;
            TennisTutorial.Finished += onFinished;
            Time.timeScale = 8;
            try
            {
                // 11-21 order: serve, then forehand feeds, then backhand feeds
                Assert.AreEqual(TutorialLesson.Kind.Serve, tutorial.Lesson.Current.Kind);
                yield return new WaitForSeconds(1.6f);
                // (a loose toss is not a sure fault on the first point: each serve that faults must retry with coaching, one that lands in moves on)
                for (int k = 0; k < 6 && tutorial.Lesson.Current.Kind == TutorialLesson.Kind.Serve; k++)
                {
                    int before = tutorial.Lesson.Misses;
                    Serve(game, k > 0); yield return null;
                    if (tutorial.Lesson.Current.Kind == TutorialLesson.Kind.Serve) Assert.AreEqual(before + 1, tutorial.Lesson.Misses, "a fault retries with coaching");
                    yield return new WaitForSeconds(1.6f);
                }
                Assert.AreEqual(TutorialLesson.Kind.Forehand, tutorial.Lesson.Current.Kind, "a serve in moves on to the forehand");
                // Search human-playable swing timing using the scheduled real coach feeds (forehand side, then backhand side).
                for (int attempt = 0; attempt < 120 && !tutorial.Lesson.Done; attempt++)
                {
                    yield return new WaitForSeconds(2);
                    Simulate(game, .6f + (attempt % 60) * .04f);
                    bool back = game.BallPosition.x < game.Player.transform.position.x;
                    game.RequestSwing(.65f, back ? -1 : 1, 0, back ? -1 : 1);
                    Simulate(game, 4);
                    yield return null;
                }
                Assert.IsTrue(tutorial.Lesson.Done, "must pass Forehand and Backhand through actual successful shots");
                Assert.GreaterOrEqual(firstContact, 0, "actual contact, not a fabricated lesson event");
                Debug.Log($"[OnboardingProof] first contact seconds={firstContact:0.000}; no steering input");
                yield return null; yield return null;
                Assert.AreEqual(1, finished);
                Assert.IsFalse(game.Drill);
            }
            finally { TennisTutorial.Finished -= onFinished; TennisGame.ContactMade -= contact; tutorial.Stop(); Time.timeScale = 1; }
        }

        [UnityTest, Timeout(180000)] public IEnumerator TenSeededPointsWinWithOnTimeSwingAndNoSwingStillEnds()
        {
            var failures = new System.Collections.Generic.List<string>();
            for (int seed = 0; seed <= 10; seed++) {
                yield return SceneManager.LoadSceneAsync("Tennis", LoadSceneMode.Single); yield return null;
                var game = Object.FindFirstObjectByType<TennisGame>();
                game.ManualSimulation = true; game.NativeControlled = true; game.OpponentDifficulty = .1f;
                typeof(TennisGame).GetField("random", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)
                    .SetValue(game, new System.Random(seed));
                game.ConfigureMatch(TennisGame.Mode.Tutorial, "", "Ray", "TUTORIAL");
                // (the lesson no longer plays a point, 2026-11-16: one point against Ray at the tutorial's difficulty, served by the player)
                game.PrepareLesson(); game.StartPlayerServe();
                yield return new WaitForSeconds(1.4f);
                float tossAge = 0; bool served = false;
                for (int frame = 0; frame < 120 * 90 && game.Match.PlayerPoints + game.Match.OpponentPoints == 0; frame++) {
                    if (game.Flow == TennisGame.Phase.PlayerServeHold) { game.Toss(1); served = false; tossAge = 0; }
                    if (game.Flow == TennisGame.Phase.PlayerServeToss) {
                        tossAge += Dt;
                        if (seed < 10 && !served && tossAge >= TennisRules.ServeApex + TennisRules.ServeLatency) { game.RequestSwing(.7f); served = true; }
                    }
                    if (seed < 10 && game.Flow == TennisGame.Phase.Rally && game.BallVelocity.z < -1 && !game.Player.Swinging) {
                        float due = (game.BallPosition.z - game.Player.transform.position.z - .65f) / -game.BallVelocity.z;
                        if (due > .1f && due <= .2f) {
                            float face = game.BallPosition.x < game.Player.transform.position.x ? -1 : 1;
                            game.AimInput = -.6f; game.RequestSwing(.7f, face, 0, face);
                        }
                    }
                    game.Step(Dt);
                    if (frame % 120 == 0) yield return null;
                }
                yield return null;
                Debug.Log($"[OnboardingProof] seed={seed} swing={seed < 10} done={game.Match.PlayerPoints + game.Match.OpponentPoints > 0} playerPoints={game.Match.PlayerPoints} opponentPoints={game.Match.OpponentPoints}");
                if (game.Match.PlayerPoints + game.Match.OpponentPoints == 0) failures.Add($"seed={seed} did not finish");
                if (seed < 10 && game.Match.PlayerPoints != 1) failures.Add($"seed={seed} did not win");
            }
            Assert.IsEmpty(failures, string.Join("; ", failures));
        }

        [UnityTest, Timeout(180000)] public IEnumerator CoachFeedsCanBeReturnedToBothAimTargetsWithGoodTiming()
        {
            yield return SceneManager.LoadSceneAsync("Tennis", LoadSceneMode.Single); yield return null;
            var game = Object.FindFirstObjectByType<TennisGame>();
            game.ManualSimulation = true; game.NativeControlled = true; game.Drill = true;
            foreach (bool backhand in new[] { false, true })
            foreach (float aim in new[] { -.6f, .6f })
            {
                bool achieved = false;
                for (float swingAt = .6f; swingAt < 3f && !achieved; swingAt += .04f)
                {
                    game.PrepareLesson(); game.AimInput = aim;
                    game.Feed(backhand);
                    bool landed = false;
                    System.Action<bool, bool, Vector3, bool> onLanding = (player, inside, at, serve) =>
                    { if (player && inside && at.x * Mathf.Sign(aim) > .8f) landed = true; };
                    TennisGame.Landed += onLanding;
                    try
                    {
                        Simulate(game, swingAt);
                        game.RequestSwing(.65f, backhand ? -1 : 1, 0, backhand ? -1 : 1);
                        Simulate(game, 4);
                        achieved = landed && game.LastGrade >= Timing.Good;
                    }
                    finally { TennisGame.Landed -= onLanding; }
                }
                Assert.IsTrue(achieved, $"Coach feed backhand={backhand}, aim={aim} must allow a GOOD in-court return to target");
            }
        }
    }
}
