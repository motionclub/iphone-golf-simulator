#!/usr/bin/env python3
"""Finite report renderer. No native/Git launches, threshold edits or staging.

Drafts write a fresh chosen path underv3. --final writes REPORT.md only after
root supplies completed phases, a fresh physical review and completed P8 facts.
All41 gate rows come verbatim from compactMeasurement, never large observed JSON.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, re


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def line(value):
    return re.sub(r'\s+', ' ', str(value)).strip().replace('|', '\\|')


def link(path, label):
    return '[' + label + '](<' + str(Path(path).resolve()) + '>)'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('summary', type=Path)
    parser.add_argument('facts', type=Path, help='Root-reviewed phase/files/commit/push/next-step JSON')
    parser.add_argument('--out', type=Path, help='Fresh draft output beneathv3')
    parser.add_argument('--final', action='store_true')
    parser.add_argument('--max-words', type=int, default=1800, help='Formatting budget only; root may raise it to retain all required facts')
    args = parser.parse_args()
    v3 = Path(__file__).resolve().parent.parent
    root = v3.parents[2]
    summary_path, facts_path = args.summary.resolve(), args.facts.resolve()
    require(summary_path.is_relative_to(v3) and facts_path.is_relative_to(v3), 'Inputs must remain beneathv3')
    summary, facts = json.loads(summary_path.read_text()), json.loads(facts_path.read_text())
    run = Path(summary['installedRun']).resolve()
    outputs = Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/ope/outputs').resolve()
    deliverables = facts.get('deliverablePaths', {})
    display_evidence = []
    def display(actual, label, key, hole=None):
        actual = Path(actual).resolve()
        mapping = deliverables.get(key, {}) if hole is not None else deliverables.get(key)
        destination = mapping.get(str(hole)) if hole is not None else mapping
        if destination:
            destination = Path(destination).resolve()
            require(destination.is_relative_to(outputs) and destination.is_file(), 'Every display link must be an existing chatoutputs file')
            require(actual.is_file() and sha(destination) == sha(actual), 'Deliverable SHA does not match primary evidence: '+str(actual))
            display_evidence.append(destination)
            return link(destination, label)
        require(not args.final, 'Final report requires copied/verified deliverablePaths: '+key+(' Hole'+str(hole) if hole is not None else ''))
        return label+': `'+str(actual)+'`'
    require(run.is_relative_to(v3/'proof/runtime/runs'), 'Actual installed RUNDIR required')
    require(summary.get('gateCount') == 41 and len(summary['gates']) == 41, 'Exactly41 gate rows required')
    inventory = json.loads((v3/'proof/report_inventory.json').read_text())
    expected = [x['gate'] for x in inventory['gates']]
    require([x['gate'] for x in summary['gates']] == expected, 'Gate identity/order must match unchanged41-row inventory')
    require(all(g['status'] in ('PASS', 'FAIL') and isinstance(g.get('compactMeasurement'), str) and g['compactMeasurement'].strip() for g in summary['gates']), 'Binary results and compact measured fields required')
    phases = facts['phases']
    require([x['phase'] for x in phases] == list(range(9)), 'Phases0–8 required in order')
    require(all(x['status'] in ('PASS', 'FAIL') for x in phases), 'Every phase row must be binary')
    review = summary['holesAndThirtyDifferences']
    holes = review['holes']
    require({h['hole'] for h in holes} == {8, 9, 10}, 'All three hole reviews required')
    require(all(sorted(d['p0_rank'] for d in h['differences']) == list(range(1, 11)) for h in holes), 'All30 original ranks required')
    require(all(d['result'] in ('PASS', 'FAIL') for h in holes for d in h['differences']), 'Every difference must remain binary')
    require(facts['push']['status'] in ('PASS', 'FAIL') and facts['commit']['status'] in ('PASS', 'FAIL'), 'Binary commit/push status required')
    evidence = [summary_path, facts_path]
    if args.final:
        require(facts.get('rootReviewedSummary') is True and facts.get('completed') is True, 'Root review/completed facts required before final publication')
        require(all(x.get('closed') is True for x in phases), 'All phase attempts must be closed before final REPORT')
        require((run/'run_exit_code.txt').is_file(), 'Actual native run must have finished')
        require(Path((run/'effective_unity_project.txt').read_text().strip()).resolve() == root/'Unity', 'Primary Unity project required')
        require('stageAssets=installed-default' in (run/'proof_scope.txt').read_text(), 'Installed scope required')
        physical = summary.get('physicalEyeReviewEvidence')
        require(physical and sha(physical['path']) == physical['sha256'], 'Fresh physical eye review required')
        eye = json.loads(Path(physical['path']).read_text())
        require(eye.get('physicalImageReview') is True and eye.get('installedRun') in (str(run), run.name), 'Physical review must bind this final run')
        evidence.append(Path(physical['path']))
        for g in summary['gates']:
            for item in g['evidence']:
                require(sha(item['path']) == item['sha256'], 'Gate evidence changed after extraction: '+item['path'])
        for part in ('commit', 'push'):
            record = facts[part]
            require(record.get('closed') is True, 'P8 '+part+' attempt/decision must be closed')
            require(record.get('evidence'), 'Exact P8 '+part+' evidence/decision record required')
            for path in record['evidence']:
                require(Path(path).resolve().is_relative_to(v3) and Path(path).is_file(), 'P8 evidence must exist underv3')
                evidence.append(Path(path))
        if facts['commit']['status'] == 'PASS':
            require(re.fullmatch('[0-9a-f]{40}', facts['commit'].get('sha', '')), 'Actual40-character commit SHA required')
        if facts['push']['status'] == 'PASS':
            require(facts['push'].get('exitCode') == 0 and facts['push'].get('force') is False, 'Actual successful no-force push required')
    counts = {s: sum(g['status'] == s for g in summary['gates']) for s in ('PASS', 'FAIL')}
    eyes_ok = all(h['recognisableFromReference'] is True and h['hasBoxPlankFlatStripStripeOrPlasticRead'] is False and all(d['result'] == 'PASS' for d in h['differences']) for h in holes)
    hard_failures = list(facts['hardRuleFailures'])
    for g in summary['gates']:
        if g['gate'] in ('PROTECTED_FILES', 'GUARDS_7_OF_7', 'SCORING_BIT_IDENTICAL', 'FBX_META_UNCHANGED') and g['status'] == 'FAIL':
            hard_failures.append(g['gate']+' FAIL: '+g['compactMeasurement'])
    overall = 'PASS' if counts['FAIL'] == 0 and summary['status'] == 'PASS' and eyes_ok and not hard_failures and all(x['status'] == 'PASS' for x in phases) and facts['commit']['status'] == facts['push']['status'] == 'PASS' else 'FAIL'
    texts = [('# POSTCARD LOOK REPORT' if args.final else '# DRAFT REPORT — final publication withheld'), '', f'Overall **{overall}**; **{counts["PASS"]}/41 PASS, {counts["FAIL"]}/41 FAIL**. Eye review overrides numerical PASS. Earlier failed attempts remain recorded.', '', f'Installed run: `{run}`. Numbers, raw failures and hashes: '+display(summary_path, 'authoritative 41-row extraction', 'authoritative_summary')+'.', '', '| Gate | Result | Measured number |', '|---|---|---|']
    for g in summary['gates']:
        texts.append('| '+g['gate']+' | '+g['status']+' | '+line(g['compactMeasurement'])+' |')
    texts += ['', 'Caps unchanged: fairway12%, green8%, water15%, landmark64px, outline80%, cuboids20%, geometry300,000/hole, tee250 draws. Retain stricter original checks; SetPass uncapped; scoring exactly0m; unsupported/stale measurements FAIL.', '', '| Phase | Result | Completed work / limit |', '|---|---|---|']
    for p in phases:
        texts.append('| P'+str(p['phase'])+' | '+p['status']+' | '+line(p['detail'])+' |')
    texts += ['', 'The original Phase0 protected snapshot was never reset. Narrow7/7 guards cannot clear broader changes. Concurrent changes remain preserved and count in the hard-rule result.']
    texts += ['Hard-rule failures: '+('; '.join(line(x) for x in hard_failures) if hard_failures else 'none recorded by the completed original-baseline checks.')]
    texts += ['', 'Native 900×1600 captures use the primary Unity Editor Game view and actual StartHole/CameraRig/URP. Costs: one camera, three stable positive frames; Editor counters, no physical iPhone capture. Geometry and rendered/shadow triangles differ. Metal export/unsigned iphoneos Release build does not prove physical execution.', '']
    texts += ['All three holes share '+display(run/'contact_sheets/sheet_all_12.jpg', 'the complete 12-still contact sheet', 'common_contact')+'. Their individual 4-frame sheets follow.', '']
    compact_differences = facts.get('compactDifferences', {})
    for h in sorted(holes, key=lambda x: x['hole']):
        number = h['hole']
        texts += [f'**Hole{number}**: '+('YES' if h['recognisableFromReference'] else 'NO')+' recognition; '+('unwanted box/plank/flat-strip/stripe/plastic read remains.' if h['hasBoxPlankFlatStripStripeOrPlasticRead'] else 'no unwanted read reported.'), display(h['contactSheet'], f'Hole{number} 4-frame contact sheet', 'perholecontact', number)+'; '+display(h['vsRef'], f'Hole{number} versus reference', 'vsref', number)+'.', '']
        for d in sorted(h['differences'], key=lambda x: x['p0_rank']):
            override = compact_differences.get(str(number), {}).get(str(d['p0_rank']))
            remaining = override or d.get('remaining') or d['difference']
            texts.append(f'- P0#{d["p0_rank"]} {d["result"]}: '+line(remaining))
        texts.append('')
    texts += ['Files changed, grouped from the actual owned course diff/commit:', '']
    for group in facts['filesChanged']:
        texts.append('- '+line(group['group'])+': '+line(group['summary']))
    texts += ['', 'Commit **'+facts['commit']['status']+'**: '+(facts['commit'].get('sha') or 'not committed')+'; '+line(facts['commit']['detail'])+'.', 'Push **'+facts['push']['status']+'**: '+line(facts['push']['detail'])+'. No force-push/rebase over others’ work.', 'Unfinished work and exact next step: '+line(facts['nextStep']), '', f'History: {sum(c["exit"] != 0 for c in summary["commands"])} original command failures; {len(summary["rawFailuresRetained"])} raw FAIL lines. First P6 and prior eye scores remain separate.']
    report = '\n'.join(texts)+'\n'
    words = len(report.split())
    if args.final:
        require(args.max_words > 0 and words <= args.max_words, f'Report has{words} words; shorten manual wording or raise formatting budget without truncating required facts')
        for target in re.findall(r'\]\(<([^>]+)>\)', report):
            require(Path(target).resolve().is_relative_to(outputs), 'Final Markdown links must target chatoutputs only')
    out = (v3/'REPORT.md' if args.final else args.out)
    require(out is not None, 'Choose a fresh draft --out or explicitly request --final')
    out = Path(out).resolve()
    require(out.is_relative_to(v3) and not out.exists(), 'Never overwrite a report/history file')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    receipt = {'generatedUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'scope': 'FINAL' if args.final else 'DRAFT_ONLY', 'report': str(out), 'reportSha256': sha(out), 'wordCount': words, 'gateRows': 41, 'originalDifferenceRows': 30, 'overall': overall, 'inputs': [{'path':str(p), 'sha256':sha(p)} for p in evidence], 'verifiedDisplayDeliverables': [{'path':str(p), 'sha256':sha(p)} for p in display_evidence], 'source':str(Path(__file__).resolve()), 'sourceSha256':sha(__file__)}
    out.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
