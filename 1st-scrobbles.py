import aiohttp
import asyncio
import pandas as pd
from datetime import datetime, timezone
from tzlocal import get_localzone
import logging
import time
import re
import os

# Import API settings from an external module
from API import API_KEY, LIMIT, MAX_RETRIES, RATE_LIMIT_DELAY, BATCH_SIZE, BATCH_DELAY

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

now_timestamp = int(time.time())
os.makedirs('result', exist_ok=True)

def generate_filename(username):
    return f"result/{username}_1st_scrobbles_{now_timestamp}.xlsx"

# Get user's registration timestamp using user.getInfo
async def get_user_registration_timestamp(username):
    url = f"https://ws.audioscrobbler.com/2.0/?method=user.getInfo&user={username}&api_key={API_KEY}&format=json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise ValueError(f"Failed to retrieve user info: {response.status}")
            user_info = await response.json()
            return int(user_info['user']['registered']['unixtime'])  # Return the registration Unix time

async def fetch_page(session, url, page, retries=0):
    try:
        await asyncio.sleep(RATE_LIMIT_DELAY)
        async with session.get(f"{url}&page={page}") as response:
            if response.status != 200:
                logging.error(f"API returned {response.status} for page {page}")
                raise ValueError(f"API returned {response.status} for page {page}")

            response_json = await response.json()

            if 'error' in response_json:
                logging.error(f"API Error: {response_json['error']['message']}")
                raise ValueError(f"API Error: {response_json['error']['message']}")
            if 'recenttracks' not in response_json:
                logging.warning(f"Unexpected response format on page {page}: {response_json}")
                return {}

            return response_json
    except (aiohttp.ClientError, ValueError, TypeError) as e:
        logging.error(f"Error fetching page {page}: {e}")
        if retries < MAX_RETRIES:
            logging.info(f"Retrying page {page} (attempt {retries + 1}/{MAX_RETRIES})")
            await asyncio.sleep(2 ** retries)
            return await fetch_page(session, url, page, retries + 1)
        else:
            raise

# Helper function to check if scrobble date is valid or if track is "now playing"
def get_valid_scrobble_date(track):
    # Check if the track is "now playing"
    if track.get('@attr', {}).get('nowplaying') == 'true':
        return None  # Skip "now playing" track

    # Get the scrobble timestamp and convert to integer if necessary
    date = track.get('date', {}).get('uts', 0)
    if isinstance(date, str):
        try:
            date = int(date)
        except ValueError:
            date = 0

    return date

async def fetch_in_batches(session, url, total_pages):
    responses = []
    
    for i in range(1, total_pages + 1, BATCH_SIZE):
        tasks = [fetch_page(session, url, page) for page in range(i, min(i + BATCH_SIZE, total_pages + 1))]

        try:
            batch_responses = await asyncio.gather(*tasks)
            responses.extend(batch_responses)
        except Exception as e:
            logging.error(f"Error during batch fetching: {e}")
            raise

        print(f"Processed {min(i + BATCH_SIZE - 1, total_pages)} / {total_pages} pages")
        await asyncio.sleep(BATCH_DELAY)

    return responses

