from pathlib import Path
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import pandas as pd
import requests


# 出力先
DATA_DIR = Path(__file__).parents[1] / 'data'

# バリデーション用
LOWER_BOUND = 0.8
UPPER_BOUND = 1.2


def get_file_urls():
    # requests用パラメータ
    headers = {'User-Agent': ''}
    timeout_sec = 60

    # 医療保険が適用される医薬品について
    top_url = 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000078916.html'
    html = requests.get(top_url, timeout=timeout_sec, headers=headers)
    html.raise_for_status()
    soup = BeautifulSoup(html.content, 'html.parser')

    # 処方箋に記載する一般名処方の標準的な記載（一般名処方マスタ）について へのリンク
    page_url_tags = soup.find_all('a', string=re.compile('処方箋に記載する一般名処方の標準的な記載'))
    page_urls = [urljoin(top_url, tag.attrs['href']) for tag in page_url_tags]

    # 処方箋に記載する一般名処方の標準的な記載（一般名処方マスタ）について の各ページ
    file_urls = {}
    for page_url in page_urls:
        # 年度の取得
        mob = re.search(r'/shohosen_(\d{2})\d{4}.html', page_url)
        if mob:
            year = '20' + mob.group(1)
        else:
            continue

        # ページの取得
        html = requests.get(page_url, timeout=timeout_sec, headers=headers)
        html.raise_for_status()
        soup = BeautifulSoup(html.content, 'html.parser')

        # ダウンロード用リンクの取得
        file_url_tag = soup.select_one('#contents .ico-excel a')
        file_urls[year] = urljoin(page_url, file_url_tag.attrs['href'])

    return file_urls


def download_ippanmeishohou(year, file_url: str):
    """厚労省HPから、一般名処方マスタをダウンロードし、csv形式 (UTF-8) で保存する。

    Args:
        file_url:
    """
    pattern = re.compile(r"ippanmeishohoumaster_(\d{6}).xlsx")

    # ファイル名の確認
    mob = pattern.search(file_url)

    # 全体シートの読み込み
    df_all = (
        pd.read_excel(file_url, dtype=str, header=2, sheet_name=0)
        .assign(**{
            '規格': lambda d: d['規格'].str.replace(r'\n', '／', regex=True),
            '備考': lambda d: d['備考'].str.replace(r'\n', '／', regex=True),
        })
    )

    # 例外コード品目の読み込み
    df_exception = (
        pd.read_excel(file_url, dtype=str, header=2, sheet_name=1, usecols=[1,5,9,16], names=['一般名コード', '薬価基準収載医薬品コード_例外コード', '品名_例外コード', '備考_例外コード'])
        .query("薬価基準収載医薬品コード_例外コード == 薬価基準収載医薬品コード_例外コード")  # 薬価基準収載医薬品コード_例外コードのnull行を除外
        .assign(**{
            '一般名コード': lambda d: d['一般名コード'].ffill(),
            '備考_例外コード': lambda d: d['備考_例外コード'].str.replace(r'\n', '／', regex=True)
        })
    )

    # 突合
    df = df_all.merge(df_exception, how='left', on='一般名コード')

    # バリデーション
    if (DATA_DIR / 'mhlw_ippanmeishohou').is_dir():
        filepath = max(DATA_DIR.glob('mhlw_ippanmeishohou/*/*.csv'))
        df_prev = pd.read_csv(filepath, encoding='utf8')
        assert df_prev['一般名コード'].nunique() * LOWER_BOUND <= df['一般名コード'].nunique() <= df_prev['一般名コード'].nunique() * UPPER_BOUND
        assert list(df.columns) == list(df_prev.columns)
    assert (df['例外コード'].notna() == df['薬価基準収載医薬品コード_例外コード'].notna()).all()

    # csvの出力
    filepath = DATA_DIR / f'mhlw_ippanmeishohou/{year}/20{mob.group(1)}.csv'
    if not filepath.parent.is_dir():
        filepath.parent.mkdir(parents=True)
    df.to_csv(filepath, index=False, encoding='utf8')


def main():
    file_urls = get_file_urls()
    for year, url in file_urls.items():
        download_ippanmeishohou(year, url)


if __name__ == '__main__':
    main()
