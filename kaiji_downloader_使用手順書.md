# JPX適時開示情報ダウンローダー 使用手順書

## 📋 目次
1. [環境構築](#環境構築)
2. [基本的な使い方](#基本的な使い方)
3. [実行モード詳細](#実行モード詳細)
4. [ファイル出力仕様](#ファイル出力仕様)
5. [トラブルシューティング](#トラブルシューティング)
6. [応用的な使用方法](#応用的な使用方法)

## 🛠 環境構築

### 前提条件
- Python 3.11以上
- インターネット接続

### 1. uvのインストール
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows（PowerShell）
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. プロジェクトセットアップ
```bash
# プロジェクトディレクトリに移動
cd jpx_kaiji_service

# 依存関係のインストール
uv sync
```

### 3. 動作確認
```bash
# テスト実行（ソフトバンクグループの情報取得）
uv run python kaiji_downloader.py 99840
```

## 📊 基本的な使い方

### 証券コードについて
- **5桁で入力**: 99840（ソフトバンクグループ）
- **4桁の場合**: 末尾に0を追加（例: 9432 → 94320）
- **主要企業の証券コード例**:
  - 99840: ソフトバンクグループ
  - 94320: NTT
  - 60980: コスモス薬品
  - 43240: LIFULL

### 基本コマンド
```bash
# 企業基本情報のみ取得
uv run python kaiji_downloader.py {証券コード}

# 例: ソフトバンクグループの基本情報
uv run python kaiji_downloader.py 99840
```

## 🎯 実行モード詳細

### 1. 基本情報取得モード
```bash
uv run python kaiji_downloader.py {証券コード}
```
**出力内容**:
- 証券コード
- 企業名
- 市場区分
- 業種
- 決算月

### 2. 適時開示情報表示モード
```bash
uv run python kaiji_downloader.py disclosure {証券コード}
```
**出力内容**:
- 適時開示情報一覧（最新5件表示）
- 決算短信の抽出（最新3件）
- 各種URL情報

### 3. デバッグモード
```bash
uv run python kaiji_downloader.py debug {証券コード}
```
**機能**:
- HTMLファイルをdebug/フォルダに保存
- 詳細な処理ログを出力
- 開発・トラブルシューティング用

### 4. XBRLダウンロードモード
```bash
uv run python kaiji_downloader.py xbrl {証券コード}
```
**機能**:
- 構造化財務データ（XBRL）をダウンロード
- ZIPファイル形式
- 保存先: `downloads/xbrl/{証券コード}/`

### 5. HTMLサマリーダウンロードモード
```bash
uv run python kaiji_downloader.py html {証券コード}
```
**機能**:
- インラインXBRL（iXBRL）ファイルをダウンロード
- HTMLファイル形式
- 保存先: `downloads/html_summary/{証券コード}/`
 - ファイル名形式: `{開示日}_{証券コード}_{表題}_summary.htm`

### 6. 添付資料ダウンロードモード
```bash
uv run python kaiji_downloader.py attachments {証券コード}
```
**機能**:
- 定性的情報（業績予想、事業環境等）をダウンロード
- HTMLファイル形式
- 保存先: `downloads/attachments/{証券コード}/`
 - ファイル名形式: `{開示日}_{証券コード}_{表題}_attachments.htm`

### 7. 全ファイル一括ダウンロードモード
```bash
uv run python kaiji_downloader.py all {証券コード}
```
**機能**:
- XBRL + HTMLサマリー + 添付資料を一括ダウンロード
- 最も効率的な収集方法

### 8. バッチ処理モード（旧版）
```bash
uv run python kaiji_downloader.py batch {CSVファイル}
```
**機能**:
- CSVファイルから複数企業を一括処理
- CSVには証券コードの列が必要

### 9. 全銘柄一括ダウンロードモード（新機能）
```bash
# 全1,681銘柄を一括ダウンロード
uv run python kaiji_downloader.py batch-download

# テスト実行（最初の5社のみ）
uv run python kaiji_downloader.py batch-download-test
```
**機能**:
- codelist.csvから全銘柄のデータを自動一括ダウンロード
- 進捗表示・統計情報・エラーハンドリング完備
- JSON形式の詳細レポート出力
 - codelist.csvの想定: UTF-8(BOM) かつ `code`,`銘柄名`,`業種`,`TOPIXに占める個別銘柄のウエイト`,`ニューインデックス区分` の列を使用

### 10. カスタム一括ダウンロードモード
```bash
# XBRLのみ、最大100社、2秒間隔で実行
uv run python kaiji_downloader.py batch-download codelist.csv --types=xbrl --max=100 --delay=2

# 50行目から再開、HTMLサマリーと添付資料のみ
uv run python kaiji_downloader.py batch-download codelist.csv --types=html,attachments --resume=50

# 企業間待機を範囲指定（jitter）で分散（例: 2〜6秒のランダム）
uv run python kaiji_downloader.py batch-download codelist.csv --types=html,attachments,xbrl --delay-min=2 --delay-max=6
```
**オプション**:
- `--types=xbrl,html,attachments`: ダウンロード種類の選択
- `--resume=N`: N行目から再開
- `--max=N`: 最大N社まで処理
- `--delay=N`: 企業間の待機時間をN秒に設定（固定）
- `--delay-min=M --delay-max=N`: 企業間の待機を M〜N 秒の範囲でランダム化（jitter）。
  - `--delay` 未指定でも使用可。指定がある場合は `delay-min/max` が優先されます。
  - `--delay-min=3 --delay-max=3` は固定3秒（従来と同等）。
  - `delay-min > delay-max` を指定した場合は自動で入れ替えて解釈します。

## 🧩 負荷対策と待機の挙動
- アイテム単位の待機: 成功ダウンロード時のみ 1 秒。スキップ時は待機しません。
- 企業単位の待機: `--delay-min/--delay-max` の範囲でランダムに待機（未指定時は固定 3 秒）。
- 推奨設定例: `--delay-min=2 --delay-max=6`（負荷分散と処理速度のバランスが良好）。

### 503（Service Unavailable）が発生する場合の対処
- 範囲を広げる（例: `2–6秒` → `3–8秒`）。
- ダウンロード種類を限定して再実行（例: `--types=xbrl` のみ）。
- 時間を空けて再試行する。
- 仕様: 本ツールは1社あたりの開示情報取得を1回に統一し、HTML/添付/XBRLで共有しています（過剰アクセス抑制）。

## 🖨 実行ログの例（XBRLスキップ）
```
45件のXBRLファイルをダウンロード中...
[1/45] 2025年２月期 決算短信〔日本基準〕（連結）...
  URL: https://www2.jpx.co.jp/disc/39220/081220250410512874.zip
  → スキップ: 同名ファイルが既に存在します
...
ダウンロード完了: 成功 0 / 45 件
```
ポイント: スキップ時はHTTPアクセス・sleepなしで高速に進行します（成功ダウンロード時のみ 1 秒の待機あり）。

## 📁 ファイル出力仕様

### ディレクトリ構造
```
downloads/
├── xbrl/
│   └── {証券コード}/
│       ├── 2025-08-07_{証券コード}_2026年３月期第１四半期決算短信_xbrl.zip
│       └── ...
├── html_summary/
│   └── {証券コード}/
│       ├── 2025-08-07_{証券コード}_2026年３月期第１四半期決算短信_summary.htm
│       └── ...
└── attachments/
    └── {証券コード}/
        ├── 2025-08-07_{証券コード}_2026年３月期第１四半期決算短信_attachments.htm
        └── ...

data/
├── {証券コード}_{YYYYMMDD_HHMMSS}.json  # 単一企業データ
└── batch_result_{YYYYMMDD_HHMMSS}.json  # バッチ処理結果
```

### ファイル命名規則（v2.0対応）
**新しいわかりやすい形式**:
- **XBRLファイル**: `{開示日}_{表題}_xbrl.zip`
- **HTMLサマリー**: `{開示日}_{表題}_summary.htm`
- **添付資料**: `{開示日}_{表題}_attachments.htm`

**形式詳細**:
- **日付**: `YYYY-MM-DD` (例: 2025-08-07)
- **表題**: 決算短信の完全なタイトル
- **安全性**: `<>:"/\|?*` の文字は自動除去

**実例**:
```
2025-08-07_2026年３月期第１四半期決算短信_xbrl.zip
2025-08-07_2026年３月期第１四半期決算短信_summary.htm
2025-08-07_2026年３月期第１四半期決算短信_attachments.htm
```

### 既存ファイル処理仕様
種類別の挙動（実装準拠）:
- HTMLサマリー・添付資料・XBRL: 同名ファイルが存在する場合はスキップ（ファイル名で判定）
- 不完全ファイル（0バイト等）の場合は再ダウンロードして上書き保存

#### 実際の動作例
```bash
[1/1681] ソフトバンクグループ (99840) 処理開始
  ├─ 2025-08-07_2026年３月期第１四半期決算短信_xbrl.zip
  │   → ✅ スキップ: ファイルが既に存在します
  ├─ 2025-05-08_2025年３月期決算短信_xbrl.zip  
  │   → 📥 ダウンロード中... (新しいファイル)
  └─ 2025-08-07_2026年３月期第１四半期決算短信_attachments.htm
      → ✅ スキップ: ファイルが既に存在します
```

#### 新しい決算情報への対応
- **四半期決算発表時**: 新しいファイル名で保存されるため自動ダウンロード
- **既存期間の再発行**: 
  - HTML/添付/XBRL: 同一ファイル名のためスキップ（再取得が必要なら手動削除してください）

#### 強制再ダウンロードしたい場合
```bash
# 特定企業のファイルを削除してから再実行
rm -rf downloads/xbrl/99840/
uv run python kaiji_downloader.py xbrl 99840
```

### JSONデータ構造
```json
{
  "company_info": {
    "stock_code": "99840",
    "company_name": "ソフトバンクグループ",
    "market": "プライム",
    "industry": "情報・通信業",
    "fiscal_year_end": "3月"
  },
  "disclosure_documents": [
    {
      "date": "2025/08/07",
      "title": "2026年３月期 第１四半期決算短信〔ＩＦＲＳ〕（連結）",
      "pdf_url": "https://www2.jpx.co.jp/disc/99840/140120250805531214.pdf",
      "xbrl_url": "https://www2.jpx.co.jp/disc/99840/081220250805531214.zip",
      "html_summary_url": "https://www2.jpx.co.jp/disc/99840/081220250805531214_tse-qcedifsm-99840-20250807399840-ixbrl.htm",
      "attachments": [
        "https://www2.jpx.co.jp/disc/99840/081220250805531214_qualitative.htm"
      ]
    }
  ]
}
```

## 🔧 トラブルシューティング

### よくあるエラーと解決方法

#### 1. `python: command not found`
```bash
# uvを使用してPythonを実行
uv run python kaiji_downloader.py {証券コード}
```

#### 2. 証券コードが見つからない
- 5桁の証券コードを使用しているか確認
- 上場廃止企業ではないか確認
- JPXの公式サイトで証券コードを確認

#### 3. ダウンロードエラー
- インターネット接続を確認
- JPXサーバーの一時的な不具合の可能性
- 時間をおいて再実行

#### 4. ファイルが見つからない
- 企業によっては特定のファイル（HTMLサマリー、添付資料）が存在しない場合がある
- `debug`モードで詳細ログを確認

#### 5. 文字化け
- Windowsの場合、コマンドプロンプトの文字エンコーディングを確認
```cmd
chcp 65001  # UTF-8に設定
```

### デバッグ方法
1. **デバッグモードの使用**
   ```bash
   uv run python kaiji_downloader.py debug {証券コード}
   ```

2. **HTMLファイルの確認**
   - `debug/`フォルダ内のHTMLファイルを確認
   - ブラウザで開いてテーブル構造を確認

3. **ログの確認**
   - コンソール出力の詳細ログを確認
   - エラーメッセージの内容を確認

## 💡 応用的な使用方法

### 1. 段階的な大量データ収集
```bash
# 小規模テスト（最初の10社）
uv run python kaiji_downloader.py batch-download codelist.csv --max=10 --delay=1

# 業種別収集（製造業のみなど、CSVを事前に絞り込み）
uv run python kaiji_downloader.py batch-download manufacturing_companies.csv

# XBRLのみ高速収集
uv run python kaiji_downloader.py batch-download codelist.csv --types=xbrl --delay=1
```

### 2. 長時間処理の管理
```bash
# バックグラウンド実行（Linux/macOS）
nohup uv run python kaiji_downloader.py batch-download codelist.csv > batch_log.txt 2>&1 &

# 進捗確認
tail -f batch_log.txt

# 中断された場合の再開（100行目から）
uv run python kaiji_downloader.py batch-download codelist.csv --resume=100
```

### 3. 効率的な処理戦略
```bash
# 1. まずXBRLのみを全社取得（高速）
uv run python kaiji_downloader.py batch-download codelist.csv --types=xbrl --delay=1

# 2. 次にHTMLサマリーを取得
uv run python kaiji_downloader.py batch-download codelist.csv --types=html --delay=2

# 3. 最後に添付資料を取得（サイズが大きいため）
uv run python kaiji_downloader.py batch-download codelist.csv --types=attachments --delay=3
```

### 4. カスタムCSVファイルでの処理
**製造業のみの例（manufacturing.csv）**:
```csv
date,銘柄名,コード,業種,TOPIXに占める個別銘柄のウエイト,ニューインデックス区分,code
2025/6/30,信越化学工業,4063,化学,0.010521,TOPIX Core30,40630
2025/6/30,武田薬品工業,4502,医薬品,0.009774,TOPIX Core30,45020
```

**実行**:
```bash
uv run python kaiji_downloader.py batch-download manufacturing.csv
```

### 4. 定期実行の設定
**cronを使用した例（Linux/macOS）**:
```bash
# 毎日午後6時に実行
0 18 * * * cd /path/to/jpx_kaiji_service && uv run python kaiji_downloader.py all 99840
```

**タスクスケジューラーを使用（Windows）**:
1. タスクスケジューラーを開く
2. 基本タスクの作成
3. トリガー: 毎日
4. 操作: `uv run python kaiji_downloader.py all 99840`

## 📊 財務指標データの活用

### 抽出可能な財務指標
`xbrl_financial_indicators.csv`に40種類以上の財務指標をリスト化:
- 売上高・利益情報
- 資産・負債情報
- 1株当たり情報
- キャッシュフロー情報

### XBRLデータの解析
現在はファイルダウンロードまで対応。今後、自動解析機能を追加予定。

## 🔒 注意事項とベストプラクティス

### サーバー負荷軽減
- 大量データ取得時は間隔をあけて実行
- 業務時間外の実行を推奨
- 必要なデータのみを選択的にダウンロード

### データの管理
- 定期的なバックアップ
- 不要なファイルの削除
- ディスク容量の監視

### 法的遵守
- JPXの利用規約を遵守
- 商用利用時は適切な手続きを実施
- データの再配布には注意

## 📞 サポート

### 技術サポート
- GitHub Issues での質問・要望受付
- バグレポートの提出

### よくある質問
1. **Q**: 証券コードが分からない
   **A**: JPX公式サイトの銘柄検索機能を使用

2. **Q**: ダウンロードに時間がかかる
   **A**: サーバー負荷軽減のため意図的に間隔を設けています

3. **Q**: 全ファイルが必要ない場合
   **A**: 個別ダウンロードモード（xbrl、html、attachments）を使用

---

**最終更新**: 2025年8月23日  
**バージョン**: 2.0.0 (ファイル命名規則改善版)
