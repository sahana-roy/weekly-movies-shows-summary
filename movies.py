import os
import requests
import feedparser
from datetime import datetime, timedelta
from dotenv import load_dotenv
import ollama

# Load environment variables
load_dotenv("movies_api.env")

# Configuration
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_READ_ACCESS_TOKEN = os.getenv("TMDB_READ_ACCESS_TOKEN")  # Must be set correctly in .env
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# Language mapping: convert TMDb language codes to full names
LANGUAGE_MAP = {
    "en": "English",
    "ko": "Korean",
    "hi": "Hindi",
    "ml": "Malayalam",
    "ta": "Tamil",
    "bn": "Bengali"
}

# Fetch Genre Mapping for movies or TV shows
def fetch_genre_mapping(content_type):
    url = f"https://api.themoviedb.org/3/genre/{content_type}/list"
    headers = {"Authorization": f"Bearer {TMDB_READ_ACCESS_TOKEN}", "Accept": "application/json"}
    params = {"language": "en-US"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"⚠️ Error fetching genre mapping for {content_type}: {response.status_code}")
        return {}
    genre_list = response.json().get("genres", [])
    return {genre["id"]: genre["name"] for genre in genre_list}

# Fetch Movie & TV Data from TMDb
def fetch_tmdb_data(endpoint, region, content_type):
    today_date = datetime.today().strftime('%Y-%m-%d')
    four_weeks_ago = (datetime.today() - timedelta(weeks=4)).strftime('%Y-%m-%d')
    url = f"https://api.themoviedb.org/3/{endpoint}"
    headers = {"Authorization": f"Bearer {TMDB_READ_ACCESS_TOKEN}", "Accept": "application/json"}
    params = {"language": "en-US", "region": region}
    
    if content_type == "tv":
        params.update({"first_air_date.gte": four_weeks_ago, "first_air_date.lte": today_date})
    else:
        params.update({"primary_release_date.gte": four_weeks_ago, "primary_release_date.lte": today_date})
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"⚠️ Error fetching data from TMDb for {region}: {response.status_code}")
        return []
    return response.json().get("results", [])

