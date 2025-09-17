#!/usr/bin/env python3
"""
XBRL添付資料テキスト抽出ツール
基本ライブラリのみを使用してHTMLから本文を抽出し、マークダウン形式で出力

依存関係: Pythonの標準ライブラリのみ
- html.parser (HTMLパース)
- re (正規表現)
- json (JSONデータ処理)
- argparse (コマンドライン引数)
"""

"""
実行コマンド

# help表示
- python3 attachments_output.py

# 証券コード13010の全HTMファイルを処理
- python3 attachments_output.py 13010

# 全銘柄を一括処理
python3 attachments_output.py all -f txt
python3 attachments_output.py all -f json
python3 attachments_output.py all -f md
python3 attachments_output.py all -f md,txt,json(組み合わせ自由)
"""



import re
import json
import argparse
from html.parser import HTMLParser
from pathlib import Path
import sys

class XBRLTextExtractor(HTMLParser):
    """XBRL HTMLファイルからテキストを抽出するパーサー"""
    
    def __init__(self):
        super().__init__()
        self.reset_state()
    
    def reset_state(self):
        """パーサーの状態をリセット"""
        self.current_tag = None
        self.current_attrs = {}
        self.current_text = ""
        self.sections = []
        self.current_section = None
        self.text_buffer = []
        self.in_table = False
        self.table_data = []
        
        # スタイルクラスの役割定義
        self.content_classes = {
            'smt_text6': 'main_text',      # 主要本文
            'smt_text1': 'main_text',      # 本文
            'smt_text2': 'main_text',      # 本文
            'smt_text3': 'main_text',      # 本文
            'smt_head1': 'heading',        # 見出し
            'smt_head2': 'heading',        # 見出し
            'smt_head3': 'heading',        # 見出し
            'smt_tblL': 'table_data',      # テーブル左
            'smt_tblC': 'table_data',      # テーブル中央
            'smt_tblR': 'table_data',      # テーブル右
        }
    
    def handle_starttag(self, tag, attrs):
        """開始タグの処理"""
        self.current_tag = tag
        self.current_attrs = dict(attrs)
        
        # テーブル要素の検出
        if tag == 'table':
            self.in_table = True
            self.table_data = []
        elif tag == 'tr' and self.in_table:
            self.table_row = []
    
    def handle_endtag(self, tag):
        """終了タグの処理"""
        if tag == 'table':
            self.in_table = False
            if self.table_data:
                # テーブルデータを構造化して保存
                self.add_table_section(self.table_data)
        elif tag == 'tr' and self.in_table and hasattr(self, 'table_row'):
            if self.table_row:
                self.table_data.append(self.table_row)
        elif tag in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'td']:
            # テキストの処理
            text = self.current_text.strip()
            if text:
                self.process_text_content(text)
        
        # 状態をリセット
        self.current_text = ""
        self.current_tag = None
        self.current_attrs = {}
    
    def handle_data(self, data):
        """テキストデータの処理"""
        if data.strip():
            self.current_text += data.strip() + " "
            
            # テーブル内のデータ
            if self.in_table and hasattr(self, 'table_row'):
                self.table_row.append(data.strip())
    
    def process_text_content(self, text):
        """テキストコンテンツの分類と処理"""
        if len(text) < 10:  # 短すぎるテキストは除外
            return
        
        # クラス属性による分類
        css_class = self.current_attrs.get('class', '')
        content_type = None
        
        for class_name, role in self.content_classes.items():
            if class_name in css_class:
                content_type = role
                break
        
        # タグによる分類
        if not content_type:
            if self.current_tag in ['h1', 'h2', 'h3', 'h4']:
                content_type = 'heading'
            elif len(text) > 50:
                content_type = 'main_text'
            else:
                content_type = 'other'
        
        # 見出しパターンの検出
        if self.is_section_heading(text):
            self.create_new_section(text, content_type)
        elif content_type == 'main_text':
            self.add_to_current_section(text)
    
    def is_section_heading(self, text):
        """セクション見出しかどうか判定"""
        patterns = [
            r'^[１-９\d][．.]\s*',                    # 1. 形式
            r'^[（\(][１-９\d]+[）\)]\s*',          # (1) 形式
            r'^○.*',                                  # ○ 形式
            r'.*概況\s*$',                          # 概況で終わる
            r'.*予想.*説明\s*$',                    # 予想...説明で終わる
        ]
        
        for pattern in patterns:
            if re.match(pattern, text):
                return True
        return False
    
    def create_new_section(self, heading_text, content_type):
        """新しいセクションを作成"""
        # 前のセクションを保存
        if self.current_section and self.current_section['content']:
            self.sections.append(self.current_section)
        
        # 見出しレベルの判定
        level = self.determine_heading_level(heading_text)
        
        self.current_section = {
            'heading': heading_text,
            'level': level,
            'type': content_type,
            'content': []
        }
    
    def determine_heading_level(self, text):
        """見出しレベルの判定"""
        if re.match(r'^[１-９\d][．.]', text):
            return 1  # 主要セクション
        elif re.match(r'^[（\(][１-９\d]+[）\)]', text):
            return 2  # 副セクション
        elif text.startswith('○'):
            return 1  # 目次など
        else:
            return 2  # その他
    
    def add_to_current_section(self, text):
        """現在のセクションにテキストを追加"""
        # 目次やページ番号を除外
        if self.is_noise_text(text):
            return
        
        if not self.current_section:
            # セクションがない場合は汎用セクションを作成
            self.create_new_section("その他の情報", "main_text")
        
        # 長すぎるテキストは分割
        if len(text) > 500:
            sentences = re.split(r'[。．]', text)
            for sentence in sentences:
                if len(sentence.strip()) > 20:
                    self.current_section['content'].append(sentence.strip() + '。')
        else:
            self.current_section['content'].append(text)
    
    def add_table_section(self, table_data):
        """テーブルセクションを追加"""
        if len(table_data) < 2:  # ヘッダーとデータ行が必要
            return
        
        section = {
            'heading': 'データ表',
            'level': 2,
            'type': 'table',
            'content': table_data
        }
        self.sections.append(section)
    
    def is_noise_text(self, text):
        """ノイズテキストかどうか判定"""
        noise_patterns = [
            r'^.*[…\.]+P\d+\s*$',           # ページ番号
            r'^[　\s]*$',                    # 空白のみ
            r'^\(単位[：:][^)]+\)\s*$',     # 単位表記
            r'^[\d,\s]+$',                   # 数字のみ
            r'^[－\-\s]+$',                 # ダッシュのみ
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, text):
                return True
        return False
    
    def get_extracted_content(self):
        """抽出したコンテンツを取得"""
        # 最後のセクションを追加
        if self.current_section and self.current_section['content']:
            self.sections.append(self.current_section)
        
        return self.sections

