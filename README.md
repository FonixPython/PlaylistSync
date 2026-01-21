# PlaylistSync

PlaylistSync is a small desktop application to synchronize playlists from streaming services (currently includes YouTube Music support) and download/organize tracks into a local music library. It provides a PyQt6 GUI frontend and a backend with downloading, caching, and library management functionality.

Note: The repository appears to be work-in-progress. This README is based on inspecting source files (src/main.py, src/backend/*). View the repository here: https://github.com/FonixPython/PlaylistSync

---

## Features
- Download tracks from YouTube Music (yt-dlp / ytmusicapi)
- Manage local library (library.json) with per-playlist folders and playlist ID metadata
- Cache artwork and downloaded files to speed repeated operations
- Configurable download settings (codec, quality, temp/cache paths, filename template)
- Multi-threaded download/processing using a simple thread pool
- PyQt6 GUI with a dark Fusion-style theme

---

## Requirements
- Python 3.10+ (project uses recent typing features)
- ffmpeg installed and available on PATH

Python dependencies (inferred from code):
- PyQt6
- yt_dlp
- ytmusicapi
- requests
- ping3
- pillow (PIL)
- numpy
- imageio-ffmpeg
- mutagen
- eyed3

Example (install via pip):
```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install PyQt6 yt-dlp ytmusicapi requests ping3 pillow numpy imageio-ffmpeg mutagen eyed3
```
If a `requirements.txt` is added to the repo, prefer `pip install -r requirements.txt`.

---

## Installation
1. Clone the repository:
```bash
git clone https://github.com/FonixPython/PlaylistSync.git
cd PlaylistSync
```
2. (Recommended) Create/activate a virtual environment (see above).
3. Install dependencies (see Requirements).
4. Ensure ffmpeg is installed and available on PATH.
5. Run the app:
```bash
python src/main.py
```

---

## Usage
- On first run the app creates a `config.json` with defaults and a library file inside the configured download folder (default `./Music/library.json`).
- Typical flow:
  1. Launch the app (`python src/main.py`).
  2. Add playlists (YouTube Music playlist IDs) through the GUI.
  3. Sync / download missing tracks.
  4. Configure download settings (codec, quality, filename template, paths) either in `config.json` or via the GUI if available.

---

## Configuration
On first launch a `config.json` is created (defaults approximate):

```json
{
    "download_settings": {
        "encode_codec": "mp3",
        "encode_quality": 8,
        "temp_path": ".TEMP",
        "cache_path": ".CACHE",
        "download_path": "./Music",
        "filename_template": "$title$ - $artist$",
        "cover_mode": "crop",
        "max_threads": 8
    }
}
```

Important settings
- `filename_template` — template for saving tracks (supports `$title$`, `$artist$`, etc.)
- `encode_codec`, `encode_quality` — output format and quality
- `max_threads` — number of worker threads used for downloads/processing

The code uses atomic writes when saving config and library files to minimize corruption.

---

## Project layout (key files)
- `src/main.py` — application entrypoint, UI initialization, dark theme
- `src/gui/` — PyQt6 GUI components (MainWindow and widgets)
- `src/backend/config.py` — config management (defaults, atomic save)
- `src/backend/library.py` — library storage (library.json), atomic save and backup
- `src/backend/functions.py` — high-level backend logic (cache, hashing, interactions)
- `src/backend/helper_functions.py` — utilities (download, hashing, image handling, tagging)
- `src/backend/services/youtube.py` — YouTube Music integration (yt-dlp, ytmusicapi)
- `src/backend/threader.py` — simple thread pool (QueueSystem)

---

## Development notes & known limitations
- No LICENSE file is present in the repository. Add a license (e.g., MIT) if you want reuse permissions.
- The project depends on system `ffmpeg`.
- Some functions and service methods appear partially implemented files).
- No tests were found; consider adding unit tests for config, library, and helper utilities.
- ytmusicapi can require additional setup (cookies/auth headers) depending on usage.

---

## Troubleshooting
- Downloads fail: confirm internet connectivity and that `ffmpeg` is installed.
- ytmusicapi playlist fetch failures: ensure any required auth/cookie setup for ytmusicapi is configured.
- GUI issues: ensure PyQt6 is installed and you are using a supported Python version.

---

## Example quick start
1. Create virtual environment and install deps.
2. Run:
```bash
python src/main.py
```
3. Add a YouTube Music playlist ID (from YT Music) via the GUI and sync. Downloaded tracks will be saved to `./Music` by default or your configured `download_path`.

---

## Con3. Run and test locally.
4. Open a pull request describing your changes.

Suggested initial improvements:
- Add a `requirements.txt`
- Add a `LICENSE`
- Add unit tests and CI
- Improve error handling and validation

---

## License
No license file detected in the repository. All rights reserved by default. Add a LICENSE file (for example MIT or Apache-2.0) to permit reuse.

---

If you want, I can:
- Paste this content as a single downloadable text file content (ready to copy),
- Or create and commit a README.md directly into the repository (I will need confirmation to perform a repo write).