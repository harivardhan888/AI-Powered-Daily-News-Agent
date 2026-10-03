import urllib.parse
import feedparser
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Article:
    title: str
    url: str
    source: str
    content: Optional[str] = None

class GoogleNewsScraper:
    def get_news_by_genre(self, genre: str, limit: int = 3) -> List[Article]:
        encoded_genre = urllib.parse.quote(genre)
        rss_url = f"https://news.google.com/rss/search?q={encoded_genre}"
        
        feed = feedparser.parse(rss_url)
        articles: List[Article] = []

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            source = entry.get("source", {}).get("title", "Google News")

            if not title or not link:
                continue

            # We don't fetch full html for google news to keep it fast, 
            # we just use the title as summary/content
            articles.append(
                Article(
                    title=title,
                    url=link,
                    source=source,
                    content=title
                )
            )

            if len(articles) >= limit:
                break

        return articles

if __name__ == "__main__":
    scraper = GoogleNewsScraper()
    arts = scraper.get_news_by_genre("Politics", limit=3)
    for a in arts:
        print(a.title, a.url)
