# html_summary_output.py README

## 概要
東証上場企業の決算短信HTMLファイルから時系列データを抽出し、証券コードごとにCSVファイルを出力するプログラムです。

**※データ取得漏れ問題を修正済み（2025年8月対応）**
- 複数の同名XBRLタグがある場合に、有効な値を優先保持
- nil値処理の最適化
- 2015年～2025年の全期間でデータ取得を確認済み

**※データベース分析向け改良版（2025年8月追加機能）**
- メタデータ列追加：`has_value`, `is_nil`, `data_type`
- 空白値の意味を明確に分類（意図的空値 vs データ品質問題）
- データベースでの高速検索・分析に最適化

**※全銘柄一括処理機能（2025年8月新機能）**
- `all`コマンドで全銘柄自動処理
- `limit=数値`オプションでテスト処理対応
- 証券コード昇順での効率的な大量処理

## 主な機能
- 証券コード別の決算短信HTMLファイルを時系列順に処理
- XBRLタグからデータを抽出（**重複タグの有効値優先保持**）
- 財務指標の日本語名マッピング（xbrl_financial_indicators.csv参照）
- UTF-8 BOM付きCSVファイルとして出力
- 時系列分析に最適化されたデータ構造
- codelist.csvからの一括処理機能
- **全銘柄自動一括処理機能**
- 処理ログの自動記録
- **nil値処理の最適化**（`xsi:nil="true"`の正確な検出）

## 必要要件
- Python 3.11以上
- 依存ライブラリ（uvで管理）: beautifulsoup4, lxml, pandas, tqdm
- 文字コードはUTF-8（入出力ともにBOM付与）

## ディレクトリ構成
```
jpx_kaiji_service/
├── html_summary_output.py          # メインプログラム
├── xbrl_financial_indicators.csv   # XBRLタグと日本語名のマッピング
├── codelist.csv                    # 証券コードリスト（一括処理用）
├── downloads/
│   └── html_summary/               # 入力データ
│       ├── 13010/                  # 証券コード別フォルダ
│       │   ├── 2015-08-03_13010_xxx_summary.htm
│       │   └── ...
│       └── ...
├── output/
│   └── html_summary/               # 出力先（自動作成）
│       ├── 13010.csv
│       └── ...
└── logs/                           # ログファイル（自動作成）
    ├── html_summary_output_YYYYMMDD_HHMMSS.log      # codelist処理用
    └── html_summary_output_all_YYYYMMDD_HHMMSS.log  # 全銘柄処理用
```

## 入力データ形式
### HTMLファイル名規則
```
YYYY-MM-DD_証券コード_決算期間情報_summary.htm
```
- YYYY-MM-DD: 開示日
- 証券コード: 5桁の英数字（数字とアルファベット大文字の組み合わせ）
- 決算期間情報: 決算短信のタイトル
 - 先頭がYYYY-MM-DDで、拡張子が`.htm`のファイルを対象とします（上記の命名規則を推奨）

### XBRLタグ処理仕様

#### 基本情報タグ
以下のタグを基本情報として抽出：
- `tse-ed-t:FilingDate` - 提出日
- `tse-ed-t:SecuritiesCode` - 証券コード
- `tse-ed-t:CompanyName` - 企業名
- `tse-ed-t:FiscalYearEnd` - 決算期
- `tse-ed-t:QuarterlyPeriod` - 四半期（1,2,3または空欄）

#### XBRLデータ抽出ルール
- **複数同名タグ**: 有効値（nil値でない）を優先保持
- **nil属性検出**: 属性名が`xsi:nil`または`nil`で値が`true`のときnilと判定
- **マイナス値処理**: `sign="-"`属性を検出して半角マイナス記号を付与
- **タグ検索**: `ix:nonNumeric`および`ix:nonFraction`タグから抽出
- **パーサー**: lxmlパーサーを使用（HTMLパース）

## 日本語名マッピングCSVの前提
- ファイル: `xbrl_financial_indicators.csv`（UTF-8 BOM）
- 必須カラム名: `xbrl_tag`, `japanese_name`
- マッピングが存在しないタグは`factor_jp`が空欄になります

## 出力CSV形式
### カラム構成
| カラム名 | 説明 | 例 |
|---------|------|-----|
| date | 開示日（ファイル名から取得） | 2025-08-07 |
| filing_date | 提出日 | 2025年8月7日 |
| code | 証券コード | 13010 |
| company_name | 企業名 | 株式会社 極洋 |
| fiscal_year_end | 決算期 | 2026-03-31 |
| quarterly_period | 四半期 | 1,2,3,空欄(本決算) |
| factor_tag | XBRLタグ | tse-ed-t:TotalAssets |
| factor_jp | 日本語名 | 総資産 |
| value | 値（マイナス値は"-"付き） | 683112, -8638 |
| **has_value** | **値有無フラグ** | **True/False** |
| **is_nil** | **nil値フラグ** | **True/False** |
| **data_type** | **データ種別** | **'value'/'nil'/'empty'** |

