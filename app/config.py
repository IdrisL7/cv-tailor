import os
import tempfile
from pathlib import Path

try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

# Use /tmp on serverless (Vercel), local output/ dir otherwise
if os.environ.get("VERCEL"):
    OUTPUT_DIR = Path(tempfile.gettempdir()) / "cv-tailor-output"
else:
    OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MODEL_FAST = "claude-haiku-4-5-20251001"
MAX_TOKENS = 4096

REQUEST_TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
