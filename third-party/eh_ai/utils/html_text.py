# Part of the EH AI Suite by ERP Heritage.
"""Extract readable text from an HTML document.

Strips scripts, styles and markup, keeping headings, paragraphs and list text.
Falls back to a regex strip if lxml is unavailable.
"""
import re

try:
    from lxml import html as lxml_html
except ImportError:  # pragma: no cover - lxml ships with Odoo
    lxml_html = None

_TAG = re.compile(r"<[^>]+>")
_SCRIPT_STYLE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_BLANK_LINES = re.compile(r"\n\s*\n\s*\n+")


def html_to_text(content):
    if not content:
        return ""
    if lxml_html is not None:
        try:
            tree = lxml_html.fromstring(content)
            for element in tree.xpath("//script | //style | //noscript | //head"):
                element.getparent().remove(element)
            text = tree.text_content()
            return _BLANK_LINES.sub("\n\n", text).strip()
        except Exception:  # noqa: BLE001 - fall back to the regex strip
            pass
    text = _SCRIPT_STYLE.sub(" ", content)
    text = _TAG.sub(" ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return _BLANK_LINES.sub("\n\n", text).strip()