### 出力例（改良版）
```csv
date,filing_date,code,company_name,fiscal_year_end,quarterly_period,factor_tag,factor_jp,value,has_value,is_nil,data_type
2025-08-07,2025年8月7日,13010,株式会社 極洋,2026-03-31,1,tse-ed-t:TotalAssets,総資産,683112,True,False,value
2025-08-07,2025年8月7日,13010,株式会社 極洋,2026-03-31,1,tse-ed-t:OperatingIncome,営業利益,"-8,386",True,False,value
2025-08-07,2025年8月7日,13010,株式会社 極洋,2026-03-31,1,tse-ed-t:DividendPerShare,1株当たり配当金,,False,True,nil
2025-08-07,2025年8月7日,13010,株式会社 極洋,2026-03-31,1,tse-ed-t:FASFMemberMark,FASF加盟マーク,,False,False,empty
```

### 新カラムの意味
- **has_value**: 値が存在するかどうか（データベースクエリでの高速フィルタリング用）
- **is_nil**: XBRL仕様上のnil値かどうか（意図的な空値を示す）
- **data_type**: データの種別分類
  - `'value'`: 有効なデータ値
  - `'nil'`: XBRLのnil属性で空値を明示
  - `'empty'`: テキストが空だがnil属性はなし（データ品質問題の可能性）

## 実行方法

### 単一証券コード処理
```bash
python html_summary_output.py [証券コード]
# 例: python html_summary_output.py 13010
```

### 一括処理（codelist.csv使用）
```bash
python html_summary_output.py codelist
```
codelist.csvの7カラム目（code）にある全証券コードを自動処理します。

### **全銘柄処理（新機能）**
```bash
# 全銘柄処理
python html_summary_output.py all

# テスト用に最初の10銘柄のみ処理
python html_summary_output.py all limit=10
```
**特徴**:
- downloads/html_summaryフォルダの全ディレクトリを自動検出
- 証券コード昇順で処理（13010 → 13320 → ...）
- `limit=数値`で処理数を制限可能（テスト用）
- 専用ログファイル生成（`logs/html_summary_output_all_*.log`）
- エラー発生時も継続処理（失敗した銘柄をログに記録）

### コマンド比較
| コマンド | 対象 | 用途 |
|---------|-----|------|
| `python html_summary_output.py 13010` | 単一銘柄 | 特定銘柄のみ処理 |
| `python html_summary_output.py codelist` | codelist.csv記載銘柄 | 選定済み銘柄の一括処理 |
| `python html_summary_output.py all` | 全銘柄 | 全データの網羅的処理 |
| `python html_summary_output.py all limit=100` | 最初の100銘柄 | テスト・部分処理 |

## クラス・関数構成

### XBRLTimeSeriesExtractor
メインの処理クラス

#### 主要メソッド
- `__init__()` - 初期化
- `load_indicators_mapping()` - 日本語名マッピング読み込み
- `validate_securities_code()` - 証券コード検証
- `get_html_files()` - HTMLファイル取得・ソート
- `extract_xbrl_data()` - XBRLデータ抽出
- `process_all_files()` - 全ファイル処理
- `save_to_csv()` - CSV出力
- `print_summary()` - 処理サマリー表示

### メイン関数
- `process_single_code()` - 単一証券コード処理
- `process_codelist()` - codelist.csv一括処理
- **`process_all_codes()`** - **全銘柄一括処理（新機能）**
- `parse_arguments()` - コマンドライン引数解析（新機能）
- `main()` - エントリーポイント

## エラーハンドリング
- 証券コードの形式チェック（5桁英数字：数字とアルファベット大文字の任意の組み合わせ）
- ディレクトリ存在確認
- HTMLファイル解析エラーの記録と報告
- xbrl_financial_indicators.csv不在時の警告（処理は継続）
- 一括処理時のエラーログ記録（logs/フォルダに自動保存）
- エラー発生時も次の証券コードの処理を継続

## ログ機能
### ログファイル
- **単一・codelist処理**: `logs/html_summary_output_YYYYMMDD_HHMMSS.log`
- **全銘柄処理**: `logs/html_summary_output_all_YYYYMMDD_HHMMSS.log`
- 文字コード: UTF-8
- 内容:
  - 処理開始・終了時刻
  - 各証券コードの処理状況
  - エラー詳細
  - 処理結果サマリー（成功/失敗/スキップ）

