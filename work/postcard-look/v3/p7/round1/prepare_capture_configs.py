#!/usr/bin/env python3
"""Freeze camera-only JSON copies beneathv3; reject any existing destination."""
from pathlib import Path
import argparse, copy, importlib.util, json

p = argparse.ArgumentParser()
p.add_argument('root', type=Path)
p.add_argument('--out', type=Path)
a = p.parse_args()
r = a.root.resolve()
v = r / 'work/postcard-look/v3'
out = (a.out or v / 'p7/round1/capture_configs').resolve()
assert out.is_relative_to(v) and not out.exists(), 'Use a fresh destination beneathv3'
module_path = v / 'proof/runtime/config_override.py'
spec = importlib.util.spec_from_file_location('config_override', module_path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
proposal_path = v / 'p7/round1/aerial_cfg_proposed.json'
proposal = json.loads(proposal_path.read_text())
proposed = m.camera_map(proposal)
pending, entries = {}, []
for name, rel in m.FILES.items():
    source = v / rel
    before = json.loads(source.read_text())
    after = copy.deepcopy(before)
    if name in ('proof_cfg_round1.json', 'split_outline_cfg_round1.json'):
        data, differences = source.read_bytes(), []
    else:
        for s in after['shots']:
            if s.get('kind') == 'landmark' and s.get('name', '').endswith('aerial'):
                for field in ('pos', 'look', 'fov'):
                    s[field] = copy.deepcopy(proposed[s['hole']][field])
        differences = m.camera_changes(before, after, proposed, name)
        data = source.read_bytes() if not differences else m.dumps(after)
    pending[name] = data
    entries.append({'name': name, 'source': str(source), 'copy': str(out / name), 'oldSha256': m.sha(source), 'newSha256': m.hashlib.sha256(data).hexdigest(), 'differences': differences})
before = json.loads((v / m.FILES['stills_cfg_12.json']).read_text())['shots']
after = json.loads(pending['stills_cfg_12.json'])['shots']
old_address = [s for s in before if s.get('kind') == 'address']
new_address = [s for s in after if s.get('kind') == 'address']
assert len(before) == len(after) == 12 and len(new_address) == 6 and old_address == new_address
pending['cost_cfg.json'] = m.dumps({'shots': new_address})
entries.append({'name': 'cost_cfg.json', 'source': str(v / m.FILES['stills_cfg_12.json']), 'copy': str(out / 'cost_cfg.json'), 'oldSha256': m.hashlib.sha256(m.dumps({'shots': old_address})).hexdigest(), 'newSha256': m.hashlib.sha256(pending['cost_cfg.json']).hexdigest(), 'differences': [], 'scope': 'Derived six actual address shots; canonical bytes unchanged'})
manifest = {'schema': 1, 'scope': 'aerial-camera-fields-only', 'root': str(r), 'proposalSource': str(proposal_path), 'proposalSourceSha256': m.sha(proposal_path), 'proposedCameras': proposal, 'validatorSource': str(module_path), 'validatorSourceSha256': m.sha(module_path), 'preparerSource': str(v / 'proof/runtime/prepare_runtime.py'), 'preparerSourceSha256': m.sha(v / 'proof/runtime/prepare_runtime.py'), 'files': entries, 'note': 'Semantic and Split configs have no camera fields and are byte-identical copies. Only pos/look/fov of3 aerials changed in each shot config; all non-aerial and6 address frames unchanged. No native capture or visual PASS implied.'}
out.mkdir(parents=True)
for name, data in pending.items():
    (out / name).write_bytes(data)
(out / 'capture_config_manifest.json').write_bytes(m.dumps(manifest))
_, receipt = m.load_override(v, out)
(out / 'parse_validation.json').write_bytes(m.dumps(receipt))
print(json.dumps({'folder': str(out), 'manifestSha256': m.sha(out / 'capture_config_manifest.json'), 'parseValidation': 'PASS', 'changedFields': sum(len(x['differences']) for x in entries), 'unchangedAddressFrames': 6, 'nativeCaptured': False}, indent=2))
