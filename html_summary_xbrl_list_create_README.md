# html_summary_xbrl_list_create.py - 技術仕様書

## 概要
東証決算短信のインラインXBRLファイルから財務指標タグを一括抽出し、網羅的なカタログCSVを生成するツール。

## 技術アーキテクチャ

### システム構成
```
html_summary_xbrl_list_create.py
├── BulkXBRLAnalyzer クラス
│   ├── ファイル探索・読み込み
│   ├── JPEN_list読み込みエンジン
│   ├── XBRL解析エンジン
│   ├── データ集計・統計計算
│   └── CSV出力エンジン
└── 実行制御部
```

### 主要コンポーネント

#### 1. BulkXBRLAnalyzerクラス
**責務**: 全体の処理制御とデータ管理

**主要属性**:
```python
self.all_tags = defaultdict(lambda: {
    'xbrl_tag': '',           # XBRLタグ名
    'japanese_name': '',      # 日本語名（JPEN_listから自動設定）
    'english_name': '',       # 英語名（JPEN_listから自動設定）
    'category': '',           # カテゴリ分類（JPEN_list優先、自動分類フォールバック）
    'accounting_standard': '', # 会計基準
    'description': '',        # 詳細説明（JPEN_listから自動設定）
    'sample_values': [],      # サンプル値リスト
    'units': set(),          # 単位情報
    'file_count': 0,         # 出現ファイル数
    'total_occurrences': 0   # 総出現回数
})
self.jpen_mapping = {}        # JPEN_listのマッピング辞書
```

#### 2. JPEN_list読み込みエンジン
**責務**: XBRLタグの日本語・英語名・カテゴリ・詳細説明マッピング管理
**技術仕様**:
```python
def _load_jpen_mapping(self):
    """JPEN_listファイルを読み込んでマッピングを作成"""
    with open(jpen_path, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            xbrl_tag = row.get('xbrl_tag', '').strip()
            if xbrl_tag:
                self.jpen_mapping[xbrl_tag] = {
                    'japanese_name': row.get('japanese_name', '').strip(),
                    'english_name': row.get('english_name', '').strip(),
                    'category': row.get('category', '').strip(),
                    'description': row.get('description', '').strip()
                }
```

**対応ファイル形式**: UTF-8 BOM付きCSV
**必須列**: xbrl_tag, japanese_name, english_name, category, description

#### 3. ファイル解析エンジン
**技術スタック**:
- **BeautifulSoup** + **lxml-xml**: 名前空間対応XML解析
- **正規表現**: 大文字小文字を区別しないタグ検索
- **tqdm**: プログレスバー表示

注意: 入力は拡張子が`.htm`のファイルのみを対象としています（`glob('*.htm')`）。`.html`拡張子のファイルも対象にしたい場合は、コード側の探索パターンを適宜変更してください。

**解析対象タグ**:
```python
# インラインXBRLタグの抽出
non_numeric_tags = soup.find_all(re.compile(r'.*nonNumeric', re.I))
non_fraction_tags = soup.find_all(re.compile(r'.*nonFraction', re.I))
```

**JPEN_listマッピング適用**:
```python
# 初回登録時にJPEN_listからの情報設定
if xbrl_tag in self.jpen_mapping:
    self.all_tags[xbrl_tag]['japanese_name'] = self.jpen_mapping[xbrl_tag]['japanese_name']
    self.all_tags[xbrl_tag]['english_name'] = self.jpen_mapping[xbrl_tag]['english_name']
    self.all_tags[xbrl_tag]['description'] = self.jpen_mapping[xbrl_tag]['description']
    # JPEN_listのcategoryが存在する場合は優先使用
    jpen_category = self.jpen_mapping[xbrl_tag]['category']
    if jpen_category:
        self.all_tags[xbrl_tag]['category'] = jpen_category
```

#### 4. データ集計システム
**重複排除**: `defaultdict`でXBRLタグ名をキーとした自動重複排除
**統計計算**: 
- 出現詳細 = "出現ファイル数/処理ファイル数"（例: 1602/1677）

#### 5. 自動分類エンジン
**カテゴリ分類ロジック**:
```python
def _categorize_tag(self, xbrl_tag: str) -> str:
    tag_lower = xbrl_tag.lower()
    
    # 基本情報系
    if any(keyword in tag_lower for keyword in [
        'company', 'securities', 'filing', 'document', 'representative'
    ]):
        return '基本情報'
    
    # PL系（損益計算書）
    if any(keyword in tag_lower for keyword in [
        'sales', 'revenue', 'income', 'profit', 'loss'
    ]):
        return 'PL'
    
    # BS系（貸借対照表）
    if any(keyword in tag_lower for keyword in [
        'assets', 'liabilities', 'equity', 'capital'
    ]):
        return 'BS'
    
    # 他のカテゴリも同様...
```

