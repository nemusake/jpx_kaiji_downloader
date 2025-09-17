#!/usr/bin/env python3
"""
html_summary.dbから財務データを取得してCSVに出力するスクリプト
"""

"""
実行コマンド
python3 export_html_summary_query.py
"""

import sqlite3
import csv
from datetime import datetime

def export_financial_data():
    """SQLite3データベースから財務データを取得してCSVファイルに出力"""
    
    # SQLクエリ（修正決算を除去：最初の発表データのみを取得）
    query = """
    WITH RankedData AS (
        SELECT
            date,
            code,
            company_name,
            fiscal_year_end,
            quarterly_period,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:NetSales' THEN CAST(value AS NUMERIC) END) AS net_sales,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:NetSalesIFRS' THEN CAST(value AS NUMERIC) END) AS net_salesIFRS,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:OperatingIncome' THEN CAST(value AS NUMERIC) END) AS operatingincome,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:TotalRevenuesAfterDeductingFinancialExpenseUS' THEN CAST(value AS NUMERIC) END) AS financialexpense_us,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:OperatingIncomeUS' THEN CAST(value AS NUMERIC) END) AS operatingincome_us,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:OperatingIncomeIFRS' THEN CAST(value AS NUMERIC) END) AS operatingincome_ifrs,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:OrdinaryIncome' THEN CAST(value AS NUMERIC) END) AS ordinary_income,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:ProfitBeforeTaxIFRS' THEN CAST(value AS NUMERIC) END) AS profitbeforetax_ifrs,    
            MAX(CASE WHEN factor_tag = 'tse-ed-t:NetAssets' THEN CAST(value AS NUMERIC) END) AS net_assets,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:NetAssetsUS' THEN CAST(value AS NUMERIC) END) AS net_assets_us,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:TotalEquityIFRS' THEN CAST(value AS NUMERIC) END) AS totalequity_ifrs,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:CashFlowsFromOperatingActivities' THEN CAST(value AS NUMERIC) END) AS cashflow_o,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:CashFlowsFromInvestingActivities' THEN CAST(value AS NUMERIC) END) AS cashflow_i,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:CashFlowsFromFinancingActivities' THEN CAST(value AS NUMERIC) END) AS cashflow_f,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:CashAndEquivalentsEndOfPeriod' THEN CAST(value AS NUMERIC) END) AS cash_end,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:CashFlowsFromOperatingActivitiesIFRS' THEN CAST(value AS NUMERIC) END) AS cashflow_o_ifrs,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:CashFlowsFromInvestingActivitiesIFRS' THEN CAST(value AS NUMERIC) END) AS cashflow_i_ifrs,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:CashFlowsFromFinancingActivitiesIFRS' THEN CAST(value AS NUMERIC) END) AS cashflow_f_ifrs,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:CashAndCashEquivalentsAtEndOfPeriodIFRS' THEN CAST(value AS NUMERIC) END) AS cash_end_ifrs,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock' THEN CAST(value AS NUMERIC) END) AS outstanding_shares,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:NumberOfTreasuryStockAtTheEndOfFiscalYear' THEN CAST(value AS NUMERIC) END) AS treasury_shares,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:DividendPerShare' THEN CAST(value AS NUMERIC) END) AS dividend_per_share,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:TotalDividendPaidAnnual' THEN CAST(value AS NUMERIC) END) AS total_dividend_annual,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:PayoutRatio' THEN CAST(value AS NUMERIC) END) AS payout_ratio,
            MAX(CASE WHEN factor_tag = 'tse-ed-t:DocumentName' THEN value END) AS doc_name,
            ROW_NUMBER() OVER (
                PARTITION BY code, fiscal_year_end, quarterly_period 
                ORDER BY date ASC
            ) as rn
        FROM
            html_summary
        WHERE
            factor_tag
            IN
            (
            'tse-ed-t:NetAssets',
            'tse-ed-t:NetSales',
            'tse-ed-t:NetSalesIFRS',
            'tse-ed-t:OperatingIncome',
            'tse-ed-t:TotalRevenuesAfterDeductingFinancialExpenseUS',
            'tse-ed-t:OperatingIncomeUS',
            'tse-ed-t:OperatingIncomeIFRS',
            'tse-ed-t:OrdinaryIncome',
            'tse-ed-t:ProfitBeforeTaxIFRS',
            'tse-ed-t:NetAssetsUS',
            'tse-ed-t:TotalEquityIFRS',
            'tse-ed-t:CashFlowsFromOperatingActivities',
            'tse-ed-t:CashFlowsFromInvestingActivities',
            'tse-ed-t:CashFlowsFromFinancingActivities',
            'tse-ed-t:CashAndEquivalentsEndOfPeriod',
            'tse-ed-t:CashFlowsFromOperatingActivitiesIFRS',
            'tse-ed-t:CashFlowsFromInvestingActivitiesIFRS',
            'tse-ed-t:CashFlowsFromFinancingActivitiesIFRS',
            'tse-ed-t:CashAndCashEquivalentsAtEndOfPeriodIFRS',
            'tse-ed-t:NumberOfIssuedAndOutstandingSharesAtTheEndOfFiscalYearIncludingTreasuryStock',
            'tse-ed-t:NumberOfTreasuryStockAtTheEndOfFiscalYear',
            'tse-ed-t:DividendPerShare',
            'tse-ed-t:TotalDividendPaidAnnual',
            'tse-ed-t:PayoutRatio',
            'tse-ed-t:DocumentName'
            )
            AND
            (typeof(value) IN ('integer', 'real') OR factor_tag = 'tse-ed-t:DocumentName')
        GROUP BY
            date,
            code,
            company_name,
            fiscal_year_end,
            quarterly_period
    )
    SELECT 
        date,
        code,
        company_name,
        fiscal_year_end,
        quarterly_period,
        net_sales,
        net_salesIFRS,
        operatingincome,
        financialexpense_us,
        operatingincome_us,
        operatingincome_ifrs,
        ordinary_income,
        profitbeforetax_ifrs,
        net_assets,
        net_assets_us,
        totalequity_ifrs,
        cashflow_o,
        cashflow_i,
        cashflow_f,
        cash_end,
        cashflow_o_ifrs,
        cashflow_i_ifrs,
        cashflow_f_ifrs,
        cash_end_ifrs,
        outstanding_shares,
        treasury_shares,
        dividend_per_share,
        total_dividend_annual,
        payout_ratio,
        doc_name
    FROM RankedData
    WHERE rn = 1
    ORDER BY
        code ASC,
        date DESC
    """
    
    # データベース接続
    conn = sqlite3.connect('html_summary.db')
    cursor = conn.cursor()
    
    try:
        # クエリ実行
        print("データベースからデータを取得中...")
        cursor.execute(query)
        
        # カラム名を取得
        column_names = [description[0] for description in cursor.description]
        
        # 全データを取得
        rows = cursor.fetchall()
        
        # 出力ファイル名
        output_filename = 'export_html_summary_output.csv'
        
        # CSVファイルに出力（UTF-8 with BOM）
        print(f"CSVファイルに出力中: {output_filename}")
        with open(output_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            
            # ヘッダー行を書き込み（先頭にidを追加）
            header_with_id = ['id'] + column_names
            writer.writerow(header_with_id)
            
            # データ行を書き込み（各行の先頭にIDを追加）
            for idx, row in enumerate(rows, start=1):
                row_with_id = [idx] + list(row)
                writer.writerow(row_with_id)
        
        print(f"✓ 出力完了: {output_filename}")
        print(f"  総レコード数: {len(rows):,}")
        
    except sqlite3.Error as e:
        print(f"データベースエラー: {e}")
        
    finally:
        # データベース接続を閉じる
        cursor.close()
        conn.close()

if __name__ == "__main__":
    export_financial_data()