#!/usr/bin/env python3
"""EMPTY HANDS 2026-11-12: install HeroHands.cs and its two call sites into a Unity project.  usage: patch_hands.py <Unity project dir>
Idempotent: a file already patched is left alone. Fails loudly when an anchor moved."""
import os, shutil, sys

root = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(root, 'Assets/Scripts')
shutil.copy(os.path.join(here, 'HeroHands.cs'), os.path.join(S, 'Tennis/HeroHands.cs'))


def patch(rel, anchor, insert, marker, before=False):
    p = os.path.join(S, rel)
    s = open(p).read()
    if marker in s:
        print(rel, 'already patched'); return
    if s.count(anchor) != 1:
        sys.exit(f'{rel}: anchor found {s.count(anchor)} times')
    s = s.replace(anchor, insert + anchor if before else anchor + insert)
    open(p, 'w').write(s)
    print(rel, 'patched')


# Golf: no club shown (emotes, walk / run, the idle after an emote, spectators) -> both hands empty, after the grip pass.
patch('Game/GolferView.cs',
      '                GolfArcade.Tennis.HeroGripPolish.ApplyGrip(heroFigure.Root.GetComponent<GolfArcade.Tennis.MatchHeroLook>());\n',
      '            // EMPTY HANDS 2026-11-12: with no club in the hands (an emote, walk / run, the idle after an emote, a spectator) the clip\'s\n'
      '            // racket-grip fingers and wrist give way to a relaxed hand (a fist the clip makes stays a fist). See HeroHands.\n'
      '            if (heroFigure != null && !ClubShown()) GolfArcade.Tennis.HeroHands.Empty(heroFigure.Root.GetComponent<GolfArcade.Tennis.MatchHeroLook>(), 1f);\n',
      'HeroHands.Empty')
patch('Game/GolferView.cs',
      '        public bool Perform(string move, float startAt = 0f, bool loop = true)\n',
      '        /// A club mesh is showing (in the hands): only then do the hands grip.\n'
      '        bool ClubShown() { foreach (var c in clubMeshes.Values) if (c && c.activeSelf) return true; return false; }\n',
      'bool ClubShown()', before=True)
# Plaza / menu: the hero holds nothing, so an emote's hands are empty (the stand and the walk already relax theirs).
patch('Hub/HubHeroAnimator.cs',
      '            AfterPose?.Invoke();\n',
      '            // EMPTY HANDS 2026-11-12: an emote here is played empty-handed, so its READY racket-grip fingers and wrist relax (HeroHands)\n'
      '            if (actionFade > .001f && !bowlClip && SeatWeight < .001f) HeroHands.Empty(look, actionFade);\n',
      'HeroHands.Empty', before=True)
