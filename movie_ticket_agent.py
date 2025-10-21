import requests
import asyncio
import webbrowser

MOVIE_KEY = "de44e1da55msh9c6d95e4809286bp155356jsnb5e905e1dffd"
MOVIEAPI_HOST = "imdb236.p.rapidapi.com"


def get_trending_movies():
    """
    Fetches top-rated movies using IMDb RapidAPI (Top 250 endpoint).
    Handles both list-based and dict-based responses.
    """
    url = "https://imdb236.p.rapidapi.com/api/imdb/top250-movies"
    headers = {
        "x-rapidapi-key": MOVIE_KEY,
        "x-rapidapi-host": MOVIEAPI_HOST,
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Handle if API returns a list
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "data" in data:
            items = data["data"]
        else:
            items = []

        movies = []
        for item in items[:5]:
            # Support both response formats
            title = (
                item.get("titleText", {}).get("text")
                if isinstance(item.get("titleText"), dict)
                else item.get("titleText", "Unknown")
            )
            year = (
                item.get("releaseYear", {}).get("year")
                if isinstance(item.get("releaseYear"), dict)
                else item.get("releaseYear", "N/A")
            )
            movies.append(f"{title or 'Unknown'} ({year or 'N/A'})")

        return movies if movies else ["No trending movies found."]

    except Exception as e:
        return [f"Error fetching trending movies: {str(e)}"]


def book_ticket(event_type, location, date, num_tickets=1):
    """
    AI Ticket Booking Tool using IMDb RapidAPI.
    Opens relevant booking sites for movies, trains, or flights.
    """
    try:
        if event_type.lower() == "movie":
            trending = get_trending_movies()
            if "Error" in trending[0]:
                return trending[0]

            movie_list = "\n".join(trending)
            webbrowser.open(f"https://in.bookmyshow.com/explore/movies-{location.lower()}")

            return (
                f"Here are some top trending movies according to IMDb:\n{movie_list}\n\n"
                f"Opening BookMyShow to check seat availability in {location} for {date}."
            )

        elif event_type.lower() == "train":
            webbrowser.open("https://www.irctc.co.in/")
            return f"Opening IRCTC to check train availability from {location} on {date}."

        elif event_type.lower() == "flight":
            webbrowser.open("https://www.skyscanner.co.in/")
            return f"Opening Skyscanner to check flights from {location} on {date}."

        else:
            return "Please specify a valid event type: movie, train, or flight."

    except Exception as e:
        return f"Ticket booking failed: {str(e)}"


async def interactive_book_ticket(event_type: str, location: str, date: str, num_tickets: int = 1):
    """Async wrapper for LiveKit integration."""
    return await asyncio.to_thread(book_ticket, event_type, location, date, num_tickets)



