using System;
using System.Globalization;
using System.Text;

namespace GolfArcade.Tennis
{
    /// The versus link's compact forms (TennisGame.Versus).
    ///
    /// POSE: the 30 Hz pose goes as one short line of text ("P|seat|point|time|x|z|vx|vz|prep|pt|wind|flags", about 60 bytes) instead of
    /// a VersusMessage's JSON (every field of the class, ~500 bytes, then escaped again inside the packet). Small enough that Game Center
    /// never refuses it as an unreliable message, so the peer channel never has to fall back to reliable delivery.
    ///
    /// TOSS: the toss carries its gravity after the top (slower on the server's slow TV), so the other phone draws the same fall.
    ///
    /// SCORE: both phones' "ready" for a point carry a checksum of the score as seat 0 sees it; a point starts only when the two agree.
    public static class VersusWire
    {
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
        const char Sep = '|';

        public static bool IsPose(string text) => text != null && text.Length > 2 && text[0] == 'P' && text[1] == Sep;

        public static string EncodePose(VersusMessage m)
        {
            int flags = (m.bh ? 1 : 0) | (m.serve ? 2 : 0) | (m.held ? 4 : 0) | (m.walk ? 8 : 0);
            var b = new StringBuilder(80);
            b.Append('P').Append(Sep).Append(m.s).Append(Sep).Append(m.n).Append(Sep).Append(m.t.ToString("0.####", Inv));
            Num(b, m.x); Num(b, m.z); Num(b, m.vx); Num(b, m.vz); Num(b, m.prep); Num(b, m.pt); Num(b, m.wind);
            b.Append(Sep).Append(flags);
            return b.ToString();
        }
        static void Num(StringBuilder b, float v) => b.Append(Sep).Append(float.IsNaN(v) || float.IsInfinity(v) ? "0" : v.ToString("0.###", Inv));

        public static bool TryDecodePose(string text, out VersusMessage m)
        {
            m = null;
            if (!IsPose(text) || text.Length > 256) return false;
            var f = text.Split(Sep);
            if (f.Length != 12) return false;
            const NumberStyles N = NumberStyles.Float;
            if (!int.TryParse(f[1], NumberStyles.Integer, Inv, out int s) || !long.TryParse(f[2], NumberStyles.Integer, Inv, out long n)
                || !double.TryParse(f[3], N, Inv, out double t) || !int.TryParse(f[11], NumberStyles.Integer, Inv, out int flags)) return false;
            var v = new float[7];
            for (int i = 0; i < 7; i++) if (!float.TryParse(f[4 + i], N, Inv, out v[i]) || float.IsNaN(v[i]) || float.IsInfinity(v[i])) return false;
            if (double.IsNaN(t) || double.IsInfinity(t)) return false;
            m = new VersusMessage { k = "pose", s = s, n = n, t = t, x = v[0], z = v[1], vx = v[2], vz = v[3], prep = v[4], pt = v[5], wind = v[6],
                bh = (flags & 1) != 0, serve = (flags & 2) != 0, held = (flags & 4) != 0, walk = (flags & 8) != 0 };
            return true;
        }

        /// Full gravity, and the slowest toss fall a sent value is taken at: below any TennisRules.ServeFallGravity gives (~2.3 for
        /// the real heroes at the 1 s cap, and above this for any strike at least 0.1 m under the top), so it only catches broken ones.
        public const float FullTossFall = 9.81f, SlowestTossFall = .1f;

        /// The toss fall the other phone sent: an older phone sends none (0); a broken one is full gravity, and none is slower than SlowestTossFall.
        public static float TossFall(float sent) => float.IsNaN(sent) || sent <= 0 ? FullTossFall : Math.Min(FullTossFall, Math.Max(SlowestTossFall, sent));

        /// The score as seat 0 sees it (a match is kept from its own phone's side).
        public static TennisMatch SeatZeroView(TennisMatch m, int seat) => seat == 0 ? m : m.Mirrored();

        /// A checksum of the whole score (points, games, sets, finished sets, the server, tiebreak, the result), from seat 0's side.
        /// Never 0: 0 means "not sent" (a phone that never sent one is taken at its word).
        public static int ScoreChecksum(TennisMatch seatZero)
        {
            var b = new StringBuilder(64);
            b.Append(seatZero.SetsToWin).Append(',').Append(seatZero.GamesPerSet).Append(';')
             .Append(seatZero.PlayerPoints).Append(',').Append(seatZero.OpponentPoints).Append(';')
             .Append(seatZero.PlayerGames).Append(',').Append(seatZero.OpponentGames).Append(';')
             .Append(seatZero.PlayerSets).Append(',').Append(seatZero.OpponentSets).Append(';')
             .Append(seatZero.Tiebreak ? 'T' : 't').Append(seatZero.PlayerServes ? 'S' : 's').Append(seatZero.Complete ? 'C' : 'c').Append(seatZero.PlayerWonMatch ? 'W' : 'w');
            if (seatZero.SetScores != null) foreach (var set in seatZero.SetScores) b.Append(';').Append(set);
            uint h = 2166136261;
            foreach (char c in b.ToString()) { h ^= c; h *= 16777619; }
            int sum = (int)h;
            return sum == 0 ? 1 : sum;
        }

        /// A score the other phone sent is one this game can play on (JsonUtility turns an empty or broken text into an empty match).
        public static bool Playable(TennisMatch m) =>
            m.SetsToWin >= 1 && m.SetsToWin <= 3 && m.GamesPerSet >= 1 && m.GamesPerSet <= 7
            && m.PlayerPoints >= 0 && m.OpponentPoints >= 0 && m.PlayerGames >= 0 && m.OpponentGames >= 0 && m.PlayerSets >= 0 && m.OpponentSets >= 0;
    }
}
