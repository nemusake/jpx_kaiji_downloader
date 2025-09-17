# html_summary_output.py 使用手順書

**※2025年8月修正版**: データ取得漏れ問題を修正済み。主要財務指標が正常に取得できます。

**※2025年8月改良版**: データベース分析向け機能を強化。メタデータ列追加で空白値の意味を明確化。

**※2025年8月新機能**: 全銘柄一括処理機能を追加。`all`コマンドで全データの自動処理が可能。

**※2025年8月修正**: 証券コード形式対応を改善。5桁英数字（130A0等）の証券コードに完全対応。

**※2025年8月修正**: マイナス値の正確な取得機能を追加。営業損失・経常損失などが半角マイナス記号付きで正確に出力されます。

## 1. 事前準備

### 1.1 必要な環境
- Python 3.11以上
- uv（パッケージ管理ツール）

### 1.2 必要なファイル確認
```bash
# プロジェクトルートで確認
ls -la html_summary_output.py
ls -la xbrl_financial_indicators.csv
ls -la downloads/html_summary/
```

### 1.3 依存ライブラリの確認
uvで管理されているため、pyproject.tomlに記載済みのライブラリが自動的に利用されます。

### 1.4 データ取得性能の確認
2025年8月の修正・改良・新機能により、以下が改善されました：

**データ取得漏れ修正**:
- **財務データの空白問題を解決**: 売上高、営業利益、純利益などが正常取得
- **複数名タグの適切処理**: nil値でない有効値を優先保持
- **2015年～2025年の全期間データ**: 一貫して正常処理

**データベース分析機能強化**:
- **メタデータ列追加**: `has_value`、`is_nil`、`data_type`カラム
- **空白値の意味明確化**: 意図的空値（nil）とデータ品質問題を区別
- **高速データベース検索**: booleanフラグでの効率的なフィルタリング

**全銘柄処理機能**:
- **`all`コマンド**: 全銘柄自動検出・処理
- **`limit=数値`オプション**: テスト用部分処理
- **エラー耐性**: 個別エラーでも全体処理継続

**証券コード形式対応**:
- **5桁英数字対応**: 13010（数字のみ）、130A0（英数字混在）など
- **動的パターンマッチ**: 将来的な新形式にも自動対応
- **完全な網羅処理**: 全ての証券コード形式で正常動作

**マイナス値の正確な取得**:
- **XBRLのsign属性対応**: `sign="-"`属性を検出して半角マイナス記号を付与
- **財務指標の正確性**: 営業損失、経常損失、純損失等が正しくマイナス値で出力
- **全銘柄・全コマンド適用**: 単一銘柄、codelist、allコマンドすべてに適用

## 2. 基本的な使い方

### 2.1 単一証券コードの処理
```bash
# 5桁数字の証券コードを処理
uv run python html_summary_output.py 13010

# 英数字混在の証券コードを処理  
uv run python html_summary_output.py 130A0
```

### 2.2 codelist.csvを使用した一括処理
```bash
# codelist.csvに記載された全証券コードを処理
uv run python html_summary_output.py codelist
```

### 2.3 **全銘柄一括処理（新機能）**
```bash
# 全銘柄を自動処理
uv run python html_summary_output.py all

# テスト用に最初の10銘柄のみ処理
uv run python html_summary_output.py all limit=10
```

### 2.4 実行結果の確認
```bash
# 出力されたCSVファイルの確認
ls -la output/html_summary/

# 特定のCSVファイルの先頭を確認
head output/html_summary/13010.csv

# ログファイルの確認
ls -la logs/
cat logs/html_summary_output_*.log        # codelist処理用
cat logs/html_summary_output_all_*.log    # 全銘柄処理用
```

注意:
- 既存の `output/html_summary/{証券コード}.csv` がある場合は上書き保存されます
- 入力は `downloads/html_summary/{証券コード}/` 配下の `.htm` ファイルで、ファイル名の先頭が `YYYY-MM-DD` のものが対象です

## 3. 実行例

### 3.1 単一証券コード実行
```bash
$ uv run python html_summary_output.py 13010
```

