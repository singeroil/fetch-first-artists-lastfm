# Fetch First Scrobble Dates

## Description

This Python script fetches the first scrobbled date for each unique artist from a Last.fm user's library and saves the results to an Excel file. The script uses asynchronous requests to handle large volumes of data efficiently.

## Features

- Fetches scrobble data asynchronously.
- Processes and extracts the first scrobbled date for each artist.
- Saves results to an Excel file in the `result/` directory.
- Handles API rate limiting and retries on failure.

## Requirements

- Python 3.8 or higher
- `aiohttp`
- `pandas`
- `tzlocal`

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

## Example

```sh
Enter Last.fm username: your_username
Fetching scrobbles...
Processing scrobbles...
Saving to Excel...
Data saved to 'result/your_username_1st_scrobbles.xlsx
```

## Notes

    The script handles large datasets by paginating through Last.fm's API responses.
    The result/ directory is created automatically if it does not exist.
    Ensure that your API key is valid and that you handle it securely.

## Contributing

	Feel free to open issues or submit pull requests for improvements or bug fixes.

## License

	This project is licensed under the MIT License. See the LICENSE file for details.