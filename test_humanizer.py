import sys
import os
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv(override=True)

from lib.humanizer import humanize_email, safety_filter

def test_humanizer():
    sample_html = """
    <h1>ZeroDay Weekly</h1>
    <p>Exciting news! We are launching new features today.</p>
    <ul>
        <li>Story 1: CVE-2026-0001 fix</li>
        <li>Story 2: New update available</li>
    </ul>
    <a href="http://localhost:8000/weekly">Read More</a>
    """
    
    print("--- Testing Humanization ---")
    human_text = humanize_email(sample_html, "Nirbhay", "cybersecurity news")
    print("\n[Humanized Text]:")
    print(human_text)
    print("\n" + "="*50 + "\n")
    
    print("--- Testing Safety Filter ---")
    passed = safety_filter(human_text)
    print(f"Safety Filter Passed: {passed}")
    
    if not passed:
        print("Reasons for failure (potential):")
        if any(w in human_text.lower() for w in ["exciting", "launch", "introducing", "features", "update"]):
            print("- Contains forbidden marketing words")
        lines = [l for l in human_text.split('\n') if l.strip()]
        if not (5 <= len(lines) <= 8):
            print(f"- Line count ({len(lines)}) out of range (5-8)")
        if human_text.count("http") > 1:
            print("- Too many links")

if __name__ == "__main__":
    test_humanizer()
