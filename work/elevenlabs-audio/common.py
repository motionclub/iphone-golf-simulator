import os, json, time
from elevenlabs import ElevenLabs
HERE = os.path.dirname(os.path.abspath(__file__))
for l in open(os.path.join(HERE, '../../.env.local')):
    l = l.strip().removeprefix('export ')
    if l.startswith('ELEVENLABS_API_KEY='): os.environ['ELEVENLABS_API_KEY'] = l.split('=', 1)[1].strip().strip('"\'')
client = ElevenLabs(api_key=os.environ['ELEVENLABS_API_KEY'])
JAX = 'iB0m5bo5Htdz0t9yE0xq'
def used():
    return client.user.subscription.get().character_count
def save(path, chunks):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        for c in chunks: f.write(c)
def run(items, fn, label):
    """items: [(relpath, kwargs)]. Skips existing files; logs credit cost per file."""
    for rel, kw in items:
        p = os.path.join(HERE, 'raw', rel)
        if os.path.exists(p): continue
        for attempt in range(3):
            try: save(p, fn(**kw)); break
            except Exception as e:
                print('ERR', rel, str(e)[:200]); time.sleep(3)
        print(label, rel, flush=True)
