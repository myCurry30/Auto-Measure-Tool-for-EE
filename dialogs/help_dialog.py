"""Help dialog — embedded user manual with chapter-index navigation."""
import os
import re
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QSplitter,
                                QTreeWidget, QTreeWidgetItem, QTextBrowser,
                                QPushButton, QWidget, QFileDialog)
from PySide6.QtCore import Qt


# ═══════════════════════════════════════════════════════════════════════════════
# Markdown → HTML converter (handles the manual's formatting)
# ═══════════════════════════════════════════════════════════════════════════════

def md_to_html(text: str) -> str:
    """Convert a minimal Markdown subset to HTML."""
    lines = text.split('\n')
    html = []
    in_table = False
    in_ul = False
    in_ol = False
    in_code_block = False
    code_lines = []

    def flush_list():
        nonlocal in_ul, in_ol
        if in_ul:
            html.append('</ul>')
            in_ul = False
        if in_ol:
            html.append('</ol>')
            in_ol = False

    def flush_table():
        nonlocal in_table
        if in_table:
            html.append('</tbody></table>')
            in_table = False

    for line in lines:
        # Code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                html.append(f'<pre><code>{"".join(code_lines)}</code></pre>')
                code_lines = []
                in_code_block = False
            else:
                flush_list()
                flush_table()
                in_code_block = True
            continue
        if in_code_block:
            code_lines.append(line + '\n')
            continue

        # Horizontal rule
        if line.strip() == '---':
            flush_list()
            flush_table()
            html.append('<hr>')
            continue

        # Table
        if '|' in line and line.strip().startswith('|'):
            flush_list()
            cells = [c.strip() for c in line.strip('|').split('|')]
            if all(c.replace('-', '').replace(':', '').strip() == '' for c in cells):
                continue  # separator row
            tag = 'th' if not in_table else 'td'
            row_html = '<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>'
            if not in_table:
                html.append('<table border="1" cellpadding="4" cellspacing="0">'
                            '<thead>' + row_html + '</thead><tbody>')
                in_table = True
            else:
                html.append(row_html)
            continue
        else:
            if in_table:
                # Table ended — check if next line is also a table row or not
                # Simple heuristic: if not starting with |, table ended
                flush_table()

        # Headings
        stripped = line.strip()
        if stripped.startswith('### '):
            flush_list()
            html.append(f'<h3 id="{_anchor_id(stripped[4:])}">{_inline(stripped[4:])}</h3>')
            continue
        if stripped.startswith('## '):
            flush_list()
            html.append(f'<h2 id="{_anchor_id(stripped[3:])}">{_inline(stripped[3:])}</h2>')
            continue
        if stripped.startswith('# '):
            flush_list()
            html.append(f'<h1>{_inline(stripped[2:])}</h1>')
            continue

        # Checkbox list
        cb_match = re.match(r'^- \[(.)\] (.+)', stripped)
        if cb_match:
            if not in_ul:
                flush_list()
                html.append('<ul class="checklist">')
                in_ul = True
            checked = cb_match.group(1) != ' '
            chk = '☑' if checked else '☐'
            html.append(f'<li class="checklist">{chk} {_inline(cb_match.group(2))}</li>')
            continue

        # Unordered list
        ul_match = re.match(r'^- (.+)', stripped)
        if ul_match:
            if not in_ul:
                flush_list()
                html.append('<ul>')
                in_ul = True
            html.append(f'<li>{_inline(ul_match.group(1))}</li>')
            continue

        # Ordered list
        ol_match = re.match(r'^\d+\. (.+)', stripped)
        if ol_match:
            if not in_ol:
                flush_list()
                html.append('<ol>')
                in_ol = True
            html.append(f'<li>{_inline(ol_match.group(1))}</li>')
            continue

        # Empty line — close lists
        if not stripped:
            flush_list()
            html.append('<p>')
            continue

        # Regular paragraph
        flush_list()
        html.append(f'<p>{_inline(stripped)}</p>')

    # Flush any remaining open structures
    flush_list()
    flush_table()
    if in_code_block:
        html.append(f'<pre><code>{"".join(code_lines)}</code></pre>')

    return '\n'.join(html)


def _inline(text: str) -> str:
    """Convert inline markdown to HTML."""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # Images
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
    return text


