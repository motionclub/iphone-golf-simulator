using System.Collections;
using System.Collections.Generic;
using System.Linq;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.Profile;
using GolfArcade.Shot;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    /// Local play, two golfers on one phone: whoever is up (the first drive of the second golfer above all) stands square to the
    /// ball — shoulders along the line of play, never turned to the TV — at address and again as the club comes through.
    public class GolferFacingTests
    {
        static IEnumerator WaitFor(System.Func<bool> done, float seconds, string what)
        {
            float until = Time.realtimeSinceStartup + seconds;
            while (!done())
            {
                if (Time.realtimeSinceStartup > until) Assert.Fail($"timed out waiting for {what}");
                yield return null;
            }
        }

        /// How far the golfer's shoulder line is from the line of play, degrees (0 square at address; 90 = chest to the camera).
        static float ShoulderOffLine(GolferView view, Vector3 aim)
        {
            var look = view.Hero.Root.GetComponent<GolfArcade.Tennis.MatchHeroLook>();
            var l = look.Bone(HumanBodyBones.LeftUpperArm); var r = look.Bone(HumanBodyBones.RightUpperArm);
            var line = r.position - l.position; line.y = 0;
            return Vector3.Angle(Mathf.Sign(Vector3.Dot(line, aim)) * line, aim);
        }

        static float ModelOffStance(GolferView view) =>
            Quaternion.Angle(view.Hero.Root.transform.localRotation, Quaternion.Euler(0, -90f, 0));

        static float StanceOff(GolferView view, Vector3 aim) =>
            Vector3.Angle(view.transform.forward, Vector3.Cross(Vector3.up, aim).normalized);

        [UnityTest]
        public IEnumerator SecondGolfersFirstDriveIsSquare()
        {
            Time.timeScale = 1f;
            LogAssert.ignoreFailingMessages = true;   // (other systems log on the way; this test is about the facing)
            yield return SceneManager.LoadSceneAsync("Golf", LoadSceneMode.Single);
            var cam = Camera.main;
            if (cam) cam.aspect = GameCapture.PhoneWidth / (float)GameCapture.PhoneHeight;
            var game = Object.FindFirstObjectByType<GolfGame>();
            game.InstantReplays = false;
            yield return null;
            var alex = new PlayerProfile { Name = "Alex", Body = 0, Kit = 0 };
            var sam = new PlayerProfile { Name = "Sam", Body = 1, Kit = 1 };
            game.Begin(GameSetup.LocalVersus(new[] { alex, sam }, "cliffside-12"));
            yield return WaitFor(() => game.Current == GolfGame.State.Aim, 45, "the first tee");
            var hole = game.CurrentHole;
            var tee = HoleView.ToWorld(hole.Tee);
            var aim = HoleView.ToWorld(hole.RecommendedTarget(hole.Tee)) - tee; aim.y = 0; aim.Normalize();
            var report = new List<string>();

            IEnumerator Check(string who)
            {
                var view = Object.FindFirstObjectByType<GolferView>();
                Assert.IsNotNull(view.Hero, "the Hero golfer is on the tee");
                yield return new WaitForSecondsRealtime(0.5f);
                float modelA = ModelOffStance(view), stanceA = StanceOff(view, aim), shoulderA = ShoulderOffLine(view, aim);
                report.Add($"{who} address: model {modelA:F1}  stance {stanceA:F1}  shoulders {shoulderA:F1}");
                Assert.Less(modelA, 0.5f, $"{who}: the model is square at address");
                Assert.Less(stanceA, 35f, $"{who}: the stance faces across the line at address");
                Assert.Less(shoulderA, 35f, $"{who}: the shoulders are along the line at address");
                game.StrikeToward(hole.RecommendedTarget(hole.Tee));
                float worstModel = 0;
                float end = Time.realtimeSinceStartup + 0.5f;
                while (Time.realtimeSinceStartup < end)
                {
                    yield return null;
                    worstModel = Mathf.Max(worstModel, ModelOffStance(view));
                }
                report.Add($"{who} swing: worst model {worstModel:F1}");
                Assert.Less(worstModel, 0.5f, $"{who}: the model stays square through the swing");
            }

            yield return Check("P1");
            yield return WaitFor(() => game.Current == GolfGame.State.Aim && game.TurnIndex == 1, 40, "P2's turn");
            yield return Check("P2");
            Debug.Log("FACING " + string.Join(" | ", report));
        }

        /// The party flow of a shared phone: every golfer is built idling (the studio's Idle faces the camera, a quarter turn), and when
        /// their turn is lined up they are stood on the ball and settled (GolfGame.LineUpNetworkTurn). Their first drive must be square:
        /// at address and through the strike. (HeroPoseTransition used to leave the rig's armature node turned a quarter for good after
        /// the Idle-to-address blend, so the second golfer's first drive was played facing the TV.)
        [UnityTest, Timeout(900000)]
        public IEnumerator PartyGolferLeavingIdleDrivesSquare()
        {
            LogAssert.ignoreFailingMessages = true;
            Time.timeScale = 1f;
            yield return SceneManager.LoadSceneAsync("Golf", LoadSceneMode.Single);
            yield return null;
            var parent = new GameObject("Party").transform;
            var report = new List<string>();
            foreach (var female in new[] { false, true })
            {
                var style = GolferView.Look.Player;
                style.Hero = GolferStyle.HeroOf(new CharacterLook { Body = female ? 1 : 0 });
                var golfer = GolferView.CreatePlayer(parent, style);
                golfer.name = "Party golfer · " + (female ? "F" : "M");
                golfer.Perform("Idle");
                for (int i = 0; i < 20; i++) yield return null;   // waiting their turn, idling
                var ball = new Vector3(40, 0, 60); var aim = new Vector3(0.3f, 0, 1).normalized;
                golfer.SetVisible(true); golfer.Stand(ball, aim); golfer.Settle();
                golfer.SetClub(GolfClub.Driver, false);
                float worstModel = 0, worstShoulder = 0;
                var series = new List<string>();
                float t0 = Time.time;
                while (Time.time - t0 < 1.2f)
                {
                    yield return null;
                    float t = Time.time - t0;
                    worstModel = Mathf.Max(worstModel, ModelOffStance(golfer));
                    series.Add($"{t:F2}s:{ShoulderOffLine(golfer, aim):F0}");
                    if (t > 0.6f) worstShoulder = Mathf.Max(worstShoulder, ShoulderOffLine(golfer, aim));
                }
                string who = female ? "female" : "male";
                report.Add($"{who} address: model {worstModel:F1} shoulders(after .6s) {worstShoulder:F1} series " + string.Join(" ", series.Where((x, k) => k % 6 == 0)));
                Assert.Less(worstModel, 0.5f, $"{who}: model square at address");
                Assert.Less(worstShoulder, 35f, $"{who}: shoulders along the line at address");
                golfer.ShowLoad(.7f);
                for (int i = 0; i < 30; i++) { yield return null; worstModel = Mathf.Max(worstModel, ModelOffStance(golfer)); }
                golfer.Strike();
                for (int i = 0; i < 30; i++) { yield return null; worstModel = Mathf.Max(worstModel, ModelOffStance(golfer)); }
                report.Add($"{who} swing: worst model {worstModel:F1}");
                Assert.Less(worstModel, 0.5f, $"{who}: model square through the swing");
            }
            Debug.Log("FACING " + string.Join(" | ", report));
        }
    }
}
