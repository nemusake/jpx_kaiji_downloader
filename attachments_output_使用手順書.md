# attachments_output.py 使用手順書

## 📚 目次
1. [事前準備](#事前準備)
2. [基本的な使い方](#基本的な使い方)
3. [出力形式別の使い方](#出力形式別の使い方)
4. [実践例](#実践例)
5. [よくある質問](#よくある質問)
6. [エラー対処法](#エラー対処法)

---

## 🚀 事前準備

### 1. 必要な環境
- **Python**: 3.11以上
- **OS**: Windows、macOS、Linux
- **依存パッケージ**: なし（標準ライブラリのみ）

### 2. ファイルの準備
```bash
# プログラムファイルの確認
ls -la attachments_output.py

# 実行権限の付与（Linux/macOS）
chmod +x attachments_output.py

# 入力ファイルの確認（例）
ls -la downloads/attachments/13010/*.htm
ls -la downloads/attachments/{証券コード}/*.htm
```

### 3. 動作確認
```bash
# ヘルプの表示
python3 attachments_output.py -h

# バージョン確認（Pythonのバージョン）
python3 --version
```

---

## 💡 基本的な使い方

### パターン1: ヘルプの確認
```bash
# 使用方法を確認
python3 attachments_output.py
```

**出力例:**
```
usage: attachments_output.py [-h] [-f {markdown,txt,json}] 
                             [--input-dir INPUT_DIR] [--output-dir OUTPUT_DIR]
                             [target]

XBRL添付資料から証券コード別にテキストを抽出
```

### パターン2: 特定証券コードの処理

#### 新方式（推奨）: 柔軟な引数指定
```bash
# 基本的な使い方
 python3 attachments_output.py 13010 md
python3 attachments_output.py 13010 txt
python3 attachments_output.py 13010 json

# 複数形式同時出力（順序自由）
python3 attachments_output.py 13010 txt json md
python3 attachments_output.py 13010 md,txt,json
python3 attachments_output.py 13010 json md txt

# 詳細ログ付き（logの位置自由）
python3 attachments_output.py 13010 md log
python3 attachments_output.py 13010 log md txt
python3 attachments_output.py 13010 txt log json
```

#### 従来方式: -fオプション使用
```bash
# 今でも使用可能
python3 attachments_output.py 13010
python3 attachments_output.py 13010 -f txt
python3 attachments_output.py 13010 -f txt,json,md
```

補足:
- 既定の入力ディレクトリは `downloads/attachments`、出力ディレクトリは `output/attachments` です（`--input-dir`/`--output-dir`で変更可能）。
- 入力は拡張子が`.htm`のファイルのみを対象とします（`.html`は対象外）。
- 出力先に同名のファイルが存在する場合は上書き保存されます。

**出力例:**
```
🎯 対象証券コード: 13010
📤 出力形式: markdown
📂 出力先: output/attachments/13010

📁 処理中: 13010 (12ファイル)
  ✓ 2023-02-03_13010_決算短信_attachments.htm → .md
  ✓ 2023-05-12_13010_決算短信_attachments.htm → .md
  ...
📊 完了: 成功 12件, エラー 0件
```

### パターン3: 全証券コードの一括処理

#### 新方式（推奨）
```bash
# 順序自由な形式指定
python3 attachments_output.py all txt
python3 attachments_output.py all md txt json
python3 attachments_output.py all txt,json,md

# 詳細ログ付き
python3 attachments_output.py all txt log
python3 attachments_output.py all log md txt
```

#### 従来方式
```bash
# 今でも使用可能
python3 attachments_output.py all -f txt
```

**出力例:**
```
🔍 証券コードフォルダを検索中...
📋 発見した証券コード: 3787フォルダ
📤 出力形式: txt
📂 出力先: output/attachments

[1/3787] 📁 処理中: 13010 (12ファイル)
...
🎉 全体完了: 成功 3750フォルダ, エラー 37フォルダ
```

---

## 📋 出力形式別の使い方

### 複数形式の同時出力

#### 新方式（推奨）: 柔軟な複数形式指定
```bash
# スペース区切り（順序自由）
python3 attachments_output.py 13010 txt json md
python3 attachments_output.py 13010 md txt json
python3 attachments_output.py 13010 json md txt

# コンマ区切り（順序自由）
python3 attachments_output.py 13010 txt,json,md
python3 attachments_output.py 13010 md,txt,json
python3 attachments_output.py 13010 json,md,txt

# 混合形式（コンマ+スペース）
python3 attachments_output.py 13010 txt,json md
python3 attachments_output.py 13010 md txt,json

# ログオプション付き（位置自由）
python3 attachments_output.py 13010 log txt json md
python3 attachments_output.py 13010 txt log json md
python3 attachments_output.py 13010 txt json log md
```

#### 従来方式: -fオプション
```bash
# 今でも使用可能
python3 attachments_output.py 13010 -f txt,json,md
python3 attachments_output.py 130A0 -f txt,json
python3 attachments_output.py all -f markdown,txt,json
```

**新方式の特徴:**
- **順序関係なし**: `txt json md` も `md,txt,json` も同じ結果
- **記法柔軟性**: コンマ、スペース、混合すべて対応
- **logオプションの位置自由**: 先頭、末尾、中間どこでもOK
- **従来方式と互換**: -fオプションも継続使用可能

**共通の特徴:**
- 1回の実行で複数の出力形式を生成
- mdはmarkdownの省略形として使用可能
- 処理効率が良く、重複処理を回避
- 各形式で同じセクション構造を維持

**使用場面:**
- LLM分析用のTXTとアーカイブ用のJSON同時生成
- レポート用Markdownと処理用TXTの同時作成
- 用途別に複数形式が必要な場合

### 1. Markdown形式（デフォルト）

#### 新方式
```bash
# 基本的な使い方
python3 attachments_output.py 13010 md
python3 attachments_output.py 13010 markdown

# ログ付き
python3 attachments_output.py 13010 md log
```

#### 従来方式
```bash
python3 attachments_output.py 13010
python3 attachments_output.py 13010 -f markdown
```

**特徴:**
- 見出し構造が綺麗に整理される
- テーブルがMarkdown表形式になる
- GitHubやドキュメントツールで表示可能

**使用場面:**
- 資料作成・レポート作成
- ドキュメント管理システムでの保存
- GitHubでの共有

### 2. テキスト形式

#### 新方式
```bash
# テキスト形式で出力
python3 attachments_output.py 13010 txt

# ログ付き
python3 attachments_output.py 13010 txt log
```

#### 従来方式
```bash
python3 attachments_output.py 13010 -f txt
```

**特徴:**
- シンプルなプレーンテキスト
- 見出しは「■」で表示
- 最もコンパクト

**使用場面:**
- LLMへの直接入力
- テキストエディタでの編集
- システム間でのデータ連携

### 3. JSON形式

#### 新方式
```bash
# JSON形式で出力
python3 attachments_output.py 13010 json

# ログ付き
python3 attachments_output.py 13010 json log
```

#### 従来方式
```bash
python3 attachments_output.py 13010 -f json
```

**特徴:**
- 構造化されたデータ
- メタデータ（統計情報）付き
- プログラムで処理しやすい

注意:
- JSONの `extraction_date` は固定値のサンプルです。必要に応じて現在日時に置き換えるなどの改修が可能です。

**使用場面:**
- APIでの データ連携
- データベースへの保存
- プログラムでの自動処理

---

## 🎯 実践例

### 例1: 複数企業の比較分析

#### 新方式
```bash
# 主要企業の決算短信を抽出
python3 attachments_output.py 13010 txt  # 極洋
python3 attachments_output.py 130A0 txt  # その他企業
python3 attachments_output.py 13320 txt  # その他企業

# 詳細ログ付きで実行
python3 attachments_output.py 13010 txt log
```

#### 従来方式
```bash
python3 attachments_output.py 13010 -f txt
python3 attachments_output.py 130A0 -f txt
python3 attachments_output.py 13320 -f txt
```

#### 共通の後処理
```bash
# 比較レポートを作成
echo "# 企業業績比較レポート" > comparison_report.md
echo "" >> comparison_report.md
echo "## 極洋（13010）" >> comparison_report.md
find output/attachments/13010/ -name "*.txt" -exec cat {} \; >> comparison_report.md
```

### 例2: 特定年度のデータ抽出

#### 新方式
```bash
# 2025年のデータのみ抽出したい場合
python3 attachments_output.py all json
python3 attachments_output.py all json log  # 詳細ログ付き
find output/attachments/ -name "*2025*" -type f > 2025_files.txt
```

#### 従来方式
```bash
python3 attachments_output.py all -f json
find output/attachments/ -name "*2025*" -type f > 2025_files.txt
```

### 例3: 大容量処理の分割実行

#### 新方式
```bash
# 証券コードリストを取得
ls downloads/attachments/ > security_codes.txt

# 100フォルダずつ処理（ログ付き）
head -100 security_codes.txt | while read code; do
    python3 attachments_output.py "$code" txt log
done
```

#### 従来方式
```bash
ls downloads/attachments/ > security_codes.txt
head -100 security_codes.txt | while read code; do
    python3 attachments_output.py "$code" -f txt
done
```

### 例4: エラーログ付き実行

#### 新方式
```bash
# 詳細ログ付きで処理結果をログファイルに保存
python3 attachments_output.py all txt log 2>&1 | tee processing.log

# 複数形式+ログの場合
python3 attachments_output.py all log txt json 2>&1 | tee processing.log

# エラーが発生したフォルダを確認
grep "エラー" processing.log
```

#### 従来方式
```bash
python3 attachments_output.py all -f txt 2>&1 | tee processing.log
grep "エラー" processing.log
```

### 例5: 特定の決算期のみ抽出

#### 新方式
```bash
# 第1四半期のデータのみを対象とする
python3 attachments_output.py 13010 json
python3 attachments_output.py 13010 json log  # 詳細ログ付き

# JSONファイルから特定のファイルを後でフィルタリング
find output/attachments/13010/ -name "*第1四半期*" -type f
```

#### 従来方式
```bash
python3 attachments_output.py 13010 -f json
find output/attachments/13010/ -name "*第1四半期*" -type f
```

---

## ❓ よくある質問

### Q1: どのくらいファイルサイズが削減されますか？
**A1:** 通常85-96%の削減が可能です。
```
元ファイル: 1.9MB → 抽出後: 166KB (91.2%削減)
元ファイル: 289KB → 抽出後: 12KB (95.9%削減)
```

### Q2: どの出力形式を選べばよいですか？
**A2:** 用途に応じて選択してください：
- **Markdown**: 人間が読む資料作成
- **TXT**: LLMでの分析
- **JSON**: プログラムでの自動処理

### Q3: 大容量ファイルも処理できますか？
**A3:** 可能ですが、10MB以上の場合は処理時間がかかります。
```bash
# 大容量ファイルの場合は統計情報で事前確認
python3 attachments_output.py large_file.htm --stats
```

### Q4: エラーが発生した場合は？
**A4:** [エラー対処法](#エラー対処法)セクションを参照してください。

### Q5: 既に出力されたファイルがある場合はどうなりますか？
**A5:** **自動的に上書き**されます。同じ証券コード・同じ形式で再実行すると、既存ファイルは新しい結果で置き換わります。

#### 新方式
```bash
# 初回実行
python3 attachments_output.py 13010 txt

# 再実行（上書きされる）
python3 attachments_output.py 13010 txt
```

#### 従来方式
```bash
# 初回実行
python3 attachments_output.py 13010 -f txt

# 再実行（上書きされる）  
python3 attachments_output.py 13010 -f txt
```

### Q6: 処理の順序はどうなっていますか？
**A6:** 証券コードは**辞書順（文字列ソート）**で処理されます：
```
13010 → 130A0 → 13320 → 13330 → 135A0 → ... → 165A0
```

### Q7: カスタマイズは可能ですか？
**A7:** プログラムを直接編集することで、以下をカスタマイズできます：
- セクション認識パターンの追加
- 出力形式の追加
- フィルタリングルールの修正
- 処理順序の変更

---

## 🚨 エラー対処法

### エラー1: ファイルが見つからない
```
エラー: 入力ファイルが見つかりません: input.htm
```
**対処法:**
```bash
# ファイルの存在確認
ls -la input.htm

# 絶対パスで指定
python3 attachments_output.py /full/path/to/input.htm -o output.md
```

### エラー2: 文字コードエラー
```
エラー: 'utf-8' codec can't decode byte
```
**対処法:**
```bash
# ファイルの文字コード確認
file -i input.htm

# 文字コード変換（Shift_JISの場合）
iconv -f shift_jis -t utf-8 input.htm > input_utf8.htm
```

### エラー3: 権限エラー
```
エラー: Permission denied
```
**対処法:**
```bash
# ディレクトリの権限確認
ls -ld ./

# 権限の変更
chmod 755 ./
chmod 644 attachments_output.py
```

### エラー4: Python が見つからない
```
command not found: python3
```
**対処法:**
```bash
# Python の確認
which python
which python3

# パスの確認
echo $PATH

# 直接パスを指定
/usr/bin/python3 attachments_output.py input.htm
```

### エラー5: メモリ不足
```
MemoryError
```
**対処法:**
```bash
# ファイルサイズを確認
ls -lh input.htm

# 統計情報のみ実行してファイルサイズを確認
python3 attachments_output.py input.htm --stats

# システムのメモリ使用量確認
free -h  # Linux
top      # 全OS
```

---

## 📞 サポート情報

### ログ出力の保存

#### 新方式
```bash
# 実行ログを保存（詳細ログ付き）
python3 attachments_output.py 13010 md log 2>&1 | tee process.log
python3 attachments_output.py all txt log 2>&1 | tee process.log
```

#### 従来方式
```bash
# 実行ログを保存
python3 attachments_output.py 13010 -f md 2>&1 | tee process.log
```

### デバッグ情報の確認
```bash
# Python バージョン確認
python3 -c "import sys; print(f'Python: {sys.version}')"

# ファイル存在確認
ls -la downloads/attachments/
ls -la output/attachments/
```

### 問題報告時の情報
問題が発生した場合は、以下の情報を含めてご報告ください：
1. 使用したコマンド
2. エラーメッセージ
3. 入力ファイルのサイズ
4. Python のバージョン
5. OS の種類

---

**📝 最終更新: 2025年8月27日**