def _anchor_id(heading: str) -> str:
    """Generate anchor ID from heading text (e.g. '1. 环境准备' → '1-环境准备')."""
    # Remove leading digits+dot+space, replace spaces with hyphens
    h = re.sub(r'^\d+\.\s*', '', heading)
    return h.replace(' ', '-')


# ═══════════════════════════════════════════════════════════════════════════════
# Chapter extraction
# ═══════════════════════════════════════════════════════════════════════════════

def extract_chapters(md_text: str) -> list[dict]:
    """Extract H2 and H3 headings with their anchor IDs from markdown.

    Returns list of {level, title, anchor}.
    """
    chapters = []
    for line in md_text.split('\n'):
        line = line.strip()
        if line.startswith('## ') and not line.startswith('### '):
            title = line[3:].strip()
            # Skip "目录" TOC section
            if title == '目录':
                continue
            chapters.append({
                'level': 2,
                'title': title,
                'anchor': _anchor_id(title),
                'children': []
            })
        elif line.startswith('### '):
            title = line[4:].strip()
            if chapters:
                chapters[-1]['children'].append({
                    'level': 3,
                    'title': title,
                    'anchor': _anchor_id(title),
                })
    return chapters


# ═══════════════════════════════════════════════════════════════════════════════
# Help Dialog
# ═══════════════════════════════════════════════════════════════════════════════

class HelpDialog(QDialog):
    """Resizable dialog with sidebar chapter tree and HTML content viewer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("用户操作手册 — EE Power On AutoTool V2.1")
        self.setMinimumSize(900, 640)
        self.resize(960, 700)

        # ── Load and parse manual ──────────────────────────────────────────
        self._md_text = self._load_manual()
        # Strip the document title block (H1 + subtitle + author + first HR)
        # — the Windows title bar already identifies the manual
        md_text = self._strip_title_block(self._md_text)
        self._html = md_to_html(md_text)
        self._chapters = extract_chapters(md_text)

        self._setup_ui()

    # ── Title block stripping ────────────────────────────────────────────
    @staticmethod
    def _strip_title_block(text: str) -> str:
        """Remove the document title block (H1 + metadata lines up to first HR).

        The Windows title bar already shows "用户操作手册 — EE Power On
        AutoTool V2.1", so the H1 heading, subtitle, and author lines in
        the markdown are redundant and would waste vertical space.
        """
        lines = text.split('\n')
        # Find the first heading (`# `) and the first `---` after it
        h1_idx = None
        hr_idx = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if h1_idx is None and stripped.startswith('# ') and not stripped.startswith('## '):
                h1_idx = i
            if h1_idx is not None and stripped == '---':
                hr_idx = i
                break
        if h1_idx is not None and hr_idx is not None and hr_idx > h1_idx:
            # Remove from h1_idx through hr_idx (inclusive), plus any blank
            # lines immediately after the HR
            end = hr_idx + 1
            while end < len(lines) and lines[end].strip() == '':
                end += 1
            return '\n'.join(lines[:h1_idx] + lines[end:])
        return text

    # ── File loading ───────────────────────────────────────────────────────
    def _load_manual(self) -> str:
        """Load the markdown manual file, searching multiple locations."""
        import sys
        search_paths = []

        # PyInstaller frozen: data files extracted to sys._MEIPASS
        if getattr(sys, 'frozen', False):
            search_paths.append(os.path.join(sys._MEIPASS, 'Doc', '用户操作手册.md'))
            # Also check next to the exe
            search_paths.append(os.path.join(os.path.dirname(sys.executable), 'Doc', '用户操作手册.md'))

        # Development: relative to this source file
        # dialogs/help_dialog.py → ../Doc/用户操作手册.md
        search_paths.append(
            os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Doc', '用户操作手册.md')))

        for p in search_paths:
            norm = os.path.normpath(p)
            if os.path.exists(norm):
                with open(norm, 'r', encoding='utf-8') as f:
                    return f.read()

        # Fallback: embedded minimal manual
        return self._fallback_manual()

    def _fallback_manual(self) -> str:
        return """# EE Power On AutoTool V2.1

用户操作手册文件未找到。请确认 `Doc/用户操作手册.md` 已正确打包。

