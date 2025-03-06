# Movie & TV Updates for Obsidian

This Python script aggregates recent movie and TV show data from [TMDb](https://www.themoviedb.org/) and [OMDb](http://www.omdbapi.com/), then generates beautifully formatted Markdown files (with YAML frontmatter) that you can import into your Obsidian vault. It groups content by release status (Released and Running, Just Released, Coming Soon) and by full language names, and includes key metadata such as cast, genres, language, IMDb rating, and Rotten Tomatoes scores for easy lookup and filtering.

## Features

- **Aggregates Data**: Pulls movie and TV show information using TMDb and enriches it with ratings and cast details from OMDb.
- **Date & Language Filtering**: Fetches only recent (past 4 weeks) or upcoming releases from regions like the US and India, and converts language codes to full names (e.g., `en` becomes `English`).
- **Grouping & Sorting**: Organizes entries into categories based on release status and groups them by language. Within each language group, items are sorted by descending IMDb rating.
- **YAML Frontmatter**: Generates YAML metadata with separate properties for base tags, genres, languages, and cast—allowing for advanced search and filtering in Obsidian.
- **Customizable & Aesthetic Output**: Produces aesthetically formatted Markdown notes for a clean and creative look in your Obsidian vault.

## Prerequisites

- **Python 3.7+** installed on your machine.
- The following Python packages (which you can install via pip):
  - `requests`
  - `python-dotenv`
  - `feedparser`
  - `ollama` (if you use AI summary generation; otherwise, this can be removed)

## Setup

1. **Clone this repository:**

   ```bash
   git clone https://github.com/yourusername/movie-updates.git
   cd movie-updates
   ```

2. **Set Up the Virtual Environment:**

   Create a virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   *(If you don’t have a `requirements.txt` file, you can manually install the packages:)*

   ```bash
   pip install requests python-dotenv feedparser ollama
   ```

4. **Configure Environment Variables:**

   Create a `.env` file in the repository root (this file will not be tracked by Git due to `.gitignore`):

   ```ini
   OBSIDIAN_VAULT_PATH=/path/to/your/Obsidian/Vault
   TMDB_API_KEY=your_tmdb_api_key
   TMDB_READ_ACCESS_TOKEN=your_tmdb_read_access_token
   OMDB_API_KEY=your_omdb_api_key
   ```

## Usage

Run the script from the command line:

```bash
python movies.py
```

The script will generate two Markdown files in your Obsidian vault directory:
- **Movie Updates** (e.g., `movie_updates_06-Mar-2025.md`)
- **TV Show Updates** (e.g., `tv_updates_06-Mar-2025.md`)

Each file will include YAML frontmatter with separate properties for base tags, genres, languages, and cast, followed by the organized and formatted list of movies or TV shows.

## Scheduling with Cron (Optional)

To run this script automatically every Saturday at midnight, add a crontab entry:

1. Open the crontab editor:

   ```bash
   crontab -e
   ```

2. Add the following line (adjust paths accordingly):

   ```
   0 0 * * 6 cd "/path/to/your/Obsidian/Vault" && /path/to/venv/bin/python movies.py >> movies_cron.log 2>&1
   ```

   - This command runs the script every Saturday at midnight.
   - Output is logged to `movies_cron.log` for debugging.

## Customization

- **Aesthetics:** You can further customize the Markdown formatting in the `generate_obsidian_entry` function.
- **Filtering:** Adjust the date range or regions in the script to suit your specific needs.
- **AI Summaries:** If you don’t need AI-generated summaries, you can remove the `ollama` references.