**会計基準判定**:
```python
def _determine_accounting_standard(self, filename: str, content: str) -> str:
    if 'IFRS' in filename.upper() or 'ＩＦＲＳ' in filename:
        return 'IFRS'
    elif '日本基準' in filename or '日本基準' in content[:1000]:
        return '日本基準'
    else:
        return '日本基準'  # デフォルト
```

### データフロー

#### 1. 初期化フェーズ
```python
analyzer = BulkXBRLAnalyzer(matome_dir, jpen_list_csv)
# データ構造の初期化
# JPEN_listファイル読み込み（231個のマッピング）
# ファイルリストの取得
```

#### 2. 一括解析フェーズ
```python
for each_file in html_files:
    # ファイル読み込み
    # BeautifulSoupでXML解析
    # XBRLタグ抽出
    # データ集計
```

#### 3. 統計計算フェーズ
```python
# 出現頻度計算
# サンプル値整理
# 単位情報統合
```

#### 4. CSV出力フェーズ
```python
# データソート（出現回数降順）
# UTF-8 BOM付きCSV出力
```
補足: 実装では「出現ファイル数（occurrence_detailの左辺）」の降順でソートしています。

## パフォーマンス特性

### 処理速度
- **実測値**: 1,677ファイル処理時間 約24秒
- **平均処理速度**: 約70ファイル/秒
- **メモリ使用量**: 中程度（全データをメモリ保持）

### スケーラビリティ
- **対応ファイル数**: 数千〜数万ファイル対応
- **制限要因**: メモリ使用量（全タグデータを保持）
- **改善余地**: ストリーミング処理導入で大規模対応可能

## エラーハンドリング

### エラー分類
1. **ファイル読み込みエラー**: 個別ファイルエラーで処理継続
2. **XML解析エラー**: BeautifulSoup例外キャッチ
3. **メモリエラー**: 大規模データセット時の制限

### ログ出力
```python
# エラーファイルの追跡
self.error_files.append((str(file_path), str(e)))

# プログレス表示
with tqdm(html_files, desc="ファイル解析中") as pbar:
    pbar.set_description(f"処理中: {file_path.name[:50]}")
```

## 出力仕様

### CSV構造
```csv
xbrl_tag,japanese_name,english_name,category,accounting_standard,sample_value,unit,description,occurrence_detail
```

### データ品質保証
- **UTF-8 BOM付き**: Excelでの文字化け防止
- **重複排除**: XBRLタグ名での自動重複排除
- **データ完整性**: 全フィールド必須（空文字列可）

### 実行方法の補足（プロジェクト方針）
- 依存はuvで管理されているため、実行は `uv run python html_summary_xbrl_list_create.py` を推奨します。
- スクリプト末尾（`if __name__ == "__main__":` 直下）にある `matome_dir`, `output_csv`, `jpen_list_csv` は環境に合わせて編集してください（現在は絶対パスの例が記載されています）。

## 拡張性

### 追加機能の実装ポイント
1. **JPEN_list拡張**: `xbrl_financial_indicators_JPEN_list.csv`に新しいXBRLタグのマッピング（日本語名・英語名・カテゴリ・説明文）を追加
2. **詳細分類**: `_categorize_tag()`の自動分類ルール拡張（JPEN_listのcategoryが優先されるが、フォールバック用）
3. **出力フォーマット**: `export_to_csv()`でJSON/XML出力追加
4. **フィルタリング**: 解析前段階でのファイル種別絞り込み

### 設定の外部化
現在ハードコーディングされている設定項目：
- カテゴリ分類キーワード
- 会計基準判定ルール  
- サンプル値取得数上限
- CSV出力項目
- JPEN_listファイルパス（現在は実行時指定）
- JPEN_listファイル構造（xbrl_tag, japanese_name, english_name, category, description）

## 依存関係

### 必須ライブラリ
```python
beautifulsoup4>=4.13.4  # XML/HTML解析
lxml>=6.0.0            # 高速XMLパーサー
pandas>=2.3.2          # データ処理（未使用だが依存）
tqdm>=4.67.1           # プログレスバー
```

### システム要件
- **Python**: 3.11以上
- **メモリ**: 最低2GB推奨
- **ストレージ**: 一時的に元ファイルサイズの2倍程度

## セキュリティ考慮事項

### 入力検証
- ファイルパス検証（パストラバーサル対策）
- ファイル形式検証（HTML/HTMのみ処理）
- メモリ使用量監視

### 出力セキュリティ
- CSV出力時のエスケープ処理
- ファイル上書き確認（現在は無確認上書き）

## 今後の改善計画

### パフォーマンス改善
1. **並列処理**: multiprocessingでファイル並列解析
2. **ストリーミング処理**: 大規模データセット対応
3. **インデックス化**: 高速検索のためのデータベース化

### 機能拡張
1. ✅ **JPEN_listによる日本語・英語名・カテゴリ・詳細説明の自動設定**（実装済み）
2. **Web UI**: ブラウザベースの操作画面
3. **リアルタイム更新**: ファイル監視による自動更新
4. **レポート生成**: 分析結果の可視化
