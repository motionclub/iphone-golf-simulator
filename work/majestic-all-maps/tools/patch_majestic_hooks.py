# patch_majestic_hooks.py <Unity Assets dir> : the two hook lines that route chat 9's golf layer to chat 10's courses.
# Idempotent. MajesticLook.Golf(hole) -> MajesticCourses.For(hole); the golf Kit -> MajesticCourseKit.
import sys, re, os
a = sys.argv[1]
look = os.path.join(a, 'Scripts/Majestic/MajesticLook.cs'); venue = os.path.join(a, 'Scripts/Majestic/MajesticVenue.cs')
s = open(look).read()
if 'MajesticCourses.For' not in s:
    i = s.index('public static MajesticLook Golf(int hole) => new()')
    j = s.index('};', i) + 2
    s = s[:i] + 'public static MajesticLook Golf(int hole) => MajesticCourses.For(hole);   // chat 10: one signature hour per course' + s[j:]
    open(look, 'w').write(s); print('patched', look)
v = open(venue).read()
want = 'new Kit { Build = MajesticCourseKit.Build, Restyle = MajesticCourseKit.Restyle, Animate = MajesticCourseKit.Animate }'
if want not in v:
    v2 = v.replace('new Kit { Build = MajesticGolf.Build, Animate = MajesticGolf.Animate }', want)
    v2 = v2.replace('new Kit { Build = MajesticCourseKit.Build, Animate = MajesticCourseKit.Animate }', want)
    assert v2 != v, 'golf Kit line not found'
    open(venue, 'w').write(v2); print('patched', venue)
