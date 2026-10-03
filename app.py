import os
import sys
import json
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure we can import from local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Import our cleaning pipeline
from Preprocessing.preprocessing import fetch_and_process_data, fetch_genre_data

# ==========================================
# CONFIGURATION
# ==========================================
# Ensure you have set the GROQ_API_KEY environment variable.
# You can set it via terminal: $env:GROQ_API_KEY="your_key"
# Or hardcode it here (not recommended for production).
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# ==========================================
# LANGSMITH CONFIGURATION
# ==========================================
# Set these in your environment or .env file
# export LANGCHAIN_TRACING_V2=true
# export LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
# export LANGCHAIN_API_KEY="your_langchain_api_key"
# export LANGCHAIN_PROJECT="news-agent-summarizer"

if os.environ.get("LANGCHAIN_TRACING_V2") == "true":
    if not os.environ.get("LANGCHAIN_API_KEY"):
         print("WARNING: LANGCHAIN_TRACING_V2 is true but LANGCHAIN_API_KEY is missing.")
    else:
         print(">>> LangSmith Tracing Enabled.")

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY environment variable not found.")
    print("Please set it, or the LLM call will fail.")

# Initialize the Groq Chat Model
# Using 'mixtral-8x7b-32768' or 'llama3-70b-8192' as commonly available powerful models on Groq.
llm = ChatGroq(
    temperature=0,
    model_name="qwen/qwen3.8-27b", 
    groq_api_key=GROQ_API_KEY
)

# Define the summarization prompt
summarize_prompt = ChatPromptTemplate.from_template(
    """
    You are a helpful news assistant.
    Summarize the following news content into strictly 3-4 lines.
    Capture the key points clearly.
    
    IMPORTANT: Return ONLY the summary text. Do not start with "Here is a summary" or similar phrases.

    Title: {title}
    Content: {content}

    Summary:
    """
)

# Create a chain
# Input: {"title": ..., "content": ...} -> Model -> Output (Str)
chain = summarize_prompt | llm | StrOutputParser()

def summarize_articles(articles):
    final_results = []
    for idx, article in enumerate(articles, start=1):
        try:
            print(f"\n[{idx}/{len(articles)}] Summarizing: {article['title']}")
            summary = chain.invoke({
                "title": article['title'],
                "content": article['content']
            })
            
            clean_summary = summary.strip()
            prefixes = ["Here is a summary", "Here's a summary", "The following is a summary", "Summary:"]
            for prefix in prefixes:
                if clean_summary.lower().startswith(prefix.lower()):
                    clean_summary = clean_summary[len(prefix):].strip().lstrip(":").strip()

            processed_article = {
                "source": article['source'],
                "title": article['title'],
                "url": article.get('url', ''),
                "summary": clean_summary
            }
            final_results.append(processed_article)
            print(f"Summary: {clean_summary}\n")
            print("-" * 50)
        except Exception as e:
            print(f"[ERROR] Could not summarize article: {e}")
    return final_results

def main():
    print(">>> PART 1: Fetching Unique Genres...")
    
    # Get unique genres from subscribers
    unique_genres = set()
    subscribers_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subscribers.json")
    if os.path.exists(subscribers_file):
        with open(subscribers_file, "r") as f:
            try:
                subs = json.load(f)
                for sub in subs:
                    if isinstance(sub, dict) and "genres" in sub:
                        unique_genres.update(sub["genres"])
            except:
                pass
                
    unique_genres = list(unique_genres)
    
    print(">>> PART 2: Fetching and Preprocessing Data...")
    
    all_data = {}
    
    # 1. Top News
    top_articles = fetch_and_process_data()
    all_data["Top News"] = top_articles
    
    # 2. Genres
    if unique_genres:
        genre_articles = fetch_genre_data(unique_genres)
        all_data.update(genre_articles)
        
    print(f"\n>>> PART 3: Summarizing using Groq LLM...")
    
    summarized_data = {}
    
    for category, articles in all_data.items():
        if not articles:
            continue
        print(f"\n--- Summarizing Category: {category} ---")
        summarized_data[category] = summarize_articles(articles)

    # Save to a JSON file
    output_filename = "summarized_news.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(summarized_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nDone! Summarized all categories.")
    print(f"Results saved to {output_filename}")

if __name__ == "__main__":
    main()
