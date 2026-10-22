from pathlib import Path
import uuid
p=Path('Unity/Assets/Scripts/Game/PresentationStinger.cs');p.write_text('''using UnityEngine;
namespace GolfArcade.Game {
    /// One cue source and a bounded duck envelope; cue lifetimes follow the active scene.
    public sealed class PresentationStinger : MonoBehaviour {
        static PresentationStinger instance; AudioSource source; AudioClip cue; float duckUntil;
        public static float MusicDuck => instance && Time.unscaledTime<instance.duckUntil?.5f:1;
        public static void Lead() {
            if(!instance) {
                instance=new GameObject("Presentation stinger").AddComponent<PresentationStinger>();
                instance.source=instance.gameObject.AddComponent<AudioSource>(); instance.source.playOnAwake=false;
                const int rate=22050;var samples=new float[(int)(rate*.18f)];
                for(int i=0;i<samples.Length;i++){float t=(float)i/rate;samples[i]=Mathf.Sin(2*Mathf.PI*(520*t+700*t*t))*Mathf.Exp(-t*20)*.25f;}
                instance.cue=AudioClip.Create("Presentation pop",samples.Length,1,rate,false);instance.cue.SetData(samples,0);
            }
            instance.duckUntil=Time.unscaledTime+.5f; instance.source.Stop(); instance.source.PlayOneShot(instance.cue,.7f);
        }
        public static void Stop() { if(instance){instance.source.Stop();instance.duckUntil=0;} }
        void OnDestroy(){if(instance==this)instance=null;if(cue)Destroy(cue);}
    }
}
''');p.with_suffix('.cs.meta').write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n')
p=Path('Unity/Assets/Scripts/Tennis/TennisAudioDirector.cs');s=p.read_text().replace('Music.Duck(Announcer.Speaking ? .45f : 1);','Music.Duck(Mathf.Min(Announcer.Speaking ? .45f : 1, GolfArcade.Game.PresentationStinger.MusicDuck));');p.write_text(s)
p=Path('Unity/Assets/Scripts/Tennis/TennisPresentation.cs');s=p.read_text().replace('int beatIndex; bool skipped;','int beatIndex; bool skipped, cueLed;').replace('            int entered=beatIndex;','            cueLed=false; int entered=beatIndex;',1).replace('            director.Tick(dt);','            if(!cueLed && beatIndex<2 && director.Duration-director.Elapsed<=.15f) { cueLed=true; PresentationStinger.Lead(); }\n            director.Tick(dt);',1);p.write_text(s)
p=Path('Unity/Assets/Scripts/Game/GolfGame.Presentation.cs');s=p.read_text().replace('int golfBeat; bool','bool golfCueLed; int golfBeat; bool').replace('            int entered=golfBeat;','            golfCueLed=false; int entered=golfBeat;',1).replace('            golfPresentation.Tick(dt);','            if(!golfCueLed && golfBeat<2 && golfPresentation.Duration-golfPresentation.Elapsed<=.15f) {golfCueLed=true;PresentationStinger.Lead();}\n            golfPresentation.Tick(dt);',1);p.write_text(s)
p=Path('Unity/Assets/Scripts/Game/NativeSportsSession.cs');s=p.read_text().replace('case "end": SportsMultiplayer.Shutdown();','case "end": PresentationStinger.Stop(); SportsMultiplayer.Shutdown();',1);p.write_text(s)
p=Path('GolfArcade/Unity/LoadingModel.swift');s=p.read_text().replace('    private var localReady = false','''    private(set) var tipIndex = -1
    private(set) var tipStarted: Date?
    var tipRemaining: TimeInterval { guard let tipStarted else { return 0 }; return max(0, 1.5-LoadingModel.clockNow.timeIntervalSince(tipStarted)) }
    var tip: String? {
        guard tipIndex >= 0 else { return nil }
        let golf = SportsSession.shared.sport == "golf"
        let tips = golf ? ["Check the wind before choosing your club.", "Use Overview to see the hazards before your shot.", "Read the green before putting."] : ["Meet the ball in front of you.", "Aim for open court.", "Watch the bounce, then swing."]
        return tips[tipIndex % tips.count]
    }
    private var localReady = false''').replace('        waitingPlayers = []; finishStart = nil;','        tipIndex = -1; tipStarted = nil\n        waitingPlayers = []; finishStart = nil;',1).replace('        guard localReady, playersReady, elapsed >= readMinimum else { return }','''        if !localReady && elapsed >= 2 {
            let next = Int((elapsed - 2) / 5)
            if next != tipIndex { tipIndex = next; tipStarted = now }
        }
        guard localReady, playersReady, elapsed >= readMinimum else { return }''',1);p.write_text(s)
p=Path('GolfArcade/Unity/ArcadeScreens.swift');s=p.read_text().replace('            if session.loading.elapsed >= 10,','            if let tip = session.loading.tip { Text(tip).font(IslandUI.font(compact ? 15 : 21)).multilineTextAlignment(.center).foregroundStyle(.white.opacity(0.8)) }\n            if session.loading.elapsed >= 10,',1);p.write_text(s)
p=Path('GolfArcade/Unity/SportsDisplays.swift');s=p.read_text().replace('    func finishLoadingCover() { loadingCover?.isHidden = true; loadingCover = nil }','''    private var lingeringTip: UIWindow?
    func finishLoadingCover() {
        if SportsSession.shared.loading.phase == .finished, let tip = SportsSession.shared.loading.tip,
           let scene = loadingCover?.windowScene, SportsSession.shared.loading.tipRemaining > 0 {
            let window=UIWindow(windowScene:scene); window.windowLevel = .alert
            let host=UIHostingController(rootView: VStack { Spacer(); Text(tip).font(IslandUI.font(18, bold: true)).foregroundStyle(.white).padding(16).background(IslandUI.navy, in: Capsule()).padding(.bottom, 48) })
            host.view.backgroundColor = .clear; window.backgroundColor = .clear; window.rootViewController=host
            window.isUserInteractionEnabled=false; window.isHidden=false; lingeringTip=window
            DispatchQueue.main.asyncAfter(deadline:.now()+SportsSession.shared.loading.tipRemaining) { [weak self] in
                window.isHidden=true; if self?.lingeringTip === window { self?.lingeringTip=nil }
            }
        }
        loadingCover?.isHidden = true; loadingCover = nil
    }''')
s=s.replace('        exitGeneration += 1; let generation = exitGeneration','        lingeringTip?.isHidden=true; lingeringTip=nil\n        exitGeneration += 1; let generation = exitGeneration',1)
p.write_text(s)
p=Path('Unity/Assets/Tests/EditMode/MultiplayerRulesTests.cs');s=p.read_text();a=s.index('        [Test] public void BothPlayersChooseIntroOnce');b=s.index('        [Test]',a+15);sub=s[a:b].replace('Step(m,5);','Step(m,2);').replace('Step(m,2);Assert.AreEqual("intro",m.State.phase);\n            Step(m,4);','Step(m,1.4);Assert.AreEqual("intro",m.State.phase);\n            Step(m,.2);');s=s[:a]+sub+s[b:];p.write_text(s)
