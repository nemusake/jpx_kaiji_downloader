import requests
from bs4 import BeautifulSoup
import time
import re
from typing import Dict, Optional, List
import json
import os


class JPXScraper:
    """東証適時開示情報サイトから企業情報を取得するスクレイパー"""
    
    def __init__(self, debug: bool = False):
        self.session = requests.Session()
        self.base_url = "https://www2.jpx.co.jp/tseHpFront/"
        self.debug = debug
        self.last_response = None  # 最後のレスポンスを保持
        
        # ヘッダー設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        if self.debug:
            os.makedirs("debug", exist_ok=True)
    
    def search_company(self, stock_code: str) -> Optional[Dict]:
        """
        証券コードから企業情報を検索し、基本情報ページまで遷移
        
        Args:
            stock_code: 証券コード（例: "9984"）
            
        Returns:
            企業情報の辞書、または取得失敗時はNone
        """
        try:
            # ステップ1: 初期ページアクセス
            print(f"ステップ1: 検索ページにアクセス中...")
            init_url = self.base_url + "JJK010010Action.do?Show"
            response = self.session.get(init_url)
            response.raise_for_status()
            time.sleep(1)
            
            # ステップ2: 検索フォームの送信
            print(f"ステップ2: 証券コード {stock_code} で検索中...")
            search_url = self.base_url + "JJK010010Action.do"
            
            # ブログを参考にした正しいPOSTパラメータ
            search_data = {
                'ListShow': 'ListShow',
                'sniMtGmnId': '',
                'dspSsuPd': '10',
                'dspSsuPdMapOut': '10>10件<50>50件<100>100件<200>200件<',
                'mgrMiTxtBx': '',  # 空にする
                'eqMgrCd': stock_code,  # ここに証券コードを入れる
                'szkbuChkbxMapOut': '011>プライム<012>スタンダード<013>グロース<008>TOKYO PRO Market<bj1>－<be1>－<111>外国株プライム<112>外国株スタンダード<113>外国株グロース<bj2>－<be2>－<ETF>ETF<ETN>ETN<RET>不動産投資信託(REIT)<IFD>インフラファンド<999>その他<'
            }
            
            response = self.session.post(search_url, data=search_data)
            response.raise_for_status()
            
            if self.debug:
                with open(f"debug/{stock_code}_step2_search_result.html", 'w', encoding='utf-8') as f:
                    f.write(response.text)
            
            # 検索結果ページからフォームパラメータを抽出
            soup = BeautifulSoup(response.text, 'lxml')
            
            # ステップ3: 基本情報ボタンをクリック（JJK010030Action.doへの遷移）
            print(f"ステップ3: 基本情報ページに遷移中...")
            
            # フォームから必要なパラメータを抽出
            form_params = self._extract_form_params(soup, stock_code)
            
            if not form_params:
                print("エラー: フォームパラメータが見つかりません")
                return None
            
            # 基本情報ページへのPOSTリクエスト
            basic_info_url = self.base_url + "JJK010030Action.do"
            response = self.session.post(basic_info_url, data=form_params)
            response.raise_for_status()
            
            # レスポンスを保持
            self.last_response = response.text
            
            if self.debug:
                with open(f"debug/{stock_code}_step3_basic_info.html", 'w', encoding='utf-8') as f:
                    f.write(response.text)
            
            # 基本情報ページから企業情報を抽出
            soup = BeautifulSoup(response.text, 'lxml')
            company_info = self._extract_company_info(soup, stock_code)
            
            return company_info
            
        except requests.RequestException as e:
            print(f"HTTPエラーが発生しました: {e}")
            return None
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_form_params(self, soup: BeautifulSoup, stock_code: str) -> Optional[Dict]:
        """
        検索結果ページから基本情報ページへの遷移に必要なパラメータを抽出
        """
        try:
            def get_input_value(soup, input_name):
                """特定のname属性を持つinput要素のvalue値を取得"""
                target = soup.select_one(f'input[name="{input_name}"]')
                if target:
                    return target.get('value', '')
                return ''
            
            # 必要なパラメータを収集
            params = {
                'BaseJh': get_input_value(soup, 'BaseJh'),
                'lstDspPg': get_input_value(soup, 'lstDspPg'),
                'dspGs': get_input_value(soup, 'dspGs'),
                'souKnsu': get_input_value(soup, 'souKnsu'),
                'sniMtGmnId': get_input_value(soup, 'sniMtGmnId'),
                'dspJnKbn': get_input_value(soup, 'dspJnKbn'),
                'dspJnKmkNo': get_input_value(soup, 'dspJnKmkNo'),
                'mgrCd': stock_code,  # 証券コードを手動で設定
                'jjHisiFlg': get_input_value(soup, 'jjHisiFlg')
            }
            
            # 検索結果の最初の銘柄の情報を取得（ccJjCrpSelKekkLst_st[0]）
            result_params = [
                'ccJjCrpSelKekkLst_st[0].eqMgrCd',
                'ccJjCrpSelKekkLst_st[0].eqMgrNm',
                'ccJjCrpSelKekkLst_st[0].szkbuNm',
                'ccJjCrpSelKekkLst_st[0].gyshDspNm',
                'ccJjCrpSelKekkLst_st[0].dspYuKssnKi'
            ]
            
            for param_name in result_params:
                value = get_input_value(soup, param_name)
                if value:
                    params[param_name] = value
            
            # パラメータが取得できたか確認
            if params['BaseJh']:
                if self.debug:
                    print(f"基本情報ページへのパラメータを抽出:")
                    for key, value in params.items():
                        if value:
                            print(f"  {key}: {value}")
                return params
            else:
                print("エラー: 必要なフォームパラメータが見つかりません")
                return None
            
        except Exception as e:
            print(f"パラメータ抽出エラー: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_company_info(self, soup: BeautifulSoup, stock_code: str) -> Dict:
        """
        基本情報ページから企業情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            stock_code: 証券コード
            
        Returns:
            企業情報の辞書
        """
        info = {
            'stock_code': stock_code,
            'company_name': None,
            'company_name_en': None,
            'market': None,
            'industry': None,
            'listing_date': None,
            'fiscal_year_end': None,
            'capital': None,
            'shares_outstanding': None,
            'address': None,
            'representative': None,
            'employees': None,
            'average_age': None,
            'average_salary': None
        }
        
        # テーブルから情報を抽出
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # ラベルと値を取得
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    # ラベルに基づいて情報を格納
                    if '会社名' in label and '英文' not in label:
                        info['company_name'] = value
                    elif '英文会社名' in label:
                        info['company_name_en'] = value
                    elif '市場' in label and '区分' in label:
                        info['market'] = value
                    elif '業種' in label:
                        info['industry'] = value
                    elif '上場日' in label:
                        info['listing_date'] = value
                    elif '決算期' in label:
                        info['fiscal_year_end'] = value
                    elif '資本金' in label:
                        info['capital'] = value
                    elif '発行済株式' in label:
                        info['shares_outstanding'] = value
                    elif '本社所在地' in label or '所在地' in label:
                        info['address'] = value
                    elif '代表者' in label:
                        info['representative'] = value
                    elif '従業員数' in label:
                        info['employees'] = value
                    elif '平均年齢' in label:
                        info['average_age'] = value
                    elif '平均年収' in label:
                        info['average_salary'] = value
        
        # 企業名が見つからない場合は、ページタイトルやヘッダーから探す
        if not info['company_name']:
            # h1, h2, h3タグから探す
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                text = heading.get_text(strip=True)
                if stock_code in text:
                    # 証券コードを含むヘッダーから企業名を抽出
                    company_text = text.replace(stock_code, '').strip()
                    # 括弧や記号を除去
                    company_text = re.sub(r'[（(].*?[）)]', '', company_text).strip()
                    if company_text:
                        info['company_name'] = company_text
                        break
        
        # デバッグ情報を出力
        if self.debug:
            print(f"抽出された情報:")
            for key, value in info.items():
                if value:
                    print(f"  {key}: {value}")
        
        return info
    
    def fetch_disclosure_documents(self, stock_code: str) -> List[Dict]:
        """
        適時開示書類の一覧を取得（XBRL、HTMLサマリー、PDF等）
        
        Args:
            stock_code: 証券コード
            
        Returns:
            開示書類のリスト
        """
        try:
            # まず企業の基本情報ページを取得
            print(f"証券コード {stock_code} の適時開示情報を取得中...")
            
            # 検索から基本情報ページまで遷移
            company_info = self.search_company(stock_code)
            if not company_info:
                print("基本情報ページの取得に失敗しました")
                return []
            
            # 最後に取得したHTMLから開示情報を抽出
            # （search_companyで既に基本情報ページを取得済み）
            if self.debug:
                html_file = f"debug/{stock_code}_step3_basic_info.html"
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
            else:
                # デバッグモードでない場合は再度取得が必要
                print("適時開示情報を抽出中...")
                return self._extract_disclosure_from_last_response(stock_code)
            
            soup = BeautifulSoup(html_content, 'lxml')
            return self._extract_disclosure_info(soup)
            
        except Exception as e:
            print(f"適時開示情報の取得エラー: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_disclosure_from_last_response(self, stock_code: str) -> List[Dict]:
        """
        最後のレスポンスから適時開示情報を抽出（内部使用）
        """
        if self.last_response:
            soup = BeautifulSoup(self.last_response, 'lxml')
            return self._extract_disclosure_info(soup)
        return []
    
    def _extract_disclosure_info(self, soup: BeautifulSoup) -> List[Dict]:
        """
        HTMLから適時開示情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            開示情報のリスト
        """
        import urllib.parse
        
        disclosure_list = []
        
        try:
            # 適時開示情報と縦覧書類を含むテーブルを取得
            target_tables = []
            
            # div.pagecontents配下のテーブルを探す
            table_elms = soup.select('div.pagecontents > table')
            if not table_elms:
                # 別の方法で探す
                table_elms = soup.find_all('table')
            
            for table_elm in table_elms:
                table_id = table_elm.get('id', '')
                # closeUpKaiJi* または closeUpFili* のIDを持つテーブルを探す
                # （openは除外）
                if table_id and ('KaiJi' in table_id or 'Fili' in table_id) and ('open' not in table_id):
                    target_tables.append(table_elm)
                    if self.debug:
                        print(f"開示情報テーブル発見: {table_id}")
            
            # 各テーブルから情報を抽出
            for table_elm in target_tables:
                # 入れ子になっているテーブル要素を探す
                inner_table = table_elm.select_one('table')
                if not inner_table:
                    continue
                
                # tr要素を処理
                tr_elms = inner_table.select('tr')
                for tr_elm in tr_elms:
                    tr_id = tr_elm.get('id')
                    if not tr_id:
                        continue
                    
                    disclosure_info = {
                        'date': '',
                        'title': '',
                        'pdf_url': '',
                        'xbrl_url': '',
                        'html_summary_url': '',
                        'attachments': []
                    }
                    
                    # 1つ目のtd要素: 開示日
                    date_td = tr_elm.select_one('td:nth-of-type(1)')
                    if date_td:
                        disclosure_info['date'] = date_td.get_text(strip=True)
                    
                    # 2つ目のtd要素: 表題とPDF URL
                    title_td = tr_elm.select_one('td:nth-of-type(2)')
                    if title_td:
                        a_elm = title_td.select_one('a')
                        if a_elm:
                            disclosure_info['title'] = a_elm.get_text(strip=True)
                            pdf_href = a_elm.get('href', '')
                            if pdf_href:
                                disclosure_info['pdf_url'] = urllib.parse.urljoin(
                                    'https://www2.jpx.co.jp', pdf_href.strip()
                                )
                    
                    # 3つ目のtd要素: XBRL URL
                    xbrl_td = tr_elm.select_one('td:nth-of-type(3)')
                    if xbrl_td:
                        img_elm = xbrl_td.select_one('img')
                        if img_elm:
                            onclick = img_elm.get('onclick', '')
                            if onclick:
                                # ブログを参考にしたXBRL URL抽出
                                # 例: downloadXbrl2('99840','1','/081220241105608352.zip');
                                onclick_code_str = onclick.replace('\n', '').strip()
                                parts = onclick_code_str.split(',')
                                if len(parts) >= 3:
                                    # 最後の要素がパス
                                    xbrl_path = parts[-1].strip().replace("'", '').replace(');', '')
                                    if xbrl_path and xbrl_path.startswith('/'):
                                        disclosure_info['xbrl_url'] = f'https://www2.jpx.co.jp/disc{xbrl_path}'
                                        if self.debug:
                                            print(f"XBRL URL抽出: {disclosure_info['xbrl_url']}")
                        
                        # XBRLが見つからない場合、別の要素も確認
                        if not disclosure_info['xbrl_url']:
                            # aタグでXBRLリンクがある場合
                            xbrl_link = xbrl_td.select_one('a')
                            if xbrl_link:
                                href = xbrl_link.get('href', '')
                                if href and ('.zip' in href.lower() or 'xbrl' in href.lower()):
                                    disclosure_info['xbrl_url'] = urllib.parse.urljoin(
                                        'https://www2.jpx.co.jp', href
                                    )
                    
                    # 4つ目のtd要素: HTMLサマリー
                    html_td = tr_elm.select_one('td:nth-of-type(4)')
                    if html_td:
                        # aタグのhref属性から直接URLを取得
                        html_link = html_td.select_one('a')
                        if html_link:
                            href = html_link.get('href', '')
                            if href and '.htm' in href.lower():
                                disclosure_info['html_summary_url'] = urllib.parse.urljoin(
                                    'https://www2.jpx.co.jp', href
                                )
                                if self.debug:
                                    print(f"HTMLサマリーURL抽出: {disclosure_info['html_summary_url']}")
                        
                        # href属性にない場合はimgのonclick属性も確認（後方互換性）
                        elif not disclosure_info['html_summary_url']:
                            img_elm = html_td.select_one('img')
                            if img_elm:
                                onclick = img_elm.get('onclick', '')
                                if onclick and 'window.open' in onclick:
                                    # URLを抽出
                                    import re
                                    url_match = re.search(r"window\.open\('([^']+)'", onclick)
                                    if url_match:
                                        disclosure_info['html_summary_url'] = urllib.parse.urljoin(
                                            'https://www2.jpx.co.jp', url_match.group(1)
                                        )
                    
                    # 5つ目のtd要素: 添付資料
                    attach_td = tr_elm.select_one('td:nth-of-type(5)')
                    if attach_td:
                        attach_links = attach_td.select('a')
                        for link in attach_links:
                            attach_url = link.get('href', '')
                            if attach_url:
                                disclosure_info['attachments'].append(
                                    urllib.parse.urljoin('https://www2.jpx.co.jp', attach_url)
                                )
                    
                    # 情報が含まれている場合のみリストに追加
                    if disclosure_info['title']:
                        disclosure_list.append(disclosure_info)
                        if self.debug:
                            print(f"開示情報抽出: {disclosure_info['title'][:30]}...")
            
            print(f"合計 {len(disclosure_list)} 件の開示情報を取得しました")
            
        except Exception as e:
            print(f"開示情報の抽出エラー: {e}")
            import traceback
            traceback.print_exc()
        
        return disclosure_list
    
    def download_xbrl_files(self, disclosure_docs: List[Dict], download_dir: str = "downloads/xbrl", stock_code: str = "") -> List[Dict]:
        """
        XBRL ファイルをダウンロード
        
        Args:
            disclosure_docs: 開示情報のリスト
            download_dir: ダウンロード先ディレクトリ
            stock_code: 証券コード（ファイル名生成用）
            
        Returns:
            ダウンロード結果のリスト
        """
        import os
        from urllib.parse import urlparse
        
        # ダウンロード先ディレクトリを作成
        os.makedirs(download_dir, exist_ok=True)
        
        download_results = []
        
        # XBRLがある開示情報のみを処理
        xbrl_docs = [doc for doc in disclosure_docs if doc.get('xbrl_url')]
        
        print(f"\n{len(xbrl_docs)}件のXBRLファイルをダウンロード中...")
        
        for i, doc in enumerate(xbrl_docs, 1):
            try:
                xbrl_url = doc['xbrl_url']
                
                # ファイル名を生成（わかりやすい形式）
                # 日付を yyyy-mm-dd 形式に変換
                date_formatted = doc['date'].replace('/', '-')
                
                # 表題からファイル名に使えない文字を除去
                safe_title = "".join(c for c in doc['title'] if c not in '<>:"/\\|?*').strip()
                
                # 新しいファイル名形式: 開示日_証券コード_表題_xbrl.zip
                filename = f"{date_formatted}_{stock_code}_{safe_title}_xbrl.zip"
                filepath = os.path.join(download_dir, filename)
                
                print(f"[{i}/{len(xbrl_docs)}] ダウンロード中: {doc['title'][:50]}...")
                
                # XBRLファイルをダウンロード
                response = self.session.get(xbrl_url)
                response.raise_for_status()
                
                # ファイルに保存
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                download_result = {
                    'title': doc['title'],
                    'date': doc['date'],
                    'xbrl_url': xbrl_url,
                    'local_file': filepath,
                    'file_size': len(response.content),
                    'status': 'success'
                }
                
                download_results.append(download_result)
                
                print(f"  → 完了: {filename} ({len(response.content):,} bytes)")
                
                # サーバーへの負荷を考慮して待機
                if i < len(xbrl_docs):
                    time.sleep(1)
                    
            except Exception as e:
                error_result = {
                    'title': doc['title'],
                    'date': doc['date'],
                    'xbrl_url': doc.get('xbrl_url', ''),
                    'local_file': None,
                    'file_size': 0,
                    'status': 'error',
                    'error': str(e)
                }
                download_results.append(error_result)
                print(f"  → エラー: {e}")
        
        print(f"\nダウンロード完了: 成功 {sum(1 for r in download_results if r['status'] == 'success')} / {len(download_results)} 件")
        
        return download_results
    
    def download_html_summaries(self, stock_code: str) -> List[Dict]:
        """
        HTMLサマリーファイルをダウンロード
        
        Args:
            stock_code: 証券コード
            
        Returns:
            ダウンロード結果のリスト
        """
        import os
        import time
        import requests
        from urllib.parse import urlparse
        
        # 適時開示情報を取得
        disclosure_info = self.fetch_disclosure_documents(stock_code)
        
        # HTMLサマリーURLが存在するもののみフィルタ
        html_docs = [doc for doc in disclosure_info if doc.get('html_summary_url')]
        
        if not html_docs:
            print("HTMLサマリーファイルが見つかりませんでした。")
            return []
        
        # ダウンロードディレクトリを作成
        download_dir = os.path.join('downloads', 'html_summary', stock_code)
        os.makedirs(download_dir, exist_ok=True)
        
        print(f"\nHTMLサマリーダウンロード開始: {len(html_docs)} 件")
        print(f"保存先: {download_dir}")
        
        download_results = []
        
        for i, doc in enumerate(html_docs, 1):
            try:
                html_url = doc['html_summary_url']
                print(f"[{i}/{len(html_docs)}] {doc['title'][:50]}...")
                print(f"  URL: {html_url}")
                
                # ファイル名を生成（わかりやすい形式）
                # 日付を yyyy-mm-dd 形式に変換
                date_formatted = doc['date'].replace('/', '-')
                
                # 表題からファイル名に使えない文字を除去
                safe_title = "".join(c for c in doc['title'] if c not in '<>:"/\\|?*').strip()
                
                # 新しいファイル名形式: 開示日_証券コード_表題_summary.htm
                filename = f"{date_formatted}_{stock_code}_{safe_title}_summary.htm"
                
                local_file = os.path.join(download_dir, filename)
                
                # 既に存在する場合はスキップ
                if os.path.exists(local_file):
                    print(f"  → スキップ: ファイルが既に存在します")
                    download_result = {
                        'title': doc['title'],
                        'date': doc['date'],
                        'html_summary_url': html_url,
                        'local_file': local_file,
                        'file_size': os.path.getsize(local_file),
                        'status': 'skipped'
                    }
                    download_results.append(download_result)
                    continue
                
                # ダウンロード実行
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(html_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # ファイル保存
                with open(local_file, 'wb') as f:
                    f.write(response.content)
                
                download_result = {
                    'title': doc['title'],
                    'date': doc['date'],
                    'html_summary_url': html_url,
                    'local_file': local_file,
                    'file_size': len(response.content),
                    'status': 'success'
                }
                
                download_results.append(download_result)
                
                print(f"  → 完了: {filename} ({len(response.content):,} bytes)")
                
                # サーバーへの負荷を考慮して待機
                if i < len(html_docs):
                    time.sleep(1)
                    
            except Exception as e:
                error_result = {
                    'title': doc['title'],
                    'date': doc['date'],
                    'html_summary_url': doc.get('html_summary_url', ''),
                    'local_file': None,
                    'file_size': 0,
                    'status': 'error',
                    'error': str(e)
                }
                download_results.append(error_result)
                print(f"  → エラー: {e}")
        
        print(f"\nHTMLサマリーダウンロード完了: 成功 {sum(1 for r in download_results if r['status'] == 'success')} / {len(download_results)} 件")
        
        return download_results
    
    def download_attachments(self, stock_code: str) -> List[Dict]:
        """
        添付資料ファイルをダウンロード
        
        Args:
            stock_code: 証券コード
            
        Returns:
            ダウンロード結果のリスト
        """
        import os
        import time
        import requests
        from urllib.parse import urlparse
        
        # 適時開示情報を取得
        disclosure_info = self.fetch_disclosure_documents(stock_code)
        
        # 添付資料URLが存在するもののみフィルタ
        attachment_docs = []
        for doc in disclosure_info:
            if doc.get('attachments'):
                for attach_url in doc['attachments']:
                    attachment_docs.append({
                        'title': doc['title'],
                        'date': doc['date'],
                        'attachment_url': attach_url
                    })
        
        if not attachment_docs:
            print("添付資料ファイルが見つかりませんでした。")
            return []
        
        # ダウンロードディレクトリを作成
        download_dir = os.path.join('downloads', 'attachments', stock_code)
        os.makedirs(download_dir, exist_ok=True)
        
        print(f"\n添付資料ダウンロード開始: {len(attachment_docs)} 件")
        print(f"保存先: {download_dir}")
        
        download_results = []
        
        for i, doc in enumerate(attachment_docs, 1):
            try:
                attach_url = doc['attachment_url']
                print(f"[{i}/{len(attachment_docs)}] {doc['title'][:50]}...")
                print(f"  URL: {attach_url}")
                
                # ファイル名を生成（わかりやすい形式）
                # 日付を yyyy-mm-dd 形式に変換
                date_formatted = doc['date'].replace('/', '-')
                
                # 表題からファイル名に使えない文字を除去
                safe_title = "".join(c for c in doc['title'] if c not in '<>:"/\\|?*').strip()
                
                # 新しいファイル名形式: 開示日_証券コード_表題_attachments.htm
                filename = f"{date_formatted}_{stock_code}_{safe_title}_attachments.htm"
                
                local_file = os.path.join(download_dir, filename)
                
                # 既に存在する場合はスキップ
                if os.path.exists(local_file):
                    print(f"  → スキップ: ファイルが既に存在します")
                    download_result = {
                        'title': doc['title'],
                        'date': doc['date'],
                        'attachment_url': attach_url,
                        'local_file': local_file,
                        'file_size': os.path.getsize(local_file),
                        'status': 'skipped'
                    }
                    download_results.append(download_result)
                    continue
                
                # ダウンロード実行
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(attach_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # ファイル保存
                with open(local_file, 'wb') as f:
                    f.write(response.content)
                
                download_result = {
                    'title': doc['title'],
                    'date': doc['date'],
                    'attachment_url': attach_url,
                    'local_file': local_file,
                    'file_size': len(response.content),
                    'status': 'success'
                }
                
                download_results.append(download_result)
                
                print(f"  → 完了: {filename} ({len(response.content):,} bytes)")
                
                # サーバーへの負荷を考慮して待機
                if i < len(attachment_docs):
                    time.sleep(1)
                    
            except Exception as e:
                error_result = {
                    'title': doc['title'],
                    'date': doc['date'],
                    'attachment_url': doc.get('attachment_url', ''),
                    'local_file': None,
                    'file_size': 0,
                    'status': 'error',
                    'error': str(e)
                }
                download_results.append(error_result)
                print(f"  → エラー: {e}")
        
        print(f"\n添付資料ダウンロード完了: 成功 {sum(1 for r in download_results if r['status'] == 'success')} / {len(download_results)} 件")
        
        return download_results
    
    def download_all_files_batch(self, codelist_csv: str = "codelist.csv", download_types: list = None, 
                                 resume_from: int = 0, max_companies: int = None, 
                                 delay_seconds: int = 3) -> Dict:
        """
        codelist.csvから全銘柄のデータを一括ダウンロード
        
        Args:
            codelist_csv: 銘柄リストCSVファイルパス
            download_types: ダウンロード種類 ['xbrl', 'html', 'attachments'] (Noneで全種類)
            resume_from: 再開する行番号（0から開始）
            max_companies: 最大処理企業数（Noneで全企業）
            delay_seconds: 企業間の待機秒数
            
        Returns:
            処理結果サマリー
        """
        import csv
        import time
        from datetime import datetime
        import os
        
        if download_types is None:
            download_types = ['xbrl', 'html', 'attachments']
        
        print(f"🚀 codelist.csvから全銘柄一括ダウンロード開始")
        print(f"📋 対象ファイル: {codelist_csv}")
        print(f"📥 ダウンロード種類: {', '.join(download_types)}")
        print(f"⏱️  企業間待機時間: {delay_seconds}秒")
        print(f"🔄 再開位置: {resume_from}行目から")
        print("-" * 60)
        
        # CSVファイルの読み込み
        companies = []
        try:
            with open(codelist_csv, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= resume_from:
                        if max_companies and len(companies) >= max_companies:
                            break
                        companies.append({
                            'row_number': i + 1,  # ヘッダー行を考慮
                            'stock_code': row['code'],
                            'company_name': row['銘柄名'],
                            'industry': row['業種'],
                            'topix_weight': row['TOPIXに占める個別銘柄のウエイト'],
                            'index_category': row['ニューインデックス区分']
                        })
        except FileNotFoundError:
            print(f"❌ エラー: {codelist_csv} が見つかりません")
            return {'status': 'error', 'message': 'CSV file not found'}
        except Exception as e:
            print(f"❌ CSVファイル読み込みエラー: {e}")
            return {'status': 'error', 'message': str(e)}
        
        print(f"📊 処理対象企業数: {len(companies)} 社")
        
        # 結果記録用
        batch_results = {
            'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_companies': len(companies),
            'processed_companies': 0,
            'successful_companies': 0,
            'failed_companies': 0,
            'download_types': download_types,
            'results': [],
            'failed_companies_list': [],
            'statistics': {}
        }
        
        # 処理開始
        for i, company in enumerate(companies, 1):
            stock_code = company['stock_code']
            company_name = company['company_name']
            row_number = company['row_number']
            
            print(f"\n[{i}/{len(companies)}] 処理中: {company_name} ({stock_code}) - 行番号: {row_number}")
            
            company_result = {
                'row_number': row_number,
                'stock_code': stock_code,
                'company_name': company_name,
                'industry': company['industry'],
                'downloads': {},
                'total_files': 0,
                'success_files': 0,
                'status': 'processing'
            }
            
            try:
                # 適時開示情報を取得
                disclosure_info = self.fetch_disclosure_documents(stock_code)
                
                if not disclosure_info:
                    print(f"  ⚠️  適時開示情報が見つかりません")
                    company_result['status'] = 'no_disclosure_data'
                    batch_results['results'].append(company_result)
                    batch_results['failed_companies_list'].append({
                        'stock_code': stock_code,
                        'company_name': company_name,
                        'reason': 'no_disclosure_data'
                    })
                    continue
                
                print(f"  📋 適時開示情報: {len(disclosure_info)} 件取得")
                
                # 各種ファイルのダウンロード
                for download_type in download_types:
                    try:
                        if download_type == 'xbrl':
                            results = self.download_xbrl_files(disclosure_info, f"downloads/xbrl/{stock_code}", stock_code)
                        elif download_type == 'html':
                            results = self.download_html_summaries(stock_code)
                        elif download_type == 'attachments':
                            results = self.download_attachments(stock_code)
                        else:
                            continue
                        
                        # 結果集計
                        total_files = len(results)
                        success_files = sum(1 for r in results if r['status'] == 'success')
                        
                        company_result['downloads'][download_type] = {
                            'total': total_files,
                            'success': success_files,
                            'failed': total_files - success_files
                        }
                        
                        company_result['total_files'] += total_files
                        company_result['success_files'] += success_files
                        
                        print(f"    📥 {download_type.upper()}: {success_files}/{total_files} 件成功")
                        
                    except Exception as download_error:
                        print(f"    ❌ {download_type.upper()}ダウンロードエラー: {download_error}")
                        company_result['downloads'][download_type] = {
                            'total': 0,
                            'success': 0,
                            'failed': 0,
                            'error': str(download_error)
                        }
                
                # 企業の処理結果を判定
                if company_result['success_files'] > 0:
                    company_result['status'] = 'success'
                    batch_results['successful_companies'] += 1
                    print(f"  ✅ 成功: 合計 {company_result['success_files']}/{company_result['total_files']} ファイル")
                else:
                    company_result['status'] = 'failed'
                    batch_results['failed_companies'] += 1
                    batch_results['failed_companies_list'].append({
                        'stock_code': stock_code,
                        'company_name': company_name,
                        'reason': 'no_successful_downloads'
                    })
                    print(f"  ❌ 失敗: ダウンロード成功ファイルなし")
                
            except Exception as e:
                print(f"  ❌ 企業処理エラー: {e}")
                company_result['status'] = 'error'
                company_result['error'] = str(e)
                batch_results['failed_companies'] += 1
                batch_results['failed_companies_list'].append({
                    'stock_code': stock_code,
                    'company_name': company_name,
                    'reason': f'processing_error: {str(e)}'
                })
            
            batch_results['results'].append(company_result)
            batch_results['processed_companies'] += 1
            
            # 進捗表示
            progress = (i / len(companies)) * 100
            print(f"  📊 進捗: {progress:.1f}% ({i}/{len(companies)})")
            
            # 待機（最後の企業以外）
            if i < len(companies):
                print(f"  ⏳ {delay_seconds}秒待機中...")
                time.sleep(delay_seconds)
        
        # 処理完了
        batch_results['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        batch_results['status'] = 'completed'
        
        # 統計情報の生成
        batch_results['statistics'] = self._generate_batch_statistics(batch_results)
        
        # 結果レポートの保存
        self._save_batch_report(batch_results)
        
        # 最終サマリー表示
        self._display_batch_summary(batch_results)
        
        return batch_results
    
    def _generate_batch_statistics(self, batch_results: Dict) -> Dict:
        """バッチ処理の統計情報を生成"""
        stats = {
            'success_rate': 0,
            'total_files_downloaded': 0,
            'industry_breakdown': {},
            'download_type_stats': {}
        }
        
        if batch_results['processed_companies'] > 0:
            stats['success_rate'] = (batch_results['successful_companies'] / batch_results['processed_companies']) * 100
        
        for result in batch_results['results']:
            # ファイル数合計
            stats['total_files_downloaded'] += result.get('success_files', 0)
            
            # 業種別統計
            industry = result.get('industry', '不明')
            if industry not in stats['industry_breakdown']:
                stats['industry_breakdown'][industry] = {'total': 0, 'success': 0}
            
            stats['industry_breakdown'][industry]['total'] += 1
            if result['status'] == 'success':
                stats['industry_breakdown'][industry]['success'] += 1
            
            # ダウンロード種類別統計
            for download_type, download_stats in result.get('downloads', {}).items():
                if download_type not in stats['download_type_stats']:
                    stats['download_type_stats'][download_type] = {'total': 0, 'success': 0}
                
                stats['download_type_stats'][download_type]['total'] += download_stats.get('total', 0)
                stats['download_type_stats'][download_type]['success'] += download_stats.get('success', 0)
        
        return stats
    
    def _save_batch_report(self, batch_results: Dict):
        """バッチ処理結果をJSONファイルに保存"""
        import json
        import os
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"data/batch_download_report_{timestamp}.json"
        
        os.makedirs("data", exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 詳細レポートを保存しました: {report_file}")
    
    def _display_batch_summary(self, batch_results: Dict):
        """バッチ処理結果のサマリーを表示"""
        print(f"\n{'='*60}")
        print(f"🎉 全銘柄一括ダウンロード完了!")
        print(f"{'='*60}")
        print(f"⏰ 処理時間: {batch_results['start_time']} ～ {batch_results['end_time']}")
        print(f"🏢 処理企業数: {batch_results['processed_companies']} 社")
        print(f"✅ 成功企業数: {batch_results['successful_companies']} 社")
        print(f"❌ 失敗企業数: {batch_results['failed_companies']} 社")
        print(f"📊 成功率: {batch_results['statistics']['success_rate']:.1f}%")
        print(f"📁 総ダウンロードファイル数: {batch_results['statistics']['total_files_downloaded']} 件")
        
        # ダウンロード種類別統計
        print(f"\n📥 ダウンロード種類別統計:")
        for download_type, stats in batch_results['statistics']['download_type_stats'].items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  {download_type.upper()}: {stats['success']}/{stats['total']} 件 ({success_rate:.1f}%)")
        
        # 失敗企業一覧（最初の10件のみ）
        if batch_results['failed_companies_list']:
            print(f"\n❌ 失敗企業一覧（最初の10件）:")
            for i, failed in enumerate(batch_results['failed_companies_list'][:10], 1):
                print(f"  {i}. {failed['company_name']} ({failed['stock_code']}) - {failed['reason']}")
            
            if len(batch_results['failed_companies_list']) > 10:
                print(f"  ... 他 {len(batch_results['failed_companies_list']) - 10} 件")
        
        print(f"{'='*60}")