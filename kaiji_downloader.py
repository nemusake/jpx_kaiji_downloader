#!/usr/bin/env python3
"""
東証上場企業情報取得サービス
メインスクリプト
"""

"""

実行コマンド使用例

    # 例1: 全1,681社のHTMLと添付資料を収集（推定20時間程度）
        uv run python kaiji_downloader.py batch-download codelist.csv --types=html,attachments --delay-min=2 --delay-max=5

    # 例2: 最初の100社のHTMLと添付資料をテスト収集
        uv run python kaiji_downloader.py batch-download codelist.csv --types=html,attachments --max=100 --delay-min=2 --delay-max=5

    # 例3: 500行目から再開してHTMLと添付資料を収集
        uv run python kaiji_downloader.py batch-download codelist.csv --types=html,attachments --resume=500 --delay-min=2 --delay-max=5


実行コマンド一覧

codelist.csvから取得する場合

    # 1. XBRLのみ高速収集
        uv run python kaiji_downloader.py batch-download codelist.csv --types=xbrl --delay-min=2 --delay-max=5
    # 2. HTMLサマリー収集
        uv run python kaiji_downloader.py batch-download codelist.csv --types=html --delay-min=2 --delay-max=5
    # 3. 添付資料収集
        uv run python kaiji_downloader.py batch-download codelist.csv --types=attachments --delay-min=2 --delay-max=5

"""

import json
import csv
import os
from datetime import datetime
from src.scraper import JPXScraper


