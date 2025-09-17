# attachments_output.py - XBRL添付資料テキスト抽出ツール

## 概要

東証上場企業の決算短信XBRL添付資料から本文テキストを抽出し、LLM分析に適した形式で出力するツールです。証券コード別のフォルダ構造に対応し、一括処理や個別処理が可能です。

## 主な機能

- **高い削減効果**: 85-96%のデータ量削減
- **多様な出力形式**: Markdown、TXT、JSON形式に対応
- **構造化抽出**: セクション見出しと本文を自動認識
- **標準ライブラリのみ**: 外部依存なし
- **ノイズ除去**: HTMLタグ、スタイル情報、ページ番号等を自動除去
- **バッチ処理**: 証券コード別フォルダの一括処理対応
- **自動フォルダ作成**: 出力先フォルダの自動生成

## 対応ファイル形式・フォルダ構造

### 入力構造
```
downloads/attachments/
├── 13010/              # 証券コード（5桁英数字）
│   ├── YYYY-MM-DD_13010_決算短信タイトル_attachments.htm
│   ├── YYYY-MM-DD_13010_決算短信タイトル_attachments.htm
│   └── ...
├── 130A0/
│   └── ...
└── xxxxx/              # その他の証券コード
```

### 出力構造
```
output/attachments/
├── 13010/
│   ├── YYYY-MM-DD_13010_決算短信タイトル_attachments.md
│   ├── YYYY-MM-DD_13010_決算短信タイトル_attachments.txt
│   └── ...
└── xxxxx/
```

- **入力**: XBRL HTML添付資料ファイル（.htm）
- **出力**: Markdown（.md）、テキスト（.txt）、JSON（.json）

注意:
- 入力は拡張子が`.htm`のファイルのみを対象とします（`.html`は対象外）。
- 同名の出力ファイルが存在する場合は上書き保存されます。

## システム要件

- Python 3.11以上
- 標準ライブラリのみ使用（外部パッケージ不要）
  - 本ツールは標準ライブラリのみで動作するためuvは必須ではありません（任意で使用可能）。
  - 例: `uv run python attachments_output.py 13010 md` でも実行可能。

## 処理性能

| 元ファイルサイズ | 削減後サイズ | 削減率 | 処理時間（目安） |
|----------------|------------|--------|-----------------|
| 162KB | 17-25KB | 85-90% | < 1秒 |
| 289KB | 12-22KB | 89-96% | < 1秒 |
| 1.9MB | 164-239KB | 87-91% | < 3秒 |

## インストール

- 本リポジトリに含まれるため、特別なインストールは不要です。
- （任意）Linux/macOSでは `chmod +x attachments_output.py` で直接実行可能にできます。

## 基本的な使用方法

### パターン1: ヘルプ表示
```bash
python3 attachments_output.py
```

### パターン2: 特定証券コードの処理
```bash
# 証券コード13010の全HTMファイルを処理（Markdown形式）
python3 attachments_output.py 13010

# 従来方式: -fオプション使用
python3 attachments_output.py 13010 -f txt
python3 attachments_output.py 130A0 -f json
python3 attachments_output.py 13010 -f txt,json,md

# 新方式: 柔軟な引数順序対応
python3 attachments_output.py 13010 txt
python3 attachments_output.py 130A0 json
python3 attachments_output.py 13010 txt,json,md
python3 attachments_output.py 13010 txt json md
python3 attachments_output.py 13010 md,txt,json
```

### パターン3: 全証券コードの一括処理
```bash
# 従来方式
python3 attachments_output.py all -f txt

# 新方式: 順序自由な形式指定
python3 attachments_output.py all md
python3 attachments_output.py all txt,json
python3 attachments_output.py all md,txt,json
python3 attachments_output.py all txt json md
```

### パターン4: ログオプション付き実行
```bash
# 詳細ログ表示（順序自由）
python3 attachments_output.py all md log
python3 attachments_output.py all log md
python3 attachments_output.py all txt,json log
python3 attachments_output.py all log txt json md
python3 attachments_output.py all md log txt,json
```

### カスタムディレクトリ指定
```bash
# 入力・出力ディレクトリをカスタマイズ
python3 attachments_output.py all --input-dir custom/input --output-dir custom/output
```

## 出力形式の詳細