# Fetch IMDb Ratings and Cast from OMDb
def fetch_imdb_data(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
    print(f"🔍 Fetching IMDb data for: {title}")
    data = requests.get(url).json()
    return (data.get("imdbRating", "N/A"),
            data.get("Ratings", []),
            data.get("Released", "N/A"),
            data.get("Actors", "Unknown"))

# Fetch cast from TMDb (fallback)
def fetch_tmdb_cast(movie_id, content_type):
    url = f"https://api.themoviedb.org/3/{content_type}/{movie_id}/credits"
    headers = {"Authorization": f"Bearer {TMDB_READ_ACCESS_TOKEN}", "Accept": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return "Unknown"
    cast_data = response.json().get("cast", [])
    return ", ".join([actor["name"] for actor in cast_data[:5]]) if cast_data else "Unknown"

# Aggregate Movie & TV Data
def fetch_all_data(content_type):
    all_items = []
    seen_titles = set()
    four_weeks_ago = datetime.today() - timedelta(weeks=4)
    
    # Get genre mapping (for converting genre_ids to names)
    genre_mapping = fetch_genre_mapping(content_type)
    
    regions = ["US", "IN"]  # Fetch from both US and India
    new_items = []
    for region in regions:
        if content_type == "movie":
            new_items.extend(fetch_tmdb_data(f"discover/{content_type}", region, content_type))
            new_items.extend(fetch_tmdb_data("movie/upcoming", region, content_type))
        else:
            new_items.extend(fetch_tmdb_data(f"discover/{content_type}", region, content_type))
            new_items.extend(fetch_tmdb_data("tv/airing_today", region, content_type))
    
    for item in new_items:
        if item.get("original_language") not in ["en", "ko", "hi", "ml", "ta", "bn"]:
            continue
        title = item.get("title", item.get("name", "Unknown"))
        if title in seen_titles:
            continue
        seen_titles.add(title)
        imdb_rating, ratings, release_date, imdb_cast = fetch_imdb_data(title)
        rt_rating = next((r["Value"] for r in ratings if "Rotten Tomatoes" in r["Source"]), "N/A")
        summary = item.get("overview", "No summary available")
        cast = fetch_tmdb_cast(item.get("id"), content_type)
        
        # Map genres: if full genres not present, use genre_ids with mapping
        genres = "Unknown"
        if item.get("genres"):
            genres = ", ".join([g["name"] for g in item.get("genres")])
        elif item.get("genre_ids"):
            genres = ", ".join([genre_mapping.get(gid, "Unknown") for gid in item.get("genre_ids")])
        
        # Convert release_date to datetime object for filtering
        try:
            release_date_obj = datetime.strptime(release_date, '%d %b %Y') if release_date != "N/A" else None
        except ValueError:
            release_date_obj = None
        
        if release_date_obj and release_date_obj < four_weeks_ago:
            continue
        
        # Convert language code to full name
        lang_code = item.get("original_language", "Unknown")
        full_language = LANGUAGE_MAP.get(lang_code, lang_code)
        
        all_items.append({
            "title": title,
            "release_date": release_date,
            "imdb_rating": imdb_rating,
            "rt_rating": rt_rating,
            "genres": genres,
            "summary": summary,
            "cast": cast if cast != "Unknown" else imdb_cast,
            "release_date_obj": release_date_obj,
            "language": full_language
        })
    
    print(f"🔍 Total {content_type}s fetched: {len(all_items)}")
    return all_items

# Generate Obsidian Markdown with YAML frontmatter and grouping by language and descending IMDb rating
def generate_obsidian_entry(items, title, filename):
    today = datetime.today()
    # Build sets for metadata properties
    genres_set = {genre for m in items if m["genres"] != "Unknown" for genre in m["genres"].split(", ") if genre}
    languages_set = {m["language"] for m in items if m["language"] != "Unknown"}
    cast_set = {actor.strip() for m in items if m["cast"] != "Unknown" for actor in m["cast"].split(", ") if actor.strip()}
    
    # Generate YAML frontmatter with separate properties
    metadata = "---\n"
    metadata += f"title: {title} - {today.strftime('%Y-%m-%d')}\n"
    metadata += "base_tags:\n"
    for tag in ["Movies", "TV", "OTT", "Theater", "WeeklyReview"]:
        metadata += f"  - \"{tag}\"\n"
    metadata += "genres:\n"
    for tag in sorted(genres_set):
        metadata += f"  - \"{tag}\"\n"
    metadata += "languages:\n"
    for tag in sorted(languages_set):
        metadata += f"  - \"{tag}\"\n"
    metadata += "cast:\n"
    for tag in sorted(cast_set):
        metadata += f"  - \"{tag}\"\n"
    metadata += "---\n\n"
    
    # Start content with header
    content = metadata + f"# {title} - {today.strftime('%Y-%m-%d')}\n\n"
    
    # Sort items by IMDb rating (descending) and then by title
    items.sort(key=lambda x: (-float(x['imdb_rating']) if x['imdb_rating'] not in ['N/A', None] else 0, x['title']))
    
    # Categorize items
    released_running = [m for m in items if m['release_date_obj'] and m['release_date_obj'] <= today - timedelta(weeks=1)]
    just_released = [m for m in items if m['release_date_obj'] and today - timedelta(weeks=1) < m['release_date_obj'] <= today]
    coming_soon = [m for m in items if not m['release_date_obj'] or m['release_date_obj'] > today]
    
    for category, category_items in [
        ("🎬 Released and Running", released_running),
        ("🔥 Just Released", just_released),
        ("🎥 Coming Soon", coming_soon)
    ]:
        if category_items:
            content += f"## {category}\n\n"
            # Group by full language name
            lang_groups = {}
            for item in category_items:
                lang = item.get("language", "Unknown")
                lang_groups.setdefault(lang, []).append(item)
            for lang in sorted(lang_groups.keys()):
                content += f"### Language: {lang}\n\n"
                # Sort each language group by descending IMDb rating
                group_items = sorted(lang_groups[lang], key=lambda x: (-float(x['imdb_rating']) if x['imdb_rating'] not in ['N/A', None] else 0, x['title']))
                for item in group_items:
                    content += f"**[[{item.get('title', 'Unknown')}]]** (IMDb: {item.get('imdb_rating', 'N/A')})  \n"
                    content += f"*Release Date:* {item.get('release_date', 'Unknown')}  \n"
                    content += f"*Rotten Tomatoes:* {item.get('rt_rating', 'N/A')}  \n"
                    content += f"*Genres:* {item.get('genres', 'Unknown')}  \n"
                    content += f"*Cast:* {item.get('cast', 'Unknown')}  \n"
                    content += f"> {item.get('summary', 'No summary available')}\n\n"
    
    content += "---\n\n"
    
    file_path = f"{OBSIDIAN_VAULT_PATH}/{filename}_{today.strftime('%d-%b-%Y')}.md"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"✅ Obsidian entry created: {file_path}")

if __name__ == "__main__":
    movie_data = fetch_all_data("movie")
    tv_data = fetch_all_data("tv")
    generate_obsidian_entry(movie_data, "Movie Updates", "movie_updates")
    generate_obsidian_entry(tv_data, "TV Show Updates", "tv_updates")