#### 出力例
```
指標マッピングを読み込み中: /home/user/jpx_kaiji_service/xbrl_financial_indicators.csv
  231個のタグマッピングを読み込みました
  42個のHTMLファイルを発見

13010の決算短信を処理中...
ファイル処理中: 100%|██████████| 42/42 [00:00<00:00, 79.52it/s]

CSVファイルを出力中: /home/user/jpx_kaiji_service/output/html_summary/13010.csv
  3638行のデータを出力しました

============================================================
処理完了サマリー
============================================================
証券コード: 13010
処理ファイル数: 42
出力レコード数: 3638

ユニークな財務指標数: 121
データ期間: 2015-08-03 〜 2025-08-04

データ分類結果（改良版）:
  - 有効データ: 2107件 (has_value=True)
  - nil値: 588件 (is_nil=True) 
  - 空テキスト: 943件 (data_type=empty)

処理が完了しました。
```

**※注意**: 修正版では上記のように2015年から最新までのデータが正常に処理され、主要財務指標の値が適切に取得されます。

### 3.2 **全銘柄一括処理実行（新機能）**
```bash
$ uv run python html_summary_output.py all limit=2
```

#### 出力例
```
処理対象証券コード数: 2（limit=2）

[1/2] 証券コード 13010 を処理中...
  42個のHTMLファイルを発見
  処理中...
  3638行のデータを出力しました

[2/2] 証券コード 13320 を処理中...
  44個のHTMLファイルを発見
  処理中...
  3808行のデータを出力しました

============================================================
全銘柄一括処理完了サマリー
============================================================
総証券コード数: 2
成功: 2
失敗: 0

ログファイル: /home/user/jpx_kaiji_service/logs/html_summary_output_all_20250824_081334.log
```

### 3.3 codelist一括処理実行
```bash
$ uv run python html_summary_output.py codelist
```

#### 出力例
```
処理対象証券コード数: 6

[1/6] 証券コード 99320 を処理中...
  41個のHTMLファイルを発見
  処理中...
  3429行のデータを出力しました

[2/6] 証券コード 99460 を処理中...
  41個のHTMLファイルを発見
  処理中...
  3386行のデータを出力しました

============================================================
一括処理完了サマリー
============================================================
総証券コード数: 6
成功: 6
失敗: 0
スキップ（ディレクトリなし）: 0

ログファイル: /home/user/jpx_kaiji_service/logs/html_summary_output_20250824_064741.log
```

## 4. 複数銘柄の一括処理方法比較

### 4.1 **全銘柄一括処理（新機能・推奨）**
```bash
# 全銘柄自動処理
uv run python html_summary_output.py all

# テスト用（最初の100銘柄のみ）
uv run python html_summary_output.py all limit=100
```

**メリット:**
- **自動検出**: downloads/html_summaryの全フォルダを自動発見
- **管理不要**: 銘柄リストの手動管理が不要
- **エラー耐性**: 個別銘柄エラーでも全体処理継続
- **テスト対応**: limit機能で部分処理可能
- **専用ログ**: 全銘柄処理専用ログファイル

### 4.2 codelist.csvを使用した一括処理（選択的処理）
```bash
# codelist.csvから自動的に全証券コードを読み込んで処理
uv run python html_summary_output.py codelist
```

**メリット:**
- 証券コードリストの一元管理
- 特定銘柄のみの選択的処理
- 自動的なエラーハンドリング
- ログファイルへの記録

### 4.3 処理方法の選択指針

| 用途 | コマンド | 適用場面 |
|------|---------|----------|
| **全データ処理** | `uv run python html_summary_output.py all` | 初回全データ取得、定期全体更新 |
| **テスト処理** | `uv run python html_summary_output.py all limit=10` | 機能テスト、部分データ確認 |
| **選択的処理** | `uv run python html_summary_output.py codelist` | 特定銘柄群の処理 |
| **個別処理** | `uv run python html_summary_output.py 13010` | 単一銘柄の詳細確認 |

## 5. 出力ファイルの活用

### 5.1 CSVファイルの場所
```
output/html_summary/
├── 13010.csv
├── 13320.csv
├── 13330.csv
└── ...
```

