from pathlib import Path
import uuid
root=Path('.')
def edit(f,old,new):
 p=root/f;s=p.read_text();assert old in s,f+' missing '+old[:60];p.write_text(s.replace(old,new,1))
def new(f,s):
 p=root/f;p.write_text(s);p.with_suffix(p.suffix+'.meta').write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n')
new('Unity/Assets/Scripts/Game/PresentationPolicy.cs','''using System;
using UnityEngine;
namespace GolfArcade.Game {
    /// Content revision scopes first-view flags; skipping never writes a flag.
    public static class PresentationPolicy {
        public const int Revision = 1;
        public static PresentationCut Preference = PresentationCut.Full;
        public static bool Constrained, BigMoments = true, Multiplayer;
        public static event Action<string> Trace;
        public static void Configure(string preference, bool constrained, bool bigMoments, bool multiplayer) {
            Preference = preference == "off" ? PresentationCut.Off : preference == "short" ? PresentationCut.Short : PresentationCut.Full;
            Constrained = constrained; BigMoments = bigMoments; Multiplayer = multiplayer;
        }
        static string Key(string beat) => "presentation.v" + Revision + "." + beat;
        public static PresentationCut Cut(string beat) => PresentationDirector.Select(Preference, PlayerPrefs.GetInt(Key(beat), 0) == 1, Multiplayer, Constrained);
        public static void Seen(string beat) { PlayerPrefs.SetInt(Key(beat), 1); PlayerPrefs.Save(); }
        public static void Event(string beat, string state, int sequence, string detail = "") {
            var line = $"{Revision}|{sequence}|{beat}|{state}|{Time.realtimeSinceStartupAsDouble:F3}|{detail}";
            Debug.Log("[Presentation] " + line); Trace?.Invoke(line);
        }
    }
}
''')
edit('Unity/Assets/Scripts/Game/NativeSportsSession.cs','public string[] emotes;','public string[] emotes; public string intros="full"; public bool presentationConstrained,bigMoments=true;')
edit('Unity/Assets/Scripts/Game/NativeSportsSession.cs','            TennisQuality.Apply();','            PresentationPolicy.Configure(m.intros,m.presentationConstrained,m.bigMoments,!string.IsNullOrEmpty(m.network));\n            TennisQuality.Apply();')
edit('Unity/Assets/Scripts/Game/NativeSportsSession.cs','            TennisGame.RecordingPointStarted+=SportsRecorderBeginPoint;','            PresentationPolicy.Trace += PresentationTrace;\n            TennisGame.RecordingPointStarted+=SportsRecorderBeginPoint;')
edit('Unity/Assets/Scripts/Game/NativeSportsSession.cs','            TennisGame.RecordingPointStarted-=SportsRecorderBeginPoint;','            PresentationPolicy.Trace -= PresentationTrace;\n            TennisGame.RecordingPointStarted-=SportsRecorderBeginPoint;')
edit('Unity/Assets/Scripts/Game/NativeSportsSession.cs','        void Emit(string type,','        void PresentationTrace(string line) => Emit("presentation",line);\n        void Emit(string type,')
edit('GolfArcade/Unity/SportsSession.swift','    /// A short loading transition, gated by actual runtime readiness.','''    var presentationIntros = UserDefaults.standard.string(forKey: "sports.presentationIntros") ?? "full" {
        didSet { UserDefaults.standard.set(presentationIntros, forKey: "sports.presentationIntros") }
    }
    var presentationBigMoments = (UserDefaults.standard.object(forKey: "sports.presentationBigMoments") as? Bool) ?? true {
        didSet { UserDefaults.standard.set(presentationBigMoments, forKey: "sports.presentationBigMoments") }
    }
    /// A short loading transition, gated by actual runtime readiness.''')
edit('GolfArcade/Unity/SportsSession.swift','        pending=["version":1,','        pending=["intros":presentationIntros,"bigMoments":presentationBigMoments,"presentationConstrained":reduceMotion || ProcessInfo.processInfo.thermalState == .serious || ProcessInfo.processInfo.thermalState == .critical,"version":1,')
edit('GolfArcade/Unity/TennisMenu.swift','case .gameplay: ["level", "resetProgress"]','case .gameplay: ["level", "presentationIntros", "presentationBigMoments", "resetProgress"]')
edit('GolfArcade/Unity/TennisMenu.swift','        case "sound": s.sound.toggle()','''        case "presentationIntros":
            let values = ["full", "short", "off"]
            s.presentationIntros = values[cycle(values.firstIndex(of: s.presentationIntros) ?? 0, values.count)]
        case "presentationBigMoments": s.presentationBigMoments.toggle()
        case "sound": s.sound.toggle()''')
edit('GolfArcade/Unity/IslandScreens.swift','        case "coaching": return Item','''        case "presentationIntros": return Item(title: "Match intros", detail: "Full plays once, then uses short cuts. Off goes straight to Ready.", control: .choice(["Full", "Short", "Off"], ["full", "short", "off"].firstIndex(of: s.presentationIntros) ?? 0))
        case "presentationBigMoments": return Item(title: "Big moments", detail: "Allow one special camera moment per golf hole.", control: .toggle(s.presentationBigMoments))
        case "coaching": return Item''')
