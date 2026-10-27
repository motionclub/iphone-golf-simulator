using GolfArcade.Bowling;
using UnityEngine;

namespace GolfArcade.Game
{
    /// The `bowling` session (PLAN_Bowling.md §4, §11). Same bridge as golf and tennis: the phone's
    /// motion samples stream in on the binary channel and buttons arrive as commands.
    ///
    ///   phone -> Unity   start{sport:"bowling", mode: players "Ana|Sam" (one lane, turns; "cpu:<skill>:<name>" = a computer bowler)}  bowlMove{value: boards, + = left}
    ///                    bowlHold{value: 1 ball held / 0 thumb lifted}  latency{value: TV delay, s}  end
    ///   Unity -> phone   bowling(phase|player|frame|ball|board|grade|mph|hook°|rpm|standing pins), 4 a second
    ///                    bowlCue(top | bottom | crash:<pins>): the self-timed swing's haptic confirmations and the pin crash, the moment they happen
    ///                    bowlingGame("score=..;strikes=..;..."): the game is over (the phone's player), for XP
    public sealed partial class NativeSportsSession
    {
        BowlingGame bowling;

        static string SceneFor(string sport) => sport == "tennis" ? "Tennis" : sport == "bowling" ? "Bowling" : "Golf";

        void BowlingLoaded(Message m)
        {
            bowling.Clock = SportsClock;
            bowling.MotionInput = !m.touch;
            bowling.Cue -= BowlingCue; bowling.Cue += BowlingCue;
            bowling.GameFinished -= BowlingOver; bowling.GameFinished += BowlingOver;
            var players = string.IsNullOrEmpty(m.mode) ? new[] { string.IsNullOrEmpty(m.playerName) ? "You" : m.playerName } : m.mode.Split('|');
            // exhibition: a computer bowler is "cpu:<skill 0..1>:<name>"
            bowling.CpuSkill.Clear();
            for (int i = 0; i < players.Length; i++)
            {
                var part = players[i].Split(new[] { ':' }, 3);
                if (part.Length == 3 && part[0] == "cpu" && float.TryParse(part[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float skill))
                { players[i] = part[2]; while (bowling.CpuSkill.Count < i) bowling.CpuSkill.Add(-1); bowling.CpuSkill.Add(Mathf.Clamp01(skill)); }
            }
            bowling.NewGame(players);
        }

        void BowlingCue(string cue) => Emit("bowlCue", cue);
        void BowlingOver(string summary) => Emit("bowlingGame", summary);

        bool BowlingReceive(Message m)
        {
            if (!bowling) return false;
            switch (m.action)
            {
                case "bowlMove": if (!paused && !float.IsNaN(m.value)) bowling.PlayerMove(Mathf.Clamp(m.value, -39, 39)); return true;
                case "bowlHold": if (!paused) bowling.PlayerHold(m.value > 0); return true;
                case "latency": bowling.DisplayLatency = Mathf.Clamp(m.value, 0, .5f); return true;
            }
            return false;
        }

        void BowlingSample(in Sample s)
        {
            if (bowling && !paused && !touch && s.valid) bowling.NativeMotion(s.time, s.qx, s.qy, s.qz, s.qw, s.rx, s.ry, s.rz);
        }
    }
}
