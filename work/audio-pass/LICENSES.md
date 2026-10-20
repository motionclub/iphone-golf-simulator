# Audio licences — every sound the game plays (2026-10-19, chat D)

No ripped, recorded or downloaded sound is in the game. Nothing was paid for, and no account was used.

| Asset | Where | Source | Licence / ownership |
|---|---|---|---|
| Announcer lines, golf (32 files) | `Unity/Assets/Resources/Audio/Announcer/Golf/*.wav` | Generated text-to-speech, voice `af_heart`, by `work/audio-pass/tools/make_voices.py` | Our output. Model **Kokoro-82M** weights + voice packs: **Apache-2.0** (hexgrad/Kokoro-82M; files `kokoro-v1.0.onnx`, `voices-v1.0.bin` from the kokoro-onnx GitHub release). Commercial use allowed; keep this notice. |
| Announcer lines, tennis (46 files) | `Unity/Assets/Resources/Audio/Announcer/Tennis/*.wav` | Same tool. Umpire calls `bm_george`, commentator `af_heart`. Text = `TennisAnnouncer.Script` | As above (Apache-2.0 model; output ours) |
| Crowd voices: ooh, aww, cheer, roar | `Unity/Assets/Resources/Audio/Crowd/*.wav` | The same TTS: ~56 takes over 27 English Kokoro voices, layered with random offsets, pitch and distance, plus a synthetic room. No crowd recording used | As above |
| Crowd murmur beds (gallery, stands) | `Unity/Assets/Resources/Audio/Crowd/*_murmur.wav` | Same TTS reading invented small talk, low-passed until no word is readable, looped | As above |
| Soundtrack: "Clubhouse Pop" (menu/plaza), "Fairway Breeze" (golf) | `Unity/Assets/Scripts/Game/GameMusic.cs` (rendered in code at run time) | Original compositions, written for this game in this pass | Project-owned (no third-party material) |
| Tennis calypso + stingers | `Unity/Assets/Scripts/Tennis/TennisMusic.cs` | Original, already in the project | Project-owned |
| All contact/impact/ambient SFX (club strikes and takes, pure/thin layers, putts, racket pops, frame clank, bounces, applause, weather) | `GolfSounds.cs`, `TennisSounds.cs`, `TennisAmbience.cs`, `EventSounds.cs`, `PresentationStinger.cs` | Synthesised in code at start-up | Project-owned |

Tools used only to make the files (not shipped): kokoro-onnx (MIT), onnxruntime (MIT), phonemizer (GPL-3.0) +
espeak-ng (GPL-3.0) for text → phonemes, numpy/scipy/soundfile (BSD). GPL tools run offline; their output (phonemes →
audio) is not covered by the GPL, and none of their code ships in the app.

Not used: macOS `say` voices (Apple's licence forbids using them in a commercial product), any paid generator (the credit-based
audio tools connected to this workspace — not used, per the brief "ask Adnan first").

To regenerate: see the header of `work/audio-pass/tools/make_voices.py`.
