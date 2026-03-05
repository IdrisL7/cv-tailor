import anthropic
import asyncio
import json
import re
from app.config import CLAUDE_API_KEY, CLAUDE_MODEL, CLAUDE_MODEL_FAST, MAX_TOKENS
from app.services.docx_handler import CVSection


def _get_async_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=CLAUDE_API_KEY)


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


async def extract_keywords(job_description: str) -> dict:
    client = _get_async_client()
    response = await client.messages.create(
        model=CLAUDE_MODEL_FAST,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this job description and extract structured information.

Return a JSON object with these exact keys:
- "title": the job title
- "company": the company name (or "Unknown" if not found)
- "hard_skills": list of specific technical skills required
- "soft_skills": list of soft skills mentioned or implied
- "tools": list of specific tools, platforms, or technologies mentioned
- "qualifications": list of qualifications/certifications mentioned
- "responsibilities": list of key responsibilities (brief phrases)
- "keywords": list of the 15 most important keywords/phrases a recruiter would scan for

Return ONLY valid JSON, no other text.

JOB DESCRIPTION:
{job_description}""",
            }
        ],
    )
    return json.loads(_strip_json_fences(response.content[0].text))


async def tailor_cv_sections(
    sections: list[CVSection], job_keywords: dict
) -> dict[str, list[str]]:
    client = _get_async_client()

    sections_data = {}
    for s in sections:
        if s.heading == "__HEADER__":
            continue
        sections_data[s.heading] = s.content_lines

    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": f"""You are a professional CV/resume writer. Tailor this CV to better match the target job.

CRITICAL RULES:
1. NEVER fabricate, invent, or add experience, skills, projects, or qualifications the candidate does not already have.
2. ONLY rephrase, reorder emphasis, or adjust wording of EXISTING content.
3. Incorporate relevant keywords from the job naturally into existing bullet points where the candidate's experience genuinely supports them.
4. If a section has no relevant connection to the job, return it UNCHANGED.
5. Preserve the EXACT same number of lines per section.
6. Keep the same general tone and length per line.

TARGET JOB KEYWORDS:
{json.dumps(job_keywords, indent=2)}

CV SECTIONS (JSON: section heading -> list of content lines):
{json.dumps(sections_data, indent=2)}

Return a JSON object with the SAME keys (section headings) mapping to lists of tailored content lines. Each list MUST have the SAME number of items as the input.
Return ONLY valid JSON, no other text.""",
            }
        ],
    )
    result = json.loads(_strip_json_fences(response.content[0].text))

    # Fabrication guard: reject lines with too many new proper nouns
    for heading, new_lines in result.items():
        if heading in sections_data:
            result[heading] = _validate_no_fabrication(
                sections_data[heading], new_lines
            )

    return result


def _validate_no_fabrication(
    original_lines: list[str], tailored_lines: list[str]
) -> list[str]:
    original_text = " ".join(original_lines)
    validated = []
    for i, new_line in enumerate(tailored_lines):
        orig = original_lines[i] if i < len(original_lines) else ""
        new_proper = set(re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b", new_line))
        orig_proper = set(
            re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b", original_text)
        )
        introduced = new_proper - orig_proper
        if len(introduced) > 2:
            validated.append(orig)
        else:
            validated.append(new_line)
    return validated


async def generate_prep_summary(job_keywords: dict, sections: list[CVSection]) -> str:
    client = _get_async_client()

    cv_text = "\n\n".join(
        f"## {s.heading}\n" + "\n".join(s.content_lines)
        for s in sections
        if s.heading != "__HEADER__"
    )

    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": f"""Based on this job description analysis and CV, create an interview preparation summary in markdown format.

Include these sections:

## Key Talking Points
5-7 bullet points connecting the candidate's experience to job requirements.

## Likely Interview Questions
8-10 questions they should prepare for, with brief suggested angles based on their actual experience (not fabricated).

## Skills to Emphasize
Which of their existing skills are most relevant and how to frame them.

## Potential Gaps to Address
Areas where the job asks for something not clearly in the CV, with suggestions for how to honestly address the gap.

## Questions to Ask the Interviewer
5 thoughtful questions based on the role.

JOB ANALYSIS:
{json.dumps(job_keywords, indent=2)}

CANDIDATE CV:
{cv_text}

Return markdown formatted text.""",
            }
        ],
    )
    return response.content[0].text


async def generate_cover_letter(job_keywords: dict, sections: list[CVSection]) -> str:
    client = _get_async_client()

    # Pull candidate name from header section
    candidate_name = ""
    for s in sections:
        if s.heading == "__HEADER__" and s.content_lines:
            candidate_name = s.content_lines[0]
            break

    cv_text = "\n\n".join(
        f"## {s.heading}\n" + "\n".join(s.content_lines)
        for s in sections
        if s.heading != "__HEADER__"
    )

    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": f"""Write a professional cover letter for this candidate applying to this role.

RULES:
1. Use ONLY experience and skills that genuinely appear in the CV — never fabricate.
2. Directly connect the candidate's background to the specific role requirements.
3. Keep it to 3–4 paragraphs: opening, 2 experience paragraphs, closing.
4. Tone: confident, professional, concise. No clichés like 'I am writing to apply'.
5. Address it 'Dear Hiring Manager,' — do not invent a name.
6. Sign off with the candidate's name: {candidate_name or 'the candidate'}.
7. Do NOT include placeholders like [Company Name] — use the actual company name from the job data.

JOB DETAILS:
{json.dumps(job_keywords, indent=2)}

CANDIDATE CV:
{cv_text}

Return only the cover letter text, no extra commentary.""",
            }
        ],
    )
    return response.content[0].text


async def run_pipeline(
    sections: list[CVSection], job_keywords: dict
) -> tuple[dict[str, list[str]], str, str]:
    """Run tailoring, prep summary, and cover letter in parallel."""
    tailored, prep, cover = await asyncio.gather(
        tailor_cv_sections(sections, job_keywords),
        generate_prep_summary(job_keywords, sections),
        generate_cover_letter(job_keywords, sections),
    )
    return tailored, prep, cover
