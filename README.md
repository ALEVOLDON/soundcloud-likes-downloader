# SoundCloud Likes Downloader 🎵

A convenient GUI application for downloading your liked tracks from SoundCloud.

## Features 🚀

- Automatic collection of links from your likes page
- Smart filtering (skips mixes, podcasts, and playlists)
- Graphical interface with download progress
- Download speed visualization
- Saves all tracks in a dedicated folder
- Process and error logging
- Ability to stop downloading at any time

## Installation 🔧

1. Make sure you have Python 3.7 or higher installed
2. Clone the repository:
```bash
git clone https://github.com/ALEVOLDON/soundcloud-likes-downloader.git
cd soundcloud-likes-downloader
```

3. Create and activate virtual environment:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/MacOS
source .venv/bin/activate
```

4. Install dependencies:
```bash
pip install selenium matplotlib scdl
```

5. Install Chrome WebDriver:
   - Download [ChromeDriver](https://sites.google.com/chromium.org/driver/) for your Chrome version
   - Add it to PATH or place it in the project folder

## Usage 💻

1. Open `soundcloud_likes_downloader.py` and replace the URL in the `LIKES_URL` variable with your SoundCloud likes page URL:
```python
LIKES_URL = "https://soundcloud.com/your-username/likes"
```

2. Run the program:
```bash
python soundcloud_likes_downloader.py
```

3. Click "▶ Start Download" in the opened window
4. Monitor progress in the interface
5. All downloaded tracks will be in the `downloads` folder

## Filter Settings 🔍

You can customize which tracks to skip by editing the `EXCLUDE_KEYWORDS` list in `soundcloud_likes_downloader.py`:

```python
EXCLUDE_KEYWORDS = [
    "mix", "set", "podcast", "dj", "hour", "live", "sessions",
    "/sets/", "/likes/", "/reposts/", "playlist"
]
```

## Requirements 📋

- Python 3.7+
- Chrome browser
- ChromeDriver
- Internet access
- Sufficient disk space for downloading tracks

## Troubleshooting ⚠️

1. If you get a ChromeDriver error:
   - Make sure ChromeDriver version matches your Chrome version
   - Verify that ChromeDriver is available in PATH

2. If tracks are not downloading:
   - Check your internet connection
   - Make sure the track is available for download on SoundCloud
   - Check the logs in the interface

## License 📄

MIT License - do whatever you want, just give credit 😊

## Support 💖

If you have suggestions for improvements or found a bug, create an Issue or Pull Request! 