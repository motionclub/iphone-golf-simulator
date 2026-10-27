using System.Collections.Generic;
using System.Threading.Tasks;
using GolfArcade.Game;
using UnityEngine;

namespace GolfArcade.Bowling
{
    /// The bowling soundscape on the game's buses (PLAN_Bowling.md §10 audio), built on real recordings
    /// (Resources/Audio/v2/sfx/bowling: CC0/CC-BY Freesound recordings cut by work/bowling/audio/kit.py;
    /// the first, fully synthesised pass sounded like chimes and a sub-bass hum, 10-25):
    ///   * the pin crash: every impact the pin physics found triggers a real pin-knock grain and a real
    ///     crash sits under the first hit (BowlingSynth.Mix), mixed on a worker thread while the ball
    ///     rolls, so it lands on the first pin frame and scales with the pins;
    ///   * the ball: the release whoosh, the real drop on the lane, a real roll loop pitched by speed and
    ///     louder on the dry back end, the gutter's rattle; the foul buzzer;
    ///   * the machine: the real pinsetter, the ball rolling back up the return;
    ///   * the room: a real bowling-alley recording per venue (chatter, other lanes crashing; it dips
    ///     while a bowler holds Ready and walks), the venue's ambience and music, the crowd's reactions;
    ///   * the announcer (GameVoice, "bowl_*" lines: silent until those lines exist).
    public sealed class BowlingAudio : MonoBehaviour
    {
        BowlingGame game;
        BowlingSynth.Room room;
        AudioSource shot, crash, roll, gutter, bed, amb, music, neighbour;
        AudioClip landing, buzzer, whooshSoft, whooshHard;
        AudioClip[] neighbours, machines, wobbles, pinHits;
        BowlingSynth.Kit kit;
        readonly Dictionary<string, AudioClip> crowd = new Dictionary<string, AudioClip>();
        float nextNeighbour, ballReturnAt = -1, returnUntil, ambVolume, musicVolume;
        AudioSource returnRoll;

        // the crash being rendered for the pin action in flight
        PinAction rendering; Task<float[]> render; bool crashWanted; float crashWantedAt;

        public static BowlingAudio Create(BowlingGame game, BowlingVenueKind venue)
        {
            var go = new GameObject("BowlingAudio");
            go.transform.SetParent(game.transform, false);
            var a = go.AddComponent<BowlingAudio>();
            a.game = game;
            a.room = venue switch { BowlingVenueKind.NeonNights => BowlingSynth.Room.Neon, BowlingVenueKind.TikiShores => BowlingSynth.Room.Beach, BowlingVenueKind.MagmaLanes => BowlingSynth.Room.Cave, _ => BowlingSynth.Room.Club };
            a.Build(venue);
            return a;
        }

        AudioSource Source(bool loop = false, int priority = 128)
        {
            var s = gameObject.AddComponent<AudioSource>();
            s.playOnAwake = false; s.spatialBlend = 0; s.loop = loop; s.priority = priority; s.volume = loop ? 0 : 1;
            return s;
        }

        static AudioClip Clip(string name, float[] stereo)
        {
            var c = AudioClip.Create(name, stereo.Length / 2, 2, BowlingSynth.Rate, false);
            c.SetData(stereo, 0);
            return c;
        }

