from pathlib import Path
import uuid
p=Path('Unity/Assets/Scripts/Game/GolfGame.Presentation.cs')
p.write_text('''using UnityEngine;
namespace GolfArcade.Game {
    public sealed partial class GolfGame {
        readonly PresentationDirector golfPresentation = new();
        PresentationCut golfVenueCut, golfWalkCut, golfStartCut;
        int golfBeat; bool golfSkipped, pendingNativeIntro, overviewReturn, introReady;
        System.Numerics.Quaternion? lastReadyGrip;
        string GolfVenueKey => "golf.venue." + course.Key + "." + hole.Number;
        public bool PresentationBusy => Current==State.Intro;
        public bool PresentationPlaying => golfPresentation.Playing;
        void BeginGolfPresentation() {
            golfPresentation.Cancel(); golfBeat=0; golfSkipped=false; overviewReturn=false;
            golfVenueCut=PresentationPolicy.Cut(GolfVenueKey);
            golfWalkCut=PresentationPolicy.Cut("golf.walkon");
            golfStartCut=PresentationPolicy.Cut("golf.start");
            BeginGolfBeat();
        }
        void BeginGolfBeat() {
            if(golfBeat>2) {
                EndShowcase(); hud.HideNameplate();
                if(overviewReturn) { Current=State.Aim; hud.HideHoleIntro(); hud.ShowPlayHud(true); FrameAim(); RefreshControls(); }
                else { BeginAim(false); if(introReady) NativeReady(lastReadyGrip); }
                return;
            }
            var beat=golfBeat==0?PresentationBeat.Venue:golfBeat==1?PresentationBeat.WalkOn:PresentationBeat.Start;
            var cut=golfBeat==0?golfVenueCut:golfBeat==1?golfWalkCut:golfStartCut;
            float duration=PresentationDirector.Budget(beat,true,cut);
            if(golfBeat==0 && holeIndex>0 && cut==PresentationCut.Full) duration=3;
            int entered=golfBeat;
            PresentationPolicy.Event(beat.ToString(),"begin",golfPresentation.Sequence+1,cut.ToString());
            golfPresentation.Begin(beat,cut,duration,.3f,()=>{},()=>{
                PresentationPolicy.Event(beat.ToString(),golfSkipped?"skipped":"complete",golfPresentation.Sequence);
                if(!golfSkipped && !overviewReturn && cut==PresentationCut.Full && entered<2) PresentationPolicy.Seen(entered==0?GolfVenueKey:"golf.walkon");
                golfBeat=overviewReturn?3:entered+1; BeginGolfBeat();
            },shared:PresentationPolicy.Multiplayer);
        }
        void TickGolfPresentation(float dt) {
            if(Current!=State.Intro)return;
            if(golfBeat==0) {
                rig.Showcase(hole,golfPresentation.Fraction);
                hud.SetHoleIntroAlpha(1);
            } else if(golfBeat==1) {
                MeetThePlayer(golfPresentation.Elapsed);
            } else {
                EndShowcase(); hud.HideNameplate(); hud.HideHoleIntro(); hud.ShowPlayHud(true);
                golfer.SetVisible(true); golfer.Stand(ball.position,TeeAim());
                rig.RestoreFov(); rig.ResetZoom(); FrameAim();
            }
            golfPresentation.Tick(dt);
            if(Input.GetMouseButtonDown(0)) SkipPresentation();
        }
        public void SkipPresentation() {
            if(Current!=State.Intro || PresentationPolicy.Multiplayer || golfPresentation.Elapsed<.3f || golfBeat==2)return;
            golfSkipped=true; golfPresentation.Cancel(); EndShowcase();
            golfBeat=overviewReturn?3:2; BeginGolfBeat();
        }
        public void Overview() {
            if(Current!=State.Aim || NativeCalibrating || PresentationPolicy.Multiplayer)return;
            overviewReturn=true; golfSkipped=false; golfBeat=0; golfVenueCut=PresentationCut.Full;
            hud.ShowHoleIntro(Tournament,hole.Number,hole.Name,hole.Par,hole.Length,Wind.Describe(heading));
            Current=State.Intro; Swing.Armed=false; BeginGolfBeat(); RefreshControls();
        }
        public void TryNativePresentation() {
            if(!pendingNativeIntro || NativeCalibrating || !NativeShotReady || PresentationPolicy.Multiplayer)return;
            pendingNativeIntro=false; introReady=NativeShotReady;
            // Setup has completed at the original address; no scoring or turn changes occur.
            meeting=cheered=false; golfer.SetVisible(false); hud.ShowPlayHud(false);
            hud.ShowHoleIntro(Tournament,hole.Number,hole.Name,hole.Par,hole.Length,Wind.Describe(heading));
            Enter(State.Intro); BeginGolfPresentation(); RefreshControls();
        }
        void OnDisable() { golfPresentation.Cancel(); }
    }
}
''')
p.with_suffix('.cs.meta').write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n')
p=Path('Unity/Assets/Scripts/Game/GolfGame.cs');s=p.read_text()
s=s.replace('if (Current == State.Intro && stateTime > 0.3f) BeginAim(false);','SkipPresentation();')
s=s.replace('            Enter(State.Intro);\n            RefreshControls();','            Enter(State.Intro);\n            BeginGolfPresentation();\n            RefreshControls();',1)
s=s.replace("            if (Current == State.Intro) rig.SnapNext(); // cut from the flyover, don't glide the length of the hole",'            // L4 blends to the established address composition before input is released.')
a=s.index('                case State.Intro:',s.index('        void Frame()'));b=s.index('                case State.Aim:',a)
s=s[:a]+'''                case State.Intro:
                    TickGolfPresentation(Time.deltaTime);
                    break;

'''+s[b:]
s=s.replace('const float YouSeconds = 2.8f, GallerySeconds = 1.9f;','float YouSeconds => golfWalkCut==PresentationCut.Full?1.5f:.8f;\n        const float GallerySeconds = 0f;')
s=s.replace('float MeetSeconds => YouSeconds + (gallery.Count > 0 ? GallerySeconds : 0f);','float MeetSeconds => YouSeconds;')
s=s.replace('hud.ShowNameplate("YOU", $"On the tee   ·   Hole {hole.Number}");','hud.ShowNameplate(Match?.Current?.Name ?? "YOU", $"On the tee   ·   Hole {hole.Number}");')
s=s.replace('if (t < YouSeconds || gallery.Count == 0)','if (t <= YouSeconds || gallery.Count == 0)')
s=s.replace('                    if (Demo && stateTime > 4.5f) ContinueShotResult();','''                    if (stateTime >= ResultReactionSeconds || (stateTime >= ResultSkipAfter && Input.GetMouseButtonDown(0))) ContinueShotResult();''')
s=s.replace('                    if (stateTime > 3f)','''                    if (stateTime >= PresentationDirector.Budget(holeIndex+1>=course.Holes.Length?PresentationBeat.MatchEnd:PresentationBeat.HoleOut,true,PresentationPolicy.Cut("golf.boundary")) || (stateTime>= (holeIndex+1>=course.Holes.Length?1.5f:.5f) && Input.GetMouseButtonDown(0)))''')
s=s.replace('                        ShowRoundCard();\n                        Enter(State.RoundDone);','''                        if(NativeControlled && holeIndex+1<course.Holes.Length) { NextPresentationHole(); }
                        else { ShowRoundCard(); Enter(State.RoundDone); }''',1)
