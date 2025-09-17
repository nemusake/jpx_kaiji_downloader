# html_summary_xbrl_list_create.py - 使用手順書

## 概要
東証決算短信のインラインXBRLファイルから財務指標タグを一括抽出し、網羅的なカタログCSVを生成するツール。JPEN_listファイルを使用してXBRLタグの日本語・英語名を自動設定します。

## 事前準備

### 1. 必要なライブラリの確認
以下のライブラリが既にuv.lockに含まれています：
```bash
uv sync  # 依存関係の同期
```

必要なライブラリ：
- beautifulsoup4>=4.13.4 (HTML/XML解析)
- lxml>=6.0.0 (高速XMLパーサー)
- pandas>=2.3.2 (データ処理)
- tqdm>=4.67.1 (プログレスバー表示)

### 2. データファイルの配置
matomeディレクトリ内にHTMLファイル（.htm）が配置されていることを確認：
```bash
ls downloads/matome/*.htm | head -5
```

### 3. JPEN_listファイルの配置
XBRLタグの日本語・英語名・説明文マッピングファイルが配置されていることを確認：
```bash
ls xbrl_financial_indicators_JPEN_list.csv
```
このファイルには以下の列が必要です：
- `xbrl_tag`: XBRLタグ名
- `japanese_name`: 日本語名
- `english_name`: 英語名
- `category`: カテゴリ分類
- `description`: XBRLタグの詳細説明

## 基本的な使用方法

### 1. スクリプトの直接実行
```bash
uv run python html_summary_xbrl_list_create.py
```

### 2. カスタムディレクトリでの実行
スクリプト末尾（`if __name__ == "__main__":` 直下）にある以下の変数を環境に合わせて編集してください：
```python
matome_dir = "/path/to/your/matome/directory"
output_csv = "/path/to/your/output.csv"
jpen_list_csv = "/path/to/your/JPEN_list.csv"
```

### 3. 実行時の出力例
```
JPEN_list読み込み中: xbrl_financial_indicators_JPEN_list.csv
JPEN_listから231個のマッピングを読み込みました
matomeフォルダ内のファイル一覧取得中...
発見されたHTMLファイル: 1677個
ファイル解析中: 100%|████████████| 1677/1677 [00:24<00:00, 70.12it/s]

解析完了:
  処理成功: 1677ファイル
  エラー: 0ファイル
  発見されたユニークXBRLタグ: 231個

統計情報計算中...
CSV出力中...
CSV出力完了: xbrl_financial_indicators.csv
総レコード数: 231
```

## 出力ファイルの内容

### CSVファイル構造
生成されるCSVファイルには以下の列が含まれます：

| 列名 | 説明 | 例 |
|------|------|-----|
| xbrl_tag | XBRLタグ名 | tse-ed-t:CompanyName |
| japanese_name | 日本語名（JPEN_listから自動設定） | 会社名 |
| english_name | 英語名（JPEN_listから自動設定） | Company Name |
| category | カテゴリ分類（JPEN_list優先、自動分類フォールバック） | 基本情報、PL、BS、CF、指標、その他 |
| accounting_standard | 会計基準 | 日本基準、IFRS、日本基準, IFRS |
| sample_value | サンプル値（最大3個） | リョーサン菱洋ホールディングス株式会社 |
| unit | 単位情報 | JPY, Pure, JPYPerShares |
| description | 詳細説明（JPEN_listから自動設定） | 上場会社の正式名称 |
| occurrence_detail | 出現詳細 | 1602/1677 |

### ファイル形式
- エンコーディング: UTF-8 BOM付き（Excel対応）
- 区切り文字: カンマ（CSV形式）
- ソート順: 出現ファイル数（occurrence_detail左辺）の降順
 
注意:
- 出力先に同名のCSVが存在する場合は上書き保存されます
- 入力対象は拡張子が`.htm`のファイルです（`.html`は対象外）

## トラブルシューティング

### よくある問題と対処法

#### 1. ファイルが見つからないエラー
```
エラー: HTMLファイルが見つかりません
```
**対処法**: matomeディレクトリのパスが正しいか確認

#### 2. メモリ不足エラー
大量のファイルを処理する際にメモリ不足が発生した場合：
- システムメモリを確認（最低2GB推奨）
- 処理するファイル数を制限（一時的）

#### 3. エンコーディングエラー
個別ファイルでエンコーディングエラーが発生した場合：
- エラーファイルはスキップされて処理が継続されます
- エラー詳細は最終レポートで確認可能

#### 4. CSV出力の文字化け
ExcelでCSVを開いた際に文字化けが発生した場合：
- UTF-8 BOM付きで出力されているため、通常は問題ありません
- 古いExcelの場合は、データ→外部データの取り込みを使用