        void Build(BowlingVenueKind venue)
        {
            shot = Source(); crash = Source(priority: 0);   // the crash is the most important sound in the game
            roll = Source(true, 10); gutter = Source(true, 20); bed = Source(true); amb = Source(true); music = Source(true); neighbour = Source(); returnRoll = Source(true);
            kit = LoadKit(out pinHits, out machines, out wobbles);
            var rollClip = Resources.Load<AudioClip>(Kit + "roll_1");
            roll.clip = rollClip ? rollClip : Clip("BowlRoll", BowlingSynth.RollLoop());
            gutter.clip = roll.clip;   // the gutter is the same ball, higher and hollower, with knocks (Rolling)
            returnRoll.clip = roll.clip;
            landing = Resources.Load<AudioClip>(Kit + "landing_1") ?? Clip("BowlLanding", BowlingSynth.Landing(0));
            buzzer = Clip("BowlFoul", BowlingSynth.Buzzer());
            whooshSoft = Clip("BowlWhooshSoft", BowlingSynth.Whoosh(.3f)); whooshHard = Clip("BowlWhooshHard", BowlingSynth.Whoosh(.9f));
            // other lanes: the room recording already has them; the synthetic ones only when it is missing
            neighbours = new AudioClip[0];

            // the crowd's reactions: the tennis and golf crowds (one audience, EQ-matched in the 10-25 pass)
            foreach (var (key, file) in new[]
            {
                ("strike", "sfx/crowd/tennis_ovation"), ("streak", "sfx/crowd/golf_roar"), ("spare", "sfx/crowd/tennis_applause_short"),
                ("converted", "sfx/crowd/tennis_applause_long"), ("gutter", "sfx/crowd/golf_aww"), ("foul", "sfx/crowd/golf_groan"),
                ("split", "sfx/crowd/golf_ooh"), ("close", "sfx/crowd/tennis_ooh"), ("miss", "sfx/crowd/tennis_sigh"), ("clap", "sfx/crowd/golf_clap"),
            })
            {
                AudioClip c = null; GameAudio.Swap(ref c, file); if (c) crowd[key] = c;
            }
            // the room: a real alley recording per venue (chatter, balls, other lanes' crashes)
            string roomKey = venue switch { BowlingVenueKind.NeonNights => "room_neon", BowlingVenueKind.TikiShores => "room_tiki", BowlingVenueKind.MagmaLanes => "room_magma", _ => "room_club" };
            bed.clip = Resources.Load<AudioClip>(Kit + roomKey + "_1") ?? GameAudio.Load("sfx/crowd/tennis_murmur")?[0];
            if (!Resources.Load<AudioClip>(Kit + roomKey + "_1"))
            {
                var r = room; neighbours = new AudioClip[3];
                for (int i = 0; i < neighbours.Length; i++) neighbours[i] = Clip("BowlNeighbour" + i, BowlingSynth.NeighbourCrash(100 + i, r));
            }
            nextNeighbour = Time.time + Random.Range(3f, 8f);
            // the venue: Tiki's surf and birds, Magma's rumbling cave; music in the lounges, the neon hall's own track when it exists
            amb.clip = venue switch { BowlingVenueKind.TikiShores => GameAudio.Load("sfx/amb/golf_wildisles")?[0], BowlingVenueKind.MagmaLanes => GameAudio.Load("sfx/amb/golf_magma")?[0], _ => null };
            ambVolume = venue == BowlingVenueKind.MagmaLanes ? .5f : .4f;
            music.clip = venue switch
            {
                BowlingVenueKind.NeonNights => Resources.Load<AudioClip>("Audio/v2/music/bowl_neon") ?? Resources.Load<AudioClip>("Audio/v2/music/game_light"),
                BowlingVenueKind.MagmaLanes => Resources.Load<AudioClip>("Audio/v2/music/bowl_magma"),
                BowlingVenueKind.TikiShores => Resources.Load<AudioClip>("Audio/v2/music/bowl_tiki") ?? Resources.Load<AudioClip>("Audio/v2/music/game_light"),
                _ => Resources.Load<AudioClip>("Audio/v2/music/bowl_club") ?? Resources.Load<AudioClip>("Audio/v2/music/game_light"),
            };
            musicVolume = venue == BowlingVenueKind.NeonNights ? .32f : .22f;
            foreach (var s in new[] { bed, amb, music }) if (s.clip) s.Play();
            GameVoice.Say("bowl_welcome_" + venue.ToString().ToLowerInvariant(), 1, true);
        }

        const string Kit = "Audio/v2/sfx/bowling/";

