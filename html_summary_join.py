#!/usr/bin/env python3
"""
HTML Summary CSV結合ツール

output/html_summaryフォルダ内の各証券コードごとのCSVファイルを
1つのCSVファイルに結合、またはデータクレンジング処理を行います。

使用方法:
    python html_summary_join.py                    # ヘルプを表示
    python html_summary_join.py all                # 全CSVファイルを結合
    python html_summary_join.py 20250101-20250701  # 日付範囲で結合
    python html_summary_join.py 13010-99840        # 証券コード範囲で結合
    python3 html_summary_join.py cleansing          # 証券コードとvalue数値のクレンジング処理
"""

import sys
import os
import csv
import glob
from datetime import datetime
from typing import List, Tuple, Optional


def show_help():
    """ヘルプメッセージを表示"""
    help_message = """
HTML Summary CSV結合ツール

使用方法:
    python html_summary_join.py                    # ヘルプを表示
    python html_summary_join.py all                # 全CSVファイルを結合
    python html_summary_join.py 20250101-20250701  # 日付範囲で結合（YYYYMMDD形式）
    python html_summary_join.py 13010-99840        # 証券コード範囲で結合
    python html_summary_join.py cleansing          # 証券コードとvalue数値のクレンジング処理

説明:
    output/html_summaryフォルダ内の各証券コードごとのCSVファイルを
    1つのCSVファイルに結合します。
    
    全結合: フォルダ内の全5桁コードCSVファイルを結合
    日付範囲指定: CSV内のdateカラムを参照してフィルタリング
    証券コード範囲指定: ファイル名（証券コード）でフィルタリング
    クレンジング: 4桁の証券コードを5桁に正規化（末尾に0を追加）＋value数値からカンマ除去
    
出力:
    all: html_summary_all.csv
    日付範囲: html_summary_date_yyyymmdd-yyyymmdd.csv
    証券コード範囲: html_summary_code_xxxxx-xxxxx.csv
    cleansing: 各CSVファイルを直接更新
"""
    print(help_message)