p.write_text(s)
p=Path('Unity/Assets/Scripts/Game/GolfGame.Native.cs');s=p.read_text();s=s.replace('            BeginAim(false); hud.ShowPlayHud(true); RefreshControls();','            golfPresentation.Cancel(); pendingNativeIntro=true;\n            BeginAim(false); hud.ShowPlayHud(true); RefreshControls();',1)
s=s.replace('            if (Current == State.Result) { ContinueShotResult(); return; }','            if(Current==State.Intro) { SkipPresentation(); return; }\n            if (Current == State.Result) { ContinueShotResult(); return; }',1)
s=s.replace('            if (Current == State.Intro) BeginAim(false);','')
s=s.replace('            Swing.Detector.SetReadyPose(q); needsReadyPose=false;','            lastReadyGrip=q; Swing.Detector.SetReadyPose(q); needsReadyPose=false;',1)
p.write_text(s)
p=Path('Unity/Assets/Scripts/Game/GolfGame.Results.cs');s=p.read_text();s=s.replace('        void ShowShotResult()','''        float ResultReactionSeconds => LastShot!=null && LastShot.IsHoled ? PresentationDirector.GolfReaction(holeStrokes-hole.Par,holeStrokes==1,PresentationPolicy.Cut("golf.reaction")) : .5f;
        float ResultSkipAfter => LastShot!=null && LastShot.IsHoled && holeStrokes==1 ? 1f : 0f;
        void NextPresentationHole() { Enter(State.RoundDone); NextHole(); }
        void ShowShotResult()''',1)
s=s.replace('            if (Current != State.Result || Time.timeScale <= 0) return;','            if (Current != State.Result || Time.timeScale <= 0 || stateTime<ResultSkipAfter) return;',1)
p.write_text(s)
p=Path('Unity/Assets/Scripts/Game/NativeSportsSession.cs');s=p.read_text().replace('if(!value) { resumedAt=SportsClock(); if(tennis) tennis.LockLoadout(); }','if(!value) { resumedAt=SportsClock(); if(tennis) tennis.LockLoadout(); if(golf) golf.TryNativePresentation(); }')
s=s.replace('                    case "golfContinue":','                    case "presentationSkip": if(!paused) { if(tennis) tennis.RequestSwing(.1f); if(golf) golf.NativeContinue(); } break;\n                    case "golfOverview": if(golf && !paused) golf.Overview(); break;\n                    case "golfContinue":',1)
p.write_text(s)
p=Path('Unity/Assets/Scripts/Tennis/TennisPresentation.cs');s=p.read_text().replace('float Length =>','public const float Length = FullLength;\n        float TotalLength =>');# all own dynamic refs
s=s.replace('t=Length','t=TotalLength').replace('t = Length','t = TotalLength').replace('t < Length','t < TotalLength').replace('Length -','TotalLength -').replace('t >= Length','t >= TotalLength').replace(': Length;',': TotalLength;')
p.write_text(s)
