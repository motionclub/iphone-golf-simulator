"""Ship menu postcards from reviewed game captures, retaining source provenance."""
from pathlib import Path
import hashlib, json, sys
from PIL import Image

repo = Path(__file__).resolve().parents[2]
golf = repo / sys.argv[1]
tennis = repo / sys.argv[2]
sources = {
    'map-golf-cliffside': golf / 'hole12_preview.png',
    'map-golf-postcards': golf / 'hole07_preview.png',
    'map-golf-wildisles': golf / 'hole19_preview.png',
    'map-golf-magma': golf / 'hole21_preview.png',
    'map-resort': tennis / 'resort_2_postcard.png',
    'map-skyscraper': tennis / 'skyscraper_2_postcard.png',
    'map-volcano': tennis / 'volcano_2_postcard.png',
}
for source in sources.values():
    if not source.is_file(): raise FileNotFoundError(source)
records = []
for name, source in sources.items():
    destination = repo / 'GolfArcade/Unity/MenuArt' / (name + '.jpg')
    with Image.open(source) as image:
        image = image.convert('RGB')
        image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        image.save(destination, quality=94, optimize=True)
        size = image.size
    records.append({
        'name': name, 'source': str(source.relative_to(repo)),
        'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'output': str(destination.relative_to(repo)), 'size': size,
        'outputSha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
        'provenance': 'Actual Unity runtime capture; aspect-preserving downsample and JPEG encoding only',
    })
(repo / 'work/full-visual-overhaul/menu-art-provenance.json').write_text(json.dumps(records, indent=2))
print('Updated seven actual-game menu postcards.')