def parse_date_range(range_str: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """日付範囲文字列をパース
    
    Args:
        range_str: "YYYYMMDD-YYYYMMDD"形式の文字列
        
    Returns:
        (開始日, 終了日)のタプル
    """
    try:
        parts = range_str.split('-')
        if len(parts) != 2:
            return None, None
            
        # 8桁の数字かチェック
        if len(parts[0]) == 8 and len(parts[1]) == 8:
            start_date = datetime.strptime(parts[0], '%Y%m%d')
            end_date = datetime.strptime(parts[1], '%Y%m%d')
            return start_date, end_date
    except ValueError:
        pass
    
    return None, None


def parse_code_range(range_str: str) -> Tuple[Optional[str], Optional[str]]:
    """証券コード範囲文字列をパース
    
    Args:
        range_str: "13010-99840"形式の文字列
        
    Returns:
        (開始コード, 終了コード)のタプル
    """
    try:
        parts = range_str.split('-')
        if len(parts) != 2:
            return None, None
            
        # 4-5桁の数字または英数字かチェック
        start_code = parts[0].strip()
        end_code = parts[1].strip()
        
        # 証券コードの妥当性を簡易チェック（4-5文字）
        if 4 <= len(start_code) <= 5 and 4 <= len(end_code) <= 5:
            return start_code, end_code
    except:
        pass
    
    return None, None


def filter_by_date(rows: List[dict], start_date: datetime, end_date: datetime) -> List[dict]:
    """日付範囲でデータをフィルタリング
    
    Args:
        rows: CSVデータの行リスト
        start_date: 開始日
        end_date: 終了日
        
    Returns:
        フィルタリング後の行リスト
    """
    filtered_rows = []
    for row in rows:
        try:
            # dateカラムから日付を取得
            date_str = row.get('date', '')
            if date_str:
                # YYYY-MM-DD形式を想定
                row_date = datetime.strptime(date_str, '%Y-%m-%d')
                if start_date <= row_date <= end_date:
                    filtered_rows.append(row)
        except ValueError:
            # 日付パースエラーの場合はスキップ
            continue
    
    return filtered_rows


def get_csv_files(directory: str, start_code: Optional[str] = None, 
                  end_code: Optional[str] = None) -> List[str]:
    """CSVファイルリストを取得（証券コード範囲でフィルタリング）
    
    Args:
        directory: 検索ディレクトリ
        start_code: 開始証券コード
        end_code: 終了証券コード
        
    Returns:
        CSVファイルパスのリスト
    """
    csv_files = glob.glob(os.path.join(directory, '*.csv'))
    
    if start_code and end_code:
        filtered_files = []
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            code = os.path.splitext(filename)[0]
            
            # 証券コードの範囲チェック
            if start_code <= code <= end_code:
                filtered_files.append(file_path)
        
        return sorted(filtered_files)
    
    return sorted(csv_files)


def combine_csv_files(csv_files: List[str], 
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> Tuple[List[dict], int]:
    """複数のCSVファイルを結合
    
    Args:
        csv_files: CSVファイルパスのリスト
        start_date: フィルタリング開始日
        end_date: フィルタリング終了日
        
    Returns:
        (結合データ, 処理ファイル数)のタプル
    """
    all_rows = []
    processed_files = 0
    
    for file_path in csv_files:
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                # 日付フィルタリングが指定されている場合
                if start_date and end_date:
                    rows = filter_by_date(rows, start_date, end_date)
                
                if rows:  # データがある場合のみ追加
                    all_rows.extend(rows)
                    processed_files += 1
                    
            print(f"処理中: {os.path.basename(file_path)} ({len(rows)}行)")
            
        except Exception as e:
            print(f"エラー: {os.path.basename(file_path)} - {str(e)}", file=sys.stderr)
            continue
    
    return all_rows, processed_files


def is_comma_separated_number(value: str) -> bool:
    """カンマ区切り数値かどうか判定（正規表現不使用）
    
    Args:
        value: チェック対象の文字列（CSVリーダーでクォート除去済み）
        
    Returns:
        カンマ区切り数値の場合True
    """
    if not value or not isinstance(value, str):
        return False
    
    # 空文字でないかチェック
    if not value:
        return False
    
    # カンマを含むかチェック
    if ',' not in value:
        return False
    
    # カンマを除去して全て数字かチェック（負の数も考慮）
    no_comma = value.replace(',', '')
    # 先頭のマイナス記号を除去してチェック
    if no_comma.startswith('-'):
        no_comma = no_comma[1:]
    if not no_comma.isdigit():
        return False
    
    # 3桁区切りの形式かチェック（基本的な検証）
    # マイナス記号を除去
    check_value = value
    if check_value.startswith('-'):
        check_value = check_value[1:]
    
    parts = check_value.split(',')
    if len(parts) < 2:
        return False
    
    # 先頭は1-3桁、それ以降は3桁ずつかチェック
    if not (1 <= len(parts[0]) <= 3 and parts[0].isdigit()):
        return False
    
    for part in parts[1:]:
        if len(part) != 3 or not part.isdigit():
            return False
    
    return True


def clean_comma_separated_number(value: str) -> str:
    """カンマ区切り数値からカンマを除去
    
    Args:
        value: カンマ区切り数値文字列（CSVリーダーでクォート除去済み）
        
    Returns:
        カンマ除去後の数値文字列
    """
    return value.replace(',', '')


def convert_fullwidth_to_halfwidth(text: str) -> str:
    """全角英数字を半角に変換
    
    Args:
        text: 変換対象の文字列
        
    Returns:
        半角変換後の文字列
    """
    if not text or not isinstance(text, str):
        return text
    
    # 全角→半角変換マップ
    fullwidth_chars = "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
    halfwidth_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    
    # 文字ごとに変換
    result = ""
    for char in text:
        if char in fullwidth_chars:
            # 全角文字のインデックスを取得して対応する半角文字に変換
            index = fullwidth_chars.index(char)
            result += halfwidth_chars[index]
        else:
            result += char
    
    return result


def is_numeric_value(value: str) -> bool:
    """数値データ（全角数字・カンマ区切り含む）かどうか判定
    
    Args:
        value: チェック対象の文字列
        
    Returns:
        数値データの場合True
    """
    if not value or not isinstance(value, str):
        return False
    
    # まず全角を半角に変換
    converted_value = convert_fullwidth_to_halfwidth(value)
    
    # カンマ区切り数値の場合
    if is_comma_separated_number(converted_value):
        return True
    
    # シンプルな数値の場合（負の数も考慮）
    test_value = converted_value
    if test_value.startswith('-'):
        test_value = test_value[1:]
    
    return test_value.isdigit()


def clean_numeric_value(value: str) -> str:
    """数値データから全角英数字とカンマを正規化
    
    Args:
        value: 数値文字列
        
    Returns:
        正規化後の数値文字列
    """
    # 全角→半角変換
    converted = convert_fullwidth_to_halfwidth(value)
    # カンマ除去
    return converted.replace(',', '')


def cleanse_code_in_csv(file_path: str) -> Tuple[int, int, int]:
    """CSVファイル内の証券コードとvalueカラムのカンマと半角を正規化
    
    Args:
        file_path: CSVファイルパス
        
    Returns:
        (修正前の行数, 証券コード修正行数, value修正行数)のタプル
    """
    # ファイル名から正しい証券コードを取得
    filename = os.path.basename(file_path)
    correct_code = os.path.splitext(filename)[0]
    
    # CSVファイルを読み込み
    rows = []
    code_modified_count = 0
    value_modified_count = 0
    total_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_count += 1
                current_code = row.get('code', '')
                current_value = row.get('value', '')
                
                # 証券コードクレンジング
                code_modified = False
                
                # 1. 全角→半角変換
                halfwidth_code = convert_fullwidth_to_halfwidth(current_code)
                if halfwidth_code != current_code:
                    row['code'] = halfwidth_code
                    current_code = halfwidth_code
                    code_modified = True
                
                # 2. 4桁→5桁変換
                if len(current_code) == 4 and len(correct_code) == 5:
                    if current_code == correct_code[:4]:
                        row['code'] = current_code + '0'
                        code_modified = True
                
                if code_modified:
                    code_modified_count += 1
                
                # valueカラムクレンジング（数値データのみ）
                if is_numeric_value(current_value):
                    cleaned_value = clean_numeric_value(current_value)
                    if cleaned_value != current_value:
                        row['value'] = cleaned_value
                        value_modified_count += 1
                
                rows.append(row)
        
        # 修正があった場合のみファイルを上書き
        if code_modified_count > 0 or value_modified_count > 0:
            # カラム名の定義（既存のものと同じ）
            columns = [
                'date', 'filing_date', 'code', 'company_name', 
                'fiscal_year_end', 'quarterly_period', 'factor_tag', 
                'factor_jp', 'value', 'has_value', 'is_nil', 'data_type'
            ]
            
            # CSVファイルに書き込み
            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
        
        return total_count, code_modified_count, value_modified_count
        
    except Exception as e:
        print(f"エラー: {os.path.basename(file_path)} - {str(e)}", file=sys.stderr)
        return 0, 0, 0


def cleanse_all_csv_files(directory: str) -> None:
    """全CSVファイルの証券コードを半角に正規化
    全CSVファイルのvalueカラムが数値だった場合にカンマを除去し半角に正規化
    
    Args:
        directory: CSVファイルが格納されているディレクトリ
    """
    import re
    
    # CSVファイルのリストを取得
    all_csv_files = glob.glob(os.path.join(directory, '*.csv'))
    csv_files = []
    
    for file_path in all_csv_files:
        filename = os.path.basename(file_path)
        code = os.path.splitext(filename)[0]
        # 4-5文字の英数字のファイル名のみを対象とする
        if re.match(r'^[A-Za-z0-9]{4,5}$', code):
            csv_files.append(file_path)
    
    csv_files = sorted(csv_files)
    
    if not csv_files:
        print("警告: 処理対象のCSVファイルが見つかりません")
        return
    
    print(f"処理対象ファイル数: {len(csv_files)}")
    print("クレンジング処理を開始します...\n")
    
    total_files = len(csv_files)
    total_rows_processed = 0
    total_code_modified = 0
    total_value_modified = 0
    files_modified = 0
    
    for i, file_path in enumerate(csv_files, 1):
        filename = os.path.basename(file_path)
        rows_count, code_modified_count, value_modified_count = cleanse_code_in_csv(file_path)
        
        total_rows_processed += rows_count
        total_code_modified += code_modified_count
        total_value_modified += value_modified_count
        
        if code_modified_count > 0 or value_modified_count > 0:
            files_modified += 1
            if code_modified_count > 0 and value_modified_count > 0:
                print(f"[{i}/{total_files}] {filename}: code {code_modified_count}行、value {value_modified_count}行を修正")
            elif code_modified_count > 0:
                print(f"[{i}/{total_files}] {filename}: code {code_modified_count}行を修正")
            elif value_modified_count > 0:
                print(f"[{i}/{total_files}] {filename}: value {value_modified_count}行を修正")
        else:
            # 進捗表示（10ファイルごと）
            if i % 10 == 0:
                print(f"[{i}/{total_files}] 処理中...")
    
    # 結果の表示
    print("\n" + "="*50)
    print("クレンジング処理完了")
    print(f"処理ファイル数: {total_files}")
    print(f"修正ファイル数: {files_modified}")
    print(f"総レコード数: {total_rows_processed}")
    print(f"証券コード修正レコード数: {total_code_modified}")
    print(f"valueカンマ除去レコード数: {total_value_modified}")
    print("="*50)


def save_combined_csv(data: List[dict], output_dir: str, 
                     filter_type: str = None, filter_range: str = None) -> str:
    """結合データをCSVファイルに保存
    
    Args:
        data: 結合データ
        output_dir: 出力ディレクトリ
        filter_type: フィルタータイプ ('date', 'code', or 'all')
        filter_range: フィルター範囲文字列
        
    Returns:
        出力ファイルパス
    """
    # 出力ファイル名を生成
    if filter_type == 'all':
        # 全結合の場合: html_summary_all.csv
        output_filename = "html_summary_all.csv"
    elif filter_type == 'date' and filter_range:
        # 日付範囲指定の場合: html_summary_date_yyyymmdd-yyyymmdd.csv
        output_filename = f"html_summary_date_{filter_range}.csv"
    elif filter_type == 'code' and filter_range:
        # 証券コード範囲指定の場合: html_summary_code_xxxxx-xxxxx.csv
        output_filename = f"html_summary_code_{filter_range}.csv"
    else:
        # デフォルト（念のため）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"combined_html_summary_{timestamp}.csv"
    
    output_path = os.path.join(output_dir, output_filename)
    
    # カラム名の定義
    columns = [
        'date', 'filing_date', 'code', 'company_name', 
        'fiscal_year_end', 'quarterly_period', 'factor_tag', 
        'factor_jp', 'value', 'has_value', 'is_nil', 'data_type'
    ]
    
    # CSVファイルに書き込み
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)
    
    return output_path


def main():
    """メイン処理"""
    # コマンドライン引数のチェック
    if len(sys.argv) < 2:
        show_help()
        return
    
    # 入力ディレクトリと出力ディレクトリの設定
    input_dir = os.path.join('output', 'html_summary')
    output_dir = 'output'
    
    # ディレクトリの存在確認
    if not os.path.exists(input_dir):
        print(f"エラー: {input_dir} ディレクトリが存在しません", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 引数のパース
    range_arg = sys.argv[1]
    
    # cleansingコマンドの判定
    if range_arg.lower() == 'cleansing':
        print("クレンジングモード: 証券コードの正規化処理を実行します")
        cleanse_all_csv_files(input_dir)
        return
    
    # allコマンドの判定
    elif range_arg.lower() == 'all':
        print("全結合モード: フォルダ内の全CSVファイルを結合します")
        # 5桁コードのCSVファイルのみを取得（正規表現で5文字の英数字をチェック）
        import re
        all_csv_files = glob.glob(os.path.join(input_dir, '*.csv'))
        csv_files = []
        for file_path in all_csv_files:
            filename = os.path.basename(file_path)
            code = os.path.splitext(filename)[0]
            # 4-5文字の英数字のファイル名のみを対象とする
            if re.match(r'^[A-Za-z0-9]{4,5}$', code):
                csv_files.append(file_path)
        csv_files = sorted(csv_files)
        filter_type = 'all'
        filter_range = None
        start_date = None
        end_date = None
        
    else:
        # 日付範囲の判定
        start_date, end_date = parse_date_range(range_arg)
        filter_type = None
        filter_range = range_arg
        
        if start_date and end_date:
            print(f"日付範囲モード: {start_date.strftime('%Y-%m-%d')} から {end_date.strftime('%Y-%m-%d')}")
            csv_files = get_csv_files(input_dir)
            filter_type = 'date'
            
        else:
            # 証券コード範囲の判定
            start_code, end_code = parse_code_range(range_arg)
            if start_code and end_code:
                print(f"証券コード範囲モード: {start_code} から {end_code}")
                csv_files = get_csv_files(input_dir, start_code, end_code)
                filter_type = 'code'
            else:
                print(f"エラー: 無効な範囲指定です: {range_arg}", file=sys.stderr)
                print("正しい形式: all, YYYYMMDD-YYYYMMDD または 証券コード-証券コード")
                sys.exit(1)
    
    if not csv_files:
        print("警告: 処理対象のCSVファイルが見つかりません")
        sys.exit(0)
    
    print(f"\n処理対象ファイル数: {len(csv_files)}")
    print("処理を開始します...\n")
    
    # CSVファイルの結合
    combined_data, processed_count = combine_csv_files(csv_files, start_date, end_date)
    
    if not combined_data:
        print("\n警告: 結合するデータがありません")
        sys.exit(0)
    
    # 結果の保存
    output_path = save_combined_csv(combined_data, output_dir, filter_type, filter_range)
    
    # 結果の表示
    print("\n" + "="*50)
    print("処理完了")
    print(f"処理ファイル数: {processed_count}")
    print(f"総レコード数: {len(combined_data)}")
    print(f"出力ファイル: {output_path}")
    print("="*50)


if __name__ == "__main__":
    main()