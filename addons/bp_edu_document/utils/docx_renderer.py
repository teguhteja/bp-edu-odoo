"""
DOCX Renderer — port dari rps_bp/edit_rps.py
Mengganti placeholder {field}, {list[0].key}, {nested.field} di template DOCX.

Tidak ada dependensi Odoo — pure python-docx + Pillow.
"""
import re
import io

from docx import Document
from docx.shared import Inches
from docx.oxml import parse_xml


# ─── Placeholder Parser ──────────────────────────────────────────────────────

def _parse_placeholder(placeholder: str) -> list:
    """'{cpl_prodi[0].kode}' → ['cpl_prodi', 0, 'kode']"""
    if placeholder.startswith('{') and placeholder.endswith('}'):
        placeholder = placeholder[1:-1]
    placeholder = placeholder.replace(' ', '')
    parts = re.split(r'\.|\[|\]', placeholder)
    parts = [p for p in parts if p]
    return [int(p) if p.isdigit() else p for p in parts]


def _get_value(data: dict, path_parts: list):
    """Navigate nested dict/list by path. Falls back to data['meta'][key] for flat placeholders."""
    if len(path_parts) == 1 and isinstance(data, dict):
        key = 'pangkat_golongan' if path_parts[0] == 'pangkat' else path_parts[0]
        if key not in data and 'meta' in data and key in data.get('meta', {}):
            return data['meta'][key]

    value = data
    try:
        for part in path_parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list):
                value = value[part]
            else:
                return None
            if value is None:
                return None
        return value
    except (IndexError, KeyError, TypeError):
        return None


# ─── Image helper ────────────────────────────────────────────────────────────

def _set_image_in_front_of_text(picture):
    """Change image wrapping to 'In Front of Text' via XML manipulation."""
    drawing = picture._inline.getparent()
    inline = drawing.find('.//wp:inline', namespaces=drawing.nsmap)
    if inline is None:
        return
    extent = inline.find('.//wp:extent', namespaces=inline.nsmap)
    effectExtent = inline.find('.//wp:effectExtent', namespaces=inline.nsmap)
    docPr = inline.find('.//wp:docPr', namespaces=inline.nsmap)
    cNvGraphicFramePr = inline.find('.//wp:cNvGraphicFramePr', namespaces=inline.nsmap)
    graphic = inline.find('.//a:graphic', namespaces=inline.nsmap)
    if None in [extent, docPr, graphic]:
        return
    anchor_xml = (
        '<wp:anchor xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'distT="0" distB="0" distL="114300" distR="114300" simplePos="0" '
        'relativeHeight="251658240" behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1">'
        '<wp:simplePos x="0" y="0"/>'
        '<wp:positionH relativeFrom="column"><wp:posOffset>0</wp:posOffset></wp:positionH>'
        '<wp:positionV relativeFrom="paragraph"><wp:posOffset>0</wp:posOffset></wp:positionV>'
        '</wp:anchor>'
    )
    anchor = parse_xml(anchor_xml)
    anchor.append(extent)
    if effectExtent is not None:
        anchor.append(effectExtent)
    anchor.append(parse_xml(
        '<wp:wrapNone xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"/>'
    ))
    anchor.append(docPr)
    if cNvGraphicFramePr is not None:
        anchor.append(cNvGraphicFramePr)
    anchor.append(graphic)
    drawing.replace(inline, anchor)


# ─── Text replacement ────────────────────────────────────────────────────────

def _replace_text(text: str, data: dict) -> str:
    if not text:
        return text
    pattern = r'\{[^{}]+\}'

    def replacer(match):
        ph = match.group(0)
        path = _parse_placeholder(ph)
        value = _get_value(data, path)
        if value is None:
            return ph
        if isinstance(value, list):
            return '\n'.join(str(v) for v in value)
        return str(value)

    return re.sub(pattern, replacer, text)


# ─── Paragraph & table processors ───────────────────────────────────────────

_IMAGE_PLACEHOLDERS = {
    '{dosen_sign}': ('dosen_sign', False),
    '{dosen_sign_small}': ('dosen_sign', True),
    '{mahasiswa_sign}': ('mahasiswa_sign', False),
    '{mahasiswa_sign_small}': ('mahasiswa_sign', True),
}


def _process_paragraph(paragraph, data: dict, images: dict):
    full_text = ''.join(run.text for run in paragraph.runs)
    if not full_text.strip():
        return

    # Image placeholder handling
    for placeholder, (key, is_small) in _IMAGE_PLACEHOLDERS.items():
        if placeholder in full_text and images.get(key):
            img_bytes = images[key]
            width = Inches(0.5) if is_small else Inches(1.0)
            for run in paragraph.runs:
                run.text = ''
            run = paragraph.add_run()
            try:
                from PIL import Image
                with Image.open(io.BytesIO(img_bytes)) as img:
                    if img.mode not in ('RGB', 'RGBA'):
                        img = img.convert('RGBA')
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    buf.seek(0)
                    pic = run.add_picture(buf, width=width)
                    _set_image_in_front_of_text(pic)
            except Exception:
                pass
            return

    new_text = _replace_text(full_text, data)
    if new_text == full_text:
        return
    if paragraph.runs:
        paragraph.runs[0].text = new_text
        for run in paragraph.runs[1:]:
            run.text = ''
    else:
        paragraph.add_run(new_text)


def _process_table(table, data: dict, images: dict):
    for row in table.rows:
        for cell in row.cells:
            for para in cell.paragraphs:
                _process_paragraph(para, data, images)


# ─── Public API ──────────────────────────────────────────────────────────────

def render(template_bytes: bytes, context: dict, images: dict = None) -> bytes:
    """
    Render template DOCX dengan context dict.

    Args:
        template_bytes : bytes dari file DOCX template
        context        : dict — keys matching placeholder names dalam template
        images         : dict — {'dosen_sign': bytes_png, 'mahasiswa_sign': bytes_png}

    Returns:
        bytes DOCX hasil render
    """
    if images is None:
        images = {}

    doc = Document(io.BytesIO(template_bytes))

    for para in doc.paragraphs:
        _process_paragraph(para, context, images)

    for table in doc.tables:
        _process_table(table, context, images)

    for section in doc.sections:
        for para in section.header.paragraphs:
            _process_paragraph(para, context, images)
        for para in section.footer.paragraphs:
            _process_paragraph(para, context, images)
        for table in section.header.tables:
            _process_table(table, context, images)
        for table in section.footer.tables:
            _process_table(table, context, images)

    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()
