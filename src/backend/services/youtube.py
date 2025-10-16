from .. import helper_functions
import yt_dlp
import ytmusicapi


class YouTube():
    def __init__(self):
        self.yt_music_api = ytmusicapi.YTMusic()

    def download_track(self, youtube_id: str = None, download_folder: str = None):
        if not helper_functions.check_network():
            raise ConnectionError("No internet connection!")
        if youtube_id is None:
            raise ValueError("No youtube id given!")
        if download_folder is None:
            raise ValueError("Output folder wasn't given!")
        if len(youtube_id) != 11:
            ValueError("Invalid youtube id given!")
        ydl_config = {
            'format': "bestaudio/best",
            'outtmpl': download_folder,
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_config) as ydl:
                info = ydl.extract_info(f"https://music.youtube.com/watch?v={youtube_id}")

            audio_file = info["requested_downloads"][0]["filepath"]
            title = helper_functions.sanitize(info.get('title', "Unknown Title"))
            artist_list = info.get('artists', [info.get('uploader', "Unknown Artist")])
            artist_str = helper_functions.sanitize(", ".join(artist_list))
            album = helper_functions.sanitize(info.get('album', "Unknown Album"))
            release_year = info.get('release_year') or int(info.get('upload_date', "20000000")[0:4] or 0)
            length = info.get('duration', 200)
            covers = info.get('thumbnails')
            if not covers[2].get('height', 1) == covers[2].get('width', 0):
                cover_url = info.get('thumbnail')
            else:
                cover_url = covers[2]["url"]

            return {
                "id": id,
                "title": title,
                "artists": artist_list,
                "album": album,
                "release": release_year,
                "file_path": audio_file
            }

        except Exception as e:
            raise e

    def get_playlist(self, youtube_id: str = None):
        if not helper_functions.check_network():
            raise ConnectionError("No internet connection!")
        if youtube_id is None:
            raise ValueError("No youtube id given!")
        if len(youtube_id) != 34:
            ValueError("Invalid youtube id given!")

        try:
            data = self.yt_music_api.get_playlist(playlistId=id, limit=None)
            return_dict = {}
            return_dict["tracks"] = []
            for track in data["tracks"]:
                track_dict = {}
                track_dict["title"] = track.get("title", "Unknown title")
                track_dict["artists"] = [i.get("name", "Unknown artist") for i in track.get("artists")] if track.get(
                    "artists") is not None else ["Unknown artist"]
                track_dict["album"] = track.get("album", {}).get("name", "Unknown album")
                track_dict["duration_seconds"] = track.get("duration", 0)
                track_dict["thumbnail"] = track.get("thumbnails")[0]["url"].split("=")[0] + "=w600-h600" if track.get(
                    "thumbnails") is not None else None
                return_dict["tracks"].append(track_dict)
            playlist_info = {}
            playlist_info["title"] = data.get("title", "Unknwon Title")
            playlist_info["thumbnail"] = data.get("thumbnails", [])[-1].get("url", None)

            return return_dict

        except Exception as e:
            raise ValueError("Playlist is unreachable! Most likely caused by a playlist that is private! Set it to link only or public!")