#!/usr/bin/env python3
"""
batch_download_reportのJSONファイルから
success_filesが1以上のstock_codeを抽出してCSVに出力するスクリプト
"""

import json
import csv
import codecs
import sys
from pathlib import Path
from datetime import datetime


def extract_successful_stocks(json_file_path, output_csv_path):
    """
    JSONファイルからsuccess_filesが1以上のstock_codeを抽出
    
    Args:
        json_file_path: 入力JSONファイルのパス
        output_csv_path: 出力CSVファイルのパス
    """
    # JSONファイルを読み込み
    print(f"JSONファイルを読み込み中: {json_file_path}")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # success_filesが1以上のstock_codeを抽出
    successful_stocks = []
    total_count = 0
    success_count = 0
    
    for result in data.get('results', []):
        total_count += 1
        success_files = result.get('success_files', 0)
        # 種別別の成功数（存在しない場合は0）
        downloads = result.get('downloads', {}) or {}
        html_success = (downloads.get('html', {}) or {}).get('success', 0)
        attachments_success = (downloads.get('attachments', {}) or {}).get('success', 0)
        xbrl_success = (downloads.get('xbrl', {}) or {}).get('success', 0)
        
        if success_files >= 1:
            stock_code = result.get('stock_code', '')
            company_name = result.get('company_name', '')
            successful_stocks.append({
                'stock_code': stock_code,
                'company_name': company_name,
                'success_files': success_files,
                'html_success': html_success,
                'attachments_success': attachments_success,
                'xbrl_success': xbrl_success
            })
            success_count += 1
            print(
                f"  ✓ {stock_code}: {company_name} (成功ファイル数: {success_files} | "
                f"html: {html_success}, attachments: {attachments_success}, xbrl: {xbrl_success})"
            )
    
    print(f"\n集計結果:")
    print(f"  総企業数: {total_count}")
    print(f"  成功企業数: {success_count}")
    
    # UTF-8 BOM付きCSVファイルとして出力
    print(f"\nCSVファイルに出力中: {output_csv_path}")
    
    # BOM付きでファイルを開く
    with open(output_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        if successful_stocks:
            # CSVヘッダーと行を書き込み
            fieldnames = [
                'stock_code',
                'company_name',
                'success_files',
                'html_success',
                'attachments_success',
                'xbrl_success',
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(successful_stocks)
            print(f"  {len(successful_stocks)}件のデータを出力しました")
        else:
            # データがない場合もヘッダーだけ出力
            writer = csv.writer(f)
            writer.writerow([
                'stock_code',
                'company_name',
                'success_files',
                'html_success',
                'attachments_success',
                'xbrl_success',
            ])
            print("  成功したデータが見つかりませんでした")
    
    return successful_stocks


def find_batch_download_reports(data_dir='data'):
    """dataフォルダ内のbatch_download_report_*.jsonファイルを検索"""
    data_path = Path(data_dir)
    if not data_path.exists():
        return []
    
    # batch_download_reportで始まるJSONファイルを検索
    json_files = list(data_path.glob('batch_download_report_*.json'))
    
    # ファイル名でソート（日付順になることが多い）
    json_files.sort(key=lambda x: x.name, reverse=True)
    
    return json_files


def select_file_interactively(json_files):
    """対話式でファイルを選択"""
    if not json_files:
        print("エラー: dataフォルダにbatch_download_report_*.jsonファイルが見つかりません")
        return None
    
    print("\n利用可能なレポートファイル:")
    print("-" * 60)
    
    for i, file_path in enumerate(json_files, 1):
        # ファイル名から日時情報を抽出（可能であれば）
        file_name = file_path.name
        file_size = file_path.stat().st_size / 1024 / 1024  # MB単位
        modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        print(f"{i:2}. {file_name}")
        print(f"    サイズ: {file_size:.2f} MB")
        print(f"    更新日時: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    # ユーザーに選択を促す
    while True:
        try:
            choice = input("処理するファイルの番号を入力してください (1-{0}): ".format(len(json_files)))
            if not choice:
                print("キャンセルされました")
                return None
                
            index = int(choice) - 1
            if 0 <= index < len(json_files):
                selected_file = json_files[index]
                print(f"\n選択されたファイル: {selected_file.name}")
                return selected_file
            else:
                print(f"1から{len(json_files)}の範囲で入力してください")
        except ValueError:
            print("数値を入力してください")
        except KeyboardInterrupt:
            print("\nキャンセルされました")
            return None


def main():
    """メイン処理"""
    json_file = None
    output_csv = 'successful_stocks.csv'
    
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        # 引数が指定された場合は従来の動作
        json_file = sys.argv[1]
        if len(sys.argv) > 2:
            output_csv = sys.argv[2]
    else:
        # 引数がない場合は対話式でファイル選択
        print("batch_download_reportファイルを検索中...")
        json_files = find_batch_download_reports()
        
        if json_files:
            selected_file = select_file_interactively(json_files)
            if selected_file:
                json_file = str(selected_file)
                # 出力ファイル名を入力ファイル名に基づいて生成
                base_name = selected_file.stem  # 拡張子を除いたファイル名
                output_csv = f"{base_name}_successful_stocks.csv"
            else:
                sys.exit(0)
        else:
            print("dataフォルダにbatch_download_report_*.jsonファイルが見つかりません")
            print("\n使用方法:")
            print("  python3 extract_successful_stocks.py [JSONファイル] [出力CSVファイル]")
            sys.exit(1)
    
    # ファイルの存在確認
    json_path = Path(json_file)
    if not json_path.exists():
        print(f"エラー: JSONファイルが見つかりません: {json_file}")
        sys.exit(1)
    
    # 抽出処理を実行
    try:
        successful_stocks = extract_successful_stocks(json_file, output_csv)
        print(f"\n処理が完了しました。出力ファイル: {output_csv}")
        
    except json.JSONDecodeError as e:
        print(f"エラー: JSONファイルの解析に失敗しました: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"エラー: 処理中にエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
