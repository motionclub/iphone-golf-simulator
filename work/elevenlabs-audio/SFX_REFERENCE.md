# SFX reference sheet and call-site list (2026-10-22)

## How Wii/Switch Sports-style hits are built (design notes from general knowledge of these games; not measured from their audio)
- **Layers:** a short bright transient (the strike), a body (the thump of ball mass), and a tiny tail. Usually two to three layers, mixed to read as ONE sound.
- **Length:** contact sounds are short, roughly 0.15–0.5 s. The tail is the natural decay of the strike, not a musical tail.
- **Loudness:** hits are the loudest thing in the mix, compressed so every hit lands at a similar level; the tier (soft / sweet / smash) comes from timbre (thin vs full vs sharp), not from big volume jumps.
- **Tiers by realism:** mishit = thin and dull, normal = clean pock, sweet spot = fuller and deeper, smash = hard crack.
- **Pitch/variation:** two or three variations per sound, small random pitch (about +-3%), so repeats don't machine-gun.
- **UI:** quiet, soft, short, well under the hits.
- Mario Tennis and PGA 2K follow the same recipe with a little more reverb and crowd; the cartoon sounds (boings, zaps, jingles) belong to the character moments, not the contact.

## Where the code plays hit / bounce / swing / cup / UI sounds
Methods (all in Unity/Assets/Scripts): `Game/GolfSounds.cs` (PlayStrike, PlayWhoosh, PlayCup, PlaySplash, PlayThud, PlayLanding, PlayKnock, PlayLeaves, PlayTick, PlayReady, PlayFanfare, PlayHoleOut), `Tennis/TennisSounds.cs` (Hit, RivalHit, Whiff, Bounce, Net, Whoosh, Call, Gasp, Applaud), `Game/EventSounds.cs` (world events: thunder, boing, horn..., untouched), `UI/Club.cs:504` (club UI one-shot).
Call sites (file:line method):

