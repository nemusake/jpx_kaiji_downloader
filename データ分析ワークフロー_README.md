# 📊 東証上場企業財務データ分析フロー

## 概要
東証上場会社情報サービスから決算短信データを自動取得し、データベース化して分析可能な形式に変換するワークフローです。

東証上場会社情報サービスに掲載している各種情報は毎日午前1時頃に更新されます。

## 🔄 データ処理の全体フロー

```bash
Webサイト → HTMLダウンロード → CSV抽出 → クレンジング → データベース格納 → 分析用CSV出力

step 0 : 決算短信HTMLファイルのダウンロード(codelist.csvにある銘柄を全てDLする)
    uv run python kaiji_downloader.py batch-download codelist.csv --types=html,attachments,xbrl --delay=3
↓
step 1 : HTMLファイルからCSV抽出(DLした決算短信HTMLをまとめて時系列CSVを作成する)
    uv run python html_summary_output.py all
↓
step 2 : 作成した時系列CSVのクレンジング(証券codeを5桁に,数を文字列→数値,数値からカンマ除去)
    uv run python html_summary_join.py cleansing
step 3 : クレンジング済みCSVを結合出力(個別の全CSVファイルをDB蓄積用ファイル1つに統合する)
    uv run python html_summary_join.py all
↓
step 4 : SQLiteデータベースへ格納(html_summary.csvをhtml_summary.dbにインポートする)
    html_summary_all.csvをhtml_summary.csvに名称変更
    cd output
    uv run python import_html_summary.py
↓
step 5 : 分析用データ出力(データベースから修正決算を除去した分析用のクリーンなCSVを出力する)
    cd output
    uv run python export_html_summary_query.py
```

## 📋 ステップ別実行手順

### ステップ0: 決算短信HTMLファイルのダウンロード
東証上場会社情報サービスから最新の決算短信を自動ダウンロードします。

#### 0-1. 単一銘柄のダウンロード
```bash
# HTMLサマリーファイルのダウンロード（推奨）
uv run python kaiji_downloader.py html 13010

# 全ファイル（XBRL + HTMLサマリー + 添付資料）のダウンロード
uv run python kaiji_downloader.py all 13010
```

#### 0-2. 全銘柄一括ダウンロード（codelist.csv使用）
```bash
# 全1,681銘柄を一括ダウンロード
uv run python kaiji_downloader.py batch-download

# テスト実行（最初の5社のみ）
uv run python kaiji_downloader.py batch-download-test

# HTMLサマリーのみ、最大100社、2秒間隔で実行
uv run python kaiji_downloader.py batch-download codelist.csv --types=html --max=100 --delay=2
```

**入力**: JPX適時開示情報サービス（Web）  
**出力**: `downloads/html_summary/[証券コード]/`内のHTMLファイル  
**処理時間**: 
- 単一銘柄: 数秒
- 全銘柄（約1,681社）: 2-4時間（間隔2秒の場合）

**ファイル命名規則**:
- 形式: `{開示日}_{表題}_summary.htm`
- 例: `2025-08-07_2026年３月期第１四半期決算短信_summary.htm`

**既存ファイルの扱い**: 
- 同名ファイルは自動スキップ（重複ダウンロード防止）
- 新しい四半期決算は新規ファイルとして追加

### ステップ1: HTMLファイルからCSV抽出
決算短信HTMLファイルから財務データを抽出し、個別銘柄ごとのCSVファイルを作成します。

```bash
# 全銘柄を一括処理（推奨）
uv run python html_summary_output.py all

# テスト用に最初の10銘柄のみ処理
uv run python html_summary_output.py all limit=10

# 特定の証券コードのみ処理
uv run python html_summary_output.py 13010
```

**入力**: `downloads/html_summary/[証券コード]/`内のHTMLファイル  
**出力**: `output/html_summary/[証券コード].csv`  
**処理時間**: 全銘柄で約1-2時間

### ステップ2: CSVファイルのクレンジング
データ品質向上のため、証券コードの正規化と数値フォーマットの統一を行います。

```bash
# 証券コードの正規化とカンマ除去
uv run python html_summary_join.py cleansing
```

**処理内容**:
- 4桁証券コード→5桁に修正（例: 1333→13330）
- value列の3桁区切りカンマを除去（例: "1,234,567"→1234567）
- SQLiteデータベース格納用に数値を正規化

**注意**: 元のCSVファイルを直接更新します（バックアップ推奨）

### ステップ3: クレンジング済みCSVを結合
個別のCSVファイルを1つの大きなファイルに結合します。

```bash
# 全CSVファイルを1つに結合
python3 html_summary_join.py all

# 特定期間のデータのみ結合（例：2024年）
python3 html_summary_join.py 20240101-20241231

# 特定の証券コード範囲のみ結合（例：13000番台）
python3 html_summary_join.py 13000-139ZZ
```

**出力**: `output/html_summary_all.csv`（全結合時は数GB）

### ステップ4: SQLiteデータベースへ格納
結合したCSVファイルをSQLiteデータベースに格納します。

```bash
# データベースへのインポート（既存の場合は更新）
# ※具体的なインポートコマンドは環境に応じて調整
sqlite3 html_summary.db < import_script.sql

実行コマンド: uv run python import_html_summary.py
```

**出力**: `html_summary.db`

### ステップ5: 分析用クリーンデータの出力
データベースから修正決算を除去した分析用のクリーンなCSVを出力します。

```bash
# SQLiteデータベースから財務データを取得
cd output
python3 export_html_summary_query.py
```

**出力**: `export_html_summary_output.csv`  
**特徴**: 
- 修正決算を自動除去（先読みバイアス防止）
- 営業利益（日本基準・米国基準・IFRS）を含む
- 純資産（日本基準・米国基準・IFRS）を含む
- 金融費用控除後総収益（米国基準）を含む

