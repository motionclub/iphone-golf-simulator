using System;
using System.Collections.Generic;
using System.Linq;
using GolfArcade.Multiplayer;
using UnityEngine;

namespace GolfArcade.Bowling
{
    /// Bowling across phones (local or online), one lane, players taking turns (PLAN_Bowling.md §13: "1 by 1"). Like tennis versus,
    /// every phone runs the whole game itself and only the balls travel: the bowler's phone bowls its own ball with its own swing,
    /// then sends the throw (board, speed, revs, axis, launch, loft, grade) and its pinfall as soon as its pin physics has settled
    /// it. Every other phone bowls that same throw on its own lane (the integrator is deterministic) and scores it with the
    /// bowler's pinfall, so every score sheet agrees. A player who drops is bowled for by the host as a computer bowler.
    public sealed partial class BowlingGame
    {
        [Serializable] public sealed class NetBall
        {
            public string kind;        // "throw" | "hb" (heartbeat between turns)
            public int ball, seat, grade, after;
            public float board, speed, rpm, axis, launch, loft;
        }

        NetworkConfiguration net;
        int localIndex = -1;
        int[] seatOfPlayer = new int[0];
        readonly Dictionary<int, NetBall> remoteBalls = new Dictionary<int, NetBall>();
        readonly HashSet<int> hostBowls = new HashSet<int>();
        int ballsBowled, authAfter = -1;
        bool netSendPending;
        float nextBeat;
        NetBall remoteBall;

        public bool Networked => net != null;
        bool HostPhone => net != null && net.hostID == net.localID;
        /// The player this phone bowls for (0 when alone or passing the phone; -1 for a spectator).
        public int LocalPlayer => Networked ? localIndex : 0;
        /// This phone bowls for that player: always when alone; in a network game, its own seat (and the host, a dropped player's).
        public bool IsLocal(int player) => !Networked || player == localIndex || (HostPhone && hostBowls.Contains(player));

        /// A network game: the seated players in seat order, this phone's own among them.
        public void ConfigureNetwork(NetworkConfiguration c)
        {
            net = c;
            var seated = c.participants.Where(p => p.seat >= 0).OrderBy(p => p.seat).ToList();
            seatOfPlayer = seated.Select(p => p.seat).ToArray();
            localIndex = seated.FindIndex(p => p.id == c.localID);
            remoteBalls.Clear(); hostBowls.Clear(); ballsBowled = 0; authAfter = -1; remoteBall = null; netSendPending = false;
            CpuSkill.Clear(); Autoplay.Clear();
            PlayerFemale.Clear(); PlayerFemale.AddRange(seated.Select(p => p.female));
            PlayerLook.Clear(); PlayerLook.AddRange(seated.Select(p => (p.loadout?.skinHex ?? "", p.loadout?.shirtHex ?? "", p.loadout?.shortsHex ?? "", p.loadout?.shoesHex ?? "")));
            NewGame(seated.Select(p => string.IsNullOrEmpty(p.name) ? "Player" : p.name).ToList());
        }

        /// A packet from another phone (SportsMultiplayer's "peer").
        public void ReceiveNetwork(string payload)
        {
            NetBall m; try { m = JsonUtility.FromJson<NetBall>(payload); } catch { return; }
            if (m == null || m.kind != "throw" || m.ball < ballsBowled) return;
            remoteBalls[m.ball] = m;
        }

        /// A player left the game: the host bowls the rest of their frames as a computer bowler (the others see the balls arrive as usual).
        public void NetworkDrop(int seat)
        {
            int player = Array.IndexOf(seatOfPlayer, seat);
            if (player < 0 || !HostPhone) return;
            hostBowls.Add(player);
            while (CpuSkill.Count <= player) CpuSkill.Add(-1);
            CpuSkill[player] = .5f;
            if (Current == player && Flow == Phase.Setup) EnterSetup();
        }

        void NetworkUpdate()
        {
            if (!Networked) return;
            // between turns nothing else travels: a heartbeat keeps the link from looking dropped
            if (Time.unscaledTime >= nextBeat) { nextBeat = Time.unscaledTime + 1; SportsMultiplayer.Instance?.SendPeer("{\"kind\":\"hb\"}", false); }
            // another phone's ball arrived and its bowler is set: bowl it here
            if (Flow == Phase.Setup && !IsLocal(Current) && remoteBall == null && (!Bowler || Bowler.Arrived) && remoteBalls.TryGetValue(ballsBowled, out var m))
            {
                remoteBalls.Remove(ballsBowled); remoteBall = m;
                boards[Current] = m.board; authAfter = m.after;
                Flow = Phase.Approach; approachT = 0; released = false;
                Bowler?.PlayClip(BowlingClips.Shot, 0, false, true);
            }
            // the remote bowler lets go at the moment the bowler did (the grade carries the timing)
            if (Flow == Phase.Approach && remoteBall != null && approachT >= BowlingApproach.IdealRelease + GradeTiming((ReleaseGrade)remoteBall.grade))
            {
                var m2 = remoteBall; remoteBall = null;
                Deliver(new BowlingThrow { Board = m2.board, Speed = m2.speed, RevRpm = m2.rpm, AxisDeg = m2.axis, LaunchDeg = m2.launch, LoftHeight = m2.loft, Grade = (ReleaseGrade)m2.grade });
            }
        }

        /// When a release of that grade leaves the hand, against the ideal (for the remote bowler's animation).
        static float GradeTiming(ReleaseGrade g) => g switch
        {
            ReleaseGrade.Early => -.15f, ReleaseGrade.Late => .15f, ReleaseGrade.Foul => BowlingRelease.MissWindow + .05f,
            ReleaseGrade.Drop => -1f, _ => 0,
        };

        void SendThrow(BowlingThrow th, int after)
        {
            authAfter = after;
            var m = new NetBall
            {
                kind = "throw", ball = ballsBowled, seat = Current < seatOfPlayer.Length ? seatOfPlayer[Current] : -1, grade = (int)th.Grade, after = after,
                board = th.Board, speed = th.Speed, rpm = th.RevRpm, axis = th.AxisDeg, launch = th.LaunchDeg, loft = th.LoftHeight,
            };
            SportsMultiplayer.Instance?.SendPeer(JsonUtility.ToJson(m), true);
        }

        /// The game is over: this phone's player's line for XP, and (host) the lobby's result.
        void GameOver()
        {
            int me = LocalPlayer;
            if (me >= 0) GameFinished?.Invoke(Summary(me));
            if (Networked && HostPhone)
            {
                int winner = Leader();
                string score = string.Join("-", Scores.Select(s => s.Total));
                SportsMultiplayer.Instance?.BowlingResult(winner < seatOfPlayer.Length ? seatOfPlayer[winner] : -1, score);
            }
        }
    }
}
