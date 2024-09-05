import streamlit as st
import aiohttp
import asyncio
import pandas as pd
from datetime import datetime, timezone
from tzlocal import get_localzone
from io import BytesIO
import logging

API_KEY = st.secrets["LASTFM_API_KEY"]

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LIMIT = 200
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 1  # seconds between requests

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

async def get_scrobbles(username, limit=200, st_progress_placeholder=None):
    url = f"https://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user={username}&api_key={API_KEY}&format=json&limit={limit}"
    async with aiohttp.ClientSession() as session:
        first_page = await fetch_page(session, url, 1)
        if not first_page or 'recenttracks' not in first_page:
            raise ValueError("Failed to retrieve initial page or unexpected format")

        total_pages = int(first_page['recenttracks']['@attr']['totalPages'])
        logging.info(f"Total pages: {total_pages}")

        tasks = [fetch_page(session, url, page) for page in range(1, total_pages + 1)]
        responses = await asyncio.gather(*tasks)

        all_scrobbles = []
        for idx, response in enumerate(responses, start=1):
            if st_progress_placeholder:
                st_progress_placeholder.progress((idx / total_pages) * 100, f"Processing page {idx} of {total_pages}")
            logging.info(f"Processing page {idx} of {total_pages}")
            if not response or 'recenttracks' not in response:
                logging.warning(f"Unexpected response format on page {idx}")
                continue

            tracks = response['recenttracks']['track']
            if isinstance(tracks, dict):  # Only one track returned
                tracks = [tracks]

            for track in tracks:
                if 'date' in track:
                    artist_name = track['artist']['#text']
                    track_name = track['name']
                    album_name = track['album']['#text'] if 'album' in track else 'Unknown'
                    scrobble_date = int(track['date']['uts'])
                    all_scrobbles.append({
                        'artist': artist_name,
                        'track': track_name,
                        'album': album_name,
                        'date': scrobble_date
                    })

        return all_scrobbles

def get_first_scrobble_dates(scrobbles):
    artist_first_scrobble = {}

    for scrobble in scrobbles:
        artist = scrobble['artist']
        scrobble_date = scrobble['date']
        track = scrobble['track']
        album = scrobble['album']

        if artist not in artist_first_scrobble or scrobble_date < artist_first_scrobble[artist]['date']:
            artist_first_scrobble[artist] = {
                'date': scrobble_date,
                'track': track,
                'album': album
            }

    return artist_first_scrobble

def save_to_excel(artist_first_scrobbles, username, file_like_object):
    rows = []
    local_tz = get_localzone()

    for artist, details in artist_first_scrobbles.items():
        utc_date = datetime.fromtimestamp(details['date'], tz=timezone.utc)
        local_date = utc_date.astimezone(local_tz)
        readable_date = local_date.strftime('%Y-%m-%d %H:%M:%S')
        rows.append([artist, details['track'], details['album'], readable_date])

    df = pd.DataFrame(rows, columns=['Artist', 'First Track', 'First Album', 'First Scrobbled Date'])
    df.sort_values(by='First Scrobbled Date', inplace=True)
    df.to_excel(file_like_object, index=False)

    logging.info(f"Data saved to '{username}_1st_scrobbles.xlsx'")

def main():
    st.title("First Scrobbles Tracker")
    username = st.text_input("Enter your Last.fm username", "")

    if username:
        st.write(f"Fetching data for {username}...")

        if st.button("Get First Scrobbles"):
            with st.spinner('Processing...'):
                try:
                    # Create a placeholder for the progress bar
                    progress_placeholder = st.progress(0)

                    # Fetch scrobbles and update progress
                    all_scrobbles = asyncio.run(get_scrobbles(username, st_progress_placeholder=progress_placeholder))
                    artist_scrobbles = get_first_scrobble_dates(all_scrobbles)

                    # Update the progress to 100%
                    progress_placeholder.progress(100, "Processing complete")

                    # Convert the results to a DataFrame and save to Excel in-memory
                    output = BytesIO()
                    save_to_excel(artist_scrobbles, username, output)
                    output.seek(0)

                    # Provide download button
                    st.download_button(
                        label="Download as Excel",
                        data=output,
                        file_name=f'{username}_1st_scrobbles.xlsx',
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                except Exception as e:
                    st.error(f"Error fetching data: {str(e)}")

if __name__ == "__main__":
    main()