        static AudioClip[] Series(string name, int max)
        {
            var list = new List<AudioClip>();
            for (int i = 1; i <= max; i++) { var c = Resources.Load<AudioClip>(Kit + name + "_" + i); if (c) list.Add(c); }
            return list.ToArray();
        }

        /// A clip's samples as interleaved stereo at the synth rate (for the worker-thread mixer).
        static float[] Samples(AudioClip c)
        {
            if (!c) return null;
            if (c.loadState != AudioDataLoadState.Loaded) c.LoadAudioData();
            var d = new float[c.samples * c.channels];
            if (!c.GetData(d, 0)) return null;
            int frames = c.samples; float step = c.frequency / (float)BowlingSynth.Rate;
            int outFrames = Mathf.FloorToInt(frames / step); var o = new float[outFrames * 2];
            for (int i = 0; i < outFrames; i++)
            {
                int k = Mathf.Min(frames - 1, Mathf.RoundToInt(i * step));
                o[2 * i] = d[k * c.channels]; o[2 * i + 1] = d[k * c.channels + (c.channels > 1 ? 1 : 0)];
            }
            return o;
        }

        static float[][] Data(AudioClip[] clips) { var o = new List<float[]>(); foreach (var c in clips) { var d = Samples(c); if (d != null) o.Add(d); } return o.ToArray(); }

        /// The recorded kit (empty sets when the files are missing: the synthesised crash is the fallback).
        public static BowlingSynth.Kit LoadKit(out AudioClip[] pinHits, out AudioClip[] machines, out AudioClip[] wobbles)
        {
            pinHits = Series("pin_hit", 24); machines = Series("machine", 6); wobbles = Series("wobble", 6);
            return new BowlingSynth.Kit
            {
                PinHits = Data(pinHits), BallHits = Data(Series("ball_hit", 8)), Crashes = Data(Series("crash", 8)),
                Wobbles = Data(wobbles), Landings = Data(Series("landing", 4)),
            };
        }

        // ------------------------------------------------------------------ calls from BowlingGame

        /// The ball leaves the hand: a whoosh by swing speed; a foul's buzzer as the slide crosses the line.
        public void Release(BowlingThrow th)
        {
            float speed01 = Mathf.InverseLerp(5.5f, 9.5f, th.Speed);
            shot.Shot(speed01 > .5f ? whooshHard : whooshSoft, Mathf.Lerp(.35f, .7f, speed01));
            if (th.Foul) shot.Shot(buzzer, .55f);
        }

        int lastIndex = -1; BallPhase lastPhase = BallPhase.Air; float rollSeen, nextKnock;
        /// Every frame the ball is on the lane: `deckResult` is the pin action once the deck has simulated it.
        public void Rolling(List<BallState> record, float playT, PinAction deckResult)
        {
            if (deckResult != null && rendering != deckResult) StartRender(deckResult);
            if (record.Count == 0) return;
            int i = Mathf.Min(record.Count - 1, Mathf.FloorToInt(playT * 60));
            var s = record[i];
            if (i != lastIndex)
            {
                // touching down: from the air onto the lane (a loft is a deeper, louder drop)
                if (lastPhase == BallPhase.Air && s.Phase != BallPhase.Air && lastIndex >= 0)
                {
                    float vy = Mathf.Abs(record[Mathf.Max(0, i - 1)].Velocity.y);
                    float prev = shot.pitch; shot.pitch = vy > 1.2f ? .85f : 1;
                    shot.Shot(landing, Mathf.Clamp01(.4f + vy * .3f)); shot.pitch = prev;
                }
                lastPhase = s.Phase; lastIndex = i;
            }
            rollSeen = Time.time;
            float speed = s.Velocity.magnitude;
            bool onLane = s.Phase == BallPhase.Skid || s.Phase == BallPhase.Roll || s.Phase == BallPhase.Deck;
            bool inGutter = s.Phase == BallPhase.Gutter;
            // the back end is dry: the ball grips and the rumble gets louder past the oil (~12 m)
            float backEnd = Mathf.InverseLerp(10, 14, s.Position.z);
            Drive(roll, onLane ? Mathf.Clamp01(speed / 7f) * Mathf.Lerp(.75f, 1f, backEnd) : 0, Mathf.Lerp(.85f, 1.12f, Mathf.InverseLerp(3, 9, speed)));
            // the gutter: the same ball in a narrow channel, higher and hollower, knocking its sides
            Drive(gutter, inGutter ? Mathf.Clamp01(speed / 7f) * .7f : 0, Mathf.Lerp(1.15f, 1.35f, Mathf.InverseLerp(3, 9, speed)));
            if (inGutter && pinHits.Length > 0 && Time.time >= nextKnock)
            {
                nextKnock = Time.time + Random.Range(.12f, .4f);
                float prev = shot.pitch; shot.pitch = Random.Range(.5f, .62f); shot.Shot(pinHits[Random.Range(0, pinHits.Length)], .12f); shot.pitch = prev;
            }
        }

