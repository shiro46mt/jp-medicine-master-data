from datetime import datetime
import json
from pathlib import Path


# 出力先
data_dir = Path(__file__).parents[1] / 'data'

catalog = {
    'update': datetime.now().strftime('%Y-%m-%d'),
    'data': {},
}

# csvファイルの一覧を取得
data_subdirs = sorted(data_dir.glob('*'))
for d in data_subdirs:
    if d.is_dir():
        catalog['data'][d.name] = []

        files = sorted(d.glob('**/*.csv'))
        for f in files:
            catalog['data'][d.name].append(f.relative_to(d).as_posix())

# 変更の有無の確認
filepath = data_dir / 'data_catalog.json'
with open(filepath, 'r', encoding='utf8') as f:
    catalog_prev = json.load(f)

# 変更があれば出力
if catalog['data'] != catalog_prev['data']:
    with open(filepath, 'w', newline='', encoding='utf8') as f:
        json.dump(catalog, f, indent=4, ensure_ascii=False)
