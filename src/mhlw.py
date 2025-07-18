from pathlib import Path
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import pandas as pd
import requests


# 出力先
data_dir = Path(__file__).parents[1] / 'data'

# requests用パラメータ
headers = {'User-Agent': ''}
timeout_sec = 60


def get_file_urls():
    # 医療保険が適用される医薬品について
    top_url = 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000078916.html'
    html = requests.get(top_url, timeout=timeout_sec, headers=headers)
    html.raise_for_status()
    soup = BeautifulSoup(html.content, 'html.parser')

    # 薬価基準収載品目リストについて へのリンク
    page_url_tags = soup.find_all('a', string=re.compile('薬価基準収載品目リストについて'))
    page_urls = [urljoin(top_url, tag.attrs['href']) for tag in page_url_tags]

    # 薬価基準収載品目リストについて の各ページ
    file_urls = {}
    for page_url in page_urls:
        # 年度の取得
        mob = re.search(r'/tp(\d{4})\d{4}-01.html', page_url)
        if mob:
            year = mob.group(1)
        else:
            continue

        # ページの取得
        html = requests.get(page_url, timeout=timeout_sec, headers=headers)
        html.raise_for_status()
        soup = BeautifulSoup(html.content, 'html.parser')

        # ダウンロード用リンクの取得
        file_url_tags = soup.select('#contents .ico-excel a')[:5]
        file_urls[year] = [urljoin(page_url, tag.attrs['href']) for tag in file_url_tags]

    return file_urls


def download_price(year, file_urls: list[str]):
    """厚労省HPから、(1)-(4)薬価基準収載品目リストの一覧ファイルをダウンロードし、csv形式 (UTF-8) で保存する。

    Args:
        file_urls:
    """
    pattern = re.compile(r"(tp(\d{8})-01_0?[1234].xlsx?)")
    dfs = []
    max_update = '00000000'

    for file_url in file_urls:
        # ファイル名の確認
        mob = pattern.search(file_url)
        if mob is None:
            continue

        # ファイルの読み込み
        df = pd.read_excel(file_url, dtype=str)
        # df['file'] = mob.group(1)
        dfs.append(df)

        # 更新日の更新
        max_update = max(max_update, mob.group(2))

    # データフレームの連結
    df = pd.concat(dfs)

    # 列名の矯正
    df = df.rename(columns={'Unnamed: 4': '日本薬局方', 'Unnamed: 5': '麻薬', 'Unnamed: 6': '業者名追記'})

    # バリデーション
    assert set(df['区分'].unique()) == set(['内用薬', '注射薬', '外用薬', '歯科用薬剤'])

    # csvの出力
    filepath = data_dir / f'mhlw_price/{year}/{max_update}.csv'
    if not filepath.parent.is_dir():
        filepath.parent.mkdir()
    df.to_csv(filepath, index=False, encoding='utf8')


def download_ge(year, file_urls: list[str]):
    """厚労省HPから、(5)後発医薬品に関する情報の一覧ファイルをダウンロードし、csv形式 (UTF-8) で保存する。

    Args:
        file_urls:
    """
    pattern = re.compile(r"(tp(\d{8})-01_0?5.xlsx?)")

    file_url = max([f for f in file_urls if pattern.search(f)])

    # ファイル名の確認
    mob = pattern.search(file_url)

    # ファイルの読み込み
    df = pd.read_excel(file_url, dtype=str)
    # df['file'] = mob.group(1)

    # 列名の矯正
    df = df.rename(columns={'収載年月日(YYYYMMDD)\n【例】\n2016年4月1日\n(20160401)': '収載年月日'})

    # バリデーション

    # csvの出力
    filepath = data_dir / f'mhlw_ge/{year}/{mob.group(2)}.csv'
    if not filepath.parent.is_dir():
        filepath.parent.mkdir()
    df.to_csv(filepath, index=False, encoding='utf8')


def main():
    file_urls = get_file_urls()
    for year, urls in file_urls.items():
        download_price(year, urls)
        download_ge(year, urls)


if __name__ == '__main__':
    main()
