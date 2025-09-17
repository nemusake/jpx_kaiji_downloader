#!/usr/bin/env python3
"""
HTML Summary CSVファイルをSQLiteデータベースにインポートするプログラム

このプログラムは、html_summary.csvファイルを読み込み、
既存のhtml_summary.dbデータベースに重複チェックを行いながらデータを追加します。
Python標準ライブラリのみを使用したポータブルな実装です。
"""

"""
実行コマンド
python3  import_html_summary.py
"""


import sqlite3
import csv
import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ログ設定
log_filename = f'import_html_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HtmlSummaryImporter:
    """HTML SummaryデータのCSVからデータベースへのインポーター"""
    
    def __init__(self, csv_path: str = 'html_summary.csv', 
                 db_path: str = 'html_summary.db',
                 batch_size: int = 1000):
        """
        初期化
        
        Args:
            csv_path: CSVファイルのパス
            db_path: SQLiteデータベースのパス
            batch_size: バッチ処理のサイズ
        """
        self.csv_path = csv_path
        self.db_path = db_path
        self.batch_size = batch_size
        self.conn = None
        self.cursor = None
        
        # 統計情報
        self.stats = {
            'total_rows': 0,
            'inserted': 0,
            'skipped': 0,
            'errors': 0
        }
        
    def validate_files(self) -> bool:
        """必要なファイルの存在を確認"""
        if not os.path.exists(self.csv_path):
            logger.error(f"CSVファイルが見つかりません: {self.csv_path}")
            return False
            
        if not os.path.exists(self.db_path):
            logger.error(f"データベースファイルが見つかりません: {self.db_path}")
            return False
            
        # CSVファイルのサイズを確認
        csv_size = os.path.getsize(self.csv_path)
        logger.info(f"CSVファイルサイズ: {csv_size:,} bytes")
        
        return True
        
    def connect_db(self) -> bool:
        """データベースに接続"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"データベースに接続しました: {self.db_path}")
            
            # テーブルの存在確認
            self.cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='html_summary'
            """)
            if not self.cursor.fetchone():
                logger.error("html_summaryテーブルが存在しません")
                return False
                
            # 既存データ件数を確認
            self.cursor.execute("SELECT COUNT(*) FROM html_summary")
            existing_count = self.cursor.fetchone()[0]
            logger.info(f"既存データ件数: {existing_count:,}")
            
            # インデックスの作成（高速化のため）
            self._create_index()
            
            return True
            
        except sqlite3.Error as e:
            logger.error(f"データベース接続エラー: {e}")
            return False
            
    def _create_index(self):
        """重複チェック用のインデックスを作成（存在しない場合）"""
        try:
            # 既存のインデックスを削除（5カラムのみの古いインデックス）
            self.cursor.execute("DROP INDEX IF EXISTS idx_duplicate_check")
            
            # 主要カラムで新しいインデックスを作成（全カラムは多すぎるので主要なものに絞る）
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_full_duplicate_check
                ON html_summary(date, code, fiscal_year_end, quarterly_period, factor_tag, filing_date, company_name)
            """)
            self.conn.commit()
            logger.info("重複チェック用インデックスを確認/作成しました（全カラム対応版）")
        except sqlite3.Error as e:
            logger.warning(f"インデックス作成時の警告: {e}")
            
    def check_duplicate(self, row: Dict[str, str]) -> bool:
        """
        重複チェック（全カラムが一致する場合のみ重複とみなす）
        
        Args:
            row: チェックする行データ
            
        Returns:
            重複している場合True
        """
        # quarterly_periodを整数に変換（比較のため）
        quarterly_period = None
        if row['quarterly_period'] and row['quarterly_period'].strip():
            try:
                quarterly_period = int(row['quarterly_period'])
            except ValueError:
                pass
        
        # 全カラムでの重複チェック（IS演算子を使用してNULL値も正確に比較）
        query = """
            SELECT 1 FROM html_summary 
            WHERE date IS ? 
            AND filing_date IS ?
            AND code IS ? 
            AND company_name IS ?
            AND fiscal_year_end IS ? 
            AND quarterly_period IS ? 
            AND factor_tag IS ?
            AND factor_jp IS ?
            AND value IS ?
            AND has_value IS ?
            AND is_nil IS ?
            AND data_type IS ?
            LIMIT 1
        """
        
        value_param = row['value'] if row['value'] else None
        params = (
            row['date'],
            row['filing_date'],
            row['code'],
            row['company_name'],
            row['fiscal_year_end'],
            quarterly_period,
            row['factor_tag'],
            row['factor_jp'],
            value_param,
            row['has_value'],
            row['is_nil'],
            row['data_type']
        )
        
        self.cursor.execute(query, params)
        return self.cursor.fetchone() is not None
        
    def prepare_row_data(self, row: Dict[str, str]) -> Optional[Tuple]:
        """
        行データを挿入用に準備
        
        Args:
            row: 元の行データ
            
        Returns:
            挿入用のタプル、エラーの場合None
        """
        try:
            # quarterly_periodを整数に変換
            quarterly_period = None
            if row['quarterly_period'] and row['quarterly_period'].strip():
                try:
                    quarterly_period = int(row['quarterly_period'])
                except ValueError:
                    logger.warning(f"quarterly_periodの変換エラー: {row['quarterly_period']}")
                    
            # valueを適切な型に変換
            value = row['value']
            if row['data_type'] == 'empty' or not value:
                value = None
            elif row['data_type'] == 'value':
                # 数値の可能性があるものは試みる
                try:
                    if '.' in str(value):
                        value = float(value)
                    else:
                        value = int(value)
                except (ValueError, TypeError):
                    # 文字列のままにする
                    pass
                    
            return (
                row['date'],
                row['filing_date'],
                row['code'],
                row['company_name'],
                row['fiscal_year_end'],
                quarterly_period,
                row['factor_tag'],
                row['factor_jp'],
                value,
                row['has_value'],
                row['is_nil'],
                row['data_type']
            )
            
        except Exception as e:
            logger.error(f"データ準備エラー: {e}, 行データ: {row}")
            return None
            
    def import_batch(self, batch: List[Dict[str, str]]) -> int:
        """
        バッチ単位でデータをインポート
        
        Args:
            batch: インポートする行のリスト
            
        Returns:
            挿入された行数
        """
        inserted = 0
        insert_query = """
            INSERT INTO html_summary (
                date, filing_date, code, company_name, 
                fiscal_year_end, quarterly_period, factor_tag, factor_jp,
                value, has_value, is_nil, data_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        for row in batch:
            try:
                # 重複チェック
                if self.check_duplicate(row):
                    self.stats['skipped'] += 1
                    continue
                    
                # データ準備
                data = self.prepare_row_data(row)
                if data is None:
                    self.stats['errors'] += 1
                    continue
                    
                # 挿入
                self.cursor.execute(insert_query, data)
                inserted += 1
                self.stats['inserted'] += 1
                
            except sqlite3.Error as e:
                logger.error(f"挿入エラー: {e}, 行番号: {self.stats['total_rows']}")
                self.stats['errors'] += 1
                
        return inserted
        
    def import_csv(self) -> bool:
        """
        CSVファイルをインポート
        
        Returns:
            成功した場合True
        """
        try:
            # BOM付きUTF-8に対応
            encoding = 'utf-8-sig'
            
            with open(self.csv_path, 'r', encoding=encoding) as csvfile:
                # カンマ区切りを明示的に指定
                reader = csv.DictReader(csvfile, delimiter=',')
                
                # 必要なカラムの存在確認
                first_row = next(reader, None)
                if not first_row:
                    logger.error("CSVファイルが空です")
                    return False
                    
                required_columns = [
                    'date', 'filing_date', 'code', 'company_name',
                    'fiscal_year_end', 'quarterly_period', 'factor_tag',
                    'factor_jp', 'value', 'has_value', 'is_nil', 'data_type'
                ]
                
                missing_columns = [col for col in required_columns if col not in first_row]
                if missing_columns:
                    logger.error(f"必要なカラムが不足: {missing_columns}")
                    return False
                    
                # ファイルを最初から読み直し
                csvfile.seek(0)
                reader = csv.DictReader(csvfile, delimiter=',')
                
                batch = []
                start_time = time.time()
                last_report_time = start_time
                
                logger.info("インポート処理を開始します...")
                
                for row in reader:
                    self.stats['total_rows'] += 1
                    batch.append(row)
                    
                    # バッチサイズに達したら処理
                    if len(batch) >= self.batch_size:
                        self.import_batch(batch)
                        self.conn.commit()
                        batch = []
                        
                        # 進捗報告（5秒ごと）
                        current_time = time.time()
                        if current_time - last_report_time >= 5:
                            self._report_progress(start_time)
                            last_report_time = current_time
                            
                # 残りのバッチを処理
                if batch:
                    self.import_batch(batch)
                    self.conn.commit()
                    
                # 最終報告
                self._report_progress(start_time)
                
                return True
                
        except Exception as e:
            logger.error(f"CSVインポートエラー: {e}")
            if self.conn:
                self.conn.rollback()
            return False
            
    def _report_progress(self, start_time: float):
        """進捗状況を報告"""
        elapsed = time.time() - start_time
        rate = self.stats['total_rows'] / elapsed if elapsed > 0 else 0
        
        logger.info(
            f"進捗: 処理済み {self.stats['total_rows']:,} 行 "
            f"(新規 {self.stats['inserted']:,}, "
            f"スキップ {self.stats['skipped']:,}, "
            f"エラー {self.stats['errors']:,}) "
            f"- {rate:.0f} 行/秒"
        )
        
    def close(self):
        """データベース接続を閉じる"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("データベース接続を閉じました")
        
    def run(self) -> bool:
        """
        インポート処理を実行
        
        Returns:
            成功した場合True
        """
        logger.info("=" * 50)
        logger.info("HTML Summary インポートプログラム")
        logger.info("=" * 50)
        
        # ファイル確認
        if not self.validate_files():
            return False
            
        # データベース接続
        if not self.connect_db():
            return False
            
        try:
            # インポート実行
            success = self.import_csv()
            
            if success:
                logger.info("=" * 50)
                logger.info("インポート完了")
                logger.info(f"処理行数: {self.stats['total_rows']:,}")
                logger.info(f"新規追加: {self.stats['inserted']:,}")
                logger.info(f"重複スキップ: {self.stats['skipped']:,}")
                logger.info(f"エラー: {self.stats['errors']:,}")
                logger.info("=" * 50)
            else:
                logger.error("インポートに失敗しました")
                
            return success
            
        finally:
            self.close()


def main():
    """メイン処理"""
    importer = HtmlSummaryImporter()
    
    try:
        success = importer.run()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.warning("\n処理が中断されました")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()