### 5.2 Pythonでの読み込み例（改良版）
```python
import pandas as pd

# CSVファイルを読み込み（UTF-8 BOM付き）
df = pd.read_csv('output/html_summary/13010.csv', encoding='utf-8-sig')

# 改良版でのデータフィルタリング
# 1. 有効データのみを抽出（高速）
valid_data = df[df['has_value'] == True]

# 2. 特定の財務指標でフィルタ
net_sales = valid_data[valid_data['factor_tag'] == 'tse-ed-t:NetSales']
total_assets = valid_data[valid_data['factor_tag'] == 'tse-ed-t:TotalAssets']

# 3. nil値の特定（意図的な空値）
dividend_nil = df[(df['factor_tag'].str.contains('Dividend')) & (df['is_nil'] == True)]

# 4. データ品質問題の特定
quality_issues = df[df['data_type'] == 'empty']

# 5. 結果表示
print(f"総データ数: {len(df)}")
print(f"有効データ数: {len(valid_data)}")
print(f"nil値数: {len(df[df['is_nil'] == True])}")
print(f"データ品質問題: {len(quality_issues)}")
print(f"売上高データ: {len(net_sales)}")
print(f"データ期間: {df['date'].min()} 〜 {df['date'].max()}")

# 6. データタイプ別集計
data_type_summary = df['data_type'].value_counts()
print("\nデータタイプ別集計:")
print(data_type_summary)
```

### 5.3 Excelでの開き方
1. Excelを起動
2. 「データ」→「テキストまたはCSVから」を選択
3. CSVファイルを選択
4. 文字コード「UTF-8」を選択
5. 「読み込み」をクリック

## 6. データ品質の確認

### 6.1 改良版でのデータ品質確認
```bash
# 1. 有効データの確認
grep "True.*value" output/html_summary/13010.csv | wc -l

# 2. nil値データの確認
grep "True.*nil" output/html_summary/13010.csv | wc -l

# 3. データ品質問題の確認
grep "False.*empty" output/html_summary/13010.csv | wc -l

# 4. 特定指標の有効データのみ確認
grep "NetSales.*True.*value" output/html_summary/13010.csv | head -3

# 5. 配当のnil値確認
grep "DividendPerShare.*True.*nil" output/html_summary/13010.csv | head -3

# 6. マイナス値データの確認
grep '"-[0-9,]*".*True.*value' output/html_summary/13010.csv | head -5

# 7. 営業利益・経常利益のマイナス値確認
grep -E "(OperatingIncome|OrdinaryIncome).*\"-[0-9,]*\"" output/html_summary/44780.csv
```

**期待結果**（証券コード13010の例）:
- 有効データ: 2,107件
- nil値: 588件
- データ品質問題: 943件
- 総データ: 3,638件

### 6.2 データ異常チェック（改良版）
```python
import pandas as pd

df = pd.read_csv('output/html_summary/13010.csv', encoding='utf-8-sig')

# 主要指標のデータ品質分析（改良版）
key_indicators = ['tse-ed-t:NetSales', 'tse-ed-t:OperatingIncome', 
                 'tse-ed-t:OrdinaryIncome', 'tse-ed-t:ProfitAttributableToOwnersOfParent']

print("主要指標のデータ品質分析:")
print("=" * 80)

for indicator in key_indicators:
    data = df[df['factor_tag'] == indicator]
    total_count = len(data)
    valid_count = len(data[data['has_value'] == True])
    nil_count = len(data[data['is_nil'] == True])
    empty_count = len(data[data['data_type'] == 'empty'])
    
    print(f"\n{indicator}:")
    print(f"  総数: {total_count}")
    print(f"  有効: {valid_count} ({valid_count/total_count*100:.1f}%)")
    print(f"  nil値: {nil_count} ({nil_count/total_count*100:.1f}%)")
    print(f"  空テキスト: {empty_count} ({empty_count/total_count*100:.1f}%)")

# 全体のデータ品質サマリー
print("\n全体データ品質サマリー:")
print("=" * 40)
print(df['data_type'].value_counts())
print(f"\n有効データ率: {len(df[df['has_value'] == True]) / len(df) * 100:.1f}%")
```

## 7. トラブルシューティング

### 7.1 証券コードが見つからない
```
エラー: 指定された証券コードのディレクトリが存在しません
```
**対処法**: downloads/html_summary/内に該当する証券コードフォルダがあるか確認

