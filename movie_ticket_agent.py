import requests
import asyncio
import webbrowser
import logging

MOVIE_KEY = "de44e1da55msh9c6d95e4809286bp155356jsnb5e905e1dffd"
MOVIEAPI_HOST = "imdb236.p.rapidapi.com"


def get_trending_movies():
    """
    Fetches top-rated movies using IMDb RapidAPI (Top 250 endpoint).
    Handles both list-based and dict-based responses.
    Improved with better error handling and fallbacks.
    """
    url = "https://imdb236.p.rapidapi.com/api/imdb/top250-movies"
    headers = {
        "x-rapidapi-key": MOVIE_KEY,
        "x-rapidapi-host": MOVIEAPI_HOST,
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        # Check for various error status codes
        if response.status_code == 401:
            return ["I apologize, Boss. There's an authentication issue with the movie service. The API key may need to be updated."]
        elif response.status_code == 403:
            return ["I'm sorry, Boss. Access to the movie service is currently restricted."]
        elif response.status_code == 429:
            return ["The movie service is currently rate-limited, Boss. Please try again in a few moments."]
        elif response.status_code == 500:
            return ["The movie service is experiencing server issues, Boss. Please try again later."]
        
        response.raise_for_status()
        
        try:
            data = response.json()
        except ValueError:
            return ["I received an invalid response from the movie service, Boss. Please try again later."]

        # Handle if API returns a list
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Try multiple possible keys
            items = data.get("data") or data.get("results") or data.get("movies") or []
            if not items and isinstance(data.get("message"), str):
                return [f"I couldn't retrieve movies, Boss. {data.get('message')}"]
        else:
            items = []

        if not items:
            return ["No trending movies found in the response, Boss. The service may be temporarily unavailable."]

        movies = []
        for item in items[:5]:
            if not isinstance(item, dict):
                continue
                
            # Support both response formats
            title = None
            if "titleText" in item:
                title_obj = item.get("titleText")
                title = title_obj.get("text") if isinstance(title_obj, dict) else title_obj
            
            # Try alternative title fields
            if not title:
                title = item.get("title") or item.get("name") or "Unknown Movie"
            
            # Get year
            year = None
            if "releaseYear" in item:
                year_obj = item.get("releaseYear")
                year = year_obj.get("year") if isinstance(year_obj, dict) else year_obj
            
            if not year:
                year = item.get("year") or item.get("release_date", "").split("-")[0] if item.get("release_date") else "N/A"
            
            movies.append(f"{title} ({year or 'N/A'})")

        return movies if movies else ["No trending movies found, Boss. Please try again later."]

    except requests.exceptions.Timeout:
        return ["The movie service timed out, Boss. Please try again in a moment."]
    except requests.exceptions.ConnectionError:
        return ["I couldn't connect to the movie service, Boss. Please check your internet connection and try again."]
    except requests.exceptions.HTTPError as e:
        return [f"I encountered an HTTP error with the movie service, Boss. Status code: {e.response.status_code if hasattr(e, 'response') else 'Unknown'}"]
    except Exception as e:
        logging.error(f"Error fetching trending movies: {e}")
        return [f"I apologize, Boss. An unexpected error occurred while fetching movies: {str(e)}. Please try again later."]


def book_ticket(event_type, location, date, num_tickets=1):
    """
    AI Ticket Booking Tool using IMDb RapidAPI.
    Opens relevant booking sites for movies, trains, or flights.
    Improved with better error handling and user-friendly messages.
    """
    try:
        event_type_lower = event_type.lower().strip() if event_type else ""
        location_clean = location.strip() if location else ""
        date_clean = date.strip() if date else ""
        
        if not event_type_lower:
            return "Boss, I need to know what type of ticket you'd like to book. Please specify: movie, train, or flight."
        
        if event_type_lower == "movie":
            trending = get_trending_movies()
            
            # Check for errors in the response
            if not trending or (len(trending) == 1 and ("Error" in trending[0] or "apologize" in trending[0] or "sorry" in trending[0].lower())):
                # If trending movies failed, still open booking site
                try:
                    location_url = location_clean.lower().replace(" ", "-") if location_clean else ""
                    if location_url:
                        webbrowser.open(f"https://in.bookmyshow.com/explore/movies-{location_url}")
                    else:
                        webbrowser.open("https://in.bookmyshow.com/")
                    
                    return (
                        f"{trending[0] if trending else ''}\n\n"
                        f"However, I've opened BookMyShow for you to browse available movies in {location_clean if location_clean else 'your area'} for {date_clean if date_clean else 'your preferred date'}."
                    )
                except Exception:
                    return trending[0] if trending else "I couldn't open the booking site, Boss. Please try accessing BookMyShow manually."

            movie_list = "\n".join(f"  • {movie}" for movie in trending[:5])
            location_url = location_clean.lower().replace(" ", "-") if location_clean else ""
            
            try:
                if location_url:
                    webbrowser.open(f"https://in.bookmyshow.com/explore/movies-{location_url}")
                else:
                    webbrowser.open("https://in.bookmyshow.com/")
            except Exception as e:
                logging.warning(f"Could not open browser: {e}")

            location_text = f" in {location_clean}" if location_clean else ""
            date_text = f" for {date_clean}" if date_clean else ""
            
            return (
                f"Here are some top trending movies according to IMDb:\n{movie_list}\n\n"
                f"I've opened BookMyShow to check seat availability{location_text}{date_text}, Boss."
            )

        elif event_type_lower == "train":
            try:
                webbrowser.open("https://www.irctc.co.in/")
                location_text = f" from {location_clean}" if location_clean else ""
                date_text = f" on {date_clean}" if date_clean else ""
                return f"I've opened IRCTC for you, Boss, to check train availability{location_text}{date_text}."
            except Exception as e:
                return f"I couldn't open IRCTC automatically, Boss. Please visit https://www.irctc.co.in/ manually. Error: {str(e)}"

        elif event_type_lower == "flight":
            try:
                webbrowser.open("https://www.skyscanner.co.in/")
                location_text = f" from {location_clean}" if location_clean else ""
                date_text = f" on {date_clean}" if date_clean else ""
                return f"I've opened Skyscanner for you, Boss, to check flights{location_text}{date_text}."
            except Exception as e:
                return f"I couldn't open Skyscanner automatically, Boss. Please visit https://www.skyscanner.co.in/ manually. Error: {str(e)}"

        else:
            return f"I apologize, Boss. '{event_type}' is not a valid booking type. Please specify: movie, train, or flight."
            
    except Exception as e:
        logging.error(f"Ticket booking error: {e}")
        return f"I apologize, Boss. An unexpected error occurred while booking tickets: {str(e)}. Please try again."


async def interactive_book_ticket(event_type: str, location: str, date: str, num_tickets: int = 1):
    """Async wrapper for LiveKit integration."""
    return await asyncio.to_thread(book_ticket, event_type, location, date, num_tickets)



