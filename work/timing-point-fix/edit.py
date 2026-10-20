from pathlib import Path
import json,shutil
r=Path.cwd(); files=[]
def edit(f,fn):
 p=r/f;s=p.read_text();n=fn(s)
 if s!=n:p.write_text(n);files.append(f)
def session(s):
 s=s.replace('    private static let flashes = 4, gameModeHint = 0.14','    private var flashProbeID = UUID()\n    private static let flashes = 4, gameModeHint = 0.14')
 start=s.index('    func measureTVDelay()');end=s.index('    func savePlayers()',start)
 s=s[:start]+'''    func measureTVDelay() {
        guard active, ready, displayConnected, !touch, sport == "tennis", setupStage == .timing,
              !measuringDelay, !checkingTiming else { return }
        measuringDelay = true; timingPrompt = false; flashDelays = []; flashProbeID = UUID()
        let probeID = flashProbeID, launched = sessionID
        status = "Keep the rear camera aimed at the screen while it flashes."
        motion.setDelayProbe(true)
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .milliseconds(500))
            guard let self, self.active, self.sessionID == launched, self.flashProbeID == probeID, self.measuringDelay else { return }
            self.command("flash", value: Double(Self.flashes))
            try? await Task.sleep(for: .seconds(Double(Self.flashes) * 1.7 + 1.5))
            guard self.active, self.sessionID == launched, self.flashProbeID == probeID else { return }
            self.finishTVDelay()
        }
    }
    private func flashShown(at rendered: Double) {
        guard measuringDelay else { return }
        let launched = sessionID, probeID = flashProbeID
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .milliseconds(1250))
            guard let self, self.active, self.sessionID == launched, self.flashProbeID == probeID, self.measuringDelay else { return }
            if let delay = self.motion.delayAfterFlash(rendered: rendered) { self.flashDelays.append(delay) }
        }
    }
    private func finishTVDelay() {
        guard measuringDelay else { return }
        measuringDelay = false; motion.setDelayProbe(false); timingPrompt = true
        if let delay = SportsDelayProbe.combine(flashDelays) {
            tvDelay = delay; SportsTiming.store(delay, for: SportsTiming.currentTV())
            timingNote = String(format: "Screen delay measured: %.0f ms. The swing check keeps this measurement.", delay * 1000)
        } else {
            tvDelay = timingCalibration ?? 0
            timingNote = tvDelay > 0 ? "Flashes were unclear. Using this screen's last measurement; you can retry."
                : "Flashes were unclear. Point the rear camera at the screen and retry, or use the swing check."
        }
        command("latency", value: tvDelay)
        status = "Screen measurement finished. Start the swing timing check."
        delayTip = tvDelay > Self.gameModeHint ? "TV Game Mode can reduce picture delay." : ""
        SportsDiagnostics.write("tv delay flashes=\\(flashDelays.map { String(format: "%.3f", $0) }) chosen=\\(tvDelay)")
    }
'''+s[end:]
 s=s.replace('        if Self.benchmark { setupStage', '        if Self.benchmark { setupStage')
 s=s.replace('        setupStage = .scan; axisGate =', '        tvDelay = timingCalibration ?? 0\n        setupStage = .scan; axisGate =',1)
 s=s.replace('''        SportsDisplays.shared.external?.isHidden = true
    }
    func skipTimingCheck()''','''        SportsDisplays.shared.external?.isHidden = true
        measureTVDelay()
    }
    func skipTimingCheck()''',1)
 s=s.replace('              setupStage == .timing, !checkingTiming else','              setupStage == .timing, !checkingTiming, !measuringDelay else',1)
 s=s.replace('private static let key = "sports.tv.timing.v1"','private static let key = "sports.tv.timing.v2"')
 s=s.replace('all[tv] = max(0, min(0.35, lag))','guard lag.isFinite else { return }\n        all[tv] = max(0, min(1.0, lag))')
 return s
