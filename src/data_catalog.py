from datetime import datetime
import json
from pathlib import Path


# 出力先
data_dir = Path(__file__).parents[1] / 'data'

cataog = {
    'update': datetime.now().strftime('%Y-%m-%d'),
    'data': {},
}

data_subdirs = data_dir.glob('*')
for d in data_subdirs:
    cataog['data'][d.name] = []

    files = d.glob('**/*.csv')
    for f in files:
        cataog['data'][d.name].append(f.relative_to(d).as_posix())

filepath = data_dir / 'data_catalog.json'
with open(filepath, 'w', newline='', encoding='utf8') as f:
    json.dump(cataog, f, indent=4, ensure_ascii=False)
