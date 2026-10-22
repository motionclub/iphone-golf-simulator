using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Game
{
    /// Three buses (Music / SFX / Voice) over the ElevenLabs v2 files in Resources/Audio/v2, with music
    /// ducked under the announcer. Clips are swapped in over the synthesised ones: a missing file just
    /// leaves the old sound. Each swapped sound keeps its variants and rotates them without repeating.
    public static class GameAudio
    {
        public static float MusicVolume = 1, SfxVolume = 1, VoiceVolume = 1;
        /// Reads the phone's Game sound sliders (UserDefaults audio.music / audio.sfx / audio.voice via PlayerPrefs).
        public static void RefreshVolumes()
        {
            MusicVolume = Mathf.Clamp01(PlayerPrefs.GetFloat("audio.music", 1)); SfxVolume = Mathf.Clamp01(PlayerPrefs.GetFloat("audio.sfx", 1));
            VoiceVolume = Mathf.Clamp01(PlayerPrefs.GetFloat("audio.voice", 1));
        }
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)] static void Boot() { RefreshVolumes(); var _ = GameAudioHost.Instance; }
        public const float DuckDepth = .65f;
        static float voiceUntil, duck;
        static readonly Dictionary<AudioClip, AudioClip[]> variants = new Dictionary<AudioClip, AudioClip[]>();
        static readonly Dictionary<AudioClip, AudioClip> lastPlayed = new Dictionary<AudioClip, AudioClip>();

        public static void VoicePlaying(float seconds) => voiceUntil = Mathf.Max(voiceUntil, Time.unscaledTime + seconds);
        /// Music gain for this frame: the bus volume, pulled down while the announcer talks.
        public static float MusicGain()
        {
            duck = Mathf.MoveTowards(duck, Time.unscaledTime < voiceUntil ? 1 : 0, Time.unscaledDeltaTime * (Time.unscaledTime < voiceUntil ? 6f : 1.5f));
            return MusicVolume * (1 - DuckDepth * duck);
        }

        /// Loads every v2 variant of `name` ("sfx/golf/driver" -> driver_1, driver_2, ...). Null when none exist.
        public static AudioClip[] Load(string name)
        {
            var found = new List<AudioClip>();
            for (int i = 1; i <= 4; i++) { var c = Resources.Load<AudioClip>("Audio/v2/" + name + "_" + i); if (c) found.Add(c); }
            return found.Count > 0 ? found.ToArray() : null;
        }
        /// Replace `target` with the v2 sound `name` when it exists (keeps the synthesised one otherwise).
        public static void Swap(ref AudioClip target, string name)
        {
            var v = Load(name);
            if (v == null) return;
            target = v[0];
            variants[v[0]] = v;
        }
        /// PlayOneShot that rotates a swapped sound's variants and applies the SFX bus.
        public static void Shot(this AudioSource source, AudioClip clip, float volume)
        {
            if (!clip) return;
            if (variants.TryGetValue(clip, out var v) && v.Length > 1)
            {
                var pick = v[Random.Range(0, v.Length)];
                if (lastPlayed.TryGetValue(clip, out var prev) && prev == pick) pick = v[(System.Array.IndexOf(v, pick) + 1) % v.Length];
                lastPlayed[clip] = pick; clip = pick;
            }
            // A small pool of child sources, so each hit gets its own pitch (+-3 %) without bending sounds already playing.
            if (!pools.TryGetValue(source, out var pool)) pools[source] = pool = new Pool { src = new AudioSource[6] };
            var s = pool.src[pool.next = (pool.next + 1) % pool.src.Length];
            if (!s)
            {
                s = source.gameObject.AddComponent<AudioSource>();
                s.playOnAwake = false; s.spatialBlend = 0; s.loop = false; s.outputAudioMixerGroup = source.outputAudioMixerGroup; s.priority = source.priority;
                pool.src[pool.next] = s;
            }
            s.pitch = source.pitch * Random.Range(.97f, 1.03f);
            s.clip = clip; s.volume = Mathf.Clamp01(volume * SfxVolume); s.Play();
        }
        sealed class Pool { public AudioSource[] src; public int next; }
        static readonly Dictionary<AudioSource, Pool> pools = new Dictionary<AudioSource, Pool>();
    }

    /// The plaza hub's lounge music: loops while the plaza exists, ducks under the announcer, ends with the plaza.
    public sealed class PlazaMusic : MonoBehaviour
    {
        AudioSource src;
        void Start()
        {
            var clip = Resources.Load<AudioClip>("Audio/v2/music/menu_lounge");
            if (!clip) { enabled = false; return; }
            src = gameObject.AddComponent<AudioSource>();
            src.clip = clip; src.loop = true; src.spatialBlend = 0; src.playOnAwake = false; src.volume = 0; src.Play();
        }
        void Update() { if (src) src.volume = Mathf.MoveTowards(src.volume, .55f * GameAudio.MusicGain(), Time.unscaledDeltaTime * .5f + .01f); }
    }

    /// One-shot UI / stinger sounds and the golf crowd swell, on one hidden object.
    public sealed class GameAudioHost : MonoBehaviour
    {
        static GameAudioHost instance;
        AudioSource shot, swell;
        public static GameAudioHost Instance
        {
            get
            {
                if (instance) return instance;
                var go = new GameObject("Game audio host"); DontDestroyOnLoad(go); instance = go.AddComponent<GameAudioHost>();
                instance.shot = go.AddComponent<AudioSource>(); instance.shot.playOnAwake = false; instance.shot.spatialBlend = 0;
                var s = GameAudio.Load("sfx/crowd/golf_swell");
                instance.swell = go.AddComponent<AudioSource>(); instance.swell.playOnAwake = false; instance.swell.spatialBlend = 0; instance.swell.loop = true; instance.swell.volume = 0;
                if (s != null) instance.swell.clip = s[0];
                return instance;
            }
        }
        public void PlayUI(string name, float volume)
        {
            var c = GameAudio.Load(name); if (c == null) return;
            GameAudio.Swap(ref c[0], name);
            shot.Shot(c[Random.Range(0, c.Length)], volume);
        }
        float swellTarget, nextRefresh;
        public void Swell(float closeness) { swellTarget = Mathf.Clamp01(closeness); }
        void Update()
        {
            if (Time.unscaledTime > nextRefresh) { nextRefresh = Time.unscaledTime + .5f; GameAudio.RefreshVolumes(); }
            if (!swell || !swell.clip) return;
            float want = swellTarget * swellTarget * .6f * GameAudio.SfxVolume;
            swell.volume = Mathf.MoveTowards(swell.volume, want, Time.unscaledDeltaTime * (want > swell.volume ? .8f : 2.5f));
            if (swell.volume > .01f && !swell.isPlaying) swell.Play(); else if (swell.volume <= .01f && swell.isPlaying) swell.Pause();
        }
    }

    /// The map intro music: plays while the preview flyover runs, fades out when it ends. Keyed by course or venue.
    public static class IntroMusic
    {
        static AudioSource src; static string playing;
        public static void Drive(string key, bool introActive)
        {
            key = (key ?? "").ToLowerInvariant().Replace(" ", "").Replace("_", "");
            if (!src)
            {
                var go = new GameObject("Intro music"); Object.DontDestroyOnLoad(go);
                src = go.AddComponent<AudioSource>(); src.playOnAwake = false; src.spatialBlend = 0; src.loop = false; src.volume = 0;
            }
            if (introActive && playing != key)
            {
                var clip = Resources.Load<AudioClip>("Audio/v2/music/intro_" + key);
                playing = key; if (clip) { src.clip = clip; src.time = 0; src.Play(); }
            }
            if (!introActive && playing != null) playing = null;
            float want = introActive && src.clip ? .7f * GameAudio.MusicVolume : 0;
            src.volume = Mathf.MoveTowards(src.volume, want, Time.unscaledDeltaTime * (want > 0 ? 1.2f : .9f));
            if (src.volume <= 0 && src.isPlaying && !introActive) src.Stop();
        }
    }

    /// The golf announcer: Jax's lines (Resources/Audio/v2/voice), rarely and never over himself. One reaction per 8 s at most.
    public static class GameVoice
    {
        static AudioSource src; static float lastAt = -99; static readonly System.Collections.Generic.Dictionary<string, AudioClip[]> bank = new System.Collections.Generic.Dictionary<string, AudioClip[]>();
        static readonly System.Collections.Generic.Queue<AudioClip> recent = new System.Collections.Generic.Queue<AudioClip>();
        static bool welcomed;
        static void Load()
        {
            if (bank.Count > 0) return;
            var tmp = new System.Collections.Generic.Dictionary<string, System.Collections.Generic.List<AudioClip>>();
            foreach (var c in Resources.LoadAll<AudioClip>("Audio/v2/voice"))
            {
                int us = c.name.LastIndexOf('_'); string k = us > 0 ? c.name.Substring(0, us) : c.name;
                if (!tmp.TryGetValue(k, out var l)) tmp[k] = l = new System.Collections.Generic.List<AudioClip>();
                l.Add(c);
            }
            foreach (var kv in tmp) bank[kv.Key] = kv.Value.ToArray();
        }
        /// `chance` 0..1; `big` moments ignore the cooldown (a hole-in-one is always called).
        public static void Say(string key, float chance = 1, bool big = false)
        {
            Load();
            if (!bank.TryGetValue(key, out var takes)) return;
            if (!big && (Time.unscaledTime - lastAt < 8f || Random.value > chance)) return;
            if (src && src.isPlaying && !big) return;
            if (!src)
            {
                var go = new GameObject("Game voice"); Object.DontDestroyOnLoad(go);
                src = go.AddComponent<AudioSource>(); src.playOnAwake = false; src.spatialBlend = 0;
            }
            AudioClip pick = takes[Random.Range(0, takes.Length)];
            for (int i = 0; i < 4 && recent.Contains(pick) && takes.Length > 1; i++) pick = takes[Random.Range(0, takes.Length)];
            recent.Enqueue(pick); while (recent.Count > 10) recent.Dequeue();
            lastAt = Time.unscaledTime;
            src.PlayOneShot(pick, GameAudio.VoiceVolume); GameAudio.VoicePlaying(pick.length + .3f);
        }
        public static void WelcomeOnce(string courseKey)
        {
            if (welcomed) return; welcomed = true;
            Say("welcome_" + (courseKey ?? "").ToLowerInvariant().Replace(" ", ""), 1, true);
        }
    }
}