支持的示波器：MSO4/5/6、DPO7000、DPO5000
测试类型：Sequence（时序）、Monotony（单调性）
"""

    # ── UI ─────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Splitter: sidebar + content ───────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)

        # -- Sidebar --
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(4, 6, 4, 4)
        sidebar_layout.setSpacing(4)

        # -- Save button --
        save_btn = QPushButton("💾 另存为…")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #F5F5F7;
                border: 1px solid #E5E5E7;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
                color: #1D1D1F;
            }
            QPushButton:hover {
                background: #EBEBED;
                border-color: #D1D1D6;
            }
        """)
        save_btn.clicked.connect(self._save_as)
        sidebar_layout.addWidget(save_btn)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(18)
        self.tree.setRootIsDecorated(True)
        self.tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # suppress focus rect on click
        self.tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                background: #FAFAFA;
                font-size: 13px;
                padding: 4px;
            }
            QTreeWidget::item {
                padding: 5px 8px;
                border-radius: 4px;
                color: #1D1D1F;
            }
            QTreeWidget::item:hover {
                background-color: rgba(0, 122, 255, 0.08);
            }
            QTreeWidget::item:selected {
                background-color: #007AFF;
                color: white;
            }
            QTreeWidget::item:has-children {
                font-weight: 600;
            }
            QTreeWidget::item:focus {
                outline: none;
                border: none;
            }
        """)

        # Populate tree
        for ch in self._chapters:
            parent = QTreeWidgetItem(self.tree, [ch['title']])
            parent.setData(0, Qt.UserRole, ch['anchor'])
            parent.setExpanded(True)
            for sub in ch['children']:
                child = QTreeWidgetItem(parent, [sub['title']])
                child.setData(0, Qt.UserRole, sub['anchor'])

        self.tree.itemClicked.connect(self._on_chapter_clicked)
        sidebar_layout.addWidget(self.tree)
        sidebar_widget.setMinimumWidth(180)
        sidebar_widget.setMaximumWidth(260)
        splitter.addWidget(sidebar_widget)

        # -- Content --
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet("""
            QTextBrowser {
                border: none;
                background: white;
                padding: 20px 32px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        self.browser.setHtml(self._html_with_style())
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 720])

        layout.addWidget(splitter)

    def _html_with_style(self, body_html: str | None = None) -> str:
        if body_html is None:
            body_html = self._html
        css = """
        <style>
            body { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; color: #1D1D1F; line-height: 1.8; }
            h1 { font-size: 22px; margin-top: 0; padding-bottom: 8px; border-bottom: 2px solid #E5E5E7; }
            h2 { font-size: 18px; margin-top: 28px; padding-bottom: 4px; border-bottom: 1px solid #E5E5E7; }
            h3 { font-size: 15px; margin-top: 20px; color: #333; }
            table { border-collapse: collapse; width: 100%; margin: 12px 0; }
            table th { background: #F5F5F7; text-align: left; padding: 6px 10px; font-weight: 600; }
            table td { padding: 6px 10px; border-bottom: 1px solid #E5E5E7; }
            code { background: #F0F0F4; padding: 1px 5px; border-radius: 3px; font-size: 13px; }
            pre { background: #F5F5F7; padding: 12px 16px; border-radius: 6px; overflow-x: auto; }
            pre code { background: none; padding: 0; }
            a { color: #007AFF; text-decoration: none; }
            hr { border: none; border-top: 1px solid #E5E5E7; margin: 24px 0; }
            ul.checklist { list-style: none; padding-left: 0; }
            li.checklist { padding: 2px 0; }
            b { color: #1D1D1F; }
            img { max-width: 100%; }
        </style>
        """
        return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{css}</head><body>{body_html}</body></html>"

    def _on_chapter_clicked(self, item, column):
        anchor = item.data(0, Qt.UserRole)
        if anchor:
            self.browser.scrollToAnchor(anchor)

    # ── Save As ──────────────────────────────────────────────────────────
    def _save_as(self):
        """Export the manual as a standalone HTML or Markdown file."""
        path, fmt = QFileDialog.getSaveFileName(
            self,
            "另存为用户操作手册",
            "用户操作手册.html",
            "HTML 文件 (*.html);;Markdown 文件 (*.md)",
        )
        if not path:
            return  # user cancelled

        try:
            if path.lower().endswith('.md'):
                # Save original markdown
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self._md_text)
            else:
                # Render full markdown (with title block) as styled HTML
                full_html = md_to_html(self._md_text)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self._html_with_style(full_html))
        except OSError as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "保存失败", f"无法写入文件：\n{e}")