### Markdown形式（デフォルト）
- 見出し構造を保持（##、###）
- テーブルデータをMarkdown表形式に変換
- GitHubやドキュメントツールで表示可能

### TXT形式
- プレーンテキスト
- 見出しは「■」で表示
- LLMに直接入力しやすい

### JSON形式
- 構造化データ
- メタデータ付き（セクション数、段落数、文字数等）
- プログラムでの後処理に最適

## コマンドライン引数

### 基本構文
```
usage: attachments_output.py [target] [formats...] [options...]
```

### 引数の説明

**位置引数（順序自由）:**
- `target`: 証券コード（5桁英数字）または "all" で全フォルダ処理
- `formats`: 出力形式（markdown/md, txt, json）
  - 複数指定: コンマ区切り（`md,txt,json`）またはスペース区切り（`md txt json`）
  - 順序自由: `txt json md` も `md,txt,json` も同じ結果
- `log`: 詳細ログ表示オプション（任意の位置で指定可能）

**オプション引数:**
```
  -h, --help            ヘルプメッセージを表示
  -f FORMAT, --format FORMAT
                        出力形式（従来方式との互換性用）
  --input-dir INPUT_DIR
                        入力ベースディレクトリ (デフォルト: downloads/attachments)
  --output-dir OUTPUT_DIR
                        出力ベースディレクトリ (デフォルト: output/attachments)
```

### 記法の特徴

**✅ 順序関係なし**
```bash
# すべて同じ結果
python3 attachments_output.py all md txt json
python3 attachments_output.py all txt json md  
python3 attachments_output.py all json md txt
```

**✅ コンマとスペース両対応**
```bash
# すべて同じ結果
python3 attachments_output.py all md,txt,json
python3 attachments_output.py all md txt json
python3 attachments_output.py all "md,txt,json"
```

**✅ logオプションの位置自由**
```bash
# すべて同じ結果
python3 attachments_output.py all log md txt
python3 attachments_output.py all md log txt
python3 attachments_output.py all md txt log
```

## 抽出される情報

### 主要セクション
- 経営成績の概況
- 財政状態の概況
- セグメント別業績
- 将来予測情報
- 連結財務諸表

### 自動除去される情報
- HTMLタグとスタイル情報
- ページ番号（...P2、...P3等）
- 無意味な空白・記号
- 目次の点線表記

## 技術仕様

### 抽出アルゴリズム
1. **HTMLパース**: 標準ライブラリのhtml.parserを使用
2. **セクション認識**: パターンマッチング（１．、（１）、○等）
3. **クラス分析**: CSSクラス（smt_text6、smt_head2等）による分類
4. **ノイズフィルタ**: 正規表現による不要テキストの除去
5. **構造化**: 見出しレベルの自動判定

### サポートするスタイルクラス
- `smt_text6`, `smt_text1-5`: 本文テキスト
- `smt_head1-3`: 見出し
- `smt_tblL/C/R`: テーブルデータ

## トラブルシューティング

### よくあるエラー

**ファイルが見つからない**
```bash
エラー: 入力ファイルが見つかりません: input.htm
```
→ ファイルパスを確認してください

**文字化け**
```bash
エラー: ファイルを読み込めません: 'utf-8' codec can't decode
```
→ ファイルの文字コードがUTF-8であることを確認してください

**権限エラー**
```bash
エラー: ファイルを書き込めません: Permission denied
```
→ 出力ディレクトリの書き込み権限を確認してください

### パフォーマンスの最適化

- 大容量ファイル（>10MB）の場合は処理に時間がかかる場合があります
- メモリ不足の場合は、ファイルを分割して処理することを推奨します

## 開発者向け情報

### アーキテクチャ
- `XBRLTextExtractor`: HTMLParserを継承したカスタムパーサー
- `convert_to_*`: 各形式への変換関数
- `extract_xbrl_text`: メイン処理関数

### カスタマイズポイント
- セクション認識パターンの追加・修正
- スタイルクラスの対応追加
- 出力形式の追加

## ライセンス

MIT License

## 更新履歴

- v1.0.0: 初回リリース
  - Markdown、TXT、JSON形式対応
  - 基本的な抽出機能
  - 標準ライブラリのみで実装

## サポート

バグ報告や機能要望は、プロジェクトのissueトラッカーまでお願いします。