async def get_scrobbles(username, registration_timestamp, limit=200):
    # Use 'from' parameter to only fetch scrobbles after the user's registration timestamp
    url = f"https://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user={username}&api_key={API_KEY}&format=json&limit={limit}&from={registration_timestamp}"
    
    async with aiohttp.ClientSession() as session:
        first_page = await fetch_page(session, url, 1)
        if not first_page or 'recenttracks' not in first_page:
            raise ValueError("Failed to retrieve initial page or unexpected format")

        total_pages = int(first_page['recenttracks']['@attr']['totalPages'])
        print(f"Total pages to process: {total_pages}")
        logging.info(f"Total pages: {total_pages}")

        responses = await fetch_in_batches(session, url, total_pages)

        all_scrobbles = []
        for idx, response in enumerate(responses, start=1):
            logging.info(f"Processing page {idx} of {total_pages}")
            if not response or 'recenttracks' not in response:
                logging.warning(f"Unexpected response format on page {idx}")
                continue

            tracks = response['recenttracks']['track']
            if isinstance(tracks, dict):
                tracks = [tracks]

            for track in tracks:
                if isinstance(track, dict):
                    artist = track.get('artist', {})
                    album = track.get('album', {})

                    # Get valid scrobble date (skip "now playing" tracks)
                    scrobble_date = get_valid_scrobble_date(track)

                    # Skip if the track is marked as "now playing"
                    if scrobble_date is None:
                        continue  # Skip now playing tracks

                    # Filter out scrobbles with invalid dates (before registration)
                    if scrobble_date < registration_timestamp:
                        continue

                    artist_name = artist.get('#text', 'Unknown') if isinstance(artist, dict) else 'Unknown'
                    track_name = track.get('name', 'Unknown')
                    album_name = album.get('#text', 'Unknown') if isinstance(album, dict) else 'Unknown'

                    all_scrobbles.append({
                        'artist': artist_name,
                        'track': track_name,
                        'album': album_name,
                        'date': scrobble_date
                    })

        return all_scrobbles

def get_first_scrobbles_dates(scrobbles):
    artist_first_scrobbles = {}

    for scrobble in scrobbles:
        artist = scrobble.get('artist', 'Unknown')
        scrobble_date = scrobble.get('date')
        track = scrobble.get('track', 'Unknown')
        album = scrobble.get('album', 'Unknown')

        if artist not in artist_first_scrobbles or scrobble_date < artist_first_scrobbles[artist]['date']:
            artist_first_scrobbles[artist] = {
                'date': scrobble_date,
                'track': track,
                'album': album
            }

    return artist_first_scrobbles

def clean_value(value):
    if value is None:
        return ''
    # Remove non-printable ASCII control characters (e.g., \x01)
    return re.sub(r'[\x00-\x1F\x7F]', '', str(value).strip())

def save_to_excel(artist_first_scrobbles, username):
    rows = []
    artist_first_scrobbles = dict(sorted(artist_first_scrobbles.items(), key=lambda item: item[1]['date']))

    local_tz = get_localzone()  # Get local timezone for conversion

    for idx, (artist, details) in enumerate(artist_first_scrobbles.items(), start=1):
        # Convert to local timezone at the very end
        utc_date = datetime.fromtimestamp(details['date'], timezone.utc)
        local_date = utc_date.astimezone(local_tz)
        readable_date = local_date.strftime('%Y-%m-%d %H:%M:%S')

        # Prepare data row with cleaned values
        row = [
            clean_value(idx),
            clean_value(artist),
            clean_value(details['track']),
            clean_value(details['album']),
            clean_value(readable_date)
        ]

        rows.append(row)

    # Log the row where an error occurs when saving to Excel
    df = pd.DataFrame(rows, columns=['#', 'Artist', 'First Track', 'First Album', 'First Scrobbled Date'])
    
    try:
        filename = generate_filename(username)
        df.to_excel(filename, index=False)
        print(f"Data saved to {filename}")
    except Exception as e:
        logging.error(f"Error writing to Excel: {e}")
        for row in rows:
            logging.error(f"Row causing issue: {row}")
        print(f"Error writing to Excel. Check logs for details.")

async def main():
    username = input("Enter your Last.fm username: ")

    if username:
        try:
            # Get user's registration timestamp
            registration_timestamp = await get_user_registration_timestamp(username)

            # Fetch scrobbles and filter by the registration timestamp
            all_scrobbles = await get_scrobbles(username, registration_timestamp)
            artist_scrobbles = get_first_scrobbles_dates(all_scrobbles)

            # Save the filtered scrobbles to an Excel file
            save_to_excel(artist_scrobbles, username)
        except Exception as e:
            logging.error(f"Error fetching data: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())