def test_single_company(stock_code: str = "9984", debug: bool = False, fetch_disclosure: bool = False, 
                       download_xbrl: bool = False, download_html: bool = False, download_attachments: bool = False):
    """
    単一企業（ソフトバンク: 9984）でのテスト実行
    
    Args:
        stock_code: テスト対象の証券コード
        debug: デバッグモード（HTMLを保存）
        fetch_disclosure: 適時開示情報も取得するか
        download_xbrl: XBRLファイルをダウンロードするか
        download_html: HTMLサマリーファイルをダウンロードするか
        download_attachments: 添付資料ファイルをダウンロードするか
    """
    print(f"証券コード {stock_code} の情報を取得中...")
    print("-" * 50)
    
    # スクレイパーのインスタンス作成（デバッグモード有効）
    scraper = JPXScraper(debug=debug)
    
    # 企業情報を取得
    company_info = scraper.search_company(stock_code)
    
    if company_info:
        print("取得成功！")
        print("\n【取得した企業情報】")
        for key, value in company_info.items():
            if value:
                print(f"  {key}: {value}")
        
        # 適時開示情報を取得
        disclosure_docs = []
        if fetch_disclosure:
            print("\n【適時開示情報を取得中...】")
            disclosure_docs = scraper.fetch_disclosure_documents(stock_code)
            
            if disclosure_docs:
                print(f"\n【適時開示情報】 {len(disclosure_docs)}件")
                # 最新の5件を表示
                for i, doc in enumerate(disclosure_docs[:5], 1):
                    print(f"\n{i}. {doc['date']} - {doc['title']}")
                    if doc['pdf_url']:
                        print(f"   PDF: {doc['pdf_url']}")
                    if doc['xbrl_url']:
                        print(f"   XBRL: {doc['xbrl_url']}")
                    if doc['html_summary_url']:
                        print(f"   HTMLサマリー: {doc['html_summary_url']}")
                    if doc['attachments']:
                        print(f"   添付資料: {len(doc['attachments'])}件")
                
                # 決算短信のみを抽出
                kessan_docs = [doc for doc in disclosure_docs if '決算短信' in doc['title']]
                if kessan_docs:
                    print(f"\n【決算短信】 {len(kessan_docs)}件")
                    for doc in kessan_docs[:3]:
                        print(f"  {doc['date']} - {doc['title']}")
                        if doc['xbrl_url']:
                            print(f"    XBRL: {doc['xbrl_url']}")
                
                # XBRLダウンロード
                if download_xbrl:
                    print("\n【XBRLファイルをダウンロード中...】")
                    download_results = scraper.download_xbrl_files(
                        disclosure_docs,
                        download_dir=f"downloads/xbrl/{stock_code}",
                        stock_code=stock_code
                    )
                    
                    # ダウンロード結果を表示
                    successful_downloads = [r for r in download_results if r['status'] == 'success']
                    if successful_downloads:
                        print(f"\n【XBRLダウンロード成功】 {len(successful_downloads)}件")
                        for result in successful_downloads[:3]:
                            print(f"  {result['local_file']} ({result['file_size']:,} bytes)")
                
                # HTMLサマリーダウンロード
                if download_html:
                    print("\n【HTMLサマリーファイルをダウンロード中...】")
                    download_results = scraper.download_html_summaries(stock_code)
                    
                    # ダウンロード結果を表示
                    successful_downloads = [r for r in download_results if r['status'] == 'success']
                    if successful_downloads:
                        print(f"\n【HTMLサマリーダウンロード成功】 {len(successful_downloads)}件")
                        for result in successful_downloads[:3]:
                            print(f"  {result['local_file']} ({result['file_size']:,} bytes)")
                
                # 添付資料ダウンロード
                if download_attachments:
                    print("\n【添付資料ファイルをダウンロード中...】")
                    download_results = scraper.download_attachments(stock_code)
                    
                    # ダウンロード結果を表示
                    successful_downloads = [r for r in download_results if r['status'] == 'success']
                    if successful_downloads:
                        print(f"\n【添付資料ダウンロード成功】 {len(successful_downloads)}件")
                        for result in successful_downloads[:3]:
                            print(f"  {result['local_file']} ({result['file_size']:,} bytes)")
        
        # JSONファイルに保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/{stock_code}_{timestamp}.json"
        
        result_data = {
            'company_info': company_info,
            'disclosure_documents': disclosure_docs
        }
        
        os.makedirs("data", exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n結果を {output_file} に保存しました")
        return True
    else:
        print("情報の取得に失敗しました")
        return False


def batch_download_all(
    csv_file: str = "codelist.csv",
    download_types: list = None,
    resume_from: int = 0,
    max_companies: int = None,
    delay_seconds: int = 3,
    delay_min: int | None = None,
    delay_max: int | None = None,
):
    """
    codelist.csvから全銘柄のデータを一括ダウンロード
    
    Args:
        csv_file: 銘柄リストCSVファイル
        download_types: ダウンロード種類のリスト
        resume_from: 再開する行番号
        max_companies: 最大処理企業数
        delay_seconds: 企業間待機秒数
    """
    print(f"🚀 全銘柄一括ダウンロード開始")
    print(f"📋 対象ファイル: {csv_file}")
    print("-" * 50)
    
    # スクレイパーのインスタンス作成
    scraper = JPXScraper(debug=False)
    
    # バッチダウンロード実行
    results = scraper.download_all_files_batch(
        codelist_csv=csv_file,
        download_types=download_types,
        resume_from=resume_from,
        max_companies=max_companies,
        delay_seconds=delay_seconds,
        delay_min=delay_min,
        delay_max=delay_max,
    )
    
    return results


def process_batch(csv_file: str = "codelist.csv"):
    """
    CSVファイルから証券コードを読み込んでバッチ処理
    
    Args:
        csv_file: 証券コードリストのCSVファイル
    """
    if not os.path.exists(csv_file):
        print(f"エラー: {csv_file} が見つかりません")
        return
    
    print(f"{csv_file} からバッチ処理を開始...")
    print("-" * 50)
    
    # スクレイパーのインスタンス作成
    scraper = JPXScraper()
    
    # 結果を格納するリスト
    results = []
    
    # CSVファイルを読み込む
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        stock_codes = []
        
        # 証券コードカラムを探す
        if reader.fieldnames:
            code_column = None
            for field in reader.fieldnames:
                if 'code' in field.lower() or '証券' in field:
                    code_column = field
                    break
            
            if code_column:
                for row in reader:
                    stock_codes.append(row[code_column])
            else:
                # カラムが見つからない場合は最初のカラムを使用
                f.seek(0)
                next(reader)  # ヘッダーをスキップ
                for row in reader:
                    stock_codes.append(list(row.values())[0])
    
    # 各証券コードの情報を取得
    total = len(stock_codes)
    success_count = 0
    
    for i, code in enumerate(stock_codes, 1):
        print(f"\n[{i}/{total}] 証券コード {code} を処理中...")
        
        company_info = scraper.search_company(code)
        
        if company_info:
            results.append(company_info)
            success_count += 1
            print(f"  → 成功: {company_info.get('company_name', '不明')}")
        else:
            print(f"  → 失敗")
        
        # サーバーへの負荷を考慮して待機
        if i < total:
            import time
            time.sleep(2)  # 2秒待機
    
    # 結果をまとめて保存
    if results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/batch_result_{timestamp}.json"
        
        os.makedirs("data", exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n\n処理完了！")
        print(f"成功: {success_count}/{total} 件")
        print(f"結果を {output_file} に保存しました")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        # バッチ処理モード
        csv_file = sys.argv[2] if len(sys.argv) > 2 else "codelist.csv"
        process_batch(csv_file)
    elif len(sys.argv) > 1 and sys.argv[1] == "debug":
        # デバッグモード
        stock_code = sys.argv[2] if len(sys.argv) > 2 else "99840"
        test_single_company(stock_code, debug=True, fetch_disclosure=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "disclosure":
        # 適時開示情報取得モード
        stock_code = sys.argv[2] if len(sys.argv) > 2 else "99840"
        test_single_company(stock_code, debug=False, fetch_disclosure=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "xbrl":
        # XBRLダウンロードモード
        stock_code = sys.argv[2] if len(sys.argv) > 2 else "99840"
        test_single_company(stock_code, debug=True, fetch_disclosure=True, download_xbrl=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "html":
        # HTMLサマリーダウンロードモード
        stock_code = sys.argv[2] if len(sys.argv) > 2 else "99840"
        test_single_company(stock_code, debug=True, fetch_disclosure=True, download_html=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "attachments":
        # 添付資料ダウンロードモード
        stock_code = sys.argv[2] if len(sys.argv) > 2 else "99840"
        test_single_company(stock_code, debug=True, fetch_disclosure=True, download_attachments=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "all":
        # 全ファイルダウンロードモード
        stock_code = sys.argv[2] if len(sys.argv) > 2 else "99840"
        test_single_company(stock_code, debug=True, fetch_disclosure=True, 
                           download_xbrl=True, download_html=True, download_attachments=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "batch-download":
        # 全銘柄一括ダウンロードモード
        csv_file = sys.argv[2] if len(sys.argv) > 2 else "codelist.csv"
        
        # オプション解析
        download_types = None
        resume_from = 0
        max_companies = None
        delay_seconds = 3
        delay_min = None
        delay_max = None
        
        # コマンドライン引数の解析
        for i, arg in enumerate(sys.argv[3:], 3):
            if arg.startswith("--types="):
                types_str = arg.split("=")[1]
                download_types = types_str.split(",")
            elif arg.startswith("--resume="):
                resume_from = int(arg.split("=")[1])
            elif arg.startswith("--max="):
                max_companies = int(arg.split("=")[1])
            elif arg.startswith("--delay="):
                delay_seconds = int(arg.split("=")[1])
            elif arg.startswith("--delay-min="):
                delay_min = float(arg.split("=")[1])
            elif arg.startswith("--delay-max="):
                delay_max = float(arg.split("=")[1])
        # 範囲指定の正規化
        if delay_min is None and delay_max is None:
            # 旧オプション(--delay)のみ指定時は固定待機
            delay_min = delay_seconds
            delay_max = delay_seconds
        elif delay_min is None:
            delay_min = delay_max
        elif delay_max is None:
            delay_max = delay_min
        # 入力が逆の場合は入れ替え
        if delay_min > delay_max:
            delay_min, delay_max = delay_max, delay_min

        batch_download_all(
            csv_file,
            download_types,
            resume_from,
            max_companies,
            delay_seconds,
            delay_min,
            delay_max,
        )
    elif len(sys.argv) > 1 and sys.argv[1] == "batch-download-test":
        # テスト用：最初の5社のみ処理
        csv_file = sys.argv[2] if len(sys.argv) > 2 else "codelist.csv"
        batch_download_all(csv_file, max_companies=5, delay_seconds=1)
    else:
        # 単一企業テストモード（デフォルト: 99840）
        stock_code = sys.argv[1] if len(sys.argv) > 1 else "99840"
        test_single_company(stock_code)
