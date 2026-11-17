# In-game recording: handoff (2026-11-16)

Adnan paused this work; someone else is taking over in-game recording. Here is where it stands.

## What the player saw
- Record started, but the timer stayed at 0:00. Stop then said "Nothing was recorded: the game was not on screen."
- After the first fix (below), tapping Record crashed the game straight away.

## Cause 1: no frames reached the recorder (fixed in 5dd522be1)
- Frames reach both recorders (the full session, `SportsSessionRecorder`, and tennis point clips, `SportsPointRecorder`) through `Unity/Assets/Plugins/iOS/SportsPointCapture.mm`.
- That file swizzles Unity's `DisplayConnection` present method, so the render delegate's `onFrameResolved` knows which display is presenting.
- It hooked `-presentWith:`. Unity 6000.3 presents each display with `-presentWith:toMainScreen:` instead, so the hook attached to nothing and `presentingDisplay` was always nil.
- The phone's `Documents/Recordings/recorder-log.txt` showed every take ending with `frames=0 dropped=0`.
- The fix hooks `-presentWith:toMainScreen:` (keeping `-presentWith:` as a fallback) and logs when neither exists.

## Cause 2: crash on Record once frames flowed (fix written, NOT built or tested)
- Crash report `GolfArcade-2026-11-16-204236.ips`: EXC_BAD_ACCESS on the main thread, with this stack:
  `AcquireSwapchainDrawable` ← `metal::EnsureDrawableAcquiredIfNeeded` ← `TextureFromRenderBufferImpl` ← `-[SportsPointRenderDelegate onFrameResolved]` ← `PreparePresentMTL` ← `-[DisplayConnection presentWith:toMainScreen:]`.
- On iOS, Unity 6000.3 renders straight into the drawable. `targetColorRB` is only a proxy that acquires a drawable when it is used (see the comments in the exported `Classes/Unity/UnityRendering.h`, struct `UnityViewSwapchain`). Calling `TextureFromRenderBuffer(targetColorRB)` inside the present acquired a drawable at the wrong moment.
- The change in this commit reads `surface->swapchain.drawableTexture` (the drawable the frame was just drawn into, and blitted to by `PreparePresentMTL`) and skips the frame when there is none.
- **Untested:** the build with it was stopped before it reached the phone. Things to check:
  - Record on a TV: the timer runs, and Stop saves to Photos.
  - The drawable's pixel format passes `formatOK` in `SportsSessionRecorder.mm` `captureTexture`. A wide-colour `BGRA10_XR` drawable would be skipped and logged as "unrecordable TV frame skipped".
  - Tennis point clips also record.
  - Encoding into Unity's command buffer at that point (`EndCurrentCommandEncoder`, then our render pass) is still valid in 6000.3.

## Where to look on the phone
- Recorder log: `xcrun devicectl device copy from --domain-type appDataContainer --domain-identifier com.adnanandrew.motionsports --source Documents/Recordings/recorder-log.txt`
- Crash reports: `xcrun devicectl device info files --domain-type systemCrashLogs`, or on the phone, Settings → Privacy & Security → Analytics Data.

## UI already done (GolfArcade/Party/PartySettingsView.swift, CaptureDock)
- One tap starts recording and one tap stops it.
- While recording, the button is a red ■ 0:42 STOP pill.
- In golf the dock sits in the controller's top-left corner (it used to sit in the status-bar strip).
- Recording needs a TV, because it records the TV picture.