- Game/GolfGame.Events.cs:250:                        sounds.PlayKnock(false); Haptics.Tick();
- Game/GolfGame.Events.cs:257:                    sounds.PlayKnock(false); eventSounds?.Boing(); Haptics.Play(Haptics.Cue.Bounce, 0.8f);
- Game/GolfGame.Events.cs:267:                    sounds.PlayKnock(false); eventSounds?.Horn(); Haptics.Play(Haptics.Cue.Bounce, 0.5f);
- Game/GolfGame.Network.cs:200:                    golfer.Strike();sounds.PlayStrike((GolfClub)shot.club,shot.impact?.power??.7);
- Game/GolfGame.Network.cs:247:                    if(burnEffectShot!=shot.id){effects.LavaBurst(new Vector3((float)shot.restX,(float)shot.burnHeight,(float)shot.restD));sounds.PlayLavaHiss();burnEffectShot=shot.id;}
- Game/GolfGame.Network.cs:478:            sounds.PlayReady();
- Game/GolfGame.cs:1503:                sounds.PlayStrike(GolfClub.Iron, 0.9);
- Game/GolfGame.cs:1523:                sounds.PlayThud(strength);
- Game/GolfGame.cs:2286:                    if (Swing.Phase == SwingPhase.Downswing && lastPhase != SwingPhase.Downswing) { sounds.PlayWhoosh(Swing.Detector.Load); if (club != GolfClub.Putter) Haptics.Top(Swing.Detector.Load); }
- Game/GolfGame.cs:2290:                    if (Swing.Phase == SwingPhase.Address && lastPhase != SwingPhase.Address) { sounds.PlayReady(); Haptics.Tick(); }
- Game/GolfGame.cs:2312:                        strikePlayed = true; sounds.PlayStrike(club, LastShot.Power, (float)LastShot.LandingTime);
- Game/GolfGame.cs:2409:                    if (lie == CourseLie.Ice) sounds.PlayIceSkid(strength); else sounds.PlayThud(strength);
- Game/GolfGame.cs:2425:                if (k.Hard) sounds.PlayKnock(stone); else sounds.PlayLeaves();
- Game/GolfGame.cs:2434:            if (iceNow && !onIce) sounds.PlayIceSkid(velocity.magnitude / 20f);
- Game/GolfGame.cs:2447:                lipFeedback = true; sounds.PlayGroan(.6f); ExperienceTrace.Mark("golf", "lip-feedback");
- Game/GolfGame.cs:2450:                cupFeedback = true; ExperienceTrace.Mark("golf", "cup-feedback"); effects.Cup(HoleView.ToWorld(hole.Pin)); sounds.PlayCup(); Haptics.Roar();
- Game/GolfGame.cs:2466:                effects.LavaBurst(impactAt);sounds.PlayLavaHiss();Haptics.Failure();ball.gameObject.SetActive(false);
- Game/GolfGame.cs:2475:                if (InLava(LastShot, pos)) { effects.LavaBurst(new Vector3(pos.x, (float)under, pos.z)); sounds.PlayLavaHiss(); }
- Game/GolfGame.cs:2476:                else { effects.Splash(new Vector3(pos.x, (float)under, pos.z)); sounds.PlaySplash(); }
- Game/GolfGame.cs:2477:                sounds.PlayGasp(0.55f); Haptics.Failure();
- Game/GolfGame.cs:2564:            sounds.PlayReady();
- Game/GolfGame.cs:2613:            sounds.PlayReady();
- Game/GolfGame.cs:2654:            if (news.Count > 0) { hud.ShowUnlocks(news); sounds.PlayFanfare(); }
- Game/GolfGame.cs:2709:            sounds.PlayReady();
- Game/GolfGame.cs:2790:            if (r.Grade == StrikeGrade.Perfect && LastShot.Power > 0.8 && gallery.gameObject.activeSelf) sounds.PlayApplause(0.3f);
- Game/GolfGame.cs:2800:                if (shot.LippedOut) { if (!lipFeedback) sounds.PlayGroan(0.6f); }
- Game/GolfGame.cs:2801:                else if (toPin < 2.5) sounds.PlayGroan(0.3f);
- Game/GolfGame.cs:2806:                case CourseLie.OutOfBounds: sounds.PlayGroan(0.4f); return;
- Game/GolfGame.cs:2807:                case CourseLie.Bunker: sounds.PlayGroan(0.35f); return;
- Game/GolfGame.cs:2809:            if (shot.Lie.IsPuttingSurface() && toPin <= 4) { sounds.PlayGasp(0.45f); sounds.PlayApplause(0.4f); }
- Game/GolfGame.cs:2810:            else if (shot.Lie == CourseLie.Green) sounds.PlayApplause(0.25f);
- Game/GolfGame.cs:2875:                sounds.PlayStrike(club, LastShot.Power);
- Game/GolfGame.cs:2900:                sounds.PlayThud(1f);
- Game/GolfGame.cs:2908:                if (LastShot.IsHoled) { sounds.PlayCup(); sounds.PlayApplause(0.3f); ball.gameObject.SetActive(false); }
- Game/GolfGame.cs:2911:                    if (InLava(LastShot, ball.position)) { effects.LavaBurst(ball.position); sounds.PlayLavaHiss(); }
- Game/GolfGame.cs:2912:                    else { effects.Splash(ball.position); sounds.PlaySplash(); }
- Game/GolfGame.cs:3033:                if (!cupFeedback) { effects.Cup(HoleView.ToWorld(hole.Pin)); sounds.PlayCup(); Haptics.Roar(); }
- Game/GolfGame.cs:3034:                sounds.PlayFanfare();
- Game/GolfGame.cs:3036:                sounds.PlayHoleOut(holeStrokes, hole.Par);
- Game/GolfGame.cs:490:                if (!Unlocks.CourseOpen(ProfileStore.Active, key)) { sounds.PlayGroan(0.3f); courses.ShakeLock(); return; }   // not yet
- Game/GolfGame.cs:670:            sounds.PlayTick(); Haptics.Tick();
- Game/GolfGame.cs:694:        void Click() { sounds.PlayTick(); Haptics.Tick(); }
- Game/GolfGame.cs:809:        void Tick() { if (Current == State.Aim) { sounds.PlayTick(); Haptics.Tick(); } }
- Tennis/TennisGame.Network.cs:61:                        if(sounds!=null)sounds.Hit(grade,s.players[hitter].power);
- Tennis/TennisGame.Network.cs:68:                if(s.phase=="rally"&&!s.paused&&sounds!=null&&networkView!=NetworkConfiguration.ViewNone)sounds.Bounce(Mathf.Clamp01(Mathf.Sqrt(s.velocity.x*s.velocity.x+s.velocity.z*s.velocity.z)/32f));
- Tennis/TennisGame.Versus.cs:265:                    if (sounds) sounds.Gasp();
- Tennis/TennisGame.Versus.cs:347:            fx.OpponentContact(start, m.ult); sounds.RivalHit(m.srv ? .8f : Mathf.Lerp(.5f, .9f, m.power)); contactHitter = Opponent; OpponentStruck?.Invoke();
- Tennis/TennisGame.cs:1548:                    sounds.Net();
- Tennis/TennisGame.cs:1569:                    sounds.Bounce(Mathf.Abs(bounced0.y) / 8f);
- Tennis/TennisGame.cs:1601:                    { Feedback = "OUT"; sounds.Call(false); AwardPoint(incoming); }
- Tennis/TennisGame.cs:1652:                        sounds.Gasp(); AwardPoint(true, true);
- Tennis/TennisGame.cs:1680:                    Feedback = "RIVAL WHIFFED IT"; sounds.Gasp(); AwardPoint(true, true);
- Tennis/TennisGame.cs:1708:                QueueContactPresentation(Opponent, Timing.Great, ultimateBall); sounds.Rally = RallyShots; sounds.RivalHit(ultimateBall ? .9f : .6f); contactHitter = Opponent; OpponentStruck?.Invoke();
- Tennis/TennisGame.cs:2063:            sounds.Rally = RallyShots; sounds.Hit(LastGrade, Player.Power, smash);
- Tennis/TennisGame.cs:2075:            if (sounds) sounds.Whiff();
- Tennis/TennisGame.cs:2193:            QueueContactPresentation(Opponent, Timing.Great, false); sounds.RivalHit(.8f); contactHitter = Opponent; OpponentStruck?.Invoke();
- Tennis/TennisGame.cs:529:            if (beat != calibrationBeat && beat >= 0) { calibrationBeat = beat; sounds.Bounce(.6f); }
- Tennis/TennisGame.cs:773:            QueueContactPresentation(Player, verdict.Perfect ? Timing.Perfect : Timing.Great, false); sounds.Hit(verdict.Perfect ? Timing.Perfect : Timing.Great, pendingServePower); contactHitter = Player;
- Tennis/TennisGame.cs:815:            sounds.Call(false);
- Tennis/TennisGame.cs:907:            else sounds.Applaud(toPlayer ? .5f + excitement * .5f : .3f + excitement * .3f);

Note: the brief says tennis + golf + bowling, but the sound list asked for has no bowling sounds, and the code has no bowling audio yet.
