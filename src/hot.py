from io import BytesIO
from pathlib import Path
import re
from urllib.parse import urljoin
import zipfile

from bs4 import BeautifulSoup
import requests


# requests用パラメータ
headers = {'User-Agent': ''}
timeout_sec = 60

# # OpenSSLのデフォルトから、より幅広い暗号スイートを許可する設定に変更
# requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH'


def get_file_url():
    # トップページ
    top_url = 'https://www2.medis.or.jp/hcode/'.replace('https:', 'http:')
    html = requests.get(top_url, timeout=timeout_sec, headers=headers)
    html.raise_for_status()
    soup = BeautifulSoup(html.content, 'html.parser')

    # ダウンロード用リンクの取得
    file_url_tag = soup.find('a', string=re.compile('ZIP版'))
    file_url = urljoin(top_url, file_url_tag.attrs['href']).replace('https:', 'http:')

    return file_url


def download_hot(file_url: str):
    """MEDISから、医薬品HOTコードマスターをダウンロードし、csv形式 (UTF-8) で保存する。"""
    pattern_13 = re.compile(r"MEDIS(\d{8}).TXT", re.IGNORECASE)
    pattern_9 = re.compile(r"MEDIS(\d{8})_HOT9.TXT", re.IGNORECASE)

    # ファイルダウンロード
    r = requests.get(file_url, stream=True)
    r.raise_for_status()
    zip_content = BytesIO(r.content)

    # zipファイルの中のcsvファイルを読み込み
    with zipfile.ZipFile(zip_content, 'r') as zf:
        for filename in zf.namelist():
            # ファイル名のパターンを判定
            mob_13 = pattern_13.search(filename)
            mob_9 = pattern_9.search(filename)

            if mob_13:
                update = mob_13.group(1)
                target_dir = Path('data/hot13')
            elif mob_9:
                update = mob_9.group(1)
                target_dir = Path('data/hot9')
            else:
                continue

            # ファイルの読み込み
            with zf.open(filename) as cf:
                csv_content = cf.read().decode('cp932')

            # csvの出力
            filepath = target_dir / f'{update}.csv'
            filepath.write_text(csv_content, encoding='utf8', newline='')


def main():
    file_url = get_file_url()
    download_hot(file_url)


if __name__ == '__main__':
    main()