def convert_to_txt(sections, title="決算短信添付資料"):
    """抽出したセクションをプレーンテキスト形式に変換"""
    
    txt_lines = [
        f"{title}",
        "=" * len(title),
        "",
    ]
    
    for section in sections:
        heading = section['heading']
        content = section['content']
        section_type = section.get('type', 'main_text')
        
        # 見出しの生成
        txt_lines.append(f"■ {heading}")
        txt_lines.append("-" * (len(heading) + 2))
        txt_lines.append("")
        
        # コンテンツの処理
        if section_type == 'table':
            # テーブルの処理
            if content and len(content) > 0:
                for row in content:
                    if row:
                        txt_lines.append("  " + " | ".join(str(cell) for cell in row))
        else:
            # 通常テキストの処理
            for paragraph in content:
                if isinstance(paragraph, str) and paragraph.strip():
                    txt_lines.append(paragraph)
                    txt_lines.append("")
        
        txt_lines.append("")
    
    return "\n".join(txt_lines)

def convert_to_json(sections, title="決算短信添付資料"):
    """抽出したセクションをJSON形式に変換"""
    
    json_data = {
        "title": title,
        "extraction_date": "2025-08-27",  # 実際の日付に置き換え可能
        "total_sections": len(sections),
        "sections": []
    }
    
    for i, section in enumerate(sections):
        json_section = {
            "id": i + 1,
            "heading": section['heading'],
            "level": section['level'],
            "type": section.get('type', 'main_text'),
            "content": section['content']
        }
        
        # 統計情報を追加
        if section.get('type') == 'table':
            json_section['statistics'] = {
                "rows": len(section['content']) if section['content'] else 0
            }
        else:
            json_section['statistics'] = {
                "paragraphs": len(section['content']) if section['content'] else 0,
                "total_chars": sum(len(str(p)) for p in section['content']) if section['content'] else 0
            }
        
        json_data["sections"].append(json_section)
    
    return json.dumps(json_data, ensure_ascii=False, indent=2)

