from io import BytesIO
from pathlib import Path
import re
from urllib.parse import urljoin
import zipfile

from bs4 import BeautifulSoup
import pandas as pd
import requests


# 出力先
data_dir = Path(__file__).parents[1] / 'data'

# requests用パラメータ
headers = {'User-Agent': ''}
timeout_sec = 60


def get_file_urls():
    # トップページ
    top_url = 'https://shinryohoshu.mhlw.go.jp/shinryohoshu/downloadMenu/'
    html = requests.get(top_url, timeout=timeout_sec, headers=headers)
    html.raise_for_status()
    soup = BeautifulSoup(html.content, 'html.parser')

    # 各年度の診療報酬改定 へのリンク
    page_url_tags = soup.find_all('a', string=re.compile('こちら'))
    page_urls = [urljoin(top_url, tag.attrs['href']) for tag in page_url_tags]
    page_url = max([url.split(';')[0] for url in page_urls if '/kaitei/' in url])

    # 昨年度の診療報酬海底 のページ
    file_urls = {}

    # 年度の取得
    g = page_url[-3]
    if g == 'R':
        year = int(page_url[-2:]) + 2018
    else:
        raise ValueError

    # ページの取得
    html = requests.get(page_url, timeout=timeout_sec, headers=headers)
    html.raise_for_status()
    soup = BeautifulSoup(html.content, 'html.parser')

    # ダウンロード用リンクの取得
    file_url_tag = soup.find('a', string=re.compile('医薬品マスター'))
    file_urls[str(year)] = urljoin(page_url, file_url_tag.attrs['href'])

    # 最新年度のダウンロード用リンク
    file_urls[str(year+1)] = 'https://shinryohoshu.mhlw.go.jp/shinryohoshu/downloadMenu/yFile'

    return file_urls


def download_y(year, file_url: str):
    """診療報酬情報提供サービスから、医薬品マスターの一覧ファイルをダウンロードし、csv形式 (UTF-8) で保存する。"""
    pattern = re.compile(r"y_(\d{8}).csv")

    # ファイルダウンロード
    r = requests.get(file_url, stream=True)
    r.raise_for_status()
    zip_content = BytesIO(r.content)

    # zipファイルの中のcsvファイルを読み込み
    with zipfile.ZipFile(zip_content, 'r') as zf:
        for filename in zf.namelist():
            # ファイル名の確認
            mob = pattern.search(filename)
            if mob is None:
                continue

            # 更新日の更新
            update = mob.group(1)

            # ファイルの読み込み
            with zf.open(filename) as cf:
                csv_bytes = BytesIO(cf.read())
                df = pd.read_csv(csv_bytes, dtype=str, header=None, encoding='cp932')
                break

    # バリデーション


    # csvの出力
    filepath = data_dir / f'y/{year}/{update}.csv'
    if not filepath.parent.is_dir():
        filepath.parent.mkdir()

    ## ヘッダ行
    filepath_header = Path(__file__).parent / 'y_header.csv'
    filepath.write_bytes(filepath_header.read_bytes())

    ## データ
    df.to_csv(filepath, index=False, header=False, encoding='utf8', mode='a')


def main():
    file_urls = get_file_urls()
    for year, url in file_urls.items():
        download_y(year, url)


if __name__ == '__main__':
    main()
