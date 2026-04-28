"""
Report Generator — Create Jupyter Notebook from OneDZ analysis results.

Data-driven: the analysis script controls ALL content via sections.
ReportGenerator is just a formatting layer — no hardcoded chart types.

Usage:
    ctx = AnalysisContext(
        title="Analysis Title",
        task_name="your_task",
        description="What was analyzed and why.",
    )
    ctx.add_markdown("## 1. Data Loading\\nLoading the OneDZ dataset...")
    ctx.add_code_cell("import polars as pl\\nprint('data loaded')",
                      outputs=["data loaded"])
    ctx.add_figure("path/to/kde.png", "KDE of zircon ages")
    ctx.add_finding("Key finding 1")
    ctx.add_finding("Key finding 2")

    gen = ReportGenerator(ctx)
    nb_path = gen.generate(output_dir=".")
    html_path = gen.to_html(nb_path)  # requires jupyter nbconvert
"""

import base64
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell, new_output


class AnalysisContext:
    """Flexible container for notebook content — populated by the analysis script."""

    def __init__(self, title: str, task_name: str = "analysis",
                 description: str = ""):
        self.title = title
        self.task_name = task_name
        self.description = description
        self.global_record_count = 0  # set to enable auto data-loading cell
        self.sections = []            # ordered list of section dicts
        self.findings = []            # bullet points for conclusion

    def add_markdown(self, content: str):
        """Add a markdown cell."""
        self.sections.append({"type": "markdown", "content": content})

    def add_code_cell(self, source: str,
                      outputs: Optional[list] = None):
        """Add a code cell with optional pre-baked outputs."""
        self.sections.append({
            "type": "code",
            "source": source.strip(),
            "outputs": outputs or [],
        })

    def add_figure(self, path: str, caption: str = ""):
        """Embed an image (PNG)."""
        self.sections.append({"type": "figure", "path": path, "caption": caption})

    def add_table(self, headers: list, rows: list, title: str = ""):
        """Add a markdown table."""
        lines = []
        if title:
            lines.append(f"**{title}**")
        h = " | ".join(str(h) for h in headers)
        sep = " | ".join("---" for _ in headers)
        lines.append(f"| {h} |")
        lines.append(f"| {sep} |")
        for row in rows:
            r = " | ".join(str(c) for c in row)
            lines.append(f"| {r} |")
        self.add_markdown("\n".join(lines))

    def add_finding(self, text: str):
        """Add a bullet point to the conclusion section."""
        self.findings.append(text)


