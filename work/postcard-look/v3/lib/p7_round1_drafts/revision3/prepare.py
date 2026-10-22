#!/usr/bin/env python3
"""Deferred P7 shared-source fix; dry-run writes only a new physical v3 receipt.

Only the root's reviewed P7 batch may invoke --apply, under unchanged heavy.sh.
This helper never starts Blender/Unity or generates PNGs. Checkers, design, and scoring files remain protected.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

PLAN_SHA256 = 'ea2500a6769943b604817f8559228089a93afd79bb07ef298454da8d56b74055'
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def physical(path):
    p = Path(path).absolute()
    for q in (p, *p.parents):
        if q.is_symlink():
            raise RuntimeError('Symlink forbidden: ' + str(q))
    return p


def read_exact(path, expected):
    p = physical(path)
    if not p.is_file():
        raise RuntimeError('Regular file missing: ' + str(p))
    data = p.read_bytes()
    if sha(data) != expected:
        raise RuntimeError('SHA conflict: ' + str(p))
    return data


def heavy_parent(plan):
    wrapper = Path(plan['heavy_wrapper'])
    lock = wrapper.parent / 'heavy.lock' / 'owner'
    if not physical(lock).is_file():
        raise RuntimeError('Unchanged heavy.sh lock owner absent')
    pid = os.getppid()
    for _ in range(12):
        p = subprocess.run(['ps', '-p', str(pid), '-o', 'ppid=', '-o', 'args='],
                           text=True, capture_output=True, check=True)
        parts = p.stdout.strip().split(None, 1)
        if len(parts) != 2:
            break
        if str(wrapper) in parts[1]:
            return dict(pid=pid, command=parts[1], lock_owner=lock.read_text())
        pid = int(parts[0])
        if pid <= 1:
            break
    raise RuntimeError('Actual unchanged heavy.sh ancestor absent')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--result-dir', required=True)
    action = ap.add_mutually_exclusive_group(required=True)
    action.add_argument('--dry-run', action='store_true')
    action.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    plan = json.loads(read_exact(HERE / 'source_plan.json', PLAN_SHA256))
    root = physical(args.root)
    if str(root) != plan['root']:
        raise RuntimeError('Exact project root mismatch')
    out = physical(args.result_dir)
    runtime = Path(plan['v3'])
    if not out.is_relative_to(runtime) or out == runtime or out.exists():
        raise RuntimeError('Fresh physical v3 result directory required')
    allowed = {
        root / 'blender/scripts/golf_look_textures.py',
        root / 'blender/scripts/postcard_look_lib.py',
        root / 'blender/scripts/postcard_props_lib.py',
    }
    if {Path(e['target']) for e in plan['entries']} != allowed:
        raise RuntimeError('Exact three-target allowlist mismatch')
    data = []
    for e in plan['entries']:
        before = read_exact(e['target'], e['old_sha256'])
        if read_exact(e['old_snapshot'], e['old_sha256']) != before:
            raise RuntimeError('Original archive differs')
        draft = read_exact(e['draft'], e['new_sha256'])
        data.append((e, draft))
    for e in plan['protected']:
        read_exact(e['path'], e['sha256'])
    read_exact(plan['proof_wind_plan']['path'], plan['proof_wind_plan']['sha256'])
    ancestor = heavy_parent(plan) if args.apply else None
    out.mkdir(parents=True, exist_ok=False)
    receipt = dict(plan_sha256=PLAN_SHA256, mode='apply' if args.apply else 'dry-run',
                   status='PASS', installed=[], checks='All old/draft/protected SHA checks PASS',
                   heavy_ancestor=ancestor, native_verification='UNVERIFIED; texture generation, both smokes, all3 rebuilds/original gates, full installed native proof required')
    try:
        if args.apply:
            for i, (e, draft) in enumerate(data):
                temp = out / (str(i) + '.new')
                with temp.open('xb') as f:
                    f.write(draft)
                    f.flush()
                    os.fsync(f.fileno())
                temp.chmod(e['mode'])
                # Recheck immediately before replacement. Serialization and
                # SHA checks detect cooperative conflicts; no claim is made
                # that filesystem replace is compare-and-swap for other writers.
                read_exact(e['target'], e['old_sha256'])
                os.replace(temp, e['target'])
                read_exact(e['target'], e['new_sha256'])
                receipt['installed'].append(dict(path=e['target'], sha256=e['new_sha256']))
            for e in plan['protected']:
                read_exact(e['path'], e['sha256'])
    except BaseException as ex:
        receipt['status'] = 'FAIL'
        receipt['error'] = str(ex)
        receipt['partial_apply'] = bool(receipt['installed'])
        raise
    finally:
        (out / 'prepare_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
