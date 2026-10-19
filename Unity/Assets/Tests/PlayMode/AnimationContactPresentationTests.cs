using System.Collections;
using System.Reflection;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    [DefaultExecutionOrder(1200)]
    public sealed class ContactFrameProbe : MonoBehaviour
    {
        public TennisGame game;
        public bool observed;
        public float ringError, ballError;
        int previous;
        void LateUpdate()
        {
            if (!game || game.PresentedContacts == previous) return;
            previous = game.PresentedContacts;
            var strings = game.Player.StringPoint(game.LastFaceOffset);
            var ball = (Transform)typeof(TennisGame).GetField("ball", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(game);
            ringError = Vector3.Distance(game.LastPresentedContact, strings);
            ballError = Vector3.Distance(ball.position, strings);
            observed = true;
        }
    }

    public class AnimationContactPresentationTests
    {
        [UnityTest, Timeout(180000)]
        public IEnumerator ContactSurvivesLaterSubstepsAndUsesTheDisplayedStringsOnce()
        {
            yield return SceneManager.LoadSceneAsync("Tennis");
            yield return null;
            var game = Object.FindFirstObjectByType<TennisGame>(); game.ManualSimulation = true;
            game.ConfigureMatch(TennisGame.Mode.Training, null, null, null);
            var probe = game.gameObject.AddComponent<ContactFrameProbe>(); probe.game = game;
            game.Player.CancelSwing(); game.Player.Tick(2, 0);
            game.Player.transform.position = new Vector3(0, .035f, -11.2f);
            game.Player.Swing(.65f, false, TennisActor.Stroke.Drive); game.Player.Tick(.18f, 0); game.Player.Pose();
            var face = TennisRules.PositionFace(new Vector3(.65f, 1.1f, .65f), Vector3.zero);
            var hit = TennisRules.AssistedHit(0, 1 - TennisRules.FaceError(face), 1, .65f, 1);
            game.InjectBall(game.Player.StringPoint(face), Vector3.back * 12);
            const BindingFlags flags = BindingFlags.Instance | BindingFlags.NonPublic;
            typeof(TennisGame).GetField("hitLateness", flags).SetValue(game, 0f);
            int before = game.PresentedContacts;
            typeof(TennisGame).GetMethod("ReturnBall", flags).Invoke(game, new object[] { hit, face });
            // The simulation's transient hitter can be cleared by a subsequent
            // 120 Hz step before the renderer sees this contact.
            typeof(TennisGame).GetField("contactHitter", flags).SetValue(game, null);
            yield return null; yield return null;
            Assert.That(probe.observed, Is.True);
            Assert.That(game.PresentedContacts, Is.EqualTo(before + 1));
            Assert.That(probe.ringError, Is.LessThan(.001f));
            Assert.That(Mathf.Abs(probe.ballError - TennisRules.BallRadius), Is.LessThan(.015f), "The visible ball surface must touch the strings within 15 mm.");
            yield return null;
            Assert.That(game.PresentedContacts, Is.EqualTo(before + 1), "No duplicate impact next frame.");
            Object.Destroy(probe);
        }
    }
}
