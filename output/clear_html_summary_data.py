"""
html_summary.dbのデータベース構造を保持したまま、データのみを削除し、ファイルサイズを最適化するスクリプト

使用方法:
python clear_html_summary_data.py

機能:
- html_summaryテーブルの全データを削除
- VACUUMコマンドでデータベースを最適化（ファイルサイズ削減）
- 削除前後のファイルサイズ比較表示
- 削除前後の空きページ数表示

注意:
- このスクリプトは全データを削除します
- テーブル構造（カラム、インデックス等）は保持されます
- バックアップが必要な場合は事前に作成してください
- VACUUMにより大幅なファイルサイズ削減が期待できます
"""

import sqlite3
import time
import os

def get_file_size_mb(file_path):
    """ファイルサイズをMB単位で取得"""
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return size_mb, size_bytes
    return 0, 0

def clear_html_summary_data():
    """html_summaryテーブルのデータのみを削除し、ファイルサイズを最適化する"""
    
    # データベースファイルのパス（作業ディレクトリ基準）
    # 他のスクリプトと同様に、"cd output" を前提とした相対パス運用に合わせます。
    db_path = 'html_summary.db'
    
    # データベースファイルの存在確認
    if not os.path.exists(db_path):
        print(f"エラー: データベースファイルが見つかりません: {db_path}")
        return False
    
    try:
        # 削除前のファイルサイズ確認
        before_size_mb, before_size_bytes = get_file_size_mb(db_path)
        print(f'削除前ファイルサイズ: {before_size_mb:.2f} MB ({before_size_bytes:,} bytes)')
        
        print('データ削除開始...')
        start_time = time.time()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 削除前のデータ件数確認
        cursor.execute('SELECT COUNT(*) FROM html_summary')
        before_count = cursor.fetchone()[0]
        print(f'削除前データ件数: {before_count:,}件')
        
        # データ削除実行
        cursor.execute('DELETE FROM html_summary')
        conn.commit()
        
        # 削除後のデータ件数確認
        cursor.execute('SELECT COUNT(*) FROM html_summary')
        after_count = cursor.fetchone()[0]
        print(f'削除後データ件数: {after_count:,}件')
        
        # VACUUM実行前の状態確認
        cursor.execute('PRAGMA freelist_count')
        free_pages_before = cursor.fetchone()[0]
        print(f'VACUUM実行前の空きページ数: {free_pages_before:,}')
        
        # VACUUMでデータベース最適化
        print('データベース最適化中（VACUUM）...')
        vacuum_start = time.time()
        cursor.execute('VACUUM')
        vacuum_end = time.time()
        print(f'VACUUM処理時間: {vacuum_end - vacuum_start:.2f}秒')
        
        # VACUUM実行後の状態確認
        cursor.execute('PRAGMA freelist_count')
        free_pages_after = cursor.fetchone()[0]
        print(f'VACUUM実行後の空きページ数: {free_pages_after:,}')
        
        # テーブル構造が保持されているか確認
        cursor.execute('PRAGMA table_info(html_summary)')
        columns = cursor.fetchall()
        print(f'テーブル構造: {len(columns)}個のカラムが保持されています')
        
        conn.close()
        
        # 削除後のファイルサイズ確認
        after_size_mb, after_size_bytes = get_file_size_mb(db_path)
        print(f'削除後ファイルサイズ: {after_size_mb:.2f} MB ({after_size_bytes:,} bytes)')
        
        # ファイルサイズ削減効果を表示
        if before_size_bytes > 0:
            reduction_bytes = before_size_bytes - after_size_bytes
            reduction_percent = (reduction_bytes / before_size_bytes) * 100
            print(f'ファイルサイズ削減: {reduction_bytes / (1024 * 1024):.2f} MB ({reduction_percent:.2f}% 削減)')
        
        end_time = time.time()
        print(f'総処理時間: {end_time - start_time:.2f}秒')
        print('データ削除・最適化完了')
        
        return True
        
    except sqlite3.Error as e:
        print(f'データベースエラー: {e}')
        return False
    except Exception as e:
        print(f'予期しないエラー: {e}')
        return False

if __name__ == "__main__":
    # 実行確認
    response = input("html_summaryテーブルの全データを削除します。続行しますか？ (yes/no): ")
    if response.lower() in ['yes', 'y']:
        success = clear_html_summary_data()
        if success:
            print("正常に完了しました。")
        else:
            print("エラーが発生しました。")
    else:
        print("処理をキャンセルしました。")
