"""Render this README's small Markdown subset into a standalone local preview.

Trusted repository input only, not a general-purpose Markdown sanitizer.
Run from the repository root. No dependencies or network requests required.
"""
from html import escape
from pathlib import Path
import re


def inline(text):
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"\[([^\]]+)\]\((https://[^)]+)\)", r'<a href="\2">\1</a>', text)


def render(source):
    output, in_code, in_list, in_table = [], False, False, False
    for line in source.splitlines():
        if line.startswith("```"):
            output.append("</code></pre>" if in_code else "<pre><code>")
            in_code = not in_code
            continue
        if in_code:
            output.append(escape(line))
            continue
        if not line.startswith("- ") and in_list:
            output.append("</ul>")
            in_list = False
        if not line.startswith("|") and in_table:
            output.append("</tbody></table></div>")
            in_table = False
        if not line.strip():
            continue
        if line.startswith("## "):
            output.append("<h2>" + inline(line[3:]) + "</h2>")
        elif line.startswith("- "):
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append("<li>" + inline(line[2:]) + "</li>")
        elif line.startswith("|"):
            if re.fullmatch(r"[| :\-]+", line):
                continue
            cells = line.strip("|").split("|")
            if not in_table:
                output.append('<div class="table-scroll"><table><thead><tr>' + "".join("<th>" + inline(c.strip()) + "</th>" for c in cells) + "</tr></thead><tbody>")
                in_table = True
            else:
                output.append("<tr>" + "".join("<td>" + inline(c.strip()) + "</td>" for c in cells) + "</tr>")
        elif line == "---":
            output.append("<hr>")
        elif line.lstrip().startswith("<"):
            output.append(line)
        else:
            output.append("<p>" + inline(line) + "</p>")
    return "\n".join(output)


if __name__ == "__main__":
    body = render(Path("README.md").read_text())
    page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>rachts · profile preview</title>
<style>
:root{color-scheme:dark light;--bg:#0d1117;--panel:#161b22;--text:#e6edf3;--muted:#aab1bd;--line:#30363d;--accent:#A89B8C}
@media(prefers-color-scheme:light){:root{--bg:#fff;--panel:#f6f8fa;--text:#1f2328;--muted:#59636e;--line:#d0d7de}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.75 "JetBrains Mono",ui-monospace,SFMono-Regular,Consolas,monospace}
main{max-width:980px;margin:40px auto;padding:28px;border:1px solid var(--line);border-top:3px solid var(--accent);border-radius:10px}
aside{color:var(--muted);font-size:12px;border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:24px}
h2{font-size:19px;font-weight:600;margin:36px 0 18px;padding-bottom:10px;border-bottom:1px solid var(--line)}
a{color:inherit;text-decoration:underline;text-decoration-color:var(--accent);text-underline-offset:4px}a:hover{color:var(--accent)}
code{font-family:inherit;background:var(--panel);padding:2px 5px;border-radius:4px}pre{background:var(--panel);border-left:3px solid var(--accent);padding:12px 16px;overflow:auto}pre code{padding:0}
img{max-width:100%;vertical-align:middle;height:auto}picture{display:block;margin:16px 0}p{margin:16px 0}li{margin:6px 0}sub{font-size:11px;color:var(--muted);overflow-wrap:anywhere}hr{border:0;border-top:1px solid var(--line);margin:30px 0}
.table-scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:12px}th,td{text-align:left;padding:12px;border:1px solid var(--line)}th{background:var(--panel)}td code{display:inline-block;margin:2px 0}
@media(max-width:600px){main{margin:8px;padding:14px}body{font-size:13px}h2{font-size:17px}}
</style></head><body><main><aside>~/ rachts / README.md · layout preview<br>Local SVGs work offline. Banner, badges and toolbox need internet. GitHub controls its own fonts and wrapping.</aside>
'''
    Path("preview.html").write_text(page + body + "\n</main></body></html>\n")
    print("Wrote preview.html")
