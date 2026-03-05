from fpdf import FPDF
from pathlib import Path
import unicodedata


_FORMATS = {
    "classic":   {"heading_rgb": (0,   0,   0),   "font": "Helvetica", "caps": True},
    "modern":    {"heading_rgb": (0,   112, 192),  "font": "Helvetica", "caps": False},
    "executive": {"heading_rgb": (31,  73,  125),  "font": "Times",     "caps": True},
    "minimal":   {"heading_rgb": (80,  80,  80),   "font": "Helvetica", "caps": False},
}

L_MARGIN = 20
R_MARGIN = 20
BULLET_INDENT = 5   # mm extra indent for bullet lines


def _clean(text: str) -> str:
    """Replace non-latin1 characters to avoid fpdf encoding errors."""
    replacements = {
        "\u2013": "-", "\u2014": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2022": "*", "\u2026": "...",
        "\u00b7": "*", "\u25aa": "*", "\u25cf": "*", "\u25cb": "*",
        "\u25a0": "*",
    }
    out = []
    for ch in text:
        ch = replacements.get(ch, ch)
        try:
            ch.encode("latin-1")
            out.append(ch)
        except (UnicodeEncodeError, UnicodeDecodeError):
            out.append(unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode())
    return "".join(out)


class _CVPDF(FPDF):
    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def generate_pdf(
    sections: list,
    tailored_sections: dict,
    output_path: Path,
    format_key: str = "classic",
) -> None:
    fmt = _FORMATS.get(format_key, _FORMATS["classic"])
    font = fmt["font"]
    hr, hg, hb = fmt["heading_rgb"]

    pdf = _CVPDF(format="A4")
    pdf.set_margins(L_MARGIN, 20, R_MARGIN)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Effective content width
    eff_w = pdf.w - L_MARGIN - R_MARGIN          # ~170 mm
    bullet_w = eff_w - BULLET_INDENT              # ~165 mm

    for section in sections:
        if section.heading == "__HEADER__":
            lines = section.content_lines
            if not lines:
                continue
            pdf.set_font(font, "B", 18)
            pdf.set_text_color(0, 0, 0)
            pdf.set_x(L_MARGIN)
            pdf.multi_cell(eff_w, 10, _clean(lines[0]), align="C")
            pdf.set_font(font, "", 10)
            for line in lines[1:]:
                if line.strip():
                    pdf.set_x(L_MARGIN)
                    pdf.multi_cell(eff_w, 6, _clean(line), align="C")
            pdf.ln(4)
            continue

        # Section heading
        heading_text = section.heading.upper() if fmt["caps"] else section.heading
        pdf.set_text_color(hr, hg, hb)
        pdf.set_font(font, "B", 12)
        pdf.set_x(L_MARGIN)
        pdf.multi_cell(eff_w, 8, _clean(heading_text))

        # Rule
        y = pdf.get_y()
        pdf.set_draw_color(hr, hg, hb)
        pdf.set_line_width(0.4)
        pdf.line(L_MARGIN, y, pdf.w - R_MARGIN, y)
        pdf.ln(2)

        # Content
        pdf.set_text_color(30, 30, 30)
        pdf.set_font(font, "", 10)

        lines = tailored_sections.get(section.heading, section.content_lines)
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            is_bullet = stripped[0] in ("*", "\u2022", "-", "\u2013", "\u2014",
                                        "\u25aa", "\u25cf", "\u25cb", "\u25a0")
            if is_bullet:
                clean_line = _clean(stripped.lstrip("*\u2022-\u2013\u2014\u25aa\u25cf\u25cb\u25a0 "))
                # Bullet dot
                pdf.set_x(L_MARGIN + BULLET_INDENT)
                pdf.cell(4, 6, "-")
                # Save Y, set X for text, then multi_cell
                y_before = pdf.get_y()
                pdf.set_xy(L_MARGIN + BULLET_INDENT + 4, y_before)
                pdf.multi_cell(bullet_w - 4, 6, clean_line)
            else:
                pdf.set_x(L_MARGIN)
                pdf.multi_cell(eff_w, 6, _clean(stripped))

        pdf.ln(2)

    pdf.output(str(output_path))
