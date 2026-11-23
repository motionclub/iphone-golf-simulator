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
            public string kind;        // "throw" | "hb" (heartbeat between turns) | phone casting: "setup" (the bowler lining up), "pinfall"
            public int ball, seat, grade, after;
            public float board, speed, rpm, axis, launch, loft;
            /// "setup": the aim, and where the bowler is (0 set up, 1 holding the ball, the approach follows on its own).
            public float aim; public int phase;
            /// "setup": its order (slides travel unreliably, holds reliably, so they can cross: an older word never undoes a newer).
            public int seq;
            /// "emote": the TennisEmotes id a waiting player played (BowlingGame.Emotes).
            public string emote;
        }

        // ---------------------------------------------------------------- phone casting (PLAN_PhoneCasting_GolfBowling.md)
        // One phone is the screen (it bowls for no one) and each player's phone is only their controller, with no picture of its own. So the
        // bowler's phone tells the screen how it is lining up as it happens (board, aim, holding the ball), sends its throw the moment the
        // ball leaves the hand (not once its pins have settled), and its pinfall after; the screen walks the bowler up live, lets go on the
        // bowler's beat, and scores the ball with the bowler's pinfall as before, so every sheet still agrees.
        /// A phone in this game is the screen.
        bool CastMatch => net != null && net.HasCastScreen;
        /// This phone is that screen (it bowls for no one).
        bool CastScreenHere => CastMatch && localIndex < 0;
        readonly Dictionary<int, int> remotePinfalls = new Dictionary<int, int>();
        /// The screen walked another phone's bowler up as it happened; their ball has not arrived yet (never let go here on its own).
        bool remoteApproach;
        float pinfallWait, nextSetupSend; string sentSetup; int setupSeq, mirroredSeq = -1, mirroredBall = -1;
        /// How long the screen holds a ball's score for its bowler's pinfall before it scores its own (the same ball, the same physics).
        const float PinfallWaitSeconds = 3f;

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
            remotePinfalls.Clear(); remoteApproach = false; pinfallWait = 0; sentSetup = null; setupSeq = 0; mirroredSeq = mirroredBall = -1;
            CpuSkill.Clear(); Autoplay.Clear();
            PlayerFemale.Clear(); PlayerFemale.AddRange(seated.Select(p => p.female));
            PlayerLook.Clear(); PlayerLook.AddRange(seated.Select(p => (p.loadout?.skinHex ?? "", p.loadout?.shirtHex ?? "", p.loadout?.shortsHex ?? "", p.loadout?.shoesHex ?? "")));
            EquipNetworkEmotes(seated.Select(p => p.loadout?.emotes));
            NewGame(seated.Select(p => string.IsNullOrEmpty(p.name) ? "Player" : p.name).ToList());
        }

        /// A packet from another phone (SportsMultiplayer's "peer").
        public void ReceiveNetwork(string payload)
        {
            NetBall m; try { m = JsonUtility.FromJson<NetBall>(payload); } catch { return; }
            if (m != null && m.kind == "emote") { ReceiveEmote(m); return; }   // (any time: not tied to a ball)
            if (m == null || m.ball < ballsBowled) return;
            if (m.kind == "throw") remoteBalls[m.ball] = m;
            else if (m.kind == "pinfall" && CastMatch) remotePinfalls[m.ball] = m.after;
            else if (m.kind == "setup" && CastMatch) MirrorSetup(m);
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
            // another phone's ball arrived and its bowler is set: bowl it here (on the screen, into the approach it is already walking)
            bool walkingIt = remoteApproach && Flow == Phase.Approach && !released;
            if ((Flow == Phase.Setup || walkingIt) && !IsLocal(Current) && remoteBall == null && (walkingIt || !Bowler || (ballInHand && Bowler.Arrived)) && remoteBalls.TryGetValue(ballsBowled, out var m))
            {
                remoteBalls.Remove(ballsBowled); remoteBall = m;
                boards[Current] = m.board; authAfter = m.after;
                if (!walkingIt) { Flow = Phase.Approach; approachT = 0; released = false; hud?.FoldSheet(); Bowler?.PlayClip(BowlingClips.Shot, 0, false, true); }
            }
            // (after the ball: a pinfall that came with it is not overwritten by the throw's own "not known yet")
            if (CastMatch) CastUpdate();
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

        /// Phone casting, each frame: the bowler's phone tells how it is lining up; the screen takes the bowler's pinfall as it arrives.
        void CastUpdate()
        {
            if (!IsLocal(Current) && authAfter < 0 && remotePinfalls.TryGetValue(ballsBowled, out int after)) { remotePinfalls.Remove(ballsBowled); authAfter = after; }
            if (!IsLocal(Current) || IsCpu(Current) || (Flow != Phase.Setup && Flow != Phase.Hold)) return;
            int phase = Flow == Phase.Hold ? 1 : 0;
            string key = $"{ballsBowled}|{Board:0.#}|{AimDeg:0.##}|{phase}";
            if (key == sentSetup) return;
            bool phaseChanged = sentSetup == null || !sentSetup.EndsWith("|" + phase);
            if (!phaseChanged && Time.unscaledTime < nextSetupSend) return;
            sentSetup = key; nextSetupSend = Time.unscaledTime + .1f;
            var m = new NetBall { kind = "setup", ball = ballsBowled, seat = Current < seatOfPlayer.Length ? seatOfPlayer[Current] : -1, board = Board, aim = AimDeg, phase = phase, seq = ++setupSeq };
            SportsMultiplayer.Instance?.SendPeer(JsonUtility.ToJson(m), phaseChanged);   // (a hold or its end for certain; the slide as it moves)
        }
        /// The screen: another phone's bowler lining up, shown as it happens (their board and aim, picking the ball up, putting it down).
        /// The approach then starts by itself after the hold, as it does on the bowler's phone.
        void MirrorSetup(NetBall m)
        {
            if (m.ball != ballsBowled || IsLocal(Current) || IsCpu(Current) || remoteBall != null || released) return;
            if (Current >= seatOfPlayer.Length || seatOfPlayer[Current] != m.seat) return;
            if (m.ball == mirroredBall && m.seq <= mirroredSeq) return;
            mirroredBall = m.ball; mirroredSeq = m.seq;
            // put down just as the walk-up began here (the word crossed with it): back to the set-up, the throw is not coming
            if (m.phase == 0 && Flow == Phase.Approach && remoteApproach) { remoteApproach = false; Flow = Phase.Setup; holdT = approachT = 0; Bowler?.PlayClip(BowlingClips.Abort); }
            if (Flow != Phase.Setup && Flow != Phase.Hold) return;
            boards[Current] = Mathf.Clamp(m.board, 3, 37); aims[Current] = Mathf.Clamp(m.aim, -MaxAim, MaxAim);
            if (m.phase == 1 && Flow == Phase.Setup) { Flow = Phase.Hold; holdT = 0; }
            else if (m.phase == 0 && Flow == Phase.Hold) { Flow = Phase.Setup; Bowler?.PlayClip(BowlingClips.Abort); }
        }
        /// The screen holds a ball's score until its bowler's pinfall is here (or a few seconds have gone): every sheet the same.
        bool WaitingForPinfall(float dt)
        {
            if (!CastMatch || IsLocal(Current) || authAfter >= 0) { pinfallWait = 0; return false; }
            pinfallWait += dt;
            if (pinfallWait < PinfallWaitSeconds) return true;
            pinfallWait = 0; return false;
        }
        void SendPinfall(int after)
        {
            authAfter = after;
            var m = new NetBall { kind = "pinfall", ball = ballsBowled, seat = Current < seatOfPlayer.Length ? seatOfPlayer[Current] : -1, after = after };
            SportsMultiplayer.Instance?.SendPeer(JsonUtility.ToJson(m), true);
        }

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
            CardReady?.Invoke(Card());
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