class ReportGenerator:
    """Formats an AnalysisContext into Jupyter Notebook (.ipynb) and HTML."""

    CSS = """
    <style>
    /* ── Base ─────────────────────────────────────────── */
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", Helvetica, Arial, sans-serif;
        color: #1a2332;
        line-height: 1.7;
        max-width: 1000px;
        margin: 0 auto;
        padding: 2em 1.5em;
        background: #fafbfc;
    }
    h1, h2, h3, h4 { color: #0b1a2e; letter-spacing: -0.02em; }
    h1 { font-size: 2.4em; font-weight: 800; margin: 1.2em 0 0.4em; }
    h2 { font-size: 1.6em; font-weight: 700; margin: 1.6em 0 0.5em; border-bottom: 2px solid #e8edf4; padding-bottom: 0.3em; }
    h3 { font-size: 1.2em; font-weight: 600; margin: 1.2em 0 0.4em; }
    h4 { font-size: 1.05em; font-weight: 600; margin: 1em 0 0.3em; }
    p { margin: 0.6em 0; }
    a { color: #2d6da8; text-decoration: none; }
    a:hover { text-decoration: underline; }

    /* ── Title block ──────────────────────────────────── */
    .report-title {
        font-size: 2.8em; font-weight: 800; color: #0b1a2e;
        margin: 0.3em 0 0.05em; line-height: 1.2; letter-spacing: -0.03em;
    }
    .report-subtitle {
        font-size: 1.1em; color: #5a7a9a; margin: 0.2em 0 1.5em;
        font-weight: 400;
    }

    /* ── Highlight box ────────────────────────────────── */
    .highlight-box {
        padding: 1.2em 1.8em; margin: 1.2em 0;
        border-left: 5px solid #2d6da8;
        background: linear-gradient(135deg, #f0f6fc 0%, #e8f0f8 100%);
        border-radius: 6px;
        font-size: 0.95em;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .highlight-box strong { color: #1a3a5c; }

    /* ── Tables ───────────────────────────────────────── */
    table {
        border-collapse: collapse; margin: 1.2em 0; width: 100%;
        font-size: 0.92em;
        border-radius: 6px; overflow: hidden;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    th {
        background: #1a3a5c; color: white; font-weight: 600;
        padding: 0.65em 1em; text-align: left;
        border: none;
    }
    td {
        padding: 0.55em 1em; border: none;
        border-bottom: 1px solid #e8edf4;
    }
    tr:nth-child(even) td { background: #f7f9fc; }
    tr:hover td { background: #eef4fa; }

    /* ── Images ───────────────────────────────────────── */
    img {
        max-width: 100%; height: auto;
        border-radius: 6px; margin: 1em 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.10);
        display: block;
    }
    p.fig-caption {
        text-align: center !important; color: #5a7a9a;
        font-size: 0.9em; margin: -0.5em 0 1.5em;
    }

    /* ── Code ─────────────────────────────────────────── */
    code, pre {
        font-family: "SF Mono", "Cascadia Code", "Fira Code", Menlo, Consolas, monospace;
        font-size: 0.9em;
    }
    pre {
        background: #f4f6f9; padding: 1em; border-radius: 6px;
        overflow-x: auto; line-height: 1.5;
        border: 1px solid #e8edf4;
    }
    code {
        background: #f0f2f5; padding: 0.15em 0.4em; border-radius: 3px;
        color: #c7254e;
    }
    pre code { background: none; padding: 0; color: inherit; }

    /* ── Blockquote ───────────────────────────────────── */
    blockquote {
        border-left: 4px solid #2d6da8; margin: 1em 0;
        padding: 0.5em 1.2em; background: #f7f9fc;
        border-radius: 0 4px 4px 0;
    }
    blockquote p { margin: 0.3em 0; }

    /* ── Horizontal rule ──────────────────────────────── */
    hr {
        border: none; border-top: 1px solid #dce3ed;
        margin: 2em 0;
    }

    /* ── Findings / conclusion cards ──────────────────── */
    .finding-card {
        background: #f7fafd; border: 1px solid #dce8f2;
        border-radius: 6px; padding: 0.8em 1.2em; margin: 0.5em 0;
        border-left: 4px solid #27ae60;
        font-size: 0.95em;
        transition: background 0.15s;
    }
    .finding-card:hover { background: #eef4fa; }

    /* ── Emoji spacing ────────────────────────────────── */
    .highlight-box p, .finding-card p { margin: 0.2em 0; }

    /* ── Responsive ───────────────────────────────────── */
    @media (max-width: 700px) {
        body { padding: 1em; }
        .report-title { font-size: 1.8em; }
        table { font-size: 0.85em; }
    }

    /* ── Print ────────────────────────────────────────── */
    @media print {
        body { max-width: none; padding: 0; background: white; }
        img { box-shadow: none; break-inside: avoid; }
        table { box-shadow: none; }
    }
    </style>
    """

    def __init__(self, context: AnalysisContext):
        self.ctx = context

    def _img_b64(self, path: str) -> str:
        p = Path(path)
        if not p.exists():
            return ""
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _img_output(self, path: str) -> list:
        b64 = self._img_b64(path)
        return [new_output("display_data", data={"image/png": b64})] if b64 else []

    def _title_cell(self) -> list:
        css_inline = self.CSS.replace("<style>", "").replace("</style>", "").strip()
        return [new_markdown_cell(f"""<h1 class="report-title">{self.ctx.title}</h1>
<p class="report-subtitle">OneDZ Global Detrital Zircon Database · {datetime.now().strftime("%Y-%m-%d")}</p>
<style>
{css_inline}
</style>
---""")]

    def _loading_cell(self) -> list:
        if not self.ctx.global_record_count:
            return []
        code = '''"""Load the OneDZ dataset."""
import sys
from pathlib import Path

SKILL_DIR = Path.home() / ".claude" / "skills" / "onedz"
sys.path.insert(0, str(SKILL_DIR))

from scripts.onedz_handler import OneDZHandler, OneDZConfig
from datetime import datetime

config = OneDZConfig(output_dir=Path.cwd(), use_timestamp_output=False)
handler = OneDZHandler(config=config)
handler.load(source="csv", table="global_u-pb")
print(f"Global U-Pb data loaded: {handler.data.height:,} records")
'''
        cnt = self.ctx.global_record_count
        out = new_output("stream", name="stdout",
                         text=f"Global U-Pb data loaded: {cnt:,} records\n")
        return [new_code_cell(code, outputs=[out])]

    def _render_sections(self) -> list:
        cells = []
        for sec in self.ctx.sections:
            t = sec["type"]
            if t == "markdown":
                cells.append(new_markdown_cell(sec["content"]))
            elif t == "code":
                code_cell = new_code_cell(sec["source"])
                if sec.get("outputs"):
                    code_cell.outputs = sec["outputs"]
                cells.append(code_cell)
            elif t == "figure":
                path = sec["path"]
                caption = sec.get("caption", "")
                b64 = self._img_b64(path)
                if b64:
                    md = f'<img src="data:image/png;base64,{b64}" style="max-width:100%"/>'
                else:
                    md = f"![figure]({path})  *[image not found]*"
                if caption:
                    md += f'\n\n<p class="fig-caption">{caption}</p>'
                cells.append(new_markdown_cell(md))
        return cells

    def _summary_cell(self) -> list:
        if not self.ctx.findings:
            return []
        cards = "".join(f'<div class="finding-card">{f}</div>\n' for f in self.ctx.findings)
        cells = [new_markdown_cell("## 核心发现与结论")]
        cells.append(new_markdown_cell(cards))
        cells.append(new_markdown_cell(f"""---

<div style="text-align:center; padding: 2em 0; color: #888;">
Generated by <b>OneDZ Skill</b> · Li et al. (2025) Earth System Science Data<br>
{datetime.now().strftime("%Y-%m-%d %H:%M")}
</div>
"""))
        return cells

    def generate(self, output_dir: str = ".") -> str:
        """Build the .ipynb notebook."""
        css_clean = self.CSS.replace("<style>", "").replace("</style>", "").strip()
        nb = new_notebook()
        nb.metadata = {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
            "onedz_css": css_clean,
        }

        cells = []
        cells.extend(self._title_cell())
        cells.extend(self._loading_cell())
        cells.extend(self._render_sections())
        cells.extend(self._summary_cell())
        nb.cells = cells

        path = Path(output_dir) / f"{self.ctx.task_name}_report.ipynb"
        with open(path, "w", encoding="utf-8") as f:
            nbf.write(nb, f)
        print(f"Notebook generated: {path}")
        return str(path)

    def _inject_css(self, html_path: str, css: str) -> None:
        """Inject custom CSS into HTML <head> and remove escaped style block."""
        if not css:
            return
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            import re
            html = re.sub(
                r'<pre><code>&lt;style&gt;.*?&lt;/style&gt;</code></pre>',
                "", html, flags=re.DOTALL
            )
            html = html.replace("</head>", f"  <style>\n{css}\n  </style>\n</head>")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            print(f"  (CSS injection skipped: {e})")

    def to_html(self, notebook_path: str) -> Optional[str]:
        """Convert .ipynb to .html via jupyter nbconvert."""
        css_clean = self.CSS.replace("<style>", "").replace("</style>", "").strip()
        try:
            result = subprocess.run(
                ["jupyter", "nbconvert", "--to", "html",
                 "--no-input", "--no-prompt",
                 notebook_path, "--output-dir", str(Path(notebook_path).parent)],
                capture_output=True, text=True, timeout=120,
            )
            html_path = str(Path(notebook_path).with_suffix(".html"))
            if result.returncode == 0:
                self._inject_css(html_path, css_clean)
                print(f"HTML report generated: {html_path}")
                return html_path
            print(f"nbconvert stderr: {result.stderr[:200]}")
            return None
        except FileNotFoundError:
            print("jupyter nbconvert not found. Install with: pip install jupyter nbconvert")
            return None
        except Exception as e:
            print(f"HTML conversion failed: {e}")
            return None