### 7.2 証券コード形式エラー
```
エラー: 証券コードは5桁の英数字である必要があります
```
**対処法**: 
- 証券コードが5桁の英数字（数字0-9、アルファベット大文字A-Z）であることを確認
- 例：13010（5桁数字）、130A0（3桁数字+英字+数字）
- 小文字のアルファベットは使用不可（大文字に変換してください）

### 7.3 日本語名が表示されない
```
警告: xbrl_financial_indicators.csv が見つかりません
```
**対処法**: xbrl_financial_indicators.csvファイルの存在と配置を確認
 - 文字コードはUTF-8（BOM付き）を推奨
 - 必須カラム名は `xbrl_tag`, `japanese_name` です

### 7.4 一括処理でエラーが発生
**ログファイルの確認**: 
- **codelist処理**: `logs/html_summary_output_YYYYMMDD_HHMMSS.log`
- **全銘柄処理**: `logs/html_summary_output_all_YYYYMMDD_HHMMSS.log`
- エラー詳細とスキップされた証券コードを確認
- 処理は継続されるため、他の証券コードは正常に完了

### 7.5 メモリ不足エラー
大量のHTMLファイルがある場合、メモリ不足になることがあります。
**対処法**: 
- システムのメモリを増やす
- `limit`オプションで部分処理を実行
- 期間を分割して処理する（将来的な機能追加予定）

### 7.6 文字化け
CSVファイルをExcelで開いた際に文字化けする場合
**対処法**: 上記「5.3 Excelでの開き方」の手順に従って開く

### 7.7 データが空白の場合（修正版での対応）
修正版でも一部データが空白の場合：

**原因**:
1. **企業側の決算短信にデータが含まれていない**（サマリー版）
2. **XBRLタグ自体が存在しない**
3. **特定時期のデータが非公開**

**対処法**:
```bash
# 実際にファイル内でデータが存在するか確認
grep -i "netsales" downloads/html_summary/13010/2025-08-04_*.htm

# 他の企業で同時期のデータが取得できているか確認
# （システム的な問題か企業固有の問題かの判定）
```

## 8. 注意事項

### 8.1 quarterly_periodの扱い
- 第1四半期: "1"
- 第2四半期: "2"
- 第3四半期: "3"
- 本決算: 空欄
- タグが存在しない場合: 空欄

※本決算とタグ不在の区別は現時点ではできません

### 8.2 処理時間（推定）
- 1証券コード（約40ファイル）: 約0.5秒
- 10証券コード: 約5秒
- 100証券コード: 約50秒
- 1000証券コード: 約10-15分
- 全上場企業（約4000社）: 約1-2時間

### 8.3 ディスク容量
- 1証券コードあたり約500KB-2MB
- 全上場企業（約4000社）: 約2-8GB
- ログファイル: 1回の一括処理で約1-10MB

### 8.4 ログファイル管理
- ログファイルは実行ごとに新規作成
- 古いログファイルは自動削除されません
- 定期的にlogsフォルダの整理を推奨

### 8.5 データ品質に関する注意（改良版）
- **複数時点データ**: 同一指標で複数の時点データ（前年同期、予想等）が含まれる場合あり
- **単位**: 百万円、千円などの単位情報はscale属性で確認可能
- **文字列データ**: 数値は文字列として保存、必要に応じて数値変換
 - 本プログラムは`scale`属性自体はCSVに出力しません。必要に応じて元HTML（XBRL）を参照してください

### 8.6 メタデータ列の活用（改良版新機能）

#### has_value列の活用
- **目的**: 有効データの高速フィルタリング
- **使用例**: `df[df['has_value'] == True]` で有効データのみ抽出

#### is_nil列の活用
- **目的**: 意図的な空値（XBRL仕様）の特定
- **例**: 配当なし企業の特定、注記なし情報の特定

#### data_type列の活用
- **'value'**: 通常のデータ分析で使用
- **'nil'**: 企業の開示方針分析、業界比較で使用
- **'empty'**: データ品質監視、エラー検知で使用

### 8.7 全銘柄処理の注意事項（新機能）
- **処理時間**: 全銘柄処理は長時間かかる場合があります
- **途中停止**: Ctrl+Cで停止可能、それまでの処理結果は保持
- **エラー耐性**: 個別銘柄のエラーでも全体処理は継続
- **limit活用**: 初回は`limit=10`などでテスト実行を推奨

