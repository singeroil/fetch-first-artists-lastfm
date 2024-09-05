import streamlit as st
import aiohttp
import asyncio
import pandas as pd
from datetime import datetime, timezone
from tzlocal import get_localzone
from io import BytesIO
import logging

API_KEY = st.secrets["LASTFM_API_KEY"]

# Inject custom CSS for button styling
st.markdown("""
    <style>
    .stDownloadButton button {
        background-color: #4CAF50;  /* Green */
        color: white;
        border-radius: 4px;
        border: none;
        padding: 8px 16px;
    }
    .stDownloadButton button:hover {
        background-color: #45a049;
        color: white;
    }
    .stDownloadButton button:active {
        background-color: #45a049;
        color: white; /* Ensure text stays white when clicked */
    }
    .stButton button {
        display: inline-block;
        background-color: transparent;
        border: none;
        font-size: 24px;
    }
    </style>
    """, unsafe_allow_html=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LIMIT = 200
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 1  # seconds between requests
BATCH_SIZE = 5       # Number of pages to fetch at once
BATCH_DELAY = 2       # Delay between each batch in seconds

# Generate the filename with latest scrobble timestamp
def generate_filename(username, latest_timestamp):
    return f"{username}_1st_scrobbles_{latest_timestamp}.xlsx"


async def fetch_page(session, url, page, retries=0):
    try:
        await asyncio.sleep(RATE_LIMIT_DELAY)  # Rate limiting
        async with session.get(f"{url}&page={page}") as response:
            response_json = await response.json()
            if 'error' in response_json:
                logging.error(f"API Error: {response_json['error']['message']}")
                raise ValueError(f"API Error: {response_json['error']['message']}")
            if 'recenttracks' not in response_json:
                logging.warning(f"Unexpected response format on page {page}: {response_json}")
                return {}
            return response_json
    except (aiohttp.ClientError, ValueError) as e:
        logging.error(f"Error fetching page {page}: {e}")
        if retries < MAX_RETRIES:
            logging.info(f"Retrying page {page} (attempt {retries + 1}/{MAX_RETRIES})")
            await asyncio.sleep(2 ** retries)  # Exponential backoff
            return await fetch_page(session, url, page, retries + 1)
        else:
            raise


async def fetch_in_batches(session, url, total_pages):
    responses = []
    progress_bar = st.progress(0)  # Initialize progress bar

    for i in range(1, total_pages + 1, BATCH_SIZE):
        tasks = [fetch_page(session, url, page) for page in range(i, min(i + BATCH_SIZE, total_pages + 1))]

        for idx, task in enumerate(asyncio.as_completed(tasks), start=i):
            response = await task
            responses.append(response)
            progress_bar.progress(int(idx / total_pages * 100))  # Update progress bar

        logging.info(f"Completed batch {i} to {min(i + BATCH_SIZE, total_pages)} of {total_pages}")

        await asyncio.sleep(BATCH_DELAY)  # Delay between batches

    progress_bar.progress(100)  # Ensure progress bar is set to 100%
    return responses


async def get_scrobbles(username, limit=200, from_timestamp=None):
    url = f"https://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user={username}&api_key={API_KEY}&format=json&limit={LIMIT}"
    
    if from_timestamp:
        url += f"&from={from_timestamp}"  # Fetch from specific timestamp if provided
    
    async with aiohttp.ClientSession() as session:
        first_page = await fetch_page(session, url, 1)
        if not first_page or 'recenttracks' not in first_page:
            raise ValueError("Failed to retrieve initial page or unexpected format")

        total_pages = int(first_page['recenttracks']['@attr']['totalPages'])
        st.write(f"Total pages to process: {total_pages}")
        logging.info(f"Total pages: {total_pages}")

        responses = await fetch_in_batches(session, url, total_pages)

        all_scrobbles = []
        for idx, response in enumerate(responses, start=1):
            logging.info(f"Processing page {idx} of {total_pages}")
            if not response or 'recenttracks' not in response:
                logging.warning(f"Unexpected response format on page {idx}")
                continue

            tracks = response['recenttracks']['track']
            if isinstance(tracks, dict):  # Only one track returned, make it a list
                tracks = [tracks]

            for track in tracks:
                if isinstance(track, dict):  # Ensure track is a dictionary
                    artist = track.get('artist', {})
                    album = track.get('album', {})
                    date = track.get('date', {})

                    # Ensure artist, album, and date are dictionaries before accessing keys
                    artist_name = artist.get('#text', 'Unknown') if isinstance(artist, dict) else 'Unknown'
                    track_name = track.get('name', 'Unknown')
                    album_name = album.get('#text', 'Unknown') if isinstance(album, dict) else 'Unknown'
                    scrobble_date = int(date.get('uts', 0)) if isinstance(date, dict) else 0

                    all_scrobbles.append({
                        'artist': artist_name,
                        'track': track_name,
                        'album': album_name,
                        'date': scrobble_date
                    })

        return all_scrobbles


def get_first_scrobble_dates(scrobbles):
    artist_first_scrobbles = {}

    for scrobble in scrobbles:
        artist = scrobble['artist']
        scrobble_date = scrobble['date']
        track = scrobble['track']
        album = scrobble['album']

        if artist not in artist_first_scrobbles or scrobble_date < artist_first_scrobbles[artist]['date']:
            artist_first_scrobbles[artist] = {
                'date': scrobble_date,
                'track': track,
                'album': album
            }

    return artist_first_scrobbles


def save_to_excel(artist_first_scrobbles, username, file_like_object):
    rows = []
    local_tz = get_localzone()

    # Sort by scrobble date
    artist_first_scrobbles = dict(sorted(artist_first_scrobbles.items(), key=lambda item: item[1]['date']))

    # Add numbering after sorting
    for idx, (artist, details) in enumerate(artist_first_scrobbles.items(), start=1):
        utc_date = datetime.fromtimestamp(details['date'], tz=timezone.utc)
        local_date = utc_date.astimezone(local_tz)
        readable_date = local_date.strftime('%Y-%m-%d %H:%M:%S')
        rows.append([idx, artist, details['track'], details['album'], readable_date])

    df = pd.DataFrame(rows, columns=['#', 'Artist', 'First Track', 'First Album', 'First Scrobbled Date'])
    df.sort_values(by='First Scrobbled Date', inplace=True)
    df.to_excel(file_like_object, index=False)


async def main():
    st.title("Initial Scrobble Retriever")

    # User input fields
    username = st.text_input("Enter your Last.fm username", "")
    from_timestamp = st.text_input("Enter start timestamp (optional):", "")

    if username:
        # Small triangle button for fetching scrobbles
        if st.button("Fetch Now ▼"):
            with st.spinner(''):
                try:
                    all_scrobbles = await get_scrobbles(username, from_timestamp=from_timestamp or None)
                    artist_scrobbles = get_first_scrobble_dates(all_scrobbles)

                    # Get the latest scrobble's timestamp for filename
                    latest_timestamp = max([details['date'] for details in artist_scrobbles.values() if isinstance(details, dict) and 'date' in details and isinstance(details['date'], int)])

                    output = BytesIO()
                    save_to_excel(artist_scrobbles, username, output)
                    output.seek(0)

                    # Provide download button with dynamic filename
                    st.download_button(
                        label="Download as Excel",
                        data=output,
                        file_name=generate_filename(username, latest_timestamp),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                except Exception as e:
                    st.error(f"Error fetching data: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())