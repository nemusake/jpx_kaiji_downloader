#!/usr/bin/env python3
"""
全matomeファイル一括XBRL解析ツール
全決算短信ファイルからXBRLタグを抽出し、財務指標の網羅的カタログを作成
"""

import os
import re
import csv
import codecs
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any, Set
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd

class BulkXBRLAnalyzer:
    """全matomeファイルのXBRL一括解析クラス"""
    
    def __init__(self, matome_dir: str, jpen_list_path: str = None):
        self.matome_dir = Path(matome_dir)
        self.jpen_list_path = jpen_list_path
        self.jpen_mapping = {}  # XBRL tag -> {japanese_name, english_name} のマッピング
        self.all_tags = defaultdict(lambda: {
            'xbrl_tag': '',
            'japanese_name': '',  
            'english_name': '',   
            'category': '',
            'accounting_standard': '',
            'description': '',
            'sample_values': [],
            'units': set(),
            'file_count': 0,
            'total_occurrences': 0
        })
        self.total_files = 0
        self.processed_files = 0
        self.error_files = []
        
        # JPEN_listの読み込み
        if self.jpen_list_path:
            self._load_jpen_mapping()
    
    def _load_jpen_mapping(self):
        """JPEN_listファイルを読み込んでマッピングを作成"""
        try:
            jpen_path = Path(self.jpen_list_path)
            if not jpen_path.exists():
                print(f"警告: JPEN_listファイルが見つかりません: {self.jpen_list_path}")
                return
                
            print(f"JPEN_list読み込み中: {jpen_path.name}")
            
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
                        
            print(f"JPEN_listから{len(self.jpen_mapping)}個のマッピングを読み込みました")
            
        except Exception as e:
            print(f"エラー: JPEN_listの読み込みに失敗しました: {e}")
        
    def analyze_all_files(self):
        """全ファイルの一括解析"""
        print("matomeフォルダ内のファイル一覧取得中...")
        
        # HTMLファイルのリストアップ
        html_files = list(self.matome_dir.glob("*.htm"))
        self.total_files = len(html_files)
        
        print(f"発見されたHTMLファイル: {self.total_files}個")
        
        if self.total_files == 0:
            print("エラー: HTMLファイルが見つかりません")
            return
            
        # プログレスバー付きで全ファイル処理
        with tqdm(html_files, desc="ファイル解析中") as pbar:
            for file_path in pbar:
                try:
                    pbar.set_description(f"処理中: {file_path.name[:50]}")
                    self._analyze_single_file(file_path)
                    self.processed_files += 1
                except Exception as e:
                    self.error_files.append((str(file_path), str(e)))
                    print(f"\nエラー: {file_path.name} - {e}")
                    
        print(f"\n解析完了:")
        print(f"  処理成功: {self.processed_files}ファイル")
        print(f"  エラー: {len(self.error_files)}ファイル")
        print(f"  発見されたユニークXBRLタグ: {len(self.all_tags)}個")
        
    def _analyze_single_file(self, file_path: Path):
        """個別ファイルの解析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # BeautifulSoupでXML解析
            soup = BeautifulSoup(content, 'lxml-xml')
            
            # 会計基準の判定
            accounting_standard = self._determine_accounting_standard(file_path.name, content)
            
            # XBRLタグの抽出
            xbrl_tags = self._extract_xbrl_tags(soup)
            
            # 各タグの情報を集計
            for tag_info in xbrl_tags:
                self._aggregate_tag_info(tag_info, accounting_standard, file_path.name)
                
        except Exception as e:
            raise Exception(f"ファイル解析エラー: {e}")
            
    def _extract_xbrl_tags(self, soup) -> List[Dict[str, Any]]:
        """XBRLタグの抽出"""
        tags = []
        
        # ix:nonNumericタグとix:nonFractionタグを抽出
        non_numeric_tags = soup.find_all(re.compile(r'.*nonNumeric', re.I))
        non_fraction_tags = soup.find_all(re.compile(r'.*nonFraction', re.I))
        
        all_xbrl_tags = non_numeric_tags + non_fraction_tags
        
        for tag in all_xbrl_tags:
            tag_name = tag.get('name', '')
            if not tag_name:
                continue
                
            # タグ情報の抽出
            tag_info = {
                'xbrl_tag': tag_name,
                'value': tag.get_text(strip=True) if tag else '',
                'context_ref': tag.get('contextRef', tag.get('contextref', '')),
                'unit_ref': tag.get('unitRef', tag.get('unitref', '')),
                'format': tag.get('format', ''),
                'decimals': tag.get('decimals', ''),
                'is_nil': tag.get(re.compile(r'.*nil', re.I)) == 'true'
            }
            
            tags.append(tag_info)
            
        return tags
        
    def _determine_accounting_standard(self, filename: str, content: str) -> str:
        """会計基準の判定"""
        if 'IFRS' in filename.upper() or 'ＩＦＲＳ' in filename:
            return 'IFRS'
        elif '日本基準' in filename or '日本基準' in content[:1000]:
            return '日本基準'
        else:
            return '日本基準'  # デフォルト
            
    def _aggregate_tag_info(self, tag_info: Dict[str, Any], accounting_standard: str, filename: str):
        """タグ情報の集計"""
        xbrl_tag = tag_info['xbrl_tag']
        
        # 初回登録時の処理
        if self.all_tags[xbrl_tag]['xbrl_tag'] == '':
            self.all_tags[xbrl_tag]['xbrl_tag'] = xbrl_tag
            
            # JPEN_listからの情報設定（優先）
            if xbrl_tag in self.jpen_mapping:
                self.all_tags[xbrl_tag]['japanese_name'] = self.jpen_mapping[xbrl_tag]['japanese_name']
                self.all_tags[xbrl_tag]['english_name'] = self.jpen_mapping[xbrl_tag]['english_name']
                self.all_tags[xbrl_tag]['description'] = self.jpen_mapping[xbrl_tag]['description']
                # JPEN_listのcategoryが存在する場合は優先使用
                jpen_category = self.jpen_mapping[xbrl_tag]['category']
                if jpen_category:
                    self.all_tags[xbrl_tag]['category'] = jpen_category
                else:
                    # JPEN_listにcategoryがない場合は自動分類を使用
                    self.all_tags[xbrl_tag]['category'] = self._categorize_tag(xbrl_tag)
            else:
                # JPEN_listにないタグは自動分類を使用
                self.all_tags[xbrl_tag]['category'] = self._categorize_tag(xbrl_tag)
            
        # 会計基準の設定（複数ある場合は併記）
        current_standard = self.all_tags[xbrl_tag]['accounting_standard']
        if accounting_standard not in current_standard:
            if current_standard:
                self.all_tags[xbrl_tag]['accounting_standard'] = f"{current_standard}, {accounting_standard}"
            else:
                self.all_tags[xbrl_tag]['accounting_standard'] = accounting_standard
                
        # サンプル値の収集（最初の5個まで）
        value = tag_info['value']
        if value and not tag_info['is_nil']:
            sample_values = self.all_tags[xbrl_tag]['sample_values']
            if len(sample_values) < 5 and value not in sample_values:
                sample_values.append(value)
                
        # 単位情報の収集
        unit_ref = tag_info['unit_ref']
        if unit_ref:
            self.all_tags[xbrl_tag]['units'].add(unit_ref)
            
        # 出現回数の集計
        self.all_tags[xbrl_tag]['total_occurrences'] += 1
        
        # ファイル数の追跡（重複チェック用にset使用）
        if 'file_set' not in self.all_tags[xbrl_tag]:
            self.all_tags[xbrl_tag]['file_set'] = set()
        self.all_tags[xbrl_tag]['file_set'].add(filename)
        
    def _categorize_tag(self, xbrl_tag: str) -> str:
        """XBRLタグのカテゴリ分類"""
        tag_lower = xbrl_tag.lower()
        
        # 基本情報系
        if any(keyword in tag_lower for keyword in [
            'company', 'securities', 'filing', 'document', 'representative',
            'inquiries', 'tel', 'url', 'stockexchange'
        ]):
            return '基本情報'
            
        # PL系（損益計算書）
        if any(keyword in tag_lower for keyword in [
            'sales', 'revenue', 'income', 'profit', 'loss', 'expense',
            'cost', 'operating', 'ordinary', 'netincome'
        ]):
            return 'PL'
            
        # BS系（貸借対照表）
        if any(keyword in tag_lower for keyword in [
            'assets', 'liabilities', 'equity', 'capital', 'debt',
            'cash', 'inventory', 'property'
        ]):
            return 'BS'
            
        # CF系（キャッシュフロー）
        if any(keyword in tag_lower for keyword in [
            'cashflow', 'financing', 'investing', 'operating'
        ]) and 'cash' in tag_lower:
            return 'CF'
            
        # その他・指標系
        if any(keyword in tag_lower for keyword in [
            'ratio', 'rate', 'change', 'pershare', 'dividend'
        ]):
            return '指標'
            
        return 'その他'
        
    def _calculate_statistics(self):
        """統計情報の計算"""
        for tag_data in self.all_tags.values():
            # ファイル数の確定
            if 'file_set' in tag_data:
                tag_data['file_count'] = len(tag_data['file_set'])
                del tag_data['file_set']  # メモリ節約のため削除
                
            # 出現詳細の作成（ファイル出現数/総ファイル数）
            tag_data['occurrence_detail'] = f"{tag_data['file_count']}/{self.processed_files}"
            
            # 単位情報を文字列に変換
            tag_data['unit'] = ', '.join(sorted(tag_data['units'])) if tag_data['units'] else ''
            
            # サンプル値を文字列に変換
            tag_data['sample_value'] = ', '.join(tag_data['sample_values'][:3]) if tag_data['sample_values'] else ''
            
    def export_to_csv(self, output_path: str):
        """CSV出力"""
        print("統計情報計算中...")
        self._calculate_statistics()
        
        print("CSV出力中...")
        
        # データの準備
        csv_data = []
        for tag_data in self.all_tags.values():
            csv_row = {
                'xbrl_tag': tag_data['xbrl_tag'],
                'japanese_name': tag_data['japanese_name'],  # 空欄（後で埋める）
                'english_name': tag_data['english_name'],    # 空欄（後で埋める）
                'category': tag_data['category'],
                'accounting_standard': tag_data['accounting_standard'],
                'sample_value': tag_data['sample_value'],
                'unit': tag_data['unit'],
                'description': tag_data.get('description', ''),  # JPEN_listから設定
                'occurrence_detail': tag_data['occurrence_detail']
            }
            csv_data.append(csv_row)
            
        # 出現ファイル数でソート（降順）
        csv_data.sort(key=lambda x: int(x['occurrence_detail'].split('/')[0]), reverse=True)
        
        # UTF-8 BOM付きCSVで出力
        with codecs.open(output_path, 'w', encoding='utf-8-sig') as csvfile:
            fieldnames = [
                'xbrl_tag', 'japanese_name', 'english_name', 'category',
                'accounting_standard', 'sample_value', 'unit', 'description',
                'occurrence_detail'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
            
        print(f"CSV出力完了: {output_path}")
        print(f"総レコード数: {len(csv_data)}")
        
    def print_summary(self):
        """解析結果サマリーの表示"""
        print("\n" + "="*60)
        print("一括XBRL解析結果サマリー")
        print("="*60)
        print(f"処理ファイル数: {self.processed_files}")
        print(f"エラーファイル数: {len(self.error_files)}")
        print(f"ユニークXBRLタグ数: {len(self.all_tags)}")
        
        # カテゴリ別集計
        category_count = Counter()
        accounting_standard_count = Counter()
        
        for tag_data in self.all_tags.values():
            category_count[tag_data['category']] += 1
            # 複数会計基準対応
            standards = [s.strip() for s in tag_data['accounting_standard'].split(',')]
            for standard in standards:
                accounting_standard_count[standard] += 1
                
        print(f"\n[カテゴリ別集計]")
        for category, count in category_count.most_common():
            print(f"  {category}: {count}タグ")
            
        print(f"\n[会計基準別集計]")
        for standard, count in accounting_standard_count.most_common():
            print(f"  {standard}: {count}タグ")
            
        # 高頻出タグ表示は省略
            
        if self.error_files:
            print(f"\n[エラーファイル]")
            for filepath, error in self.error_files[:5]:  # 最初の5件のみ表示
                filename = Path(filepath).name
                print(f"  {filename}: {error}")
            if len(self.error_files) > 5:
                print(f"  ... 他 {len(self.error_files) - 5}件")


if __name__ == "__main__":
    # 実行
    matome_dir = "/home/jptyf/workspace/jpx_kaiji_service/downloads/matome"
    output_csv = "/home/jptyf/workspace/jpx_kaiji_service/xbrl_financial_indicators.csv"
    jpen_list_csv = "/home/jptyf/workspace/jpx_kaiji_service/xbrl_financial_indicators_JPEN_list.csv"
    
    analyzer = BulkXBRLAnalyzer(matome_dir, jpen_list_csv)
    analyzer.analyze_all_files()
    analyzer.print_summary()
    analyzer.export_to_csv(output_csv)