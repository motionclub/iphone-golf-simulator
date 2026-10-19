# put_uploads.py <media_upload result json> <dir> [<dir> ...]
# PUTs each file named in the upload result (found in the given dirs) to its presigned URL with curl;
# prints "filename media_id status" and appends to refs/media_ids.tsv.
import json, re, subprocess, sys, os
r = json.load(open(sys.argv[1]))
if isinstance(r, list): r = json.loads(r[0]['text'])
out = open(os.path.join(os.path.dirname(__file__), '..', 'refs', 'media_ids.tsv'), 'a')
for u in r['uploads']:
    name = re.search(r'--data-binary @(\S+) ', u['instructions']).group(1)
    path = next((os.path.join(d, name) for d in sys.argv[2:] if os.path.exists(os.path.join(d, name))), None)
    if not path: print(name, u['media_id'], 'MISSING'); continue
    code = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-X', 'PUT', '-H', 'Content-Type: ' + u['content_type'],
                           '--data-binary', '@' + path, u['upload_url']], capture_output=True, text=True).stdout
    print(name, u['media_id'], code); out.write(f'{name}\t{u["media_id"]}\n')