#### 5. JPEN_listファイル関連の問題
```
警告: JPEN_listファイルが見つかりません: /path/to/file.csv
```
**対処法**：
- JPEN_listファイルのパスが正しいか確認
- ファイルが存在し、読み取り可能か確認
- ファイル名やディレクトリ名のスペル確認

japanese_name、english_name、descriptionが空欄の場合：
- JPEN_listファイル内に該当するxbrl_tagが存在しない
- JPEN_listファイルの列名が正しくない（xbrl_tag, japanese_name, english_name, category, description）

## 高度な使用方法

### 1. プログラムからの利用
```python
from html_summary_xbrl_list_create import BulkXBRLAnalyzer

# アナライザーの初期化（JPEN_listファイルを指定）
analyzer = BulkXBRLAnalyzer("/path/to/matome", "/path/to/JPEN_list.csv")

# 解析実行
analyzer.analyze_all_files()

# 結果の確認
analyzer.print_summary()

# CSV出力
analyzer.export_to_csv("output.csv")
```

### 2. JPEN_listなしでの実行
JPEN_listファイルを使用しない場合：
```python
# JPEN_listなしでの初期化
analyzer = BulkXBRLAnalyzer("/path/to/matome")  # 第2引数を省略

# 実行（japanese_nameとenglish_nameは空欄になります）
analyzer.analyze_all_files()
```

## 用語補足
- occurrence_detail: そのXBRLタグが出現したファイル数/全処理ファイル数を表します（実装では左辺の値で降順ソート）。

### 3. カスタムフィルタリング
特定のカテゴリのタグのみを抽出したい場合：
```python
# _categorize_tag()メソッドの分類ロジックを編集
# または出力前にデータをフィルタリング
```

### 4. エラーファイルの詳細調査
```python
analyzer = BulkXBRLAnalyzer("/path/to/matome")
analyzer.analyze_all_files()

# エラーファイルの一覧表示
for filepath, error in analyzer.error_files:
    print(f"エラーファイル: {filepath}")
    print(f"エラー内容: {error}")
```

## パフォーマンス最適化

### 処理時間の目安
- 1,677ファイル: 約24秒
- 平均処理速度: 70ファイル/秒

### メモリ使用量削減
大規模データセット処理時の最適化：
1. サンプル値取得数の制限（現在5個まで）
2. 処理完了後のfile_setの削除（自動実行）
3. バッチ処理による分割実行

## データの活用方法

### 1. Excel分析
生成されたCSVファイルをExcelで開き：
- ピボットテーブルによるカテゴリ別集計
- 出現頻度による重要指標の特定
- 会計基準別の比較分析

### 2. データベース取り込み
CSVファイルをデータベースに取り込み：
```sql
CREATE TABLE xbrl_tags (
    xbrl_tag VARCHAR(255),
    category VARCHAR(50),
    accounting_standard VARCHAR(50),
    occurrence_rate DECIMAL(5,2)
);
```

### 3. 財務分析への活用
- 業界標準指標の特定
- レポート作成時の参照辞書として活用
- XBRL標準化の進捗確認

## アップデート・拡張

### 今後の機能拡張予定
1. ✅ JPEN_listによる日本語・英語名の自動設定（実装済み）
2. より詳細な説明文の生成
3. Web UIインターフェース
4. リアルタイム更新機能

### カスタマイズポイント
- `_categorize_tag()`: 分類ルールの追加・変更
- `_determine_accounting_standard()`: 会計基準判定ロジック
- `export_to_csv()`: 出力フォーマットの変更
- `JPEN_listファイル`: 新しいXBRLタグのマッピングを追加

## サポート情報

### システム要件
- Python 3.11以上
- メモリ: 2GB以上推奨
- ディスク容量: 一時的に元ファイルサイズの2倍程度

### 実行環境
- 開発・テスト済み環境: Linux (WSL2)
- 対応OS: Windows、macOS、Linux

### ログ確認
実行中のプログレスバーで処理状況を確認：
- 現在処理中のファイル名
- 全体の進捗率
- 処理速度（ファイル/秒）

---

## クイックスタートガイド

1. **環境確認**: `uv sync`
2. **ファイル確認**: JPEN_listファイル（`xbrl_financial_indicators_JPEN_list.csv`）の配置確認
3. **実行**: `uv run html_summary_xbrl_list_create.py`  
4. **結果確認**: `xbrl_financial_indicators.csv`をExcelで開く
5. **分析開始**: 日本語・英語名・詳細説明付きで出現頻度順にソートされた231のXBRLタグを確認

これで東証決算短信から抽出された全財務指標の網羅的カタログが完成です。JPEN_listにより、各XBRLタグに対応する日本語名・英語名・カテゴリ・詳細説明が自動的に設定されます。
