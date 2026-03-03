import fitz  # PyMuPDF
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from app.services.docx_handler import CVSection


def extract_text_from_pdf(file_path: Path) -> str:
    doc = fitz.open(str(file_path))
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def extract_sections_from_pdf(file_path: Path) -> list[CVSection]:
    raw_text = extract_text_from_pdf(file_path)
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    sections: list[CVSection] = []
    current_section: Optional[CVSection] = None

    for i, line in enumerate(lines):
        is_heading = _looks_like_heading(line)

        if is_heading:
            if current_section:
                sections.append(current_section)
            current_section = CVSection(
                heading=line,
                heading_paragraph_index=i,
                content_lines=[],
                paragraph_indices=[],
            )
        elif current_section:
            current_section.content_lines.append(line)
            current_section.paragraph_indices.append(i)
        else:
            current_section = CVSection(
                heading="__HEADER__",
                heading_paragraph_index=i,
                content_lines=[line],
                paragraph_indices=[i],
            )

    if current_section:
        sections.append(current_section)

    return sections


def _looks_like_heading(line: str) -> bool:
    if len(line) > 60:
        return False
    if line.isupper() and len(line) > 2:
        return True
    common_headings = [
        "experience", "education", "skills", "summary", "profile",
        "work experience", "professional experience", "employment",
        "certifications", "projects", "achievements", "interests",
        "languages", "references", "qualifications", "technical skills",
        "core competencies", "professional summary", "objective",
        "career summary", "key skills", "publications", "awards",
        "volunteer", "training", "memberships",
    ]
    if line.lower().rstrip(":") in common_headings:
        return True
    if line.endswith(":") and len(line) < 40:
        return True
    return False
