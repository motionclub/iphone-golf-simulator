using System;
using System.Text;
using GolfArcade.Multiplayer;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// The versus link's compact pose and score checksum (VersusWire; TennisGame.Versus). The live two-phone path is exercised by
    /// VersusPeerCapture (work/tennis-online-resilience/run_versus_harness.sh).
    public class VersusWireTests
    {
        static VersusMessage Pose() => new()
        {
            k = "pose", s = 1, n = 123, t = 12345.678912, x = -3.14159f, z = -11.875f, vx = -4.25f, vz = 1.5f, prep = .875f, pt = 2.375f, wind = -1,
            bh = true, serve = false, held = true, walk = true
        };

        [Test] public void PoseRoundTripsWithinAMillimetre()
        {
            var sent = Pose();
            string text = VersusWire.EncodePose(sent);
            Assert.IsTrue(VersusWire.IsPose(text), text);
            Assert.IsTrue(VersusWire.TryDecodePose(text, out var got), text);
            Assert.AreEqual("pose", got.k); Assert.AreEqual(1, got.s); Assert.AreEqual(123, got.n);
            Assert.AreEqual(sent.t, got.t, 1e-4);
            Assert.AreEqual(sent.x, got.x, 1e-3f); Assert.AreEqual(sent.z, got.z, 1e-3f); Assert.AreEqual(sent.vx, got.vx, 1e-3f); Assert.AreEqual(sent.vz, got.vz, 1e-3f);
            Assert.AreEqual(sent.prep, got.prep, 1e-3f); Assert.AreEqual(sent.pt, got.pt, 1e-3f); Assert.AreEqual(sent.wind, got.wind, 1e-3f);
            Assert.IsTrue(got.bh); Assert.IsFalse(got.serve); Assert.IsTrue(got.held); Assert.IsTrue(got.walk);
        }

        /// The pose packet as Unity hands it to the phone (NetworkPacket with real-length ids) is a fraction of what Game Center may
        /// refuse unreliably (MultiplayerTuning.unreliableSafeBytes = 900); the old JSON pose was close to it.
        [Test] public void PosePacketIsSmallAndTheOldJsonWasNot()
        {
            string compact = VersusWire.EncodePose(Pose());
            string json = JsonUtility.ToJson(Pose());
            int Packet(string payload) => Encoding.UTF8.GetByteCount(JsonUtility.ToJson(new NetworkPacket
            {
                lobbyID = Guid.NewGuid().ToString(), matchID = Guid.NewGuid().ToString(), sender = "T:_" + new string('a', 32), kind = "peer", payload = payload, reliable = false, sentAt = 12345.678901
            }));
            int compactBytes = Packet(compact), jsonBytes = Packet(json);
            TestContext.WriteLine($"pose payload {Encoding.UTF8.GetByteCount(compact)} B, packet {compactBytes} B; old JSON payload {Encoding.UTF8.GetByteCount(json)} B, packet {jsonBytes} B");
            Assert.Less(Encoding.UTF8.GetByteCount(compact), 100);
            Assert.Less(compactBytes, 400);
            Assert.Greater(jsonBytes, compactBytes * 2, "the compact pose is the point of the exercise");
        }

        [Test] public void BrokenPosesAreRefused()
        {
            Assert.IsFalse(VersusWire.TryDecodePose(null, out _));
            Assert.IsFalse(VersusWire.TryDecodePose("{\"k\":\"pose\"}", out _));
            Assert.IsFalse(VersusWire.TryDecodePose("P|1|2|3", out _));
            Assert.IsFalse(VersusWire.TryDecodePose("P|1|2|3|NaN|0|0|0|0|0|0|0", out _));
            Assert.IsFalse(VersusWire.TryDecodePose("P|1|2|3|x|0|0|0|0|0|0|0", out _));
            Assert.IsFalse(VersusWire.TryDecodePose("P|" + new string('1', 300), out _));
            Assert.IsTrue(VersusWire.TryDecodePose("P|0|0|1.5|0|0|0|0|0|0|0|0", out var zero));
            Assert.AreEqual(1.5, zero.t, 1e-9);
        }

        [Test] public void BothSeatsComputeTheSameChecksumForTheSameScore()
        {
            // seat 0's phone keeps the match from its side; seat 1's phone keeps the mirror of it
            var seat0 = TennisMatch.New(true, 1, 3);
            var seat1 = seat0.Mirrored();
            int a = VersusWire.ScoreChecksum(VersusWire.SeatZeroView(seat0, 0)), b = VersusWire.ScoreChecksum(VersusWire.SeatZeroView(seat1, 1));
            Assert.AreEqual(a, b);
            Assert.AreNotEqual(0, a, "0 means 'not sent'");
            for (int i = 0; i < 9; i++)
            {
                bool toSeat0 = i % 3 != 1;
                seat0.AwardPoint(toSeat0); seat1.AwardPoint(!toSeat0);
                Assert.AreEqual(VersusWire.ScoreChecksum(VersusWire.SeatZeroView(seat0, 0)), VersusWire.ScoreChecksum(VersusWire.SeatZeroView(seat1, 1)), $"after point {i + 1}");
            }
        }

        [Test] public void OnePointMoreOnOnePhoneChangesTheChecksum()
        {
            var seat0 = TennisMatch.New(true, 1, 3);
            var seat1 = seat0.Mirrored();
            seat0.AwardPoint(true);   // a call that never reached seat 1
            Assert.AreNotEqual(VersusWire.ScoreChecksum(VersusWire.SeatZeroView(seat0, 0)), VersusWire.ScoreChecksum(VersusWire.SeatZeroView(seat1, 1)));
            seat1.AwardPoint(false);
            Assert.AreEqual(VersusWire.ScoreChecksum(VersusWire.SeatZeroView(seat0, 0)), VersusWire.ScoreChecksum(VersusWire.SeatZeroView(seat1, 1)));
            seat1.AwardPoint(true); seat0.AwardPoint(true);   // the same count of points, the other way round
            Assert.AreNotEqual(VersusWire.ScoreChecksum(VersusWire.SeatZeroView(seat0, 0)), VersusWire.ScoreChecksum(VersusWire.SeatZeroView(seat1, 1)));
        }

        /// ApplySync's guard: an empty or broken score (JsonUtility makes an empty match of it) is never played on.
        [Test] public void AnEmptySyncScoreIsNotPlayable()
        {
            Assert.IsFalse(VersusWire.Playable(default));
            Assert.IsFalse(VersusWire.Playable(JsonUtility.FromJson<TennisMatch>("{}")));
            var m = TennisMatch.New(false, 1, 6);
            Assert.IsTrue(VersusWire.Playable(m));
            Assert.IsTrue(VersusWire.Playable(JsonUtility.FromJson<TennisMatch>(JsonUtility.ToJson(m)).Mirrored()));
        }

        /// The ready handshake's message keeps its point number and checksum through JsonUtility (both phones run the same build).
        [Test] public void ReadyCarriesPointAndChecksum()
        {
            var ready = JsonUtility.FromJson<VersusMessage>(JsonUtility.ToJson(new VersusMessage { k = "ready", n = 7, sum = -123456789 }));
            Assert.AreEqual(7, ready.n); Assert.AreEqual(-123456789, ready.sum);
            var old = JsonUtility.FromJson<VersusMessage>("{\"k\":\"ready\",\"n\":7}");
            Assert.AreEqual(0, old.sum, "a phone that sends no checksum is read as 0 (taken at its word)");
        }

        /// The toss carries its fall after the top (a slow-TV server's is slower), so the other phone draws the same toss; a phone
        /// on an older build sends none, and its toss falls at full gravity as it always did.
        [Test] public void TossCarriesItsFallAndAnOlderPhoneFallsAtFullGravity()
        {
            var toss = JsonUtility.FromJson<VersusMessage>(JsonUtility.ToJson(new VersusMessage { k = "toss", p = Vector3.one, d = Vector3.right, acc = .9f, fall = 4.15f }));
            Assert.AreEqual(4.15f, VersusWire.TossFall(toss.fall), 1e-5f);
            var old = JsonUtility.FromJson<VersusMessage>("{\"k\":\"toss\",\"p\":{\"x\":1,\"y\":1,\"z\":1},\"d\":{\"x\":1,\"y\":0,\"z\":0},\"acc\":0.9}");
            Assert.AreEqual(0, old.fall);
            Assert.AreEqual(9.81f, VersusWire.TossFall(old.fall), "no fall sent = full gravity");
            foreach (float broken in new[] { float.NaN, float.PositiveInfinity, float.NegativeInfinity, -3f, 0f, 25f })
                Assert.AreEqual(9.81f, VersusWire.TossFall(broken), $"{broken}");
            Assert.AreEqual(VersusWire.SlowestTossFall, VersusWire.TossFall(.01f), "a near-zero fall would hang the ball in the air");
        }

        /// Every fall the server's own game can pick (TennisRules.ServeFallGravity, any TV delay, any hero's strike height) reaches
        /// the other phone unchanged: the bounds in TossFall only catch broken values.
        [Test] public void EveryServerTossFallReachesTheOtherPhoneUnchanged()
        {
            for (float lag = 0; lag <= 1.5f; lag += .05f)
                for (float drop = .2f; drop <= 1.9f; drop += .1f)
                {
                    float g = TennisRules.ServeFallGravity(lag, drop, TennisRules.ServePace);
                    Assert.AreEqual(g, VersusWire.TossFall(g), $"lag {lag:0.00} s, drop {drop:0.0} m");
                }
        }
    }
}
