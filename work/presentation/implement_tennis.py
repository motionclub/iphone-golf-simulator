from pathlib import Path
p=Path('Unity/Assets/Scripts/Tennis/TennisPresentation.cs');s=p.read_text();s=s.replace('using UnityEngine;','using GolfArcade.Game;\nusing UnityEngine;',1)
s=s.replace('public const float Drone = 5.2f, RivalIntro = 3.8f, PlayerIntro = 3.8f, Umpire = 1.3f, Swoop = 1.3f;\n        public const float Length = Drone + RivalIntro + PlayerIntro + Umpire + Swoop;','''public const float FullLength = 7.2f;
        float Drone = 3f, RivalIntro = 1.2f, PlayerIntro = 1.2f, Umpire = .6f, Swoop = 1.2f;
        float Length => Drone + RivalIntro + PlayerIntro + Umpire + Swoop;
        readonly PresentationDirector director = new();
        int beatIndex; bool skipped;
        PresentationCut venueCut, walkCut, startCut;
        string VenueKey => "tennis.venue." + TennisVenue.Selected;
        string WalkKey => "tennis.walkon";
        public void RestartShared() {
            director.Cancel(); t=0; skipped=false; rivalEmoted=playerEmoted=umpireCalled=chosenPlayed=false;
            chosenEmote=null; shownName=null; Configure(true); hud.MatchVisible=false;
        }
        void Configure(bool shared = false) {
            venueCut = shared ? PresentationCut.Short : PresentationPolicy.Cut(VenueKey);
            walkCut = shared ? PresentationCut.Short : PresentationPolicy.Cut(WalkKey);
            startCut = shared ? PresentationCut.Short : PresentationPolicy.Cut("tennis.start");
            Drone=PresentationDirector.Budget(PresentationBeat.Venue,false,venueCut);
            float walk=PresentationDirector.Budget(PresentationBeat.WalkOn,false,walkCut);
            RivalIntro=walk*.4f; PlayerIntro=walk*.4f; Umpire=walk*.2f;
            Swoop=PresentationDirector.Budget(PresentationBeat.Start,false,startCut);
            beatIndex=0; BeginBeat();
        }
        void BeginBeat() {
            if(beatIndex>2) { t=Length; SetBars(0); hud.MatchVisible=true; return; }
            var beat=beatIndex==0?PresentationBeat.Venue:beatIndex==1?PresentationBeat.WalkOn:PresentationBeat.Start;
            var cut=beatIndex==0?venueCut:beatIndex==1?walkCut:startCut;
            float duration=beatIndex==0?Drone:beatIndex==1?RivalIntro+PlayerIntro+Umpire:Swoop;
            int entered=beatIndex;
            PresentationPolicy.Event(beat.ToString(),"begin",director.Sequence+1,cut.ToString());
            director.Begin(beat,cut,duration,.3f,()=>{},()=> {
                if(!skipped) PresentationPolicy.Event(beat.ToString(),"complete",director.Sequence);
                if(!skipped && cut==PresentationCut.Full && entered<2) PresentationPolicy.Seen(entered==0?VenueKey:WalkKey);
                beatIndex=entered+1; BeginBeat();
            }, shared:PresentationPolicy.Multiplayer);
        }''')
