import httpx
from bs4 import BeautifulSoup
from app.config import REQUEST_TIMEOUT, USER_AGENT


async def fetch_job_description(url: str) -> str:
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT, follow_redirects=True
    ) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup.find_all(
        ["script", "style", "nav", "header", "footer", "aside"]
    ):
        tag.decompose()

    selectors = [
        "[class*='job-description']",
        "[class*='jobDescription']",
        "[class*='description']",
        "[id*='job-description']",
        "[id*='jobDescription']",
        "article",
        "main",
        "[role='main']",
    ]
    for selector in selectors:
        el = soup.select_one(selector)
        if el and len(el.get_text(strip=True)) > 200:
            return clean_job_text(el.get_text(separator="\n", strip=True))

    body_text = (
        soup.body.get_text(separator="\n", strip=True)
        if soup.body
        else soup.get_text(separator="\n", strip=True)
    )
    return clean_job_text(body_text)


def clean_job_text(raw_text: str) -> str:
    lines = raw_text.split("\n")
    cleaned = [line.strip() for line in lines if len(line.strip()) > 2]
    return "\n".join(cleaned)
