# Fetch First Scrobbles Dates

## Description

This application allows users to fetch and track the first scrobble dates for each artist from their Last.fm account. The data can be downloaded as an Excel file containing the artist's name, first track, first album, and the date/time of the first scrobble.

## Features

- Fetches scrobble history from Last.fm using the Last.fm API.
- Identifies the first scrobble date for each artist.
- Saves the result to an Excel file.
- Uses Streamlit for a simple user interface.

## Project Structure

```sh
fetch-first-scrobbles/
├── 1st-scrobbles.py     # Main Streamlit app script
├── requirements.txt     # Dependencies
├── LICENSE              # License information
└── README.md            # Project documentation
```

## Requirements

The following Python libraries are required to run this application:

- streamlit: For the web interface
- aiohttp: For asynchronous HTTP requests to the Last.fm API
- pandas: For handling and exporting data to Excel
- tzlocal: For converting UTC scrobble timestamps to local time
- openpyxl: For saving data to Excel files

## Usage

1. **Clone the repository:**

	```sh
	git clone https://github.com/singeroil/fetch-first-scrobbles.git
	cd fetch-first-scrobbles
	```

2. **Install dependencies:**

	- Install the required Python packages:

	```sh
	pip install -r requirements.txt
	```

3. **Add Last.fm API Key:**

	- You need to store your Last.fm API key in the secrets.toml file for Streamlit to access it. Create a secrets.toml file with the following content:

	```toml
	[general]
	LASTFM_API_KEY = "your_lastfm_api_key"
	```

4. **Run the application:**

	- Use the following command to run the Streamlit app:

	```sh
	streamlit run 1st-scrobbles.py
	```

5. **Input Last.fm Username:**

	- Enter your Last.fm username in the Streamlit interface and click Get First Scrobbles to fetch the data.
	- You can then click Download as Excel to save the results.

## Output

The app generates an Excel file named {username}_1st_scrobbles.xlsx, containing the following columns:
	- Artist
	- First Track
	- First Album
	- First Scrobbled Date (in local timezone)

## Deployment

1. To deploy this Streamlit app:
	Push your streamlit branch:

	```sh
	git push origin streamlit
	```

2. Deploy on Streamlit Cloud:
	Go to Streamlit Cloud, create a new app, and select the streamlit branch for deployment.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Contributions

Feel free to open an issue or submit a pull request if you'd like to contribute or have any suggestions!