## 9. 今後の拡張予定
- 期間指定オプション
- 並列処理対応
- データベース直接出力
- エラーリトライ機能
- 差分更新機能
- **コンテキスト参照情報の利用**: 時点情報やメンバー情報の詳細分類

## 10. 修正履歴

### 2025年8月 - データ取得漏れ修正
**修正内容**:
- 複数同名タグの有効値優先保持機能追加
- nil値処理アルゴリズムの改善
- lxmlパーサーへの変更でHTML処理を最適化

**効果**:
- 2015年～2025年の全期間で主要財務指標の正常取得を確認
- データ取得率の大幅改善

### 2025年8月 - データベース分析機能強化
**機能追加**:
- メタデータ列追加: `has_value`、`is_nil`、`data_type`
- 空白値の意味を明確化（意図的空値 vs データ品質問題）
- データベースでの高速検索・分析に最適化

**効果**:
- SQLでの高速データフィルタリング
- 意図的空値とデータ品質問題の正確な区別
- 時系列分析での企業方針変化追跡が可能
- 業界比較・データカバレッジ分析の精度向上

### 2025年8月 - 全銘柄一括処理機能追加
**機能追加**:
- `all`コマンド: 全銘柄自動検出・一括処理
- `limit=数値`オプション: テスト用部分処理機能
- 専用ログファイル: 全銘柄処理用ログ生成
- エラー耐性: 個別エラーでも全体処理継続

**効果**:
- 手動銘柄リスト管理の不要化
- 大規模データ処理の完全自動化
- テスト環境での柔軟な部分処理
- 運用環境でのエラー回復力向上

### 2025年8月 - 証券コード形式対応改善
**問題**: 英数字混在証券コード（130A0, 135A0など）の処理失敗

**原因**:
- 証券コード検証の正規表現が実際のデータ形式と不適合
- 静的な形式定義では新しいパターンに対応困難

**修正内容**:
- **正規表現を動的対応に変更**: `^\d{5}$|^\d{4}[A-Z0-9]$` → `^[0-9A-Z]{5}$`
- **柔軟性の向上**: 5桁の数字とアルファベット大文字の任意組み合わせに対応
- **将来対応**: 新しい証券コード形式の自動サポート

**効果**:
- 全ての証券コード形式（13010、130A0等）で正常処理
- `html_summary_output.py all`での完全な全銘柄処理
- 保守性向上（新形式追加時の修正不要）
- 処理成功率の大幅改善

### 2025年8月 - マイナス値の正確な取得機能追加
**問題**: XBRLのマイナス値（営業損失、経常損失等）が正の値として出力される

**原因**:
- XBRLタグの`sign="-"`属性を処理していなかった
- 決算書面では△記号で表示されるが、XBRL構造上は`sign`属性でマイナスを表現
- HTMLテキスト取得時に属性情報が失われる

**修正内容**:
- **sign属性検出機能追加**: `sign="-"`属性の自動検出
- **半角マイナス記号付与**: 条件一致時に半角"-"を値の先頭に追加
- **全財務指標対応**: 営業利益、経常利益、純利益等すべての指標に適用
- **全コマンド対応**: 単一銘柄、codelist、allコマンドすべてに適用

**効果**:
- 営業損失: `8638` → `"-8,638"`として正確に出力
- 経常損失: `8638` → `"-8,638"`として正確に出力
- 純損失等も同様にマイナス値として正確に表現
- 財務分析での損益判定が正確に実行可能

**例**: 証券コード44780（フリー株式会社）2024年6月期
```bash
# 修正前の出力例
tse-ed-t:OperatingIncome,営業利益,8386,True,False,value
tse-ed-t:OrdinaryIncome,経常利益,8638,True,False,value

# 修正後の出力例
tse-ed-t:OperatingIncome,営業利益,"-8,386",True,False,value
tse-ed-t:OrdinaryIncome,経常利益,"-8,638",True,False,value
```

**検証方法**:
```bash
# マイナス値データの確認
grep '"-[0-9,]*".*True.*value' output/html_summary/44780.csv

# 営業利益・経常利益のマイナス値確認
grep -E "(OperatingIncome|OrdinaryIncome).*\"-[0-9,]*\"" output/html_summary/44780.csv
```
