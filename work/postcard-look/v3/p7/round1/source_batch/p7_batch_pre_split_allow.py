#!/usr/bin/env python3
"""Compose/check/apply exact reviewed P7 source plans; never run a build.

Compose and dry-run write only fresh physical v3 files. Root alone invokes
apply after review under the unchanged actual heavy.sh process ancestor.
No PNG, FBX, meta, gameplay, checker, design, or Git writes are permitted.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys

ROOT = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
V3 = ROOT / 'work/postcard-look/v3'
HEAVY = ROOT / 'work/postcard-look/heavy.sh'
SCHEMA = 'postcard_p7_source_batch_v1'
ALLOWED = {ROOT / 'blender/scripts' / name for name in (
    'golf_look_textures.py', 'postcard_look_lib.py', 'postcard_props_lib.py',
    'hole08_look.py', 'hole09_look.py', 'hole10_look.py',
    'hole08_build.py', 'hole09_build.py', 'hole10_build.py')}
ALLOWED |= {ROOT / 'Unity/Assets/Editor/PostcardV3FrameProof.cs',
            ROOT / 'Unity/Assets/Resources/Course/Shaders/PostcardV3Proof.shader'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def physical(path):
    p = Path(path).absolute()
    if '..' in p.parts:
        raise RuntimeError('Noncanonical parent path forbidden: ' + str(p))
    for q in (p, *p.parents):
        if q.is_symlink():
            raise RuntimeError('Symlink forbidden: ' + str(q))
    return p


def read_exact(path, expected):
    p = physical(path)
    if not p.is_file() or len(expected) != 64:
        raise RuntimeError('Regular file / SHA missing: ' + str(p))
    data = p.read_bytes()
    if digest(data) != expected:
        raise RuntimeError('SHA conflict: ' + str(p))
    return data


def v3_file(path):
    p = physical(path)
    if not p.is_relative_to(V3) or p == V3:
        raise RuntimeError('Physical v3 path required: ' + str(p))
    return p


def mode(value):
    return int(value, 0) if isinstance(value, str) else int(value)


def assemble(refs):
    entries, guards, targets, origins = [], {}, {}, {}
    def protect(path, expected, origin):
        p = physical(path)
        if not p.is_relative_to(ROOT):
            raise RuntimeError('Guard outside exact root')
        prior = guards.get(str(p))
        if prior and prior['sha256'] != expected:
            raise RuntimeError('Conflicting protected hashes: ' + str(p))
        guards.setdefault(str(p), dict(path=str(p), sha256=expected, declared_by=[]))['declared_by'].append(origin)
    for ref in refs:
        pp = v3_file(ref['path'])
        plan = json.loads(read_exact(pp, ref['sha256']))
        if plan['root'] != str(ROOT) or plan['v3'] != str(V3):
            raise RuntimeError('Exact upstream project/v3 root conflict')
        origin = str(pp)
        if 'heavy_wrapper' in plan and plan['heavy_wrapper'] != str(HEAVY):
            raise RuntimeError('Wrong heavy wrapper')
        for raw in plan['entries']:
            target = physical(raw['target'])
            if target not in ALLOWED or target in targets:
                raise RuntimeError('Unallowed or duplicate planned target: ' + str(target))
            e = dict(target=str(target), old_sha256=raw['old_sha256'],
                     old_snapshot=str(v3_file(raw['old_snapshot'])),
                     new_sha256=raw['new_sha256'], draft=str(v3_file(raw['draft'])),
                     mode=mode(raw['mode']), source_plan=origin, source_plan_sha256=ref['sha256'])
            if e['mode'] & ~0o777 or e['mode'] & 0o022:
                raise RuntimeError('Invalid or group/world writable planned mode')
            entries.append(e); targets[target] = e; origins[str(target)] = origin
            for key, sha_key in (('meta', 'meta_sha256'), ('original_proof_source', 'original_proof_source_sha256')):
                if key in raw:
                    protect(raw[key], raw[sha_key], origin)
        for guard in plan['protected']:
            protect(guard['path'], guard['sha256'], origin)
    if not entries or str(HEAVY) not in guards:
        raise RuntimeError('Empty batch or missing exact heavy guard')
    protected, excluded = [], []
    for path, guard in sorted(guards.items()):
        e = targets.get(Path(path))
        if e:
            if guard['sha256'] != e['old_sha256']:
                raise RuntimeError('Planned target does not match protected old SHA: ' + path)
            excluded.append(dict(**guard, planned_by=origins[path], reason='Declared target old SHA still checked upfront; its declared new SHA checked after apply'))
        else:
            protected.append(guard)
    return dict(schema=SCHEMA, root=str(ROOT), v3=str(V3), source_plans=refs,
                entries=entries, protected=protected, excluded_planned_protected=excluded,
                heavy_wrapper=str(HEAVY), scope='Source bytes only; original art, geometry, static/runtime gates remain required',
                verification='UNVERIFIED; no build/install/render is performed')


def preflight(plan):
    rebuilt = assemble(plan['source_plans'])
    if rebuilt != plan:
        raise RuntimeError('Merged manifest differs from exact immutable upstream plans')
    payloads = []
    for e in plan['entries']:
        old = read_exact(e['target'], e['old_sha256'])
        if stat.S_IMODE(Path(e['target']).stat().st_mode) != e['mode']:
            raise RuntimeError('Old target mode changed: ' + e['target'])
        if read_exact(e['old_snapshot'], e['old_sha256']) != old:
            raise RuntimeError('Old archive differs')
        new = read_exact(e['draft'], e['new_sha256'])
        payloads.append((e, old, new))
    for guard in plan['protected'] + plan['excluded_planned_protected']:
        read_exact(guard['path'], guard['sha256'])
    return payloads


def heavy_parent():
    owner = physical(HEAVY.parent / 'heavy.lock/owner')
    if not owner.is_file():
        raise RuntimeError('Actual heavy lock owner missing')
    pid = os.getppid()
    for _ in range(16):
        p = subprocess.run(['ps', '-p', str(pid), '-o', 'ppid=', '-o', 'args='],
                           capture_output=True, text=True, check=True)
        fields = p.stdout.strip().split(None, 1)
        if len(fields) != 2:
            break
        argv = shlex.split(fields[1])
        # Exact wrapper argv token in an actual shell ancestor, not merely a
        # lock file or substring in another process' arbitrary command text.
        if argv and Path(argv[0]).name in ('bash', 'sh', 'zsh') and str(HEAVY) in argv[1:]:
            return dict(pid=pid, command=fields[1], lock_owner=owner.read_text())
        pid = int(fields[0])
        if pid <= 1:
            break
    raise RuntimeError('Actual unchanged heavy.sh shell ancestor missing')


def write_new(path, data, file_mode=0o644):
    path = physical(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    path.chmod(file_mode)


def receipt_write(out, receipt):
    temp = out / '.receipt.new'
    with temp.open('xb') as f:
        f.write((json.dumps(receipt, indent=2) + '\n').encode()); f.flush(); os.fsync(f.fileno())
    os.replace(temp, out / 'receipt.json')


def execute(manifest, expected, out, apply):
    raw = read_exact(v3_file(manifest), expected)
    plan = json.loads(raw)
    if plan.get('schema') != SCHEMA:
        raise RuntimeError('Wrong merged schema')
    payloads = preflight(plan)
    out = v3_file(out)
    if out.exists():
        raise RuntimeError('Fresh physical v3 output required')
    ancestor = heavy_parent() if apply else None
    out.mkdir(parents=True, exist_ok=False)
    receipt = dict(status='PENDING', manifest=str(manifest), manifest_sha256=expected,
                   mode='apply' if apply else 'dry-run', source_plans=plan['source_plans'],
                   heavy_ancestor=ancestor, archive=[], installed=[],
                   excluded_planned_protected=plan['excluded_planned_protected'],
                   verification='UNVERIFIED; complete P7 original gates and installed proof required')
    receipt_write(out, receipt)
    try:
        if apply:
            # Prepare every archive/new file before the first source mutation.
            for i, (e, old, new) in enumerate(payloads):
                archive = out / 'old' / Path(e['target']).relative_to(ROOT)
                temp = out / 'new' / str(i)
                write_new(archive, old, e['mode']); write_new(temp, new, e['mode'])
                read_exact(archive, e['old_sha256']); read_exact(temp, e['new_sha256'])
                receipt['archive'].append(dict(target=e['target'], path=str(archive), sha256=e['old_sha256']))
            receipt_write(out, receipt)
            read_exact(manifest, expected); preflight(plan)
            for i, (e, _, _) in enumerate(payloads):
                read_exact(e['target'], e['old_sha256'])
                os.replace(out / 'new' / str(i), e['target'])
                read_exact(e['target'], e['new_sha256'])
                receipt['installed'].append(dict(path=e['target'], sha256=e['new_sha256']))
                receipt_write(out, receipt)
            for e in plan['entries']:
                read_exact(e['target'], e['new_sha256'])
                read_exact(e['draft'], e['new_sha256'])
            for guard in plan['protected']:
                read_exact(guard['path'], guard['sha256'])
            for ref in plan['source_plans']:
                read_exact(ref['path'], ref['sha256'])
            read_exact(manifest, expected)
        receipt['status'] = 'PASS'
    except BaseException as ex:
        receipt['status'] = 'FAIL'; receipt['error'] = str(ex)
        receipt['partial_apply'] = bool(receipt['installed'])
        raise
    finally:
        receipt_write(out, receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('archive', 'excluded_planned_protected')}, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='command', required=True)
    compose = sub.add_parser('compose')
    compose.add_argument('--input-plan', action='append', required=True)
    compose.add_argument('--input-sha', action='append', required=True)
    compose.add_argument('--out', required=True)
    run = sub.add_parser('run')
    run.add_argument('--manifest', required=True); run.add_argument('--manifest-sha', required=True)
    run.add_argument('--result-dir', required=True)
    action = run.add_mutually_exclusive_group(required=True)
    action.add_argument('--dry-run', action='store_true'); action.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    if args.command == 'compose':
        if len(args.input_plan) != len(args.input_sha):
            raise RuntimeError('Every input plan needs its exact reviewed SHA')
        refs = [dict(path=str(v3_file(p)), sha256=s) for p, s in zip(args.input_plan, args.input_sha)]
        plan = assemble(refs); preflight(plan)
        out = v3_file(args.out)
        write_new(out, (json.dumps(plan, indent=2) + '\n').encode())
        print(json.dumps(dict(manifest=str(out), sha256=digest(out.read_bytes()), entries=len(plan['entries']),
                              protected=len(plan['protected']), excluded_planned_protected=len(plan['excluded_planned_protected'])), indent=2))
    else:
        execute(args.manifest, args.manifest_sha, args.result_dir, args.apply)


if __name__ == '__main__':
    main()
