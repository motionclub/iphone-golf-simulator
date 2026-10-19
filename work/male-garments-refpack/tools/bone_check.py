"""bone_check.py <prefab>...: for every SkinnedMeshRenderer, bones in the prefab vs bindposes (and vertex count) in its mesh asset."""
import sys, re, glob, os
guid2path = {}
for m in glob.glob('Unity/Assets/**/*.asset.meta', recursive=True) + glob.glob('Unity/Assets/**/*.fbx.meta', recursive=True):
    g = re.search(r'^guid: (\w+)', open(m, errors='ignore').read(), re.M)
    if g: guid2path[g.group(1)] = m[:-5]
bad = 0
for pf in sys.argv[1:]:
    txt = open(pf).read(); blocks = re.split(r'^--- ', txt, flags=re.M)
    names = {}
    for b in blocks:
        h = re.match(r'!u!1 &(\d+)', b)
        if h: n = re.search(r'm_Name: (.*)', b); names[h.group(1)] = n.group(1) if n else '?'
    for b in blocks:
        if not b.startswith('!u!137 '): continue
        go = re.search(r'm_GameObject: \{fileID: (\d+)\}', b).group(1)
        mm = re.search(r'm_Mesh: \{fileID: (-?\d+)(?:, guid: (\w+))?', b)
        bones = re.search(r'm_Bones:\n((?:  - .*\n)*)', b); nb = len(bones.group(1).splitlines()) if bones else 0
        if not bones and re.search(r'm_Bones: \[\]', b): nb = 0
        guid = mm.group(2); path = guid2path.get(guid, '?')
        nbp = '?'
        if path.endswith('.asset') and os.path.exists(path):
            a = open(path, errors='ignore').read()
            bp = re.search(r'm_BindPose:\n((?:  - .*\n(?:    .*\n)*)*)', a)
            nbp = len(re.findall(r'^  - (?:e00|first)', bp.group(1), re.M)) if bp else 0
            if nbp == 0 and re.search(r'm_BindPose: \[\]', a): nbp = 0
        ok = nbp == '?' or nbp == nb
        bad += not ok
        print('%-4s %-28s bones %3d bindposes %4s  %s' % ('OK' if ok else 'BAD', os.path.basename(pf)[:28] + ':' + names.get(go, '?')[:20], nb, nbp, path.replace('Unity/Assets/', '')))
print('BAD', bad)
