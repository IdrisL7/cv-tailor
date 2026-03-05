from fpdf import FPDF
from pathlib import Path


# Format settings mirroring formatter.py
_FORMATS = {
    "classic":   {"heading_rgb": (0,   0,   0),   "font": "Helvetica", "caps": True},
    "modern":    {"heading_rgb": (0,   112, 192),  "font": "Helvetica", "caps": False},
    "executive": {"heading_rgb": (31,  73,  125),  "font": "Times",     "caps": True},
    "minimal":   {"heading_rgb": (80,  80,  80),   "font": "Helvetica", "caps": False},
}


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
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    for section in sections:
        if section.heading == "__HEADER__":
            lines = section.content_lines
            if not lines:
                continue
            # Name line – large bold centred
            pdf.set_font(font, "B", 18)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, lines[0], new_x="LMARGIN", new_y="NEXT", align="C")
            # Remaining header lines (subtitle, contact)
            pdf.set_font(font, "", 10)
            for line in lines[1:]:
                if line.strip():
                    pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(4)
            continue

        # ── Section heading ──────────────────────────────────────────────
        heading_text = section.heading.upper() if fmt["caps"] else section.heading
        pdf.set_text_color(hr, hg, hb)
        pdf.set_font(font, "B", 12)
        pdf.cell(0, 8, heading_text, new_x="LMARGIN", new_y="NEXT")

        # Horizontal rule
        y = pdf.get_y()
        pdf.set_draw_color(hr, hg, hb)
        pdf.set_line_width(0.4)
        pdf.line(20, y, 190, y)
        pdf.ln(2)

        # ── Section content ──────────────────────────────────────────────
        pdf.set_text_color(30, 30, 30)
        pdf.set_font(font, "", 10)

        lines = tailored_sections.get(section.heading, section.content_lines)
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            is_bullet = stripped[0] in ("•", "-", "–", "▪", "●", "○", "■")
            if is_bullet:
                clean = stripped.lstrip("•-–▪●○■ ")
                # Indent bullet
                pdf.set_x(25)
                pdf.cell(5, 6, "•")
                pdf.set_x(30)
                pdf.multi_cell(0, 6, clean)
            else:
                pdf.multi_cell(0, 6, stripped)

        pdf.ln(2)

    pdf.output(str(output_path))
