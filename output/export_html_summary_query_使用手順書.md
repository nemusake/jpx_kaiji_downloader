# export_html_summary_query.py 使用手順書

## 概要
`export_html_summary_query.py`は、SQLite3データベース（html_summary.db）から財務データを取得し、CSV形式で出力するPythonスクリプトです。修正決算を自動的に除去し、各銘柄・決算期・四半期の最初の発表データのみを抽出します。

## 機能
- html_summary.dbから財務指標データを抽出
- **修正決算の自動除去**（先読みバイアス防止のため最初の発表データのみを取得）
- 文字化けを防ぐUTF-8（BOM付き）でのCSV出力
- 各レコードに連番IDを自動付与
- 固定ファイル名での出力（export_html_summary_output.csv）

## 必要環境
- Python 3.11以上
- 標準ライブラリのみ使用（sqlite3, csv, datetime）

## ファイル配置
```
output/
├── html_summary.db                    # SQLite3データベースファイル
├── export_html_summary_query.py       # 実行スクリプト
└── export_html_summary_output.csv     # 出力されるCSVファイル（固定名）
```

## 使用方法

### 1. 実行手順
```bash
# outputフォルダに移動
cd output

# スクリプトを実行
python3 export_html_summary_query.py
# （任意）uvで実行する場合
# uv run python export_html_summary_query.py
```

### 2. 出力結果
- ファイル名: `export_html_summary_output.csv`（固定名）
- 文字コード: UTF-8 with BOM（Excelで開いても文字化けしない）
- **重複データの除去**: 同一銘柄・決算期・四半期で複数のデータがある場合、最も古い日付のデータのみ出力

## 出力データ項目

### 基本情報
- **id**: レコード番号（1から始まる連番）
- **date**: 日付
- **code**: 銘柄コード
- **company_name**: 企業名
- **fiscal_year_end**: 決算期末
- **quarterly_period**: 四半期

### 財務指標（日本基準）
- **net_sales**: 売上高
- **operatingincome**: 営業利益
- **ordinary_income**: 経常利益
- **net_assets**: 純資産

### 財務指標（米国基準）
- **financialexpense_us**: 金融費用控除後総収益（米国基準）
- **operatingincome_us**: 営業利益（米国基準）
- **net_assets_us**: 純資産（米国基準）

### 財務指標（IFRS）
- **net_salesIFRS**: 売上収益（IFRS）
- **operatingincome_ifrs**: 営業利益（IFRS）
- **profitbeforetax_ifrs**: 税引前利益（IFRS）
- **totalequity_ifrs**: 資本合計（IFRS）

### キャッシュフロー（日本基準）
- **cashflow_o**: 営業活動によるキャッシュフロー
- **cashflow_i**: 投資活動によるキャッシュフロー
- **cashflow_f**: 財務活動によるキャッシュフロー
- **cash_end**: 現金及び現金同等物の期末残高

### キャッシュフロー（IFRS）
- **cashflow_o_ifrs**: 営業活動によるキャッシュフロー（IFRS）
- **cashflow_i_ifrs**: 投資活動によるキャッシュフロー（IFRS）
- **cashflow_f_ifrs**: 財務活動によるキャッシュフロー（IFRS）
- **cash_end_ifrs**: 現金及び現金同等物の期末残高（IFRS）

### 株式・配当情報
- **outstanding_shares**: 発行済株式総数（自己株式を含む）
- **treasury_shares**: 自己株式数
- **dividend_per_share**: 1株当たり配当金
- **total_dividend_annual**: 年間配当総額
- **payout_ratio**: 配当性向

### その他
- **doc_name**: ドキュメント名（DocumentName）。数値ではない文字列カラムですが、例外的に抽出対象として含みます。

## データの並び順
- 銘柄コード（code）: 昇順
- 日付（date）: 降順（新しい日付が上）

## 注意事項
1. **データベースファイル**: `html_summary.db`が同じフォルダに存在することを確認
2. **数値データのみ**: 文字列型のデータは除外され、数値型のみ（`typeof(value)` が `integer` または `real`）を抽出します。例外として、`factor_tag = 'tse-ed-t:DocumentName'` の場合は文字列カラム `doc_name` を含めます。
3. **NULL値**: 該当するデータがない場合はNULLとして出力
4. **修正決算の除去**: 同一銘柄・決算期・四半期で複数のデータがある場合、最初の発表（最も古い日付）のみを保持
5. **先読みバイアス防止**: 将来の修正データを除外することで、分析時の先読みバイアスを防ぐ

## トラブルシューティング

### エラー: データベースファイルが見つからない
```
データベースエラー: unable to open database file
```
**対処法**: `html_summary.db`がoutputフォルダに存在することを確認

### 文字化けする場合
- 出力されたCSVファイルはUTF-8 with BOMで保存されているため、Excelで直接開いても文字化けしません
- 他のアプリケーションで開く場合は、文字コード「UTF-8」を指定してください

## 実行例
```bash
$ cd output
$ python export_html_summary_query.py
データベースからデータを取得中...
CSVファイルに出力中: export_html_summary_output.csv
✓ 出力完了: export_html_summary_output.csv
  総レコード数: 65,897
```

## SQLクエリファイル
GUIツール用のSQLクエリも提供しています：
- **ファイル名**: `9factor_query.sql`
- **内容**: 修正決算除去機能を含む同等のSQLクエリ
- **用途**: SQLiteブラウザなどのGUIツールで直接実行可能
