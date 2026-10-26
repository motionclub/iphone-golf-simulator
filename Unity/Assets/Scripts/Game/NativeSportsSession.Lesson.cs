using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using GolfArcade.Tennis;

namespace GolfArcade.Game
{
    /// Lessons (PLAN_Onboarding_GolfLesson.md): the phone starts one with `lesson` set; the sport's lesson runs on the game and
    /// reports each station and attempt as a "lesson" event, which the phone draws over the TV (LessonCenter / LessonOverlay).
    public sealed partial class NativeSportsSession
    {
        public partial class Message { public bool lesson; public int lessonStation; }

        /// The running lesson's reports to the phone (null outside a lesson).
        public static Action<string> LessonReport;

        void LessonAttach(Message m)
        {
            LessonReport = null;
            if (!m.lesson) return;
            LessonReport = json => Emit("lesson", json);
            if (golf) golf.gameObject.AddComponent<GolfLesson>().Begin(golf, m.lessonStation);
            if (tennis) tennis.BeginLesson(m.lessonStation);
        }

        /// The phone's "Skip this step" (offered after three misses at one station).
        bool LessonReceive(Message m)
        {
            if (m.action != "lessonSkip") return false;
            if (golf && golf.TryGetComponent<GolfLesson>(out var g)) g.SkipStation();
            if (tennis && tennis.TryGetComponent<TennisTutorial>(out var t)) t.SkipStep();
            return true;
        }
    }

    /// The JSON a lesson sends (built by hand: the Shot Read rows mix strings and numbers, which JsonUtility cannot write).
    public static class LessonJson
    {
        public static string Station(string sport, int index, int count, string key, string name, string title, string ask, string hint, IList<string> tips)
        {
            var b = new StringBuilder("{\"kind\":\"station\"");
            Field(b, "sport", sport); Field(b, "index", index); Field(b, "count", count); Field(b, "key", key); Field(b, "name", name);
            Field(b, "title", title); Field(b, "ask", ask); Field(b, "hint", hint);
            b.Append(",\"tips\":[");
            for (int i = 0; i < (tips?.Count ?? 0); i++) { if (i > 0) b.Append(','); Str(b, tips[i]); }
            return b.Append("]}").ToString();
        }
        /// `read`: rows of (key, value, state) where state is 1 good, 0 a fault, 2 a note.
        public static string Attempt(bool pass, string grade, string text, int misses, IList<(string key, string value, int state)> read)
        {
            var b = new StringBuilder("{\"kind\":\"attempt\"");
            Field(b, "result", pass ? "pass" : "miss"); Field(b, "grade", grade); Field(b, "text", text); Field(b, "misses", misses);
            b.Append(",\"read\":[");
            for (int i = 0; i < (read?.Count ?? 0); i++)
            {
                if (i > 0) b.Append(',');
                b.Append('['); Str(b, read[i].key); b.Append(','); Str(b, read[i].value); b.Append(',').Append(read[i].state.ToString(CultureInfo.InvariantCulture)).Append(']');
            }
            return b.Append("]}").ToString();
        }
        public static string Done(string sport) => "{\"kind\":\"done\",\"sport\":\"" + sport + "\"}";

        static void Field(StringBuilder b, string name, string value) { b.Append(",\"").Append(name).Append("\":"); Str(b, value); }
        static void Field(StringBuilder b, string name, int value) => b.Append(",\"").Append(name).Append("\":").Append(value.ToString(CultureInfo.InvariantCulture));
        static void Str(StringBuilder b, string s)
        {
            b.Append('"');
            foreach (char c in s ?? "")
            {
                if (c == '"' || c == '\\') b.Append('\\').Append(c);
                else if (c == '\n') b.Append("\\n");
                else if (c < ' ') b.Append(' ');
                else b.Append(c);
            }
            b.Append('"');
        }
    }
}
