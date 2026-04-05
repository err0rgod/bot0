import re
import logging
from llm.client import LLMClient

logger = logging.getLogger(__name__)

def humanize_email(email_text, user_name, context="Cybersecurity updates"):
    """
    Converts email content into a casual, human-like plain text message.
    Uses LLM to ensure tone and length constraints.
    """
    # Pre-process: strip HTML to provide cleaner input to LLM
    clean_text = re.sub(r'<[^>]+>', '', email_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    client = LLMClient()
    
    prompt = f"""
    Rewrite this email as a personal, casual plain-text message from a developer to {user_name}.
    
    CONTEXT: {context}
    CONTENT: {clean_text}
    
    STRICT CONSTRAINTS:
    - Format: Plain text ONLY. No HTML, no bullets, no banners, no headings.
    - Tone: Casual and personal (like a real person typing).
    - Length: 5 to 8 lines max.
    - Forbidden Words: exciting, launch, introducing, features, update.
    - Links: Exactly 1 link (no buttons).
    - Closing: Add a natural soft question at the end (e.g., "let me know if this helps").
    - Personalization: Use the name {user_name} naturally.
    
    Make it feel like a developer personally wrote it.
    """

    try:
        humanized = client.generate([{"role": "user", "content": prompt}], max_tokens=300)
        humanized = humanized.strip()
        
        # Immediate safety check
        if not safety_filter(humanized):
            logger.warning("Humanized email failed safety filter. Retrying with stricter prompt...")
            # Simple fallback rewrite if the LLM failed to follow negative constraints
            return _fallback_humanize(user_name, context)
            
        return humanized
    except Exception as e:
        logger.error(f"Error humanizing email: {e}")
        return _fallback_humanize(user_name, context)

def safety_filter(email_text):
    """
    Returns True if the email passes human-like constraints.
    """
    lower_text = email_text.lower()
    forbidden = ["exciting", "launch", "introducing", "features", "update", "<tr>", "<td>", "http"] # http check is tricky, but we want max 1 link
    
    # Check forbidden words
    for word in forbidden[:5]: # just the marketing words for now
        if word in lower_text:
            return False
            
    # Check length (approximate)
    lines = [l for l in email_text.split('\n') if l.strip()]
    if not (3 <= len(lines) <= 10):
        return False
        
    # Check for HTML
    if "<" in email_text and ">" in email_text:
        return False
        
    # Check link count
    links = re.findall(r'https?://', email_text)
    if len(links) > 1:
        return False
        
    return True

def _fallback_humanize(user_name, context):
    """Simple hardcoded fallback if LLM fails."""
    return f"hey {user_name},\n\njust wanted to drop over some notes on {context} that I found recently. it seemed relevant to what we were looking at.\n\nhere is the link to the full list: {os.getenv('BASE_URL', 'http://localhost:8000')}/weekly\n\nlet me know if you catch anything interesting in there."

import os
