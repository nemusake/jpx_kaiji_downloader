# 実行ファイル実行フロー（output フォルダ用）

以下は、output フォルダ内の実行スクリプトを使って、データベースの初期化/取込/エクスポートを行う簡易フローです。

## 前提
- 作業ディレクトリは常に `output/` を想定
- 必要ファイル:
  - `html_summary.db`（SQLite3 データベース、テーブル `html_summary` が存在すること）
  - `html_summary.csv`（取込元 CSV、UTF-8/BOM 可）
- 依存: Python 3.11 以上（標準ライブラリのみ使用）
- すべて相対パスで動作（`cd output` 前提）

## フロー一覧

### 1) フルリビルド（DBを空にして CSV から作り直し）
```bash
cd output
python3 clear_html_summary_data.py           # html_summary の全データ削除 + VACUUM 最適化
python3 import_html_summary.py               # html_summary.csv を DB にインポート（重複スキップ）
python3 export_html_summary_query.py         # 集約 CSV を出力（export_html_summary_output.csv）
```

### 2) 追加入力のみ（CSV の増分を DB へ追加）
```bash
cd output
python3 import_html_summary.py               # 12カラム完全一致で重複スキップ
python3 export_html_summary_query.py         # 必要に応じて再エクスポート
```

### 3) 集計だけやり直す（DB はそのまま）
```bash
cd output
python3 export_html_summary_query.py
```

※ uv を使う場合（任意）: `uv run python <script>.py`

## 各スクリプトの役割
- `clear_html_summary_data.py`
  - `html_summary` テーブルのデータを全削除（構造・インデックスは維持）
  - `VACUUM` によるファイルサイズ最適化
  - 実行前に対話確認あり

- `import_html_summary.py`
  - `html_summary.csv` を `html_summary.db` の `html_summary` にインポート
  - 重複判定は「12カラム完全一致（NULL 厳密一致）」でスキップ
    - 対象: date, filing_date, code, company_name, fiscal_year_end, quarterly_period,
      factor_tag, factor_jp, value, has_value, is_nil, data_type
  - 初回に重複チェック用インデックスを作成
  - ログファイル自動生成（例: `import_html_summary_YYYYMMDD_HHMMSS.log`）

- `export_html_summary_query.py`
  - 修正決算を除去（code, fiscal_year_end, quarterly_period 単位で最初の発表データのみ）
  - 主要指標を横持ちで抽出し、`export_html_summary_output.csv` に UTF-8(BOM) で出力
  - 例外的に `doc_name`（DocumentName）を文字列カラムとして含める

## 注意事項
- `clear_html_summary_data.py` は破壊的（データ全削除）です。必要なら事前バックアップを取得してください。
- CSV の必須列（12列）: `date, filing_date, code, company_name, fiscal_year_end, quarterly_period, factor_tag, factor_jp, value, has_value, is_nil, data_type`
- 文字コードは UTF-8（BOM あり/なし）に対応。出力は UTF-8（BOM 付き）。
- 大容量処理時は `import_html_summary.py` の進捗ログとインデックスにより性能を担保します。

