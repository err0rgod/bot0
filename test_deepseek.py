import sys
import os
from dotenv import load_dotenv

# Ensure we can import the llm module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from llm.client import LLMClient

def main():
    # Load .env explicitly to ensure DEEPSEEK_API_KEY is available
    load_dotenv()
    
    print("Testing DeepSeek LLM Integration...")
    
    try:
        client = LLMClient(provider="deepseek")
        print("[+] LLMClient instantiated successfully.")
    except Exception as e:
        print(f"[-] Failed to instantiate LLMClient: {e}")
        return

    sample_prompt = """
    Summarize the following fake cybersecurity news article in highly engaging, human-like, and slightly creative prose. 
    Break the content into small, highly readable paragraphs (2-4 lines max).
    
    Article Title: Global 'FakeRansom' Campaign Hits Thousands
    Article Content: Security researchers have discovered a massive wave of ransomware attacks dubbed 'FakeRansom'. Unlike traditional ransomware, FakeRansom does not actually encrypt files. Instead, it alters system UI elements to display a terrifying countdown timer, demanding 0.5 BTC to restore access. Over 50,000 systems across small businesses have been affected. The vulnerability stems from an unpatched browser extension. Users are advised to uninstall the extension immediately and reboot their systems in safe mode to remove the malware.
    
    Return ONLY the summary paragraphs.
    """

    print("\nSending sample test prompt to DeepSeek API...")
    try:
        response = client.generate(
            messages=[
                {"role": "system", "content": "You are a highly engaging cybersecurity writer."},
                {"role": "user", "content": sample_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        print("\n=== DeepSeek API Response ===")
        print(response)
        print("===============================\n")
        print("[+] Test completed successfully!")
    except Exception as e:
        print(f"[-] Generation failed: {e}")

if __name__ == "__main__":
    main()