        static void Drive(AudioSource s, float volume, float pitch)
        {
            if (!s.clip) return;
            if (volume > .01f && !s.isPlaying) { s.time = Random.Range(0, s.clip.length); s.Play(); }
            s.volume = Mathf.MoveTowards(s.volume, volume * GameAudio.SfxVolume, Time.deltaTime * 4);
            s.pitch = pitch;
        }

        /// The ball reaches the pins: the crash plays from the first pin frame.
        public void Pins(PinAction act)
        {
            if (act == null) return;
            if (rendering != act) StartRender(act);
            crashWanted = true; crashWantedAt = Time.time;
            TryPlayCrash();
        }

        void StartRender(PinAction act)
        {
            rendering = act;
            var impacts = new List<PinImpact>(act.Impacts.Count);
            foreach (var i in act.Impacts) if (i.Strength > .35f) impacts.Add(i);
            if (impacts.Count > 400) impacts.RemoveRange(400, impacts.Count - 400);
            bool strike = act.StandingBefore == BowlingLeave.All && act.StandingAfter == 0;
            float length = Mathf.Max(1.5f, act.Frames.Count / 60f);
            int knocked = act.Knocked, hitStanding = 0;
            for (int p = 1; p <= 10; p++)
                if (BowlingLeave.Standing(act.StandingAfter, p)) foreach (var i in impacts) if (i.Pin == p && i.Kind != ImpactKind.PinPit) { hitStanding++; break; }
            var r = room; int seed = act.Frames.Count * 31 + impacts.Count; var k = kit;
            render = Task.Run(() => k != null && k.Ready ? BowlingSynth.Mix(impacts, length, knocked, strike, hitStanding, r, k, seed) : BowlingSynth.Crash(impacts, length, strike, r, seed));
        }

        void TryPlayCrash()
        {
            if (!crashWanted || render == null || !render.IsCompleted) return;
            crashWanted = false;
            if (render.IsFaulted) { Debug.LogException(render.Exception); return; }
            var clip = Clip("BowlCrash", render.Result);
            crash.Stop(); crash.clip = clip; crash.volume = GameAudio.SfxVolume;
            // a render that finished late starts where the picture already is
            crash.time = Mathf.Min(clip.length - .01f, Time.time - crashWantedAt);
            crash.Play();
        }

