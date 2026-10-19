#!/usr/bin/env python3
"""Idempotent hooks in files this chat owns only in part (their sky / backdrop sections).
   tools/patch_shared.py <unity_project>            patch the working files
   (import: patch_text(rel, text) -> new text, used by install.sh to stage index-version + hook only)

- DreamEnvironment.cs: where RenderedBackdrop has a profile for the location, the sky is the RenderedSky
  material (shared, not destroyed with the Dream object) and the rendered backdrop is built; otherwise the
  old DreamSky + panorama path runs unchanged.
- TennisLook.cs / TennisVenueBuilder.Skyscraper.cs / .Volcano.cs (sky sections): the rendered sky from the
  first frame (intro flyover), before DreamEnvironment installs.
- Backdrop.cs: the rendered karst islands replace the image-to-3D islands when golf is live.
- HubArt.cs (SkyDome): the dome is shaded by the rendered sky with the sun at the real light.
- DreamEnvironment.cs also gets `AfterApply` (end of Apply) + IsTennis/Location for chat 9's Majestic venue layer.
"""
import sys, os

FILES = ['Assets/Scripts/Environment/DreamEnvironment.cs', 'Assets/Scripts/Tennis/TennisLook.cs',
         'Assets/Scripts/Tennis/TennisVenueBuilder.Skyscraper.cs', 'Assets/Scripts/Tennis/TennisVenueBuilder.Volcano.cs',
         'Assets/Scripts/Course/Backdrop.cs', 'Assets/Scripts/Hub/HubArt.cs']
TAG = '   // rendered backgrounds (work/rendered-backgrounds)'


def _once(s, rel, mark, anchors, insert_after):
    if mark in s:
        return s
    for a in anchors:
        if s.count(a) == 1:
            return s.replace(a, a + insert_after)
    raise AssertionError(f'{rel}: no unique anchor')


def _dream(s):
    if 'RenderedBackdrop.SkyProfile' not in s:
        old = '            var shader=Resources.Load<Shader>("Environment/DreamSky");\n            if(shader){'
        assert old in s, 'DreamEnvironment anchor moved'
        s = s.replace(old, '''            // Rendered backgrounds (work/rendered-backgrounds): a sky we render from the real light
            // replaces the painted panorama where a venue has a profile; DreamSky stays the fallback.
            var rendered=RenderedSky.Enabled?RenderedBackdrop.SkyProfile(tennis,location):null;
            if(rendered!=null){sky=RenderedSky.Install(transform.parent,rendered);ownsSky=false;if(sky)RenderSettings.skybox=sky;RenderedBackdrop.Build(transform.parent,tennis,location);}
            var shader=sky?null:Resources.Load<Shader>("Environment/DreamSky");
            if(shader){''')
        old2 = 'bool fog;FogMode fogMode;AmbientMode ambientMode;'
        assert old2 in s
        s = s.replace(old2, old2 + 'bool ownsSky=true;')
        old3 = 'void OnDestroy(){Release();if(sky)Destroy(sky);}'
        assert old3 in s
        s = s.replace(old3, 'void OnDestroy(){Release();if(sky&&ownsSky)Destroy(sky);}')
    # chat 9 (majestic maps) hook: end of Apply (order 10000), before RenderedSky (10001) reads the light
    if 'AfterApply' not in s:
        old = '            // WeatherDirector owns biome-specific wetness and snow/ash deposition.\n        }'
        assert s.count(old) == 1, 'DreamEnvironment Apply end moved'
        s = s.replace(old, old[:-len('        }')] + '            AfterApply?.Invoke(this);   // venue signature-hour layers (Majestic) adjust sun/ambient/fog/sky floats here\n        }')
        old = 'bool tennis, restored;int location;'
        assert old in s
        s = s.replace(old, '/// Called at the end of every Apply, after the clock/weather light; RenderedSky reads the result.\n        public static System.Action<DreamEnvironment> AfterApply;\n        public bool IsTennis => tennis; public int Location => location;\n        ' + old)
    return s


def patch_text(rel, s):
    if rel.endswith('DreamEnvironment.cs'):
        return _dream(s)
    early = 'GolfArcade.EnvironmentArt.RenderedBackdrop.TennisEarly();' + TAG
    if rel.endswith('TennisLook.cs'):
        return _once(s, rel, 'RenderedBackdrop.TennisEarly', ['GolfArcade.EnvironmentArt.LuminousCoastPilot.TennisLight(sun);',
                     'GolfArcade.EnvironmentArt.EnvironmentLook.Tennis(sun,TennisVenueKind.Resort);'], '\n            ' + early)
    if rel.endswith('Skyscraper.cs'):
        return _once(s, rel, 'RenderedBackdrop.TennisEarly', ['                camera.backgroundColor=haze;\n'], '                ' + early + '\n')
    if rel.endswith('Volcano.cs'):
        return _once(s, rel, 'RenderedBackdrop.TennisEarly', ['                camera.backgroundColor = new Color(.36f,.29f,.34f);\n'], '                ' + early + '\n')
    if rel.endswith('Backdrop.cs'):
        if 'RenderedBackdrop.GolfIslands' in s:
            return s
        old = '            if (island)\n            {'
        assert s.count(old) == 1, 'Backdrop anchor'
        return s.replace(old, '            if (island && !GolfArcade.EnvironmentArt.RenderedBackdrop.GolfIslands(root, course, along))' + TAG + '\n            {')
    if rel.endswith('HubArt.cs'):
        return _once(s, rel, 'RenderedBackdrop.HubDome', ['        public static void SkyDome(Transform root, Vector3 centre, float radius)\n        {\n'],
                     '            if (GolfArcade.EnvironmentArt.RenderedBackdrop.HubDome(root, centre, radius)) return;' + TAG + '\n')
    raise ValueError(rel)


if __name__ == '__main__':
    root = sys.argv[1]
    for rel in FILES:
        p = os.path.join(root, rel); s = open(p).read(); n = patch_text(rel, s)
        if n != s:
            open(p, 'w').write(n); print('patched', p)
        else:
            print('already patched', p)
