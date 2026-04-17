import os
import sys
import json
from dotenv import load_dotenv

# Ensure we can import from llm module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm.client import LLMClient

import asyncio
from utils import compress_content, async_rate_limit_and_retry

# Load environment variables from the root directory's .env
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(_env_path, override=True)

MODEL = "deepseek-chat"

def _get_client() -> LLMClient:
    return LLMClient(provider="deepseek")


@async_rate_limit_and_retry(max_retries=3, base_delay=6.0)
async def summarize_article(title: str, content: str) -> str:
    """
    Summarizes a cybersecurity news article using the Groq API (LLaMA 3.3 70B).
    Returns a short, readable paragraph-based summary.
    """
    client = _get_client()
    compressed = compress_content(content)

    prompt = f"""You are an expert cybersecurity analyst writing for a general audience.
Summarize the following news article in highly engaging, human-like, and slightly creative prose. 
Target a length of 300 to 600 words for the final summary.

Break the content into small, highly readable paragraphs (2-4 lines max) that keep the reader hooked line-by-line.
Your summary must capture: 
1. The Core Threat (Intro)
2. Who is affected & Impact (Insight)
3. Recommended actions (Takeaway)

Write in a modern tech newsletter tone (not robotic). Use smooth transitions and occasional emphasis (but NO overuse of emojis).
Avoid jargon and long dense blocks of text.

Article Title: {title}
Article Content: {compressed}

Return ONLY the summary paragraphs with no titles, headers, or introductory phrases."""

    response_text = await client.generate(
        messages=[
            {"role": "system", "content": "You are a helpful, creative cybersecurity writer who explains complex topics engagingly in concise paragraphs. You always aim for a word count between 300 and 600 words."},
            {"role": "user", "content": prompt}
        ],
        model=MODEL,
        temperature=0.6,
        max_tokens=1000
    )
    return response_text.strip()


@async_rate_limit_and_retry(max_retries=3, base_delay=6.0)
async def generate_two_level_summary(title: str, content: str) -> dict:
    """
    Generates a TWO-LEVEL summary for important news stories using Groq LLaMA 3.3 70B:
    - SHORT SUMMARY: 3 to 5 readable sentences for previews/email
    - DEEP SUMMARY: Multi-paragraph in-depth breakdown for the website article view

    Returns a dictionary with 'short_summary' and 'deep_summary'.
    """
    client = _get_client()
    compressed = compress_content(content)

    prompt = f"""You are an expert cybersecurity analyst writing for a newsletter aimed at both technical and non-technical readers.
Read the following article carefully and produce TWO summaries. The output must be engaging, human-like, and slightly creative.
Break any detailed content into small readable paragraphs (2-4 lines max) to avoid long dense blocks of text.

Build curiosity and keep the reader hooked line-by-line using a modern tech newsletter tone. Include smooth transitions between sections and occasional emphasis (without overusing emojis).

**[SHORT SUMMARY]**
Write a compelling hook structured in 1-2 short paragraphs. It must immediately tell the reader what happened, why it matters, and who is at risk. Be direct, clear, and highly engaging.

**[DEEP SUMMARY]**
Write a thorough, multi-paragraph breakdown with a target length of 300 to 600 words. 
Organise it into clearly separated, concise paragraphs (2-4 lines max each) following a clear structure (Intro -> Insight -> Takeaway):
- What exactly happened (incident/vulnerability)
- Who is affected and how
- The real-world impact and consequences
- Technical breakdown (explain the "how" simply)
- What should be done — mitigation and recommendations
- Why this matters in the bigger cybersecurity landscape

Format your response EXACTLY as follows (include the exact section headers):
[SHORT SUMMARY]
(your short summary paragraphs here)

[DEEP SUMMARY]
(your deep summary paragraphs here)

Article Title: {title}
Article Content: {compressed}"""

    text = await client.generate(
        messages=[
            {"role": "system", "content": "You are a professional cybersecurity journalist who writes in a highly engaging, clear, readable style using short paragraphs. For deep summaries, you always target 300-600 words."},
            {"role": "user", "content": prompt}
        ],
        model=MODEL,
        temperature=0.5,
        max_tokens=2000
    )

    text = text.strip()

    short_summary = "Short summary generation failed."
    deep_summary = "Deep summary generation failed."

    try:
        if "[DEEP SUMMARY]" in text:
            parts = text.split("[DEEP SUMMARY]")
            deep_summary = parts[1].strip()
            short_part = parts[0].replace("[SHORT SUMMARY]", "").strip()
            short_summary = short_part
    except Exception as e:
        print(f"[Error] Parsing two-level summary failed: {e}")
        short_summary = text  # Fallback: return everything in short

    return {
        "short_summary": short_summary,
        "deep_summary": deep_summary
    }


async def summarize_from_json(json_input) -> list:
    """
    Takes JSON input (either string or parsed dict) generated by v2.py
    and summarizes all news articles and CVEs inside it.
    """
    if isinstance(json_input, str):
        try:
            data = json.loads(json_input)
        except json.JSONDecodeError as e:
            print(f"[Error] Invalid JSON string: {e}")
            return []
    else:
        data = json_input

    results = []
    tasks = []
    metadata = [] # To keep track of what task belongs to what title/type

    # Process news
    for article in data.get("news", []):
        title = article.get("title", "")
        content = article.get("content", "")
        if title and content:
            tasks.append(summarize_article(title, content))
            metadata.append({"type": "news", "title": title})

    # Process CVEs
    for cve in data.get("cves", []):
        cve_id = cve.get("cve_id", "")
        desc = cve.get("description", "")
        if cve_id and desc:
            title = f"Vulnerability: {cve_id}"
            tasks.append(summarize_article(title, desc))
            metadata.append({"type": "cve", "title": title})

    if tasks:
        summaries = await asyncio.gather(*tasks)
        for i, summary in enumerate(summaries):
            results.append({
                "type": metadata[i]["type"],
                "title": metadata[i]["title"],
                "summary": summary
            })

    return results