edit('GolfArcade/Unity/SportsSession.swift',session)
def probe(s):
 s=s.replace('        if capturingAxis {\n            evaluateGate(frame:frame,time:frameAt)', '        if capturingAxis { evaluateGate(frame:frame,time:frameAt) }\n        if capturingAxis || probing {',1)
 s=s.replace('static let shortest = 0.01, longest = 0.55', 'static let shortest = 0.01, longest = 1.0')
 start=s.index('        guard window.count >= 6, let darkIndex');end=s.index('        let delay = t - rendered',start)
 s=s[:start]+'''        guard window.count >= 6 else { return nil }
        // Each pulse has a long black lead-in, so the first frames are the baseline.
        // Searching for the darkest frame anywhere can pick the *end* of a white pulse.
        let baseline = window.prefix(6).map(\\.1).sorted()
        let dark = baseline[baseline.count / 2]
        guard let bright = window.map(\\.1).max(), bright - dark >= minimumContrast else { return nil }
        let half = (dark + bright) / 2
        guard let cross = window.indices.dropFirst().first(where: {
            window[$0 - 1].1 < half && window[$0].1 >= half && window[$0].0 >= rendered + shortest
        }) else { return nil }
        let (t1, v1) = window[cross - 1], (t2, v2) = window[cross]
        let t = v2 > v1 ? t1 + (t2 - t1) * (half - v1) / (v2 - v1) : t2
'''+s[end:]
 s=s.replace('''        return sorted[sorted.count / 2]
    }
}''','''        let median = sorted[sorted.count / 2]
        let agreeing = sorted.filter { abs($0 - median) <= 0.06 }
        guard agreeing.count >= 2 else { return nil }
        return agreeing[agreeing.count / 2]
    }
}''',1)
 return s
edit('GolfArcade/Unity/SportsMotion.swift',probe)
def controller(s):
 s=s.replace('DelayProbePanel()', 'DelayProbePanel(session: session)',1)
 s=s.replace('private struct DelayProbePanel: View {\n    @State', 'private struct DelayProbePanel: View {\n    let session: SportsSession\n    @State',1)
 s=s.replace('''            Text("Keep pointing at the TV").font''','''            SportsCameraPreview(motion: session.motion).frame(height: 180)
                .clipShape(RoundedRectangle(cornerRadius: 14))
                .overlay { Image(systemName: "plus").font(.title).foregroundStyle(.white) }
            Text("2 · Measure screen delay").font''',1)
 s=s.replace('''            ControllerButton(title: "Start timing check"''','''            if !session.timingNote.isEmpty {
                Text(session.timingNote).font(IslandUI.font(14, bold: true)).multilineTextAlignment(.center)
            }
            if !session.touch {
                Button("Retry screen flashes") { session.measureTVDelay() }.accessibilityIdentifier("timing-flashes")
            }
            ControllerButton(title: "Start timing check"''',1)
 s=s.replace('A ball will bounce on a line on the TV. Swing every time it drops onto the line — a steady rhythm, about ten seconds.', 'The flashes measure picture delay directly. Now follow the bouncing ball to check your swings. Swing every time it reaches the line; the check will keep the screen measurement.')
 return s
edit('GolfArcade/Unity/TennisPlayViews.swift',controller)
edit('Unity/Assets/Scripts/Game/NativeSportsSession.cs',lambda s:s.replace('panel.color=Color.black; yield return new WaitForSecondsRealtime(.35f);','panel.color=Color.black; yield return new WaitForSecondsRealtime(1.25f);').replace('''                    panel.color=Color.white;
                    Emit("flash"''','''                    panel.color=Color.white;
                    yield return new WaitForEndOfFrame();
                    Emit("flash"''').replace('new WaitForSecondsRealtime(.25f);','new WaitForSecondsRealtime(.45f);'))
edit('Unity/Assets/Scripts/Tennis/TennisLagLearner.cs',lambda s:s.replace('public const float Max = .35f','public const float Max = 1f'))
def beat(s):
 s=s.replace('        readonly float start;', '        readonly float start, displayDelay;')
 s=s.replace('public TennisBeatCalibration(float now, float countdown = 0) { start = now + countdown; }','public TennisBeatCalibration(float now, float countdown = 0, float measuredDisplayDelay = 0) { start = now + countdown; displayDelay = Mathf.Clamp(measuredDisplayDelay, 0, TennisLagLearner.Max); }')
 s=s.replace('BeatTime(Beats - 1) + Window','BeatTime(Beats - 1) + displayDelay + Window')
 s=s.replace('(now - start - LeadIn) / Interval','(now - start - LeadIn - displayDelay) / Interval')
 s=s.replace('if (Mathf.Abs(off) > Window)', 'if (Mathf.Abs(off - displayDelay) > Window)')
 return s
