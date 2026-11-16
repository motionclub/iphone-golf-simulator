# Onboarding visual concepts — 2026-11-16

Latest user direction: pre-game onboarding stays close to the existing menu, with more refined typography, placement and focus. In-game onboarding gets a more custom, inventive overlay system related to earlier game UI work. Mockups first.

## Design intent

- Menu: compact anchored cards; gold focus outline around the actual target; target remains visible; Next only on informational tips. TV uses the existing phone remote, phone alone uses taps.
- Tutorial: one available lesson at a time, completed lessons replayable, later lessons locked; all games unlock when the tutorial is cleared (including the existing no-TV deferral).
- Before play: static distance diagram, concise safety lines, explicit acknowledgment. No GIF outside the lesson.
- In game: split demonstration card using the existing GIF, then compact step rail and one coaching line; after-attempt feedback stays clear of ball, target and character.
- Small custom landmark details on lesson bars refer to each setting; typography and chrome retain the shared navy/cream/gold brand.
- Retry hints after two misses; Skip belongs on the phone after three. Existing control layout stays context, not a general HUD overhaul.
- Numbers and scenery are illustrative. No runtime screenshot, accessibility or interaction-validation claim.

## Source crosswalk

| Design surface | Existing source |
| --- | --- |
| Menu coach layout/focus | Unity/Assets/Scripts/Hub/Menu/MenuHud.Coach.cs |
| Tip order and actions | GolfArcade/Onboarding/OnboardingFlow.swift, coach(tv:) |
| Tutorial list/locks | Unity/Assets/Scripts/Hub/Menu/MenuHud.Tutorial.cs |
| Play-safe acknowledgment | GolfArcade/Onboarding/PlaySafe.swift |
| Lesson intro/coaching/feedback | GolfArcade/Onboarding/LessonCenter.swift |
| Demonstration footage | GolfArcade/Onboarding/HowTo/howto-{golf,tennis,bowling}.gif |
| Swing lesson steps | Unity/Assets/Scripts/Game/GolfLesson.cs |
| Court lesson steps | Unity/Assets/Scripts/Tennis/TennisTutorial.cs |
| Lane lesson steps | Unity/Assets/Scripts/Bowling/BowlingLesson.cs |

## Review

Open ../gallery.html for all new boards. proof/ contains five primary PNG boards plus an additional live court state. PROMPTS.md and manifest.json record exact prompts and reference inputs. The image generator reached its usage limit after the first menu exploration. Current final onboarding boards were authored as HTML/CSS layouts and rendered by local headless Chromium at 1536 × 1120. The original generated menu exploration is in archive/. No API/CLI image-generation fallback was used. Open native/index.html for the editable, interactive mockups; query board=menu, safe, swing, court or lane. The lesson preview button switches between demonstration and live coach layouts. Existing images and GIFs are used as supplied; no scene assets were repainted. No implementation.



The phone controller area is simplified context for an overlay study, not a proposed controller replacement. Text below the phone and board captions are design annotations. Exact original HUD text remains baked into source screenshots and is not new lesson UI. Device sizing, interaction behavior and runtime integration still need implementation-time verification.
