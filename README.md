# Fetch First Scrobble Dates

## Description

This Python script fetches the first scrobbled date for each unique artist from a Last.fm user's library and saves the results to an Excel file. The script uses asynchronous requests to handle large volumes of data efficiently.

## Features

- Fetches scrobble data asynchronously from Last.fm using their API.
- Processes and extracts the **first scrobble date** for each artist in the user's listening history.
- Saves results to an **Excel file** in the `result/` directory with the filename format `username_1st_scrobbles_<timestamp>.xlsx`.
- Automatically handles **API rate limiting**, retries on failure, and fetches data in batches.
- Provides parameters such as **MAX_RETRIES**, **LIMIT**, **RATE_LIMIT_DELAY**, **BATCH_SIZE**, and **BATCH_DELAY**, that can be adjusted to control the frequency and volume of API requests.
- Filters out invalid scrobble dates (e.g., "now playing" tracks) and ensures no scrobbles before the user's registration date are processed.
- Provides detailed logging for any errors, including problematic data rows that cause issues during the writing process to Excel.
- Removes **non-printable ASCII control characters** to ensure Excel compatibility, while still preserving characters from other languages.

## Requirements

- Python 3.8 or higher
- `aiohttp`: For asynchronous HTTP requests.
- `pandas`: For processing and writing data to Excel.
- `tzlocal`: For converting timestamps to the user's local time.
- `openpyxl`: (optional) Required if you want to work with `.xlsx` files in Excel format.

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/yourusername/fetch-first-scrobble-dates.git
    cd fetch-first-scrobble-dates
    ```

2. **Install dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

3. **Set your Last.fm API key:**
   
   Replace `YOUR_API_KEY_HERE` in the script with your actual Last.fm API key. You can obtain an API key from [Last.fm API](https://www.last.fm/api). Follow these steps to obtain one:

    1. Go to the [Last.fm API page](https://www.last.fm/api).
    2. Log in with your Last.fm account. If you don't have an account, you'll need to create one.
    3. Click on "Create an API account" or "Register for an API key."
    4. Fill in the required details:
        - **Application Name:** Choose a name for your application (e.g., "Fetch First Scrobbles").
        - **Application Website:** You can provide a URL or leave it blank.
        - **Description:** Provide a brief description of your application.
    5. Submit the form to receive your API key.
    6. Copy the API key provided.

## Usage

1. **Run the script:**

    ```sh
    python 1st-scrobbles.py
    ```

2. **Input your Last.fm username when prompted.**

3. **Check the `result/` directory for the generated Excel file.**

## Result Sample

| #  | Artist               | First Track                             | First Album                               | First Scrobbled Date   |
|----|----------------------|-----------------------------------------|-------------------------------------------|------------------------|
| 1  | Coheed and Cambria    | In Keeping Secrets of Silent Earth: 3   | Live At The Starland Ballroom             | 2009-06-20 11:42:57    |
| 2  | Soko                 | The Dandy Cowboys                       | Not Sokute                                | 2009-06-20 12:49:14    |
| 3  | I Was a Cub Scout     | Save Your Wishes                        | I Want You to Know That There Is Always Hope | 2009-06-20 13:19:40    |
| ...| ...                  | ...                                     | ...                                       | ...                    |

## Notes

    The script handles large datasets by paginating through Last.fm's API responses.
    The result/ directory is created automatically if it does not exist.
    Ensure that your API key is valid and that you handle it securely.

## Contributing

	Feel free to open issues or submit pull requests for improvements or bug fixes.

## License

	This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.