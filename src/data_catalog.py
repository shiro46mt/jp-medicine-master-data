from datetime import datetime
import json
from pathlib import Path


# 出力先
DATA_DIR = Path(__file__).parents[1] / 'data'


def main():
    # カタログ情報
    catalog_info_fielpath = Path(__file__).parent / 'data_catalog_info.json'
    catalog_info = json.loads(catalog_info_fielpath.read_text(encoding='utf8'))

    # カタログの初期化
    catalog = {
        'update': datetime.now().strftime('%Y-%m-%d'),
        'data': [],
    }

    # csvファイルの一覧を取得
    for dirname, info_dict in catalog_info.items():
        data_subdir = DATA_DIR / dirname
        if data_subdir.is_dir():
            # カタログアイテムの初期化
            info_dict['files'] = []

            # ファイルの一覧のリスト化
            files = sorted(data_subdir.glob('**/*.csv'))
            for f in files:
                info_dict['files'].append(f.relative_to(data_subdir).as_posix())

            # カタログアイテムの追加
            catalog['data'].append(info_dict)

    # 変更の有無の確認
    filepath = DATA_DIR / 'data_catalog.json'
    if filepath.is_file():
        with open(filepath, 'r', encoding='utf8') as f:
            catalog_prev = json.load(f)
    else:
        catalog_prev = {
            'update': None,
            'data': [],
        }

    # 変更があれば出力
    if catalog['data'] != catalog_prev['data']:
        with open(filepath, 'w', newline='', encoding='utf8') as f:
            json.dump(catalog, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()
