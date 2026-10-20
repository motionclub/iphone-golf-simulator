using System.Collections;
using GolfArcade.Game;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Q = System.Numerics.Quaternion;
using V = System.Numerics.Vector3;

namespace GolfArcade.PlayTests {
    public class GolfMotionReadyTests {
        static void Sample(GolfGame game, ref double time, float angle, float rate, Q grip) {
            time += .01;
            Q q = Q.Normalize(Q.CreateFromAxisAngle(V.UnitX, angle) * grip);
            game.NativeMotion(new NativeSportsSession.Sample { time=time,qx=q.X,qy=q.Y,qz=q.Z,qw=q.W,rx=rate });
        }
        static void Stroke(GolfGame game, ref double time, Q grip) {
            float angle=0;
            foreach (var leg in new[]{(.2f,0f),(.8f,1.8f),(.15f,1.8f),(.25f,-.5f),(.2f,-.5f)}) {
                int n=Mathf.RoundToInt(leg.Item1*100); float delta=(leg.Item2-angle)/n;
                for(int i=0;i<n;i++) { angle+=delta; Sample(game,ref time,angle,delta/.01f,grip); }
            }
        }
        [UnityTest, Timeout(120000)] public IEnumerator EveryShotNeedsStartSwingAndImpactHasNoExtraDownswingDelay() {
            yield return SceneManager.LoadSceneAsync("Golf",LoadSceneMode.Single);
            yield return null;
            var game=Object.FindFirstObjectByType<GolfGame>(); game.PrepareNativeAddress();
            double time=1;
            foreach(var grip in new[]{Q.Identity,Q.CreateFromAxisAngle(V.UnitY,.8f)}) {
                game.DropBall(game.CurrentHole.Tee);
                game.RequireNativeReady();
                Assert.IsFalse(game.NativeShotReady);
                Stroke(game,ref time,grip);
                Assert.AreEqual(GolfGame.State.Aim,game.Current,"Motion without Ready must not spend a stroke");
                game.NativeReady();
                Assert.IsTrue(game.NativeShotReady);
                Assert.IsFalse(game.NativeSwingTracking,"Ready lines the shot up; it does not start reading the swing");
                Assert.AreEqual(0,game.NativeSwingState);
                Stroke(game,ref time,grip);
                Assert.AreEqual(GolfGame.State.Aim,game.Current,"Handling the phone before Start Swing must not spend a stroke");
                game.NativeStartSwing(grip);
                Assert.AreEqual(2,game.NativeSwingState,"A supplied grip is ready to swing at once");
                Stroke(game,ref time,grip);
                Assert.AreEqual(GolfGame.State.Flight,game.Current,"Each fresh grip must accept a complete stroke");
                Assert.IsFalse(game.NativeShotReady);
                Assert.IsFalse(game.NativeSwingTracking,"A shot ends the swing: the next one needs Start Swing again");
                Assert.GreaterOrEqual(game.FlightTime,0,"Physical impact must not schedule another animated downswing");
            }
        }
        [UnityTest, Timeout(120000)] public IEnumerator ChangingClubOrAimEndsAStartedSwing() {
            yield return SceneManager.LoadSceneAsync("Golf",LoadSceneMode.Single);
            yield return null;
            var game=Object.FindFirstObjectByType<GolfGame>(); game.PrepareNativeAddress();
            double time=1;
            game.DropBall(game.CurrentHole.Tee); game.NativeReady(); game.NativeStartSwing(Q.Identity);
            Assert.AreEqual(2,game.NativeSwingState);
            game.NativeClub(1);
            Assert.IsTrue(game.NativeShotReady,"Changing club must not strand the player behind Ready");
            Assert.IsFalse(game.NativeSwingTracking,"Changing club ends a started swing");
            Stroke(game,ref time,Q.Identity);
            Assert.AreEqual(GolfGame.State.Aim,game.Current,"A swing started before the club change must not count");
            game.NativeStartSwing(Q.Identity);
            game.NativeAimDirection(1,0);
            Assert.IsFalse(game.NativeSwingTracking,"A new aim ends a started swing");
            game.NativeStartSwing(Q.Identity);
            Stroke(game,ref time,Q.Identity);
            Assert.AreEqual(GolfGame.State.Flight,game.Current,"Start Swing after lining up must accept the stroke");
        }
        // the stroke's first legs: at the address, then the club taken back (Stroke continues from here)
        static void Backswing(GolfGame game, ref double time, Q grip) {
            float angle=0;
            foreach (var leg in new[]{(.2f,0f),(.8f,1.8f),(.15f,1.8f)}) {
                int n=Mathf.RoundToInt(leg.Item1*100); float delta=(leg.Item2-angle)/n;
                for(int i=0;i<n;i++) { angle+=delta; Sample(game,ref time,angle,delta/.01f,grip); }
            }
        }
        static void Downswing(GolfGame game, ref double time, Q grip, int samples) {
            float angle=1.8f, delta=(-.5f-1.8f)/25;
            for(int i=0;i<samples;i++) { angle+=delta; Sample(game,ref time,angle,delta/.01f,grip); }
        }
        // Hold to swing: holding the button arms the swing, letting go before contact resets it.
        [UnityTest, Timeout(120000)] public IEnumerator LettingGoBeforeContactResetsTheSwing() {
            yield return SceneManager.LoadSceneAsync("Golf",LoadSceneMode.Single);
            yield return null;
            var game=Object.FindFirstObjectByType<GolfGame>(); game.PrepareNativeAddress();
            double time=1;
            for(int putt=0;putt<2;putt++) {
                game.DropBall(game.CurrentHole.Tee); game.NativeReady();
                // putts follow the same rule
                if(putt==1) for(int i=0;i<12 && game.ClubInHand!=GolfArcade.Shot.GolfClub.Putter;i++) game.NativeClub(1);
                game.NativeStartSwing(Q.Identity);
                Backswing(game,ref time,Q.Identity);
                Assert.AreEqual(GolfArcade.Swing.SwingPhase.Backswing,game.Swing.Phase,"the club is on its way back");
                game.NativeReleaseSwing();
                Assert.AreEqual(GolfGame.State.Aim,game.Current,"Letting go before contact hits nothing");
                Assert.IsFalse(game.NativeSwingTracking,"Letting go resets the swing");
                Assert.AreEqual(0,game.NativeSwingState,"The button asks to be held again");
                Assert.IsTrue(game.NativeShotReady,"A reset needs no Ready again");
                Stroke(game,ref time,Q.Identity);
                Assert.AreEqual(GolfGame.State.Aim,game.Current,"A swing after letting go does not count");
                game.NativeStartSwing(Q.Identity);
                Stroke(game,ref time,Q.Identity);
                Assert.AreEqual(GolfGame.State.Flight,game.Current,"Held again, a whole stroke is struck");
                game.NativeReleaseSwing();
                Assert.AreEqual(GolfGame.State.Flight,game.Current,"Letting go after contact changes nothing");
                yield return null;
            }
        }
        [UnityTest, Timeout(120000)] public IEnumerator ALetGoInTheDownswingWaitsAMomentForContact() {
            yield return SceneManager.LoadSceneAsync("Golf",LoadSceneMode.Single);
            yield return null;
            var game=Object.FindFirstObjectByType<GolfGame>(); game.PrepareNativeAddress();
            double time=1;
            // a thumb off just before contact: the ball is still struck
            game.DropBall(game.CurrentHole.Tee); game.NativeReady(); game.NativeStartSwing(Q.Identity);
            Backswing(game,ref time,Q.Identity); Downswing(game,ref time,Q.Identity,3);
            Assert.AreEqual(GolfArcade.Swing.SwingPhase.Downswing,game.Swing.Phase,"the club is on its way down");
            game.NativeReleaseSwing();
            Assert.IsTrue(game.NativeSwingTracking,"A let-go in the downswing waits for contact");
            Downswing(game,ref time,Q.Identity,40);
            Assert.AreEqual(GolfGame.State.Flight,game.Current,"Contact inside the grace keeps the struck ball");
            // a let-go in the downswing that never reaches contact still resets
            yield return new WaitForSeconds(.5f);
            game.DropBall(game.CurrentHole.Tee); game.NativeReady(); game.NativeStartSwing(Q.Identity);
            Backswing(game,ref time,Q.Identity); Downswing(game,ref time,Q.Identity,3);
            game.NativeReleaseSwing();
            yield return new WaitForSeconds(GolfGame.ReleaseGraceSeconds+.15f);
            Assert.AreEqual(GolfGame.State.Aim,game.Current);
            Assert.IsFalse(game.NativeSwingTracking,"No contact after the grace: the swing resets");
        }
        [UnityTest, Timeout(120000)] public IEnumerator StartSwingTakesTheGripOnlyOnceThePhoneIsHeldStill() {
            yield return SceneManager.LoadSceneAsync("Golf",LoadSceneMode.Single);
            yield return null;
            var game=Object.FindFirstObjectByType<GolfGame>(); game.PrepareNativeAddress();
            double time=1;
            game.DropBall(game.CurrentHole.Tee); game.NativeReady(); game.NativeStartSwing();
            Assert.AreEqual(1,game.NativeSwingState,"Without a grip the phone is asked to hold still");
            // lifting the phone from the tap into the stance is not a grip
            for(int i=0;i<100;i++) Sample(game,ref time,i*.02f,3f,Q.Identity);
            Assert.AreEqual(1,game.NativeSwingState,"A moving phone is not a grip");
            for(int i=0;i<30;i++) Sample(game,ref time,2f,0f,Q.Identity);
            Assert.AreEqual(1,game.NativeSwingState,"A moment's stillness is not yet a grip");
            for(int i=0;i<40;i++) Sample(game,ref time,2f,0f,Q.Identity);
            Assert.AreEqual(2,game.NativeSwingState,"Held still in the stance, the grip is set");
        }
    }
}
