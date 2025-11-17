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
    Improved with retries and better error handling.
    """
    import time
    
    # Validate inputs
    if not category or not category.strip():
        category = "business"
    
    try:
        count = max(1, min(int(count), 10))  # Limit between 1-10
    except (ValueError, TypeError):
        count = 5
    
    category_clean = category.strip().lower()
    query = _CATEGORY_TO_QUERY.get(category_clean, f"latest {category_clean} news")
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            with DDGS(timeout=15) as ddgs:
                results = list(ddgs.news(
                    keywords=query,
                    region="wt-wt",
                    safesearch="off",
                    time=None,
                    max_results=max(count, 5)
                ))
            
            if not results:
                # Try generic news on retry
                if attempt < max_retries - 1:
                    query = "latest news"
                    time.sleep(1)
                    continue
                return f"I couldn't find any {category_clean} news at the moment, Boss. Please try again in a moment or try a different category."
            
            formatted = _format_news_items(results, count)
            if formatted and formatted != "No news available.":
                return formatted
            
        except Exception as e:
            logging.error(f"Error fetching {category_clean} news (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return f"I apologize, Boss. I encountered an issue fetching {category_clean} news. The service may be temporarily unavailable. Please try again in a moment."
    
    return f"I couldn't retrieve {category_clean} news at this time, Boss. Please try again later."

