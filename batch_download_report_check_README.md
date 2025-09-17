# batch_download_report_check.py

## 概要
`kaiji_downloader.py`で生成されたダウンロードレポート（JSONファイル）から、ダウンロードに成功した企業のstock_codeを抽出し、UTF-8 BOM付きCSVファイルとして出力するツールです。

## 主な機能
- batch_download_reportのJSONファイルから成功企業を自動抽出
- 対話式でファイル選択が可能
- UTF-8 BOM付きCSVで出力（Excelでの文字化けを防止）
- Python標準ライブラリのみで動作（追加インストール不要）

## 必要要件
- Python 3.11以上
- 標準ライブラリのみ使用（追加インストール不要）

## インストール
特別なインストールは不要です。Pythonがインストールされていれば動作します。

## 使用方法

### 対話式モード（推奨）
引数なしで実行すると、dataフォルダ内のレポートファイルから選択できます：
```bash
uv run python batch_download_report_check.py
```

### 直接指定モード
特定のファイルを指定して実行：
```bash
uv run python batch_download_report_check.py data/batch_download_report_20250912_175054.json
```

出力ファイル名も指定する場合：
```bash
uv run python batch_download_report_check.py input.json output.csv
```

## 出力形式
### CSVファイルの内容
- `stock_code`: 証券コード
- `company_name`: 企業名
- `success_files`: 成功したダウンロード数

### ファイル形式
- UTF-8エンコーディング（BOM付き）
- カンマ区切り（CSV）
- ヘッダー行あり

注意:
- 対話式モードでは、出力CSVはカレントディレクトリ（実行ディレクトリ）に `{元のファイル名}_successful_stocks.csv` の形式で作成されます。
- `data/` 以外の場所にあるJSONを対象にする場合は、直接指定モードでフルパスまたは相対パスを渡してください。

## 抽出条件
- `success_files`が1以上の企業のみを抽出
- ダウンロードに1つでも成功した企業が対象

## ディレクトリ構成
```
jpx_kaiji_service/
├── batch_download_report_check.py  # 本スクリプト
├── data/                            # レポートファイル格納ディレクトリ
│   └── batch_download_report_*.json # kaiji_downloaderの出力ファイル
└── *.csv                            # カレントディレクトリに出力されるCSVファイル
```

## 実行例
```bash
$ uv run python batch_download_report_check.py
batch_download_reportファイルを検索中...

利用可能なレポートファイル:
------------------------------------------------------------
 1. batch_download_report_20250912_175054.json
    サイズ: 1.54 MB
    更新日時: 2025-09-12 17:50:54

処理するファイルの番号を入力してください (1-1): 1

選択されたファイル: batch_download_report_20250912_175054.json
JSONファイルを読み込み中: data/batch_download_report_20250912_175054.json
  ✓ 14330: 企業A (成功ファイル数: 1)
  ✓ 14360: 企業B (成功ファイル数: 1)
  ...

集計結果:
  総企業数: 3794
  成功企業数: 122

CSVファイルに出力中: batch_download_report_20250912_175054_successful_stocks.csv
  122件のデータを出力しました

処理が完了しました。出力ファイル: batch_download_report_20250912_175054_successful_stocks.csv
```

## エラー処理
- JSONファイルが見つからない場合はエラーメッセージを表示
- JSONの解析エラー時は詳細情報を表示
- Ctrl+Cでいつでも処理を中断可能

## 注意事項
- 大きなJSONファイル（数MB以上）の処理には時間がかかる場合があります
- 出力CSVファイルは既存ファイルを上書きします
- BOM付きUTF-8のため、Excelで直接開いても文字化けしません

## ライセンス
本プロジェクトのライセンスに準拠

## 作成者
Claude (Anthropic)

## 更新履歴
- 2025-09-13: 初版作成
  - 対話式ファイル選択機能追加
  - UTF-8 BOM付きCSV出力対応
  - 標準ライブラリのみで実装
