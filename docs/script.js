// --- 設定項目 ---
const GITHUB_OWNER = "shiro46mt";
const GITHUB_REPO = "jp-medicine-master-data";
const GITHUB_BRANCH = "main";
// ----------------

const BASE_DOWNLOAD_URL = `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/${GITHUB_BRANCH}/`;
const CATALOG_URL = BASE_DOWNLOAD_URL + 'data/data_catalog.json';

document.addEventListener('DOMContentLoaded', fetchCatalogAndGenerateLinks);

async function fetchCatalogAndGenerateLinks() {
    const container = document.getElementById('downloads-container');
    try {
        const response = await fetch(CATALOG_URL);
        if (!response.ok) throw new Error(`カタログファイルの読み込みに失敗: ${response.statusText}`);
        const catalog = await response.json();

        container.innerHTML = '';
        if(catalog.update) {
            document.getElementById('updated-date').textContent = `カタログ更新日: ${catalog.update}`;
        }

        const data = catalog.data;
        for (const item of data) {
            const categoryId = item.id;
            const categoryName = item.name;
            const files = item.files;

            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'category';

            const title = document.createElement('h2');
            title.textContent = `${categoryName}`;
            categoryDiv.appendChild(title);

            if (files && files.length > 0) {
                const downloadDiv = document.createElement('div');
                downloadDiv.className = 'download-controls';

                // 1. ファイルを日付の降順（新しい順）に並べ替える
                // 元の配列が日付で昇順になっている前提で、reverse()で降順にする
                const sortedFiles = files.reverse();

                // 2. バージョン選択用の <select> 要素を作成
                const select = document.createElement('select');
                select.className = 'version-select';

                // 3. ファイルを反復処理し、<option>を作成
                sortedFiles.forEach((filePath, index) => {
                    const fileName = filePath.split('/').pop();

                    // ファイル名から日付部分(yyyymmdd)を抽出
                    // 8桁の数字が末尾から12文字目から始まると仮定
                    // 例: "sales_data20240115.csv" の場合、20240115を抽出
                    const dateMatch = fileName.match(/(\d{8})\.csv$/);

                    let dateString = '';
                    if (dateMatch) {
                        const yyyymmdd = dateMatch[1];
                        // yyyy-mm-dd 形式に変換
                        dateString = `${yyyymmdd.substring(0, 4)}-${yyyymmdd.substring(4, 6)}-${yyyymmdd.substring(6, 8)}`;
                    } else {
                        // 日付が抽出できない場合のフォールバック（例: ファイル名全体を表示）
                        dateString = fileName;
                        console.warn(`ファイル名から日付を抽出できませんでした: ${fileName}`);
                    }

                    const option = document.createElement('option');
                    // オプションの表示テキストを yyyy-mm-dd 形式にする
                    option.textContent = dateString;
                    // optionのvalueにはファイルのフルパスを設定
                    option.value = filePath;

                    // 降順ソート後の最初の要素 (最新のファイル) をデフォルトで選択
                    if (index === 0) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });

                // 4. ダウンロードボタンの作成
                const button = document.createElement('a');
                button.className = 'download-button';
                button.textContent = `Download`;
                button.href = '#';

                // 5. 初期選択されたファイル (最新) の情報を取得
                const initialSelectedFile = sortedFiles[0];
                let currentDownloadUrl = BASE_DOWNLOAD_URL + `data/${categoryId}/${initialSelectedFile}`;
                let currentOriginalFileName = initialSelectedFile.split('/').pop();
                let currentNewFileName = `${categoryId}_${currentOriginalFileName}`;

                // 6. 選択肢が変更された時の処理
                select.addEventListener('change', (event) => {
                    const selectedFilePath = event.target.value;
                    const selectedOriginalFileName = selectedFilePath.split('/').pop();

                    // ダウンロードURLと表示ファイル名を更新
                    currentDownloadUrl = BASE_DOWNLOAD_URL + `data/${categoryId}/${selectedFilePath}`;
                    currentOriginalFileName = selectedOriginalFileName;
                    currentNewFileName = `${categoryId}_${currentOriginalFileName}`;
                });

                // 7. ダウンロードボタンのクリックイベント
                button.addEventListener('click', (event) => {
                    event.preventDefault(); // ページ遷移をキャンセル
                    // 現在選択されているURLとファイル名を使用してダウンロードを実行
                    handleDownload(button, currentDownloadUrl, currentNewFileName);
                });

                // 8. 要素をコンテナに追加
                downloadDiv.appendChild(select);
                downloadDiv.appendChild(button);
                categoryDiv.appendChild(downloadDiv);
            } else {
                const noFileText = document.createElement('p');
                noFileText.className = 'no-file';
                noFileText.textContent = '利用可能なファイルがありません。';
                categoryDiv.appendChild(noFileText);
            }
            container.appendChild(categoryDiv);
        }
    } catch (error) {
        console.error('エラー:', error);
        container.innerHTML = `<p style="color: red;">エラーが発生しました。${error.message}</p>`;
    }
}

// ファイルを強制ダウンロードさせるための関数
async function handleDownload(button, url, filename) {
    const originalText = button.textContent;
    button.textContent = 'ダウンロード中...';
    button.classList.add('is-downloading');

    try {
        // 1. fetch APIでファイルデータを取得
        const response = await fetch(url);
        if (!response.ok) throw new Error('ファイルの取得に失敗しました');

        // 2. データをBlobオブジェクトに変換
        const blob = await response.blob();

        // 3. Blobから一時的なURLを生成
        const blobUrl = URL.createObjectURL(blob);

        // 4. 見えないリンクを作成してクリックさせ、ダウンロードをトリガー
        const tempLink = document.createElement('a');
        tempLink.href = blobUrl;
        tempLink.setAttribute('download', filename); // ★プレフィックス付きのファイル名を設定
        tempLink.style.display = 'none';
        document.body.appendChild(tempLink);
        tempLink.click();

        // 5. 後片付け
        document.body.removeChild(tempLink);
        URL.revokeObjectURL(blobUrl);

    } catch (error) {
        console.error('Download failed:', error);
        button.textContent = 'ダウンロード失敗';
        // 2秒後に元のテキストに戻す
        setTimeout(() => { button.textContent = originalText; }, 2000);
    } finally {
        // ボタンの表示を元に戻す
        if (button.textContent !== 'ダウンロード失敗') {
            button.textContent = originalText;
        }
        button.classList.remove('is-downloading');
    }
}
