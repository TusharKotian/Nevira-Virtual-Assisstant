import logging
from typing import List
from ddgs import DDGS


# Map simple categories to generic queries if source does not provide categories
_CATEGORY_TO_QUERY = {
    "business": "latest business news",
    "technology": "latest technology news",
    "tech": "latest technology news",
    "sports": "latest sports news",
    "entertainment": "latest entertainment news",
    "world": "latest world news",
    "politics": "latest politics news",
    "science": "latest science news",
    "health": "latest health news",
}


def _format_news_items(items: List[dict], count: int) -> str:
    formatted = []
    for i, item in enumerate(items[:count], start=1):
        title = item.get("title") or item.get("source") or "No title"
        # ddgs.news returns keys like title, source, date, url
        url = item.get("url") or item.get("link") or ""
        source = item.get("source") or "Unknown"
        date = item.get("date") or item.get("published") or ""
        formatted.append(
            f"{i}. {title}\n"
            f"Source: {source}{(' • ' + date) if date else ''}\n"
            f"Read more: {url}\n"
            "---------------------------------------------------"
        )
    return "\n".join(formatted) if formatted else "No news available."


def get_latest_news(category: str = "business", count: int = 5) -> str:
    """
    Fetch latest news using DuckDuckGo News (no API key required).
    Falls back to a generic query if the category is unknown.
    """
    try:
        query = _CATEGORY_TO_QUERY.get(category.lower(), f"latest {category} news")
        with DDGS() as ddgs:
            results = list(ddgs.news(keywords=query, region="wt-wt", safesearch="off", time=None, max_results=max(count, 5)))
        if not results:
            return "No news available."
        return _format_news_items(results, count)
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return f"Error fetching news: {str(e)}"

