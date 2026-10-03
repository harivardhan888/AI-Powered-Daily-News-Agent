import json
from typing import List, Dict
import sys
import os

# Ensure we can import from News_Agents
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from News_Agents.bbc_news_agent import NewsScraper as BBCScraper
from News_Agents.cnn_news_agent import NewsScraper as CNNScraper
from News_Agents.youtube_news_agent import YoutubeNewsAgent
from News_Agents.google_news_agent import GoogleNewsScraper

def fetch_and_process_data():
    unified_data = []

    print("Fetching BBC News...")
    bbc_scraper = BBCScraper()
    bbc_articles = bbc_scraper.get_bbc_news(limit=7)
    for art in bbc_articles:
        unified_data.append({
            "source": f"BBC",
            "title": art.title,
            "url": art.url,
            "content": art.content
        })

    print("Fetching CNN News...")
    cnn_scraper = CNNScraper()
    cnn_articles = cnn_scraper.get_cnn_news(limit=7)
    for art in cnn_articles:
        unified_data.append({
            "source": f"CNN",
            "title": art.title,
            "url": art.url,
            "content": art.content
        })

    print("Fetching YouTube Transcripts...")
    yt_agent = YoutubeNewsAgent()
    yt_items = yt_agent.get_transcripts(limit_per_channel=1)
    unified_data.extend(yt_items) # they are already in dict format from my helper

    print(f"\nTotal items fetched: {len(unified_data)}")
    
    # Processing
    processed_data = preprocess_data(unified_data)
    
    return processed_data

def fetch_genre_data(genres: List[str]) -> Dict[str, List[Dict[str, str]]]:
    genre_data = {}
    scraper = GoogleNewsScraper()
    for genre in genres:
        print(f"Fetching Google News for Genre: {genre}...")
        articles = scraper.get_news_by_genre(genre, limit=7)
        unified_data = []
        for art in articles:
            unified_data.append({
                "source": art.source,
                "title": art.title,
                "url": art.url,
                "content": art.content
            })
        genre_data[genre] = preprocess_data(unified_data)
        
    return genre_data

def preprocess_data(data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen_titles = set()
    cleaned_data = []

    for item in data:
        # 1. Strip extra whitespace
        title = item.get("title", "").strip()
        content = item.get("content", "")
        if content:
             content = content.strip()
        else:
            content = ""

        # 2. Duplicate Removal (simple title check)
        if title in seen_titles:
            continue
        seen_titles.add(title)

        # 3. Limit content length
        if len(content) > 3000:
            content = content[:3000] + "..."

        cleaned_item = {
            "source": item["source"],
            "title": title,
            "url": item.get("url", ""),
            "content": content
        }
        cleaned_data.append(cleaned_item)

    return cleaned_data

if __name__ == "__main__":
    data = fetch_and_process_data()
    print("\n" + "="*50)
    print("FINAL PROCESSED DATA")
    print("="*50)
    print(json.dumps(data, indent=2))