        /// The verdict: the crowd, and the announcer for the calls that have a name.
        public void Result(string kind, int knocked, int strikeStreak, bool firstBall)
        {
            string streak = BowlingLeave.Streak(strikeStreak);
            switch (kind)
            {
                case "Strike": React("strike", .6f); Say("bowl_strike"); break;
                case "Turkey":
                    React(strikeStreak >= 3 ? "streak" : "strike", .65f);
                    Say(streak != null ? "bowl_" + streak.ToLowerInvariant().Replace("-", "_").Replace(" ", "_") : "bowl_strike"); break;
                case "Spare": React("spare", .5f); Say("bowl_spare", .8f); break;
                case "ConvertedSplit": React("converted", .6f); Say("bowl_split_converted"); break;
                case "Gutter": React("gutter", .45f); Say("bowl_gutter", .7f); break;
                case "Foul": React("foul", .45f); Say("bowl_foul"); break;
                case "SevenTen": React("split", .5f); Say("bowl_seven_ten"); break;
                case "Split": React("split", .45f); Say("bowl_split", .8f); break;
                case "Miss": React("miss", .4f); break;
                default:
                    if (firstBall && knocked == 9) { React("close", .45f); Say("close", .5f); }
                    else if (knocked >= 7) React("clap", .3f);
                    break;
            }
        }

        void React(string key, float volume) { if (crowd.TryGetValue(key, out var c)) shot.Shot(c, volume); }
        static void Say(string key, float chance = 1) => GameVoice.Say(key, chance, chance >= 1);

        /// The pinsetter clears the deck; the ball comes back up the return a moment later.
        public void Sweep()
        {
            if (machines.Length > 0) shot.Shot(machines[Random.Range(0, machines.Length)], .5f);
            else shot.Shot(Clip("BowlSweep", BowlingSynth.Sweep(room)), .45f);
            ballReturnAt = Time.time + 1.4f;
        }

        // ------------------------------------------------------------------ the room

        void Update()
        {
            TryPlayCrash();
            // the loops fall silent when the lane stops feeding them
            if (Time.time - rollSeen > .1f) { Drive(roll, 0, roll.pitch); Drive(gutter, 0, gutter.pitch); }
            if (roll.isPlaying && roll.volume <= 0) roll.Stop();
            if (gutter.isPlaying && gutter.volume <= 0) gutter.Stop();
            // the ball return: the ball rumbling back under the lanes, then knocking into the rack
            if (ballReturnAt > 0 && Time.time >= ballReturnAt)
            {
                ballReturnAt = -1; returnUntil = Time.time + 1.1f;
                returnRoll.pitch = .7f; returnRoll.time = 0; returnRoll.Play();
            }
            if (returnRoll.isPlaying)
            {
                bool on = Time.time < returnUntil;
                returnRoll.volume = Mathf.MoveTowards(returnRoll.volume, on ? .3f * GameAudio.SfxVolume : 0, Time.deltaTime * (on ? 2 : 6));
                if (!on && returnRoll.volume <= 0) { returnRoll.Stop(); float prev = shot.pitch; shot.pitch = .7f; shot.Shot(landing, .45f); shot.pitch = prev; }
            }

            // the crowd hushes while a bowler holds Ready and walks up, and breathes out after the crash
            var f = game ? game.Flow : BowlingGame.Phase.Setup;
            bool hush = f == BowlingGame.Phase.Hold || f == BowlingGame.Phase.Approach;
            float sfx = GameAudio.SfxVolume, mus = GameAudio.MusicGain();
            bed.volume = Mathf.MoveTowards(bed.volume, (hush ? .3f : .55f) * sfx, Time.deltaTime * .5f);
            amb.volume = Mathf.MoveTowards(amb.volume, ambVolume * sfx, Time.deltaTime * .3f);
            music.volume = Mathf.MoveTowards(music.volume, (hush ? .6f : 1f) * musicVolume * mus, Time.deltaTime * .4f);

            // somebody else is bowling too: a crash a lane or two away now and then
            if (Time.time >= nextNeighbour && neighbours.Length > 0)
            {
                nextNeighbour = Time.time + Random.Range(7f, 17f);
                if (!hush && !crash.isPlaying)
                {
                    neighbour.panStereo = Random.value < .5f ? -.6f : .6f;
                    neighbour.pitch = Random.Range(.95f, 1.05f);
                    neighbour.PlayOneShot(neighbours[Random.Range(0, neighbours.Length)], Random.Range(.08f, .16f) * sfx);
                }
            }
        }
    }
}