def convert_to_markdown(sections, title="決算短信添付資料"):
    """抽出したセクションをMarkdown形式に変換"""
    
    markdown_lines = [
        f"# {title}",
        "",
        "---",
        "",
    ]
    
    for section in sections:
        heading = section['heading']
        level = section['level']
        content = section['content']
        section_type = section.get('type', 'main_text')
        
        # 見出しの生成
        if level == 1:
            markdown_lines.append(f"## {heading}")
        else:
            markdown_lines.append(f"### {heading}")
        markdown_lines.append("")
        
        # コンテンツの処理
        if section_type == 'table':
            # テーブルの処理
            if content and len(content) > 0:
                markdown_lines.append("| " + " | ".join(content[0]) + " |")
                markdown_lines.append("| " + " | ".join(["---"] * len(content[0])) + " |")
                for row in content[1:]:
                    if row:  # 空行をスキップ
                        markdown_lines.append("| " + " | ".join(row) + " |")
        else:
            # 通常テキストの処理
            for paragraph in content:
                if isinstance(paragraph, str) and paragraph.strip():
                    # 長い段落は適度に分割
                    if len(paragraph) > 200:
                        sentences = re.split(r'([。．])', paragraph)
                        current_para = ""
                        for i in range(0, len(sentences), 2):
                            if i + 1 < len(sentences):
                                sentence = sentences[i] + sentences[i + 1]
                            else:
                                sentence = sentences[i]
                            
                            if len(current_para + sentence) > 200:
                                if current_para:
                                    markdown_lines.append(current_para.strip())
                                    markdown_lines.append("")
                                current_para = sentence
                            else:
                                current_para += sentence
                        
                        if current_para:
                            markdown_lines.append(current_para.strip())
                    else:
                        markdown_lines.append(paragraph)
                    markdown_lines.append("")
        
        markdown_lines.append("")
    
    return "\n".join(markdown_lines)

def extract_xbrl_text(input_file, output_file=None, output_format='markdown', silent=False):
    """XBRL HTMLファイルからテキストを抽出"""
    
    # ファイル読み込み
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"エラー: ファイルを読み込めません: {e}")
        return None
    
    # HTMLをパース
    extractor = XBRLTextExtractor()
    extractor.feed(html_content)
    sections = extractor.get_extracted_content()
    
    # 統計情報（silentモードでない場合のみ表示）
    total_sections = len(sections)
    total_paragraphs = sum(len(s.get('content', [])) for s in sections)
    
    if not silent:
        print(f"抽出完了:")
        print(f"  - セクション数: {total_sections}")
        print(f"  - 段落数: {total_paragraphs}")
    
    # 形式に応じて変換
    file_name = Path(input_file).stem
    title = f"{file_name} - 決算短信添付資料"
    
    if output_format.lower() == 'json':
        content = convert_to_json(sections, title)
        format_name = "JSON"
    elif output_format.lower() == 'txt':
        content = convert_to_txt(sections, title)
        format_name = "テキスト"
    else:  # markdown (default)
        content = convert_to_markdown(sections, title)
        format_name = "Markdown"
    
    # 出力
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            if not silent:
                print(f"  - 出力ファイル: {output_file}")
                print(f"  - 出力形式: {format_name}")
        except Exception as e:
            print(f"エラー: ファイルを書き込めません: {e}")
            return None
    else:
        if not silent:
            print(f"\n" + "="*50)
            print(f"抽出結果（{format_name}形式）:")
            print("="*50)
            print(content)
    
    return content

def parse_formats(format_string):
    """出力形式文字列を解析して有効な形式リストを返す"""
    valid_formats = ['markdown', 'txt', 'json']
    format_aliases = {'md': 'markdown'}  # 省略形対応
    
    if ',' in format_string:
        # コンマ区切りの場合
        formats = [f.strip().lower() for f in format_string.split(',')]
    else:
        # 単一形式の場合
        formats = [format_string.strip().lower()]
    
    # 省略形を正式名に変換
    normalized_formats = []
    for fmt in formats:
        if fmt in format_aliases:
            normalized_formats.append(format_aliases[fmt])
        else:
            normalized_formats.append(fmt)
    
    # 有効性チェック
    invalid_formats = [f for f in normalized_formats if f not in valid_formats]
    if invalid_formats:
        original_invalid = [formats[i] for i, f in enumerate(normalized_formats) if f in invalid_formats]
        raise ValueError(f"無効な出力形式: {', '.join(original_invalid)}")
    
    # 重複を除去して返す
    return list(dict.fromkeys(normalized_formats))  # 順序を保持して重複除去