### ログレベル
- INFO: 正常処理の記録
- WARNING: スキップ処理（ディレクトリ不在等）
- ERROR: エラー発生時の詳細

## 制限事項
- quarterly_periodが空欄の場合、本決算とタグ不在を区別できない
- 大量ファイル処理時はメモリ使用量に注意
- XBRLタグの値は文字列として保存（数値変換は行わない）
- 企業によっては決算短信に詳細な財務数値が含まれない場合がある（サマリー版）
- 出力先に同名のCSVが存在する場合、上書き保存します

## 修正履歴
### 2025年8月修正 - データ取得漏れ問題の解決
**問題**: 2015年〜現在まで主要財務指標（売上高、営業利益等）の値が空白で取得されない

**原因**: 
1. 複数の同名XBRLタグがある場合、最後の値（多くがnil値）で上書き
2. nil値処理で正規表現による属性検索が正常動作せず
3. lxml-xmlパーサーによる名前空間処理の問題

**修正内容**:
1. **データ保持ロジック修正**: nil値でない有効値を優先保持
2. **nil値処理改善**: 属性名を正確にチェック（`xsi:nil="true"`）
3. **パーサー変更**: `lxml-xml` → `lxml`（HTMLパーサー）

**効果**: 2015年〜2025年の全期間で財務データの正常取得を確認

### 2025年8月改良 - データベース分析向け機能強化
**機能追加**: 空白値の意味を明確化するためのメタデータ列追加

**追加カラム**:
1. **has_value**: 値の有無を示すbooleanフラグ（高速検索用）
2. **is_nil**: XBRL仕様上のnil値かどうかを示すフラグ
3. **data_type**: データ種別の分類（'value'/'nil'/'empty'）

**メリット**:
- データベースでの高速フィルタリング（`WHERE has_value = TRUE`）
- 意図的空値（nil）とデータ品質問題の区別
- 時系列分析での企業方針変化追跡
- 業界比較・データカバレッジ分析の精度向上

### 2025年8月新機能 - 全銘柄一括処理機能
**機能追加**: 全銘柄を自動検出して一括処理する`all`コマンド

**新機能**:
1. **`all`コマンド**: downloads/html_summaryの全フォルダを自動処理
2. **`limit=数値`オプション**: テスト用の処理数制限
3. **専用ログ**: 全銘柄処理専用のログファイル生成
4. **エラー耐性**: 個別銘柄でエラーが発生しても全体処理を継続

**メリット**:
- 手動での銘柄リスト管理が不要
- 大規模データ処理の自動化
- テスト環境での部分処理が容易
- 運用時のエラー回復力向上

### 2025年8月修正 - 証券コード形式対応改善
**問題**: 4桁+英数字の証券コード（例：130A0, 135A0など）が処理されない

**原因**: 
- 証券コード検証の正規表現が実際のデータ形式に対応していなかった
- `^\d{4}[A-Z0-9]$` では `130A0`（3桁数字+英字+数字）にマッチしない

**修正内容**:
- **正規表現を動的対応に変更**: `^[0-9A-Z]{5}$`
- **柔軟な証券コード形式サポート**: 5桁の数字とアルファベット大文字の任意の組み合わせに対応

**効果**:
- 既存の5桁数字証券コード（13010等）と英数字混在証券コード（130A0等）の両方に対応
- 将来的な新しい証券コード形式にも自動対応
- `html_summary_output.py all`コマンドで全銘柄の正常処理が可能

### 2025年8月修正 - マイナス値の正確な取得
**問題**: XBRLのマイナス値（営業損失、経常損失等）が正の値として出力される

**原因**: 
- XBRLタグの`sign="-"`属性を処理していなかった
- 決算書面では△記号で表示されるが、XBRL構造上は`sign`属性でマイナスを表現

**修正内容**:
- **sign属性処理追加**: `sign="-"`属性を検出して半角マイナス記号("-")を付与
- **全タグ対応**: 営業利益、経常利益、純利益等すべての財務指標に適用
- **全コマンド適用**: 単一銘柄、codelist、allコマンドすべてに適用

**効果**:
- 営業損失: `8638` → `"-8,638"`として正確に出力
- 経常損失: `8638` → `"-8,638"`として正確に出力
- 財務分析での損益判定が正確に可能

**例**: 証券コード44780（フリー株式会社）2024年6月期
```
営業利益: "-8,386" (修正前: 8386)
経常利益: "-8,638" (修正前: 8638)
```

## 依存ライブラリ
- BeautifulSoup4 - HTML/XML解析
- lxml - XMLパーサー
- pandas - データ処理
- tqdm - プログレスバー表示
