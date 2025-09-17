# プロジェクトの目的
- 東証上場会社情報サービスから各企業の情報を取得しデータを蓄積するプロジェクト
- 参考url: https://www2.jpx.co.jp/tseHpFront/JJK010030Action.do

## ライブラリ管理の方針
- 通常のPythonプロジェクトではuvを必須とする

## プロジェクトポリシー
- 1stepごとに実装内容含め、提案や相談しながら進めてほしい

### 実装ファイル
- **kaiji_downloader.py**: 参考URLからデータをダウンロードするプログラム
- **html_summary_xbrl_list_create.py**: html_summmaryのxbrlを用いた決算短信にどのような情報があるのか調査しリスト化するプログラム。全銘柄のサンプルデータが置いてあるdownload/matomeフォルダのデータを全てリスト化する
- **html_summary_output.py**: 決算短信のHTML要約データから必要な情報を抽出・整形して出力するプログラム
- **html_summary_join.py**: 複数の決算短信HTML要約データを結合・統合処理するプログラム
- **attachments_output.py**: XBRL添付資料から本文テキストを抽出してMarkdown/TXT/JSON形式で出力するプログラム。HTMLタグやスタイル情報を除去し、LLM分析用に85-96%のデータ削減を実現