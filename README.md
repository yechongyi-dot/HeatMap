# HeatMap — 日本投資動画ランキング

YouTube・ニコニコ動画の日本語投資動画をスクレイピングし、熱度スコアでランキングするデスクトップアプリ。

---

## 必要環境

| 項目 | 要件 |
|------|------|
| OS | Windows 10 / 11（64ビット） |
| Python | **3.10 以上**（3.10未満では起動しない） |
| ffmpeg | PATH に通っていること（下記参照） |

### ffmpeg のインストール

```bat
winget install ffmpeg
```

またはバイナリを直接 [ffmpeg.org](https://ffmpeg.org/download.html) からダウンロードして PATH に追加。

> **なぜ必要？**  
> - `bestvideo+bestaudio` 形式のダウンロードで映像・音声を結合するため  
> - 素材ライブラリのサムネイル生成（フレーム抽出）のため

---

## インストール

```bat
pip install -r requirements.txt
```

---

## 起動方法

**ダブルクリック:**
```
launch.bat
```

**コマンドライン:**
```bat
python main.py
```

---

## 毎日自動スクレイピング（Windows タスクスケジューラ）

| 設定項目 | 値 |
|----------|----|
| プログラム | `python` |
| 引数 | `scheduler\daily_job.py` |
| **起始目录（重要）** | `C:\path\to\hm`（プロジェクトのルートフォルダ） |

---

## データ保存場所

```
%LOCALAPPDATA%\HeatMap\
├── data\videos_v2.db    # SQLite データベース
├── downloads\           # ダウンロード動画（変更可）
├── thumbnails\          # サムネイル
└── cookies.txt          # ニコニコ用 Cookie（任意）
```

`HEATMAP_DATA_DIR` 環境変数で変更可能。

---

## ニコニコ動画のログイン（任意）

会員限定動画をダウンロードしたい場合、ブラウザ拡張 [Get cookies.txt](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) でエクスポートした `cookies.txt` を以下に配置：

```
%LOCALAPPDATA%\HeatMap\cookies.txt
```

---

## 在线更新 (Online update)

パッケージ版（`HeatMap.exe`）は GitHub Releases を見て自動更新します。再インストール不要。

- **起動時**：新しいバージョンがあれば確認ダイアログを表示 → 「立即更新」で自動ダウンロード＆再起動。
- **手動**：右上のバージョンチップ（`v0.1.0`）をクリックして更新チェック。

仕組み：実行中の `.exe` は自身を上書きできないため、新ビルドを一時フォルダへ展開し、アプリ終了後にバッチスクリプトがファイルを差し替えて再起動します（ユーザーデータは `%LOCALAPPDATA%\HeatMap\` にあるため影響なし）。

> 開発モード（`python main.py`）では在線更新は無効です（`git pull` を使用）。

---

## ビルドとリリース（メンテナ向け）

```bat
pip install pyinstaller
```

`vendor_ffmpeg/` は容量の都合で Git 管理対象外です。ビルド前に以下のファイルを `vendor_ffmpeg/` に配置してください（リポジトリには含まれません）：

```
vendor_ffmpeg\ffmpeg.exe  ffprobe.exe  avcodec-*.dll  avformat-*.dll  avutil-*.dll
              avfilter-*.dll  avdevice-*.dll  swresample-*.dll  swscale-*.dll
```

新バージョンを配信する手順：

1. `version.py` の `__version__` を上げる（例: `0.1.0` → `0.2.0`）
2. リリーススクリプトを実行（PyInstaller ビルド → zip → `gh release create`）：

```bat
python scripts\release.py
```

これで既存のクライアントは次回起動時に更新を検知します。`gh` の認証が必要です（`gh auth login`）。
