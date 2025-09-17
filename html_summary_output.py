#!/usr/bin/env python3
"""
html_summary_output.py
東証上場企業の決算短信HTMLファイルから時系列データを抽出し、
証券コードごとにCSVファイルを出力するプログラム
"""

"""

実行コマンド

単一証券コードの処理
uv run python html_summary_output.py 13010

codelist.csvを使用した一括処理
uv run python html_summary_output.py codelist

全銘柄一括処理
uv run python html_summary_output.py all

# テスト用に任意銘柄数を処理
uv run python html_summary_output.py all limit=10

"""

import os
import re
import sys
import csv
import codecs
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

class XBRLTimeSeriesExtractor:
    """XBRLデータを時系列で抽出するクラス"""
    
    def __init__(self, securities_code: str, html_summary_dir: str, indicators_csv_path: str):
        """
        初期化
        
        Args:
            securities_code: 証券コード（5桁）
            html_summary_dir: html_summaryフォルダのパス
            indicators_csv_path: xbrl_financial_indicators.csvのパス
        """
        self.securities_code = securities_code
        self.html_summary_dir = Path(html_summary_dir)
        self.indicators_csv_path = Path(indicators_csv_path)
        self.target_dir = self.html_summary_dir / securities_code
        
        # XBRLタグと日本語名のマッピング
        self.tag_jp_mapping = {}
        
        # 基本情報タグ（これらは別扱い）
        self.basic_info_tags = {
            'tse-ed-t:FilingDate',
            'tse-ed-t:SecuritiesCode', 
            'tse-ed-t:CompanyName',
            'tse-ed-t:FiscalYearEnd',
            'tse-ed-t:QuarterlyPeriod'
        }
        
        # 結果を格納するリスト
        self.results = []
        
        # エラーファイルのリスト
        self.error_files = []
        
    def load_indicators_mapping(self):
        """xbrl_financial_indicators.csvからタグと日本語名のマッピングを読み込む"""
        try:
            if not self.indicators_csv_path.exists():
                print(f"警告: {self.indicators_csv_path} が見つかりません。日本語名なしで処理を続けます。")
                return
                
            print(f"指標マッピングを読み込み中: {self.indicators_csv_path}")
            
            # UTF-8 BOM付きで読み込み
            with open(self.indicators_csv_path, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    xbrl_tag = row.get('xbrl_tag', '').strip()
                    japanese_name = row.get('japanese_name', '').strip()
                    if xbrl_tag:
                        self.tag_jp_mapping[xbrl_tag] = japanese_name
                        
            print(f"  {len(self.tag_jp_mapping)}個のタグマッピングを読み込みました")
            
        except Exception as e:
            print(f"エラー: 指標マッピングの読み込みに失敗しました: {e}")
            
    def validate_securities_code(self) -> bool:
        """証券コードの妥当性をチェック"""
        # 5桁の英数字（数字とアルファベットの任意の組み合わせ）チェック
        if not re.match(r'^[0-9A-Z]{5}$', self.securities_code):
            print(f"エラー: 証券コードは5桁の英数字である必要があります: {self.securities_code}")
            return False
            
        # 対象ディレクトリの存在チェック
        if not self.target_dir.exists():
            print(f"エラー: 指定された証券コードのディレクトリが存在しません: {self.target_dir}")
            return False
            
        return True
        
    def get_html_files(self) -> List[Path]:
        """対象ディレクトリからHTMLファイルを取得し、日付順にソート"""
        html_files = list(self.target_dir.glob("*.htm"))
        
        if not html_files:
            print(f"警告: {self.target_dir} にHTMLファイルが見つかりません")
            return []
            
        # ファイル名の日付でソート（YYYY-MM-DD形式）
        def extract_date(file_path):
            filename = file_path.name
            date_match = re.match(r'^(\d{4}-\d{2}-\d{2})', filename)
            if date_match:
                return date_match.group(1)
            return '9999-99-99'  # 日付が取得できない場合は最後にソート
            
        html_files.sort(key=extract_date)
        
        print(f"  {len(html_files)}個のHTMLファイルを発見")
        return html_files
        
    def extract_xbrl_data(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """単一のHTMLファイルからXBRLデータを抽出"""
        try:
            # ファイル名から開示日を取得
            filename = file_path.name
            date_match = re.match(r'^(\d{4}-\d{2}-\d{2})', filename)
            if not date_match:
                print(f"  警告: ファイル名から日付を取得できません: {filename}")
                return None
                
            disclosure_date = date_match.group(1)
            
            # HTMLファイルを読み込み
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # BeautifulSoupで解析（lxmlパーサーを使用）
            soup = BeautifulSoup(content, 'lxml')
            
            # 基本情報の抽出
            basic_info = {
                'date': disclosure_date,
                'filing_date': '',
                'code': '',
                'company_name': '',
                'fiscal_year_end': '',
                'quarterly_period': ''
            }
            
            # XBRLタグを抽出
            all_tags = {}
            
            # ix:nonNumericタグとix:nonFractionタグを抽出
            non_numeric_tags = soup.find_all(re.compile(r'.*nonNumeric', re.I))
            non_fraction_tags = soup.find_all(re.compile(r'.*nonFraction', re.I))
            
            for tag in non_numeric_tags + non_fraction_tags:
                tag_name = tag.get('name', '')
                if not tag_name:
                    continue
                    
                # nil値チェック（修正版）
                is_nil = False
                for attr_name, attr_value in tag.attrs.items():
                    if attr_name.endswith(':nil') or attr_name == 'nil':
                        if attr_value == 'true':
                            is_nil = True
                            break
                
                if is_nil:
                    tag_value = ''
                else:
                    tag_value = tag.get_text(strip=True) if tag else ''
                    # sign属性がマイナスの場合、マイナス記号を付ける
                    if tag and tag.get('sign') == '-' and tag_value:
                        tag_value = '-' + tag_value
                    
                # 基本情報タグの処理
                if tag_name == 'tse-ed-t:FilingDate':
                    basic_info['filing_date'] = tag_value
                elif tag_name == 'tse-ed-t:SecuritiesCode':
                    basic_info['code'] = tag_value
                elif tag_name == 'tse-ed-t:CompanyName':
                    basic_info['company_name'] = tag_value
                elif tag_name == 'tse-ed-t:FiscalYearEnd':
                    basic_info['fiscal_year_end'] = tag_value
                elif tag_name == 'tse-ed-t:QuarterlyPeriod':
                    basic_info['quarterly_period'] = tag_value
                else:
                    # その他のタグは財務指標として保存
                    if tag_name not in self.basic_info_tags:
                        # nil値でない有効な値を優先保持
                        if tag_name not in all_tags:
                            # タグが存在しない場合は保存（nil情報も含む）
                            all_tags[tag_name] = {
                                'value': tag_value,
                                'is_nil': is_nil
                            }
                        elif all_tags[tag_name]['value'] == '':
                            # 既存値が空白の場合、新しい値が有効なら上書き
                            if tag_value != '' and not is_nil:
                                all_tags[tag_name] = {
                                    'value': tag_value,
                                    'is_nil': is_nil
                                }
                        
            return {
                'basic_info': basic_info,
                'tags': all_tags
            }
            
        except Exception as e:
            print(f"  エラー: ファイル解析失敗 {file_path.name}: {e}")
            self.error_files.append((str(file_path), str(e)))
            return None
            
    def process_all_files(self):
        """全HTMLファイルを処理"""
        html_files = self.get_html_files()
        
        if not html_files:
            return
            
        print(f"\n{self.securities_code}の決算短信を処理中...")
        
        for file_path in tqdm(html_files, desc="ファイル処理中"):
            data = self.extract_xbrl_data(file_path)
            
            if data:
                basic_info = data['basic_info']
                tags = data['tags']
                
                # 各タグについてCSV行を作成
                for tag_name, tag_info in tags.items():
                    # タグ情報を取得
                    tag_value = tag_info['value']
                    is_nil = tag_info['is_nil']
                    
                    # 日本語名を取得
                    japanese_name = self.tag_jp_mapping.get(tag_name, '')
                    
                    # 追加メタデータの算出
                    has_value = bool(tag_value and tag_value.strip())
                    
                    # データ種別の判定
                    if is_nil:
                        data_type = 'nil'
                    elif not has_value and not is_nil:
                        data_type = 'empty'  # テキストが空だがnil属性もない
                    else:
                        data_type = 'value'
                    
                    # 改良版CSV行を作成
                    row = {
                        'date': basic_info['date'],
                        'filing_date': basic_info['filing_date'],
                        'code': basic_info['code'],
                        'company_name': basic_info['company_name'],
                        'fiscal_year_end': basic_info['fiscal_year_end'],
                        'quarterly_period': basic_info['quarterly_period'],
                        'factor_tag': tag_name,
                        'factor_jp': japanese_name,
                        'value': tag_value,
                        'has_value': has_value,
                        'is_nil': is_nil,
                        'data_type': data_type
                    }
                    
                    self.results.append(row)
                    
    def save_to_csv(self, output_path: Optional[str] = None):
        """結果をCSVファイルに保存"""
        if not self.results:
            print("警告: 出力するデータがありません")
            return
            
        if output_path is None:
            # output/html_summary階層に出力
            output_dir = Path(__file__).parent / "output" / "html_summary"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{self.securities_code}.csv"
        else:
            output_path = Path(output_path)
            
        print(f"\nCSVファイルを出力中: {output_path}")
        
        # UTF-8 BOM付きで出力
        with codecs.open(output_path, 'w', encoding='utf-8-sig') as csvfile:
            fieldnames = [
                'date', 'filing_date', 'code', 'company_name',
                'fiscal_year_end', 'quarterly_period',
                'factor_tag', 'factor_jp', 'value',
                'has_value', 'is_nil', 'data_type'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)
            
        print(f"  {len(self.results)}行のデータを出力しました")
        
    def print_summary(self):
        """処理結果のサマリーを表示"""
        print("\n" + "="*60)
        print("処理完了サマリー")
        print("="*60)
        print(f"証券コード: {self.securities_code}")
        print(f"処理ファイル数: {len(self.get_html_files())}") 
        print(f"出力レコード数: {len(self.results)}")
        
        if self.error_files:
            print(f"\nエラーファイル数: {len(self.error_files)}")
            for filepath, error in self.error_files[:5]:
                filename = Path(filepath).name
                print(f"  {filename}: {error}")
            if len(self.error_files) > 5:
                print(f"  ... 他 {len(self.error_files) - 5}件")
                
        # ユニークなfactor_tagの数を表示
        unique_tags = set(row['factor_tag'] for row in self.results)
        print(f"\nユニークな財務指標数: {len(unique_tags)}")
        
        # 期間の範囲を表示
        if self.results:
            dates = sorted(set(row['date'] for row in self.results))
            print(f"データ期間: {dates[0]} 〜 {dates[-1]}")


def process_single_code(securities_code: str, html_summary_dir: Path, indicators_csv_path: Path) -> bool:
    """単一の証券コードを処理
    
    Returns:
        bool: 処理成功時True、失敗時False
    """
    try:
        # エクストラクターの初期化
        extractor = XBRLTimeSeriesExtractor(
            securities_code=securities_code,
            html_summary_dir=html_summary_dir,
            indicators_csv_path=indicators_csv_path
        )
        
        # 証券コードの妥当性チェック
        if not extractor.validate_securities_code():
            return False
            
        # 指標マッピングの読み込み（初回のみ表示）
        extractor.load_indicators_mapping()
        
        # 全ファイルの処理
        extractor.process_all_files()
        
        # CSVファイルに保存
        extractor.save_to_csv()
        
        # サマリーの表示
        extractor.print_summary()
        
        return True
        
    except Exception as e:
        logging.error(f"証券コード {securities_code} の処理中にエラー: {str(e)}")
        print(f"エラー: 証券コード {securities_code} の処理に失敗しました: {str(e)}")
        return False


def process_codelist(codelist_path: Path, html_summary_dir: Path, indicators_csv_path: Path):
    """codelist.csvから全証券コードを処理"""
    
    # ログ設定
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"html_summary_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logging.info("="*60)
    logging.info("codelist.csv一括処理開始")
    logging.info("="*60)
    
    # codelist.csv読み込み
    if not codelist_path.exists():
        logging.error(f"codelist.csvが見つかりません: {codelist_path}")
        print(f"エラー: codelist.csvが見つかりません: {codelist_path}")
        return
        
    try:
        # UTF-8 BOM付きで読み込み
        df = pd.read_csv(codelist_path, encoding='utf-8-sig')
        
        # codeカラムの確認（7カラム目）
        if 'code' not in df.columns:
            logging.error("codeカラムが見つかりません")
            print("エラー: codelist.csvにcodeカラムが見つかりません")
            return
            
        # 証券コードリストを取得（NaNを除外し、文字列に変換）
        codes = df['code'].dropna().astype(str).str.zfill(5).unique()
        
        logging.info(f"処理対象証券コード数: {len(codes)}")
        print(f"\n処理対象証券コード数: {len(codes)}")
        
        # 処理結果の記録
        success_codes = []
        failed_codes = []
        skipped_codes = []
        
        # 各証券コードを処理
        for i, code in enumerate(codes, 1):
            print(f"\n[{i}/{len(codes)}] 証券コード {code} を処理中...")
            logging.info(f"[{i}/{len(codes)}] 証券コード {code} の処理開始")
            
            # html_summaryフォルダの存在チェック
            code_dir = html_summary_dir / code
            if not code_dir.exists():
                logging.warning(f"証券コード {code} のディレクトリが存在しません: {code_dir}")
                print(f"  スキップ: ディレクトリが存在しません")
                skipped_codes.append(code)
                continue
                
            # 処理実行
            if process_single_code(code, html_summary_dir, indicators_csv_path):
                success_codes.append(code)
                logging.info(f"証券コード {code} の処理完了")
            else:
                failed_codes.append(code)
                logging.error(f"証券コード {code} の処理失敗")
                
        # 最終サマリー
        print("\n" + "="*60)
        print("一括処理完了サマリー")
        print("="*60)
        print(f"総証券コード数: {len(codes)}")
        print(f"成功: {len(success_codes)}")
        print(f"失敗: {len(failed_codes)}")
        print(f"スキップ（ディレクトリなし）: {len(skipped_codes)}")
        
        logging.info("="*60)
        logging.info("一括処理完了")
        logging.info(f"成功: {success_codes}")
        logging.info(f"失敗: {failed_codes}")
        logging.info(f"スキップ: {skipped_codes}")
        logging.info(f"ログファイル: {log_file}")
        
        print(f"\nログファイル: {log_file}")
        
    except Exception as e:
        logging.error(f"codelist.csv処理中にエラー: {str(e)}")
        print(f"エラー: codelist.csv処理中にエラーが発生しました: {str(e)}")


def process_all_codes(html_summary_dir: Path, indicators_csv_path: Path, limit: int = None):
    """downloads/html_summaryフォルダの全証券コードを処理"""
    
    # ログ設定
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"html_summary_output_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    limit_text = f"（limit={limit}）" if limit else ""
    logging.info("="*60)
    logging.info(f"全銘柄一括処理開始{limit_text}")
    logging.info("="*60)
    
    if not html_summary_dir.exists():
        logging.error(f"html_summaryディレクトリが見つかりません: {html_summary_dir}")
        print(f"エラー: html_summaryディレクトリが見つかりません: {html_summary_dir}")
        return
    
    # 証券コードディレクトリを取得
    code_dirs = [d for d in html_summary_dir.iterdir() if d.is_dir()]
    code_dirs.sort()  # ソート
    
    # limitが指定されている場合は制限
    if limit:
        code_dirs = code_dirs[:limit]
        logging.info(f"limit={limit} により {len(code_dirs)} 銘柄に制限")
    
    logging.info(f"処理対象証券コード数: {len(code_dirs)}")
    print(f"\n処理対象証券コード数: {len(code_dirs)}{limit_text}")
    
    # 処理結果のカウンタ
    success_codes = []
    failed_codes = []
    skipped_codes = []
    
    # 各証券コードを処理
    for i, code_dir in enumerate(code_dirs, 1):
        securities_code = code_dir.name
        
        print(f"\n[{i}/{len(code_dirs)}] 証券コード {securities_code} を処理中...")
        logging.info(f"[{i}/{len(code_dirs)}] 証券コード {securities_code} 開始")
        
        try:
            if process_single_code(securities_code, html_summary_dir, indicators_csv_path):
                success_codes.append(securities_code)
                logging.info(f"証券コード {securities_code} 処理成功")
            else:
                failed_codes.append(securities_code)
                logging.warning(f"証券コード {securities_code} 処理失敗")
                
        except Exception as e:
            failed_codes.append(securities_code)
            logging.error(f"証券コード {securities_code} 処理中に例外: {str(e)}")
            print(f"  エラー: {e}")
    
    # 処理結果サマリー
    print("\n" + "="*60)
    print("全銘柄一括処理完了サマリー")
    print("="*60)
    print(f"総証券コード数: {len(code_dirs)}")
    print(f"成功: {len(success_codes)}")
    print(f"失敗: {len(failed_codes)}")
    
    if failed_codes:
        print(f"失敗した証券コード: {', '.join(failed_codes[:10])}{'...' if len(failed_codes) > 10 else ''}")
    
    logging.info("="*60)
    logging.info("全銘柄一括処理完了")
    logging.info(f"成功: {success_codes}")
    logging.info(f"失敗: {failed_codes}")
    logging.info(f"ログファイル: {log_file}")
    
    print(f"\nログファイル: {log_file}")


def parse_arguments():
    """コマンドライン引数を解析"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  単一証券コード: python html_summary_output.py [証券コード]")
        print("  一括処理: python html_summary_output.py codelist")
        print("  全銘柄処理: python html_summary_output.py all [limit=数値]")
        print("\n例:")
        print("  python html_summary_output.py 13010")
        print("  python html_summary_output.py codelist")
        print("  python html_summary_output.py all")
        print("  python html_summary_output.py all limit=10")
        sys.exit(1)
    
    command = sys.argv[1]
    limit = None
    
    # limit=x オプションの解析
    if len(sys.argv) > 2:
        for arg in sys.argv[2:]:
            if arg.startswith('limit='):
                try:
                    limit = int(arg.split('=')[1])
                    if limit <= 0:
                        print("エラー: limit値は1以上の整数を指定してください")
                        sys.exit(1)
                except ValueError:
                    print("エラー: limit値は整数を指定してください（例: limit=10）")
                    sys.exit(1)
            else:
                print(f"エラー: 不明なオプション: {arg}")
                sys.exit(1)
    
    return command, limit


def main():
    """メイン処理"""
    command, limit = parse_arguments()
    
    # パスの設定
    html_summary_dir = Path(__file__).parent / "downloads" / "html_summary"
    indicators_csv_path = Path(__file__).parent / "xbrl_financial_indicators.csv"
    
    if command.lower() == "codelist":
        if limit:
            print("警告: codelist処理ではlimitオプションは無視されます")
        # codelist.csv一括処理
        codelist_path = Path(__file__).parent / "codelist.csv"
        process_codelist(codelist_path, html_summary_dir, indicators_csv_path)
    elif command.lower() == "all":
        # 全銘柄処理
        process_all_codes(html_summary_dir, indicators_csv_path, limit)
    else:
        if limit:
            print("警告: 単一証券コード処理ではlimitオプションは無視されます")
        # 単一証券コード処理
        securities_code = command
        if process_single_code(securities_code, html_summary_dir, indicators_csv_path):
            print("\n処理が完了しました。")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()