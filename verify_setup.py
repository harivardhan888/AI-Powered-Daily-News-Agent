import os
import requests
from dotenv import load_dotenv

def check_env():
    load_dotenv()
    print("=== NewsCraft Readiness Check ===\n")
    
    # 1. Check Groq
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            # Try a very small completion
            client.chat.completions.create(
                messages=[{"role": "user", "content": "hi"}],
                model="qwen/qwen3.8-27b",
                max_tokens=5
            )
            print("[✅] GROQ_API_KEY is valid.")
        except Exception as e:
            print(f"[❌] GROQ_API_KEY check failed: {e}")
    else:
        print("[⚠️] GROQ_API_KEY is missing.")

    # 2. Check Email Ops
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")
    if gmail_user and gmail_pass:
        print(f"[✅] Email configured for: {gmail_user} (Password hidden)")
    else:
        print("[⚠️] GMAIL configuration is missing.")

    print("\nCheck complete!")

if __name__ == "__main__":
    check_env()