## 🚀 クイックスタート（推奨実行順序）

### 初回セットアップ（全データ取得）
```bash
# 0. 決算短信HTMLファイルのダウンロード
uv run python kaiji_downloader.py batch-download codelist.csv --types=html

# 1. HTMLからCSV抽出
uv run python html_summary_output.py all

# 2. CSVのクレンジング
python3 html_summary_join.py cleansing

# 3. 全CSVを1つに結合
python3 html_summary_join.py all

# 4. クリーンなデータをCSV出力
cd output
python3 export_html_summary_query.py
```

### 定期更新（四半期ごと）
```bash
# 0. 新しい決算短信のみダウンロード（既存はスキップ）
uv run python kaiji_downloader.py batch-download codelist.csv --types=html

# 1-4. 上記と同じ処理を実行
```

## 📁 ファイル構成

```
jpx_kaiji_service/
├── downloads/
│   └── html_summary/          # ダウンロードしたHTMLファイル
│       ├── 13010/
│       ├── 13320/
│       └── ...
├── output/
│   ├── html_summary/          # 個別銘柄のCSVファイル
│   │   ├── 13010.csv
│   │   ├── 13320.csv
│   │   └── ...
│   ├── html_summary_all.csv   # 結合されたCSV
│   └── export_html_summary_output.csv  # 分析用クリーンデータ
├── html_summary.db            # SQLiteデータベース
├── kaiji_downloader.py        # Webから決算短信ダウンロード
├── html_summary_output.py     # HTML→CSV変換
├── html_summary_join.py       # CSV結合・クレンジング
├── export_html_summary_query.py  # DB→クリーンCSV出力
└── codelist.csv               # 全銘柄リスト（1,681社）
```

## 🔧 各ツールの詳細

### kaiji_downloader.py
- **用途**: 東証上場会社情報サービスから決算短信を自動ダウンロード
- **特徴**: バッチ処理対応、既存ファイルスキップ、進捗表示
- **コマンド**: `html [証券コード]`, `batch-download`, `batch-download-test`

### html_summary_output.py
- **用途**: 決算短信HTMLファイルから財務データを抽出
- **特徴**: XBRLタグごとの詳細データ、メタデータ付き
- **コマンド**: `all`, `codelist`, `[証券コード]`

### html_summary_join.py
- **用途**: CSV結合とデータクレンジング
- **特徴**: 証券コード正規化、数値フォーマット統一
- **コマンド**: `all`, `cleansing`, `[日付範囲]`, `[証券コード範囲]`

### export_html_summary_query.py
- **用途**: データベースから分析用クリーンデータを出力
- **特徴**: 修正決算除去、複数会計基準対応
- **出力**: 固定名`export_html_summary_output.csv`

## 📊 出力データの項目

### 基本情報
- date: 日付
- code: 証券コード
- company_name: 企業名
- fiscal_year_end: 決算期末
- quarterly_period: 四半期（1,2,3,空白=本決算）

### 財務指標（日本基準）
- net_sales: 売上高
- operatingincome: 営業利益
- ordinary_income: 経常利益
- net_assets: 純資産

### 財務指標（米国基準）
- financialexpense_us: 金融費用控除後総収益
- operatingincome_us: 営業利益
- net_assets_us: 純資産

### 財務指標（IFRS）
- net_salesIFRS: 売上収益
- operatingincome_ifrs: 営業利益
- profitbeforetax_ifrs: 税引前利益
- totalequity_ifrs: 資本合計

### キャッシュフロー・その他
- 営業/投資/財務キャッシュフロー（日本基準・IFRS）
- 発行済株式数、自己株式数
- 配当金、配当性向

## ⚠️ 注意事項

1. **バックアップ**: クレンジング処理は元ファイルを直接更新するため、事前のバックアップを推奨
2. **処理時間**: 全銘柄処理は数時間かかる場合があります
3. **ディスク容量**: 全データで10GB以上必要な場合があります
4. **メモリ**: 大量データ処理時は十分なメモリ（8GB以上推奨）が必要

## 🔍 トラブルシューティング

### データが空白の場合
```bash
# 実際にファイル内でデータが存在するか確認
grep -i "netsales" downloads/html_summary/13010/2025-08-04_*.htm
```

### 処理状況の確認
```bash
# ログファイルの確認
ls -la logs/
tail -f logs/html_summary_output_all_*.log
```

### データベースの内容確認
```bash
# SQLite3で直接確認
sqlite3 html_summary.db
.tables
.schema html_summary
SELECT COUNT(*) FROM html_summary;
.quit
```

## 📈 分析例

### Pythonでのデータ読み込み
```python
import pandas as pd

# クリーンデータの読み込み
df = pd.read_csv('output/export_html_summary_output.csv', encoding='utf-8-sig')

# 特定銘柄のデータ抽出
code_13010 = df[df['code'] == '13010']

# 売上高の時系列データ
net_sales = code_13010[['date', 'net_sales']].dropna()
```

### Excelでの分析
1. export_html_summary_output.csvをExcelで開く
2. ピボットテーブルで集計
3. グラフ化して時系列分析

## 📝 更新履歴

- 2025-08-26: データ分析フロー文書作成
- 2025-08-26: export_html_summary_query.py修正決算除去機能追加
- 2025-08-26: 営業利益・純資産の複数会計基準対応
- 2025-08-25: 全銘柄一括処理機能追加

## 🤝 サポート

問題が発生した場合は、以下の情報と共に報告してください：
- 実行したコマンド
- エラーメッセージ
- Python バージョン（`python3 --version`）
- uv バージョン（`uv --version`）