s=s.replace('            hud.MatchVisible = false;','            hud.MatchVisible = false;\n            Configure();',1)
s=s.replace('            t = Length;\n            emoteHold = 0;','            director.Cancel(); t = Length;\n            emoteHold = 0;',1)
a=s.index('        public void Skip()');b=s.index('\n        static float Smooth',a)
s=s[:a]+'''        public void Skip() {
            if(!Playing || PresentationPolicy.Multiplayer || t<.3f || beatIndex==2) return;
            skipped=true; director.Cancel();
            titleCard.gameObject.SetActive(false); nameCard.gameObject.SetActive(false);
            // Skip input is consumed by the caller. Retain a camera settle before the serve.
            Drone=RivalIntro=PlayerIntro=Umpire=0; Swoop=.3f; t=0; beatIndex=2; BeginBeat();
            PresentationPolicy.Event("Intro","skip",director.Sequence);
        }
''' + s[b:]
a=s.index('            if (emoteHold > 0)');b=s.index('            Vector3 pos, look;',a)
s=s[:a]+'''            director.Tick(dt);
            t = beatIndex==0 ? director.Elapsed : beatIndex==1 ? Drone+director.Elapsed : beatIndex==2 ? Drone+RivalIntro+PlayerIntro+Umpire+director.Elapsed : Length;
''' + s[b:]
# No animation can extend a hard-capped beat.
s=s.replace('                    if (driver) emoteHold = Mathf.Max(0, driver.EmoteDuration(driver.CurrentAction) + .3f - (RivalIntro - s));','')
s=s.replace('                        emoteHold = Mathf.Max(0, driver.EmoteDuration(chosenEmote.Value) + .4f - (PlayerIntro - s));','')
s=s.replace('                    emoteHold = Mathf.Max(0, game.PlayEquippedIntro() + .3f - (PlayerIntro - s));','                    game.PlayEquippedIntro();')
# The last walk-on beat is a two-shot, avoiding the old umpire close-up.
s=s.replace('Vector3 seat = TennisUmpire.Seat + Vector3.up * .5f;\n                pos = seat + new Vector3(3.6f, -.6f, -2.2f + s * .5f);\n                look = seat;\n                fov = 34;','pos = new Vector3(0, 4.5f, -15);\n                look = Vector3.Lerp(player.position, rival.position, .5f) + Vector3.up;\n                fov = 48;')
s=s.replace('if (t >= Length) { hud.MatchVisible = true; SetBars(0); }','if (t >= Length) { hud.MatchVisible = true; SetBars(0); }')
# Fit cards to short beats and retain safe-area horizontal margins.
s=s.replace('(s - .25f) / .5f','s / Mathf.Min(.2f, length*.2f)').replace('(length - .45f)) / .35f','(length - .2f)) / .2f')
p.write_text(s)
p=Path('Unity/Assets/Scripts/Tennis/TennisGame.cs');s=p.read_text().replace('TennisPresentation.Length','TennisPresentation.FullLength')
s=s.replace('void ApplyTauntHold() { if (tauntHold > 0 && Flow == Phase.PointOver && resetTimer > 0 && resetTimer < 1e5f) { resetTimer = Mathf.Max(resetTimer, tauntHold); tauntHold = 0; } }','void ApplyTauntHold() { tauntHold = 0; } // Emotes share the existing beat; they never delay the next serve.')
s=s.replace('resetTimer = Match.Complete ? (AutoPlay ? 5f : ResultsHold) : (setWon ? 7f : 6f) * GameSpeed;   // Six real seconds to see the score and select a celebration.','''var cut=GolfArcade.Game.PresentationPolicy.Cut("tennis.reaction");
            float beatSeconds=Match.Complete ? GolfArcade.Game.PresentationDirector.Budget(GolfArcade.Game.PresentationBeat.MatchEnd,false,cut)
                : setWon ? GolfArcade.Game.PresentationDirector.Budget(GolfArcade.Game.PresentationBeat.Set,false,cut)
                : gameWon ? GolfArcade.Game.PresentationDirector.Budget(GolfArcade.Game.PresentationBeat.Game,false,cut)
                : !toPlayer ? .8f : Feedback!=null && Feedback.StartsWith("ACE") ? (cut==GolfArcade.Game.PresentationCut.Full?1.5f:1f)
                : GolfArcade.Game.PresentationDirector.Budget(GolfArcade.Game.PresentationBeat.Point,false,cut);
            resetTimer = beatSeconds * GameSpeed;
            pointBeatDuration=beatSeconds; pointBeatElapsed=0; pointBeatSequence++;
            GolfArcade.Game.PresentationPolicy.Event(Match.Complete?"MatchEnd":setWon?"Set":gameWon?"Game":"Point","begin",pointBeatSequence,beatSeconds.ToString("F2"));''')
s=s.replace('        float accumulator, resetTimer, charge;','        float accumulator, resetTimer, charge;\n        float pointBeatDuration, pointBeatElapsed; int pointBeatSequence;\n        public bool PresentationResultsReady => Flow==Phase.MatchOver && pointBeatElapsed>=pointBeatDuration;')
# Track real seconds outside simulation speed. Existing simulation timer uses GameSpeed.
s=s.replace('            if (!ManualSimulation)\n            {','''            if(Flow==Phase.PointOver || Flow==Phase.MatchOver) {
                float before=pointBeatElapsed; pointBeatElapsed+=Time.deltaTime;
                if(before<pointBeatDuration && pointBeatElapsed>=pointBeatDuration)
                    GolfArcade.Game.PresentationPolicy.Event(Flow==Phase.MatchOver?"MatchEnd":"Point","complete",pointBeatSequence);
            }
            if (!ManualSimulation)
            {''',1)
# No auto rematch: results remain until explicit user action, even in the editor.
s=s.replace('if (Flow == Phase.MatchOver) { if (!NativeControlled && PlayMode != Mode.Campaign) NewMatch(); }','if (Flow == Phase.MatchOver) { /* Results wait for Rematch or Leave. */ }')
# Skip point/boundary reactions consumes the swing and releases only that beat.
s=s.replace('            if (IntroPlaying) { presentation.Skip(); return; }','''            if (IntroPlaying) { presentation.Skip(); return; }
            if(Flow==Phase.MatchOver) { if(pointBeatElapsed>=1.5f) { pointBeatElapsed=pointBeatDuration; resetTimer=0; } return; }
            if(Flow==Phase.PointOver && resetTimer>0 && resetTimer<1e5f) { if(pointBeatElapsed>=.5f) resetTimer=0.001f; return; }''')
p.write_text(s)
