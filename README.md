# CV Tailor

Local web app that tailors your CV to match any job description and generates interview prep.

## Features

- Paste a job URL or job description text
- Upload your CV (DOCX or PDF)
- Get a tailored CV with relevant keywords woven in naturally
- Get interview prep: talking points, likely questions, skills to emphasize, gaps to address
- Download tailored CV as DOCX
- Download interview prep as Markdown

## Quick Start

```bash
cd cv-tailor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:8080

## Environment Variables

Create a `.env` file:

```
CLAUDE_API_KEY=your-anthropic-api-key
```

## How It Works

1. Fetches and parses the job description (from URL or pasted text)
2. Extracts your CV's structure and content from the uploaded file
3. Uses Claude to identify key skills, tools, and requirements from the job
4. Tailors each CV section by rephrasing existing content to match job language
5. Generates an interview preparation summary
6. Outputs a DOCX file preserving your original formatting

## Safety

- Never fabricates experience, skills, or qualifications
- Only rephrases and re-emphasizes what's already in your CV
- Includes a fabrication guard that rejects suspicious additions
