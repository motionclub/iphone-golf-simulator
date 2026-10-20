from pathlib import Path
import re
p=Path('Unity/Assets/Scripts/Tennis/TennisPresentation.cs');s=p.read_text()
for name in ['Drone','RivalIntro','PlayerIntro','Umpire','Swoop']:s=re.sub(r'\b'+name+r'\b',name[0].lower()+name[1:],s)
s=s.replace('public const float FullLength = 7.2f;','public const float FullLength = 7.2f;\n        public const float Drone=3, RivalIntro=1.2f, PlayerIntro=1.2f, Umpire=.6f, Swoop=1.2f;')
s=s.replace('PresentationPolicy.Seen(entered==0?VenueKey:WalkKey);','PresentationPolicy.Seen(entered==0?VenueKey:WalkKey);\n                if(!skipped && cut==PresentationCut.Full && entered==2) PresentationPolicy.Seen("tennis.start");')
s=s.replace('        void SetBars(float amount)','        void OnDisable() { director.Cancel(); }\n        void SetBars(float amount)')
p.write_text(s)
p=Path('Unity/Assets/Scripts/Game/NativeSportsSession.cs');s=p.read_text();s=s.replace('public bool matchComplete,matchWon,','public bool presentationResultReady=true; public bool matchComplete,matchWon,');s=s.replace('matchComplete=!multiplayerSession','presentationResultReady=!tennis || tennis.PresentationResultsReady,matchComplete=!multiplayerSession');s=s.replace('            TennisQuality.Apply();','            TennisQuality.Apply();\n            PresentationPolicy.Constrained |= TennisQuality.Current==TennisQuality.Tier.Low;')
p.write_text(s)
p=Path('GolfArcade/Unity/SportsSession.swift');s=p.read_text();s=s.replace('    var finishedMatch: (won: Bool, score: String)?','    var finishedMatch: (won: Bool, score: String)?\n    private var resultPresentationReady = true')
s=s.replace('        finishedMatch=nil; lastMatchStats=nil;','        resultPresentationReady = true; finishedMatch=nil; lastMatchStats=nil;',1)
s=s.replace('        guard event["matchComplete"] as? Bool == true,','        guard event["presentationResultReady"] as? Bool != false, event["matchComplete"] as? Bool == true,',1)
s=s.replace('            guard event["session"] as? String == sessionID else { continue }','            guard event["session"] as? String == sessionID else { continue }\n            if let allowed = event["presentationResultReady"] as? Bool { resultPresentationReady = allowed }',1)
s=s.replace('            case "matchOver":','            case "presentation":\n                recordPresentationEvent(event)\n            case "matchOver":\n                guard resultPresentationReady else { continue }',1)
s=s.replace('if active && finishedMatch == nil, let result = SportsRuntime.shared().tennisResult()','if active && resultPresentationReady && finishedMatch == nil, let result = SportsRuntime.shared().tennisResult()')
s=s.replace('    /// Completion is part of every Unity heartbeat,','''    private func recordPresentationEvent(_ event: [String: Any]) {
        let directory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("presentation/\\(sessionID)", isDirectory: true)
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let path = directory.appendingPathComponent("beat_events.jsonl")
        guard let data = try? JSONSerialization.data(withJSONObject: event, options: .sortedKeys) else { return }
        if !FileManager.default.fileExists(atPath: path.path) { FileManager.default.createFile(atPath: path.path, contents: nil) }
        if let file = try? FileHandle(forWritingTo: path) { defer { try? file.close() }; try? file.seekToEnd(); try? file.write(contentsOf: data + Data([10])) }
    }
    /// Completion is part of every Unity heartbeat,''',1)
p.write_text(s)
p=Path('Unity/Assets/Scripts/Tennis/TennisGame.cs');s=p.read_text().replace('cut==GolfArcade.Game.PresentationCut.Full?1.5f:1f','cut==GolfArcade.Game.PresentationCut.Full?1.45f:1f')
s=s.replace('GolfArcade.Game.PresentationPolicy.Event(Flow==Phase.MatchOver?"MatchEnd":"Point","complete",pointBeatSequence);','''{ GolfArcade.Game.PresentationPolicy.Event(Flow==Phase.MatchOver?"MatchEnd":"Point","complete",pointBeatSequence);
                    if(GolfArcade.Game.PresentationPolicy.Cut("tennis.reaction")==GolfArcade.Game.PresentationCut.Full) GolfArcade.Game.PresentationPolicy.Seen("tennis.reaction"); }''')
p.write_text(s)
p=Path('Unity/Assets/Scripts/Game/GolfGame.Results.cs');s=p.read_text();s=s.replace('float ResultReactionSeconds => LastShot!=null && LastShot.IsHoled ? PresentationDirector.GolfReaction(holeStrokes-hole.Par,holeStrokes==1,PresentationPolicy.Cut("golf.reaction")) : .5f;','''float ResultReactionSeconds => LastShot!=null && LastShot.IsHoled ? Mathf.Max(PresentationDirector.GolfReaction(holeStrokes-hole.Par,holeStrokes==1,PresentationPolicy.Cut("golf.reaction")), PresentationDirector.Budget(holeIndex+1>=course.Holes.Length?PresentationBeat.MatchEnd:PresentationBeat.HoleOut,true,PresentationPolicy.Cut("golf.boundary"))) : .5f;
        bool boundaryPresented;''')
s=s.replace('            AfterResult();','            boundaryPresented = LastShot.IsHoled;\n            AfterResult();',1)
p.write_text(s)
p=Path('Unity/Assets/Scripts/Game/GolfGame.cs');s=p.read_text().replace('if (stateTime >= PresentationDirector.Budget','if (boundaryPresented || stateTime >= PresentationDirector.Budget',1).replace('                        // another golfer on this phone still','                        boundaryPresented=false;\n                        // another golfer on this phone still',1);p.write_text(s)