edit('Unity/Assets/Scripts/Tennis/TennisBeatCalibration.cs',beat)
def game(s):
 start=s.index('                // Re-sent for the same TV');end=s.index('            }\n        }\n        readonly TennisLagLearner',start)
 s=s[:start]+'''                // A fresh camera measurement must not seed an older rhythm-derived estimate.
                if (first || Mathf.Abs(before - lag.Prior) >= .001f) lag.Reset();
'''+s[end:]
 s=s.replace('if (NativeControlled && !AutoPlay && !NativeSportsSession.Touch) lag.Observe(rawLate);','if (!lagPriorSet && NativeControlled && !AutoPlay && !NativeSportsSession.Touch) lag.Observe(rawLate);')
 s=s.replace('new TennisBeatCalibration(Time.unscaledTime, TennisBeatCalibration.Countdown)', 'new TennisBeatCalibration(Time.unscaledTime, TennisBeatCalibration.Countdown, lagPriorSet ? lag.Prior : 0)')
 s=s.replace('''            if (ok)
            {
                // The new baseline''','''            // The flash probe measures the physical screen delay. A predictable beat can
            // be anticipated and includes detector latency: it must never overwrite that.
            if (lagPriorSet && lag.Prior > 0) { measured = lag.Prior; ok = true; }
            else if (ok) measured = Mathf.Clamp(measured - TennisRules.ServeLatency, 0, TennisLagLearner.Max);
            if (ok)
            {
                // The new baseline''',1)
 s=s.replace('resetTimer = Match.Complete ? (AutoPlay ? 5f : ResultsHold) : setWon ? 4.4f : 2.4f;', 'resetTimer = Match.Complete ? (AutoPlay ? 5f : ResultsHold) : (setWon ? 7f : 6f) * GameSpeed;')
 s=s.replace('string who = why ?? (toPlayer ? "POINT " + (hud ? hud.PlayerName : "YOU") : "POINT " + (hud ? hud.OpponentName : "KAI"));', 'string who = toPlayer ? "POINT " + (hud ? hud.PlayerName : "YOU") : "POINT " + (hud ? hud.OpponentName : "RIVAL");\n            if (!string.IsNullOrEmpty(why)) who += " · " + why;')
 s=s.replace('hud.ShowCall(CallFor(call, toPlayer, winner), PointContext(toPlayer, toPlayer ? opponentMissReason : null), toPlayer);', 'hud.ShowPointResult(toPlayer ? hud.PlayerName : hud.OpponentName, $"{CallFor(call, toPlayer, winner)} · {Match.PointCall}", toPlayer);')
 return s
edit('Unity/Assets/Scripts/Tennis/TennisGame.cs',game)
def hud(s):
 s=s.replace('float callAt = -9;','float callAt = -9, callDuration = CallHold;',1)
 s=s.replace('if (scoreOnly) { calls.Clear(); badgeAt = callAt = -99; feedbackPanel.gameObject.SetActive(false); callPanel.gameObject.SetActive(false); }','if (scoreOnly) { badgeAt = -99; feedbackPanel.gameObject.SetActive(false); }')
 pos=s.index('        void NextCall()')
 s=s[:pos]+'''        /// Point winners remain visible even with the uncluttered rally HUD.
        public void ShowPointResult(string winnerName, string detail, bool good) {
            calls.Clear();
            callFallback.text = winnerName.ToUpperInvariant() + " SCORED";
            callFallback.resizeTextForBestFit = true; callFallback.resizeTextMinSize = 28; callFallback.resizeTextMaxSize = 60;
            callSub.text = detail;
            callPanel.gameObject.SetActive(true);
            callAt = HudClock.Now; callDuration = 3f;
        }
        public string PointResultText => callPanel && callPanel.gameObject.activeSelf ? callFallback.text : "";

'''+s[pos:]
 s=s.replace('            callAt = HudClock.Now;\n        }\n\n        void Burst','            callAt = HudClock.Now; callDuration = CallHold;\n        }\n\n        void Burst',1)
 s=s.replace('if (HudClock.Now - callAt > CallHold)', 'if (HudClock.Now - callAt > callDuration)')
 s=s.replace('if (t < CallHold)', 'if (t < callDuration)').replace('(CallHold-t)/.2f','(callDuration-t)/.2f')
 return s
edit('Unity/Assets/Scripts/Tennis/TennisHud.cs',hud)
(r/'work/timing-point-fix/changes.json').write_text(json.dumps(files,indent=2))
print('\n'.join(files))
