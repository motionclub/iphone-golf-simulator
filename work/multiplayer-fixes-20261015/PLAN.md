# Multiplayer fixes — October 15, 2026

User requests: receive invites in app; join either direction; retain lobby movement, mutual visibility and emotes; free text party chat with overhead bubbles; background/resume without a crash; Call Party seats everyone. No character, camera, map or gameplay tuning. No commits.

Gates: native compile + multiplayer/chat/hub regressions; Unity compile + lobby runtime tests with rendered proof; exact lifecycle forwarding without duplicate resign/background; live invitations require a configured authenticated Club Hub service and two signed phones. Any unrun device gates stay FAIL / NOT RUN.

Findings: ClubHubServerURL is empty, so the existing in-app invite transport cannot receive. GameKit exposes accepted invitations, not a pending invitation inbox. SportsHome forwards both inactive and background as a complete Unity resign/background sequence, overwriting Unity _wasPausedExternal on the second resign. Call Party only draws a beacon. PartyChat never forwards messages to Unity.