def find_security_code_folders(attachments_dir):
    """証券コードフォルダを検索する"""
    folders = []
    attachments_path = Path(attachments_dir)
    
    if not attachments_path.exists():
        return folders
    
    # 5桁の英数字パターンにマッチするフォルダを検索
    import re
    pattern = re.compile(r'^[A-Za-z0-9]{5}$')
    
    for item in attachments_path.iterdir():
        if item.is_dir() and pattern.match(item.name):
            folders.append(item.name)
    
    return sorted(folders)

def process_security_code_folder(security_code, input_base_dir, output_base_dir, output_formats=['markdown'], silent=False):
    """特定の証券コードフォルダを処理する（複数形式対応）"""
    
    input_dir = Path(input_base_dir) / security_code
    output_dir = Path(output_base_dir) / security_code
    
    # 入力フォルダの存在確認
    if not input_dir.exists():
        print(f"エラー: フォルダが見つかりません: {input_dir}")
        return False
    
    # 出力フォルダの作成
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # HTMファイルを検索
    htm_files = list(input_dir.glob("*.htm"))
    if not htm_files:
        print(f"警告: {security_code} フォルダにHTMファイルが見つかりません")
        return False
    
    # 出力形式を表示用に整形（silentモードでない場合のみ）
    if not silent:
        formats_str = ', '.join(output_formats)
        print(f"\n📁 処理中: {security_code} ({len(htm_files)}ファイル, 形式: {formats_str})")
    
    total_success = 0
    total_error = 0
    
    for htm_file in htm_files:
        file_success = 0
        file_error = 0
        
        # 各形式で出力
        for output_format in output_formats:
            try:
                # 出力ファイル名を決定
                if output_format == 'json':
                    output_file = output_dir / (htm_file.stem + '.json')
                elif output_format == 'txt':
                    output_file = output_dir / (htm_file.stem + '.txt')
                else:  # markdown
                    output_file = output_dir / (htm_file.stem + '.md')
                
                # 抽出実行
                result = extract_xbrl_text(str(htm_file), str(output_file), output_format, silent)
                
                if result:
                    file_success += 1
                else:
                    file_error += 1
                    
            except Exception as e:
                file_error += 1
                print(f"  ✗ {htm_file.name} ({output_format}形式でエラー: {str(e)})")
        
        # ファイル別の結果表示（silentモードでない場合のみ）
        if not silent:
            if file_error == 0:
                # すべて成功
                extensions = []
                for fmt in output_formats:
                    if fmt == 'json':
                        extensions.append('.json')
                    elif fmt == 'txt':
                        extensions.append('.txt')
                    else:
                        extensions.append('.md')
                print(f"  ✓ {htm_file.name} → {', '.join(extensions)}")
            elif file_success > 0:
                # 部分的に成功
                print(f"  ⚠ {htm_file.name} (成功: {file_success}形式, エラー: {file_error}形式)")
            else:
                # すべて失敗
                print(f"  ✗ {htm_file.name} (全形式で失敗)")
        
        total_success += file_success
        total_error += file_error
    
    total_files = len(htm_files) * len(output_formats)
    if not silent:
        print(f"📊 完了: 成功 {total_success}/{total_files}ファイル, エラー {total_error}ファイル")
    return total_success > 0

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="XBRL添付資料から証券コード別にテキストを抽出",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python3 attachments_output.py
    → このヘルプを表示
  
  python3 attachments_output.py 13010
    → downloads/attachments/13010/ の全HTMファイルを処理（Markdown形式）
  
  python3 attachments_output.py all md
    → 全証券コードをMarkdown形式で処理（進捗バーのみ）
  
  python3 attachments_output.py all md,txt,json
    → 全証券コードを3形式で処理（進捗バーのみ）
  
  python3 attachments_output.py all txt json md
    → 同上（順序自由）
  
  python3 attachments_output.py all log
    → 全証券コードを処理（詳細ログ表示、デフォルト形式）
  
  python3 attachments_output.py all md,txt log
    → 全証券コードを2形式で処理（詳細ログ表示）
  
  python3 attachments_output.py all log txt,json md
    → 同上（順序自由）
  
  python3 attachments_output.py all -f txt,json
    → 従来の-fオプションも利用可能
        """
    )
    
    parser.add_argument('target', nargs='?',
                       help='証券コード (5桁英数字) または "all" で全フォルダ処理')
    parser.add_argument('options', nargs='*',
                       help='出力形式 (md, txt, json, md,txt,json) と "log" の組み合わせ')
    parser.add_argument('-f', '--format', 
                       default='markdown',
                       help='出力形式 (例: markdown, txt, json, txt,json, markdown,txt,json)')
    parser.add_argument('--input-dir', 
                       default='downloads/attachments',
                       help='入力ベースディレクトリ (デフォルト: downloads/attachments)')
    parser.add_argument('--output-dir', 
                       default='output/attachments',
                       help='出力ベースディレクトリ (デフォルト: output/attachments)')
    
    args = parser.parse_args()
    
    # 引数なしの場合はヘルプを表示
    if not args.target:
        parser.print_help()
        return
    
    # 詳細ログ表示フラグ
    verbose_mode = False
    format_strings = []
    
    # 位置引数を解析
    for option in args.options:
        if option.lower() == 'log':
            verbose_mode = True
        else:
            format_strings.append(option)
    
    # 出力形式の決定
    if format_strings:
        # 位置引数に形式指定がある場合
        format_string = ','.join(format_strings)
    else:
        # 位置引数に形式指定がない場合は-fオプションまたはデフォルトを使用
        format_string = args.format
    
    # 出力形式の解析
    try:
        output_formats = parse_formats(format_string)
    except ValueError as e:
        print(f"エラー: {e}")
        print("有効な出力形式: markdown, txt, json")
        print("例: python3 attachments_output.py all md,txt,json")
        sys.exit(1)
    
    input_base_dir = Path(args.input_dir)
    output_base_dir = Path(args.output_dir)
    
    # 入力ディレクトリの存在確認
    if not input_base_dir.exists():
        print(f"エラー: 入力ディレクトリが見つかりません: {input_base_dir}")
        sys.exit(1)
    
    # 出力ベースディレクトリの作成
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    if args.target.lower() == 'all':
        # 全フォルダ処理
        print("🔍 証券コードフォルダを検索中...")
        security_codes = find_security_code_folders(input_base_dir)
        
        if not security_codes:
            print("エラー: 証券コードフォルダが見つかりません")
            sys.exit(1)
        
        print(f"📋 発見した証券コード: {len(security_codes)}フォルダ")
        print(f"📤 出力形式: {', '.join(output_formats)}")
        print(f"📂 出力先: {output_base_dir}")
        
        total_success = 0
        total_errors = 0
        
        for i, security_code in enumerate(security_codes, 1):
            # 進捗率計算
            progress_percent = (i / len(security_codes)) * 100
            
            # 進捗バー作成（20文字幅）
            bar_length = 20
            filled_length = int(bar_length * i // len(security_codes))
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            
            # 進捗表示
            if verbose_mode:
                print(f"\n[{i:4}/{len(security_codes):4}] {progress_percent:5.1f}% [{bar}] {security_code}")
            else:
                print(f"\r[{i:4}/{len(security_codes):4}] {progress_percent:5.1f}% [{bar}] {security_code}", end="", flush=True)
            
            success = process_security_code_folder(
                security_code, input_base_dir, output_base_dir, output_formats, silent=not verbose_mode
            )
            if success:
                total_success += 1
            else:
                total_errors += 1
        
        print(f"\n\n🎉 全体完了: 成功 {total_success}フォルダ, エラー {total_errors}フォルダ")
        
    else:
        # 特定フォルダ処理
        security_code = args.target
        
        # 証券コード形式チェック
        import re
        if not re.match(r'^[A-Za-z0-9]{5}$', security_code):
            print(f"エラー: 証券コードは5桁の英数字である必要があります: {security_code}")
            sys.exit(1)
        
        print(f"🎯 対象証券コード: {security_code}")
        print(f"📤 出力形式: {', '.join(output_formats)}")
        print(f"📂 出力先: {output_base_dir / security_code}")
        
        success = process_security_code_folder(
            security_code, input_base_dir, output_base_dir, output_formats
        )
        
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()