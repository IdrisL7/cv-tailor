from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

FORMATS = {
    "classic": {
        "label": "Classic",
        "description": "Clean & ATS-Friendly",
        "font": "Calibri",
        "name_size": 20,
        "heading_size": 12,
        "body_size": 10,
        "heading_color": (0, 0, 0),
        "name_bold": True,
        "margins": 1.0,
        "heading_caps": True,
    },
    "modern": {
        "label": "Modern",
        "description": "Bold Headers, Blue Accent",
        "font": "Arial",
        "name_size": 24,
        "heading_size": 12,
        "body_size": 10,
        "heading_color": (0, 112, 192),
        "name_bold": True,
        "margins": 0.75,
        "heading_caps": False,
    },
    "executive": {
        "label": "Executive",
        "description": "Senior & Director Level",
        "font": "Georgia",
        "name_size": 22,
        "heading_size": 13,
        "body_size": 10.5,
        "heading_color": (31, 73, 125),
        "name_bold": True,
        "margins": 1.0,
        "heading_caps": True,
    },
    "minimal": {
        "label": "Minimal",
        "description": "Clean One-Page Focus",
        "font": "Arial",
        "name_size": 18,
        "heading_size": 11,
        "body_size": 10,
        "heading_color": (80, 80, 80),
        "name_bold": False,
        "margins": 0.65,
        "heading_caps": False,
    },
}


def _is_visual_heading(para) -> bool:
    """Detect visually styled headings regardless of Word style."""
    if not para.runs:
        return False
    text = para.text.strip()
    if not text or len(text) > 80:
        return False
    first_run = para.runs[0]
    is_bold = first_run.bold is True
    is_upper = text.isupper()
    has_large_font = (
        first_run.font.size is not None and first_run.font.size.pt >= 13
    )
    style_name = para.style.name or ""
    is_heading_style = "Heading" in style_name
    return is_heading_style or is_bold or is_upper or has_large_font


def apply_format(doc: Document, format_key: str) -> Document:
    """Apply a named format template to a Document object."""
    fmt = FORMATS.get(format_key, FORMATS["classic"])

    # Page margins
    for section in doc.sections:
        margin = Inches(fmt["margins"])
        section.top_margin = margin
        section.bottom_margin = margin
        section.left_margin = margin
        section.right_margin = margin

    heading_color = RGBColor(*fmt["heading_color"])

    # Find first meaningful paragraph index (the name/header area)
    header_end_idx = 0
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text:
            continue
        # Header section is typically the first few centred or bold lines
        if i > 6:
            break
        if para.alignment == WD_ALIGN_PARAGRAPH.CENTER or (
            para.runs and para.runs[0].bold
        ):
            header_end_idx = i

    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text:
            continue

        style_name = para.style.name or ""
        is_heading_style = "Heading" in style_name
        is_visual = _is_visual_heading(para)

        is_header_area = i <= header_end_idx
        is_heading = (is_heading_style or is_visual) and not is_header_area

        for run in para.runs:
            run.font.name = fmt["font"]

            if is_header_area:
                # Name / subtitle area at the top
                run.font.size = Pt(fmt["name_size"] if i == 0 else fmt["body_size"] + 1)
                if i == 0:
                    run.bold = fmt["name_bold"]
                # Keep existing colour for contact details
            elif is_heading:
                run.font.size = Pt(fmt["heading_size"])
                run.bold = True
                run.font.color.rgb = heading_color
                if fmt["heading_caps"]:
                    run.font.all_caps = True
                else:
                    run.font.all_caps = False
            else:
                run.font.size = Pt(fmt["body_size"])
                # Don't override colour so hyperlinks stay blue

    return doc
