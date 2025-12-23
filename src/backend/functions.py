import os
import uuid
import json
import math

import backend.config as config
import backend.helper_functions as helper_functions
import backend.library as library
import backend.threader as threader
import backend.services.youtube as youtube
from backend.services.youtube import check_network


class Backend():
    def __init__(self):
        self.set_constants()

        self.libraryInstance = library.Library(filepath=self.DOWNLOAD_FOLDER)
        self.youtubeInstance = youtube.YouTube()
        self.threadingInstance = threader.QueueSystem(max_threads= self.MAX_THREADS)
        self.refresh_hashmaps()
        self.missing = {}
        self.progress_dict = {}

    def set_constants(self):
        self.configInstance = config.Config()
        self.TEMP_PATH = self.configInstance.get("download_settings",{}).get("temp_path","./")
        self.CACHE_PATH = self.configInstance.get("download_settings",{}).get("cache_path","./")
        self.ENCODE_QUALITY = self.configInstance.get("download_settings",{}).get("encode_quality",8)
        self.DOWNLOAD_FOLDER = self.configInstance.get("download_settings",{}).get("download_path","./")
        self.FILENAME_TEMPLATE = self.configInstance.get("download_settings",{}).get("filename_template","")
        self.COVER_MODE = self.configInstance.get("download_settings",{}).get("cover_mode","crop")
        self.CODEC = self.configInstance.get("download_settings",{}).get("encode_codec","mp3")
        self.MAX_THREADS = self.configInstance.get("download_settings",{}).get("max_threads",2)
        os.makedirs(self.DOWNLOAD_FOLDER, exist_ok=True)
        os.makedirs(self.CACHE_PATH, exist_ok=True)
        os.makedirs(self.TEMP_PATH, exist_ok=True)

    def refresh_hashmaps(self):
        cached_filename_list = [os.path.join(self.CACHE_PATH, f) for f in os.listdir(self.CACHE_PATH) if
                                os.path.isfile(os.path.join(self.CACHE_PATH, f))]
        self.cached_hash_map = {helper_functions.hash_file(i): i for i in cached_filename_list}
        playlist_folder_list = [os.path.join(self.DOWNLOAD_FOLDER, f) for f in os.listdir(self.DOWNLOAD_FOLDER) if
                                not os.path.isfile(os.path.join(self.DOWNLOAD_FOLDER, f))]
        self.song_hash_map = {}
        for i in playlist_folder_list:
            if os.path.exists(os.path.join(i, ".id_file")):
                with open(os.path.join(i, ".id_file"), "r") as f:
                    data = json.load(f)
                song_filename_list = [os.path.join(self.DOWNLOAD_FOLDER, i, f) for f in
                                      os.listdir(os.path.join(self.DOWNLOAD_FOLDER, i)) if
                                      os.path.isfile(os.path.join(self.DOWNLOAD_FOLDER, i, f))]
                self.song_hash_map[data.get("id")] = {helper_functions.hash_file(fn): fn for fn in song_filename_list}

    def check_avail(self):
        for i in self.libraryInstance.get_playlists():
            for j in self.libraryInstance.get_playlist_items_data(playlist_id=i):
                if j.get("success"):
                    song = True
                    if not j.get("file_info",{}).get("media_hash") in self.song_hash_map.get(j.get("playlist_id")):
                        song = False
                        self.missing[j.get("track_id")][j.get("playlist_id")] = True
                    if not j.get("file_info",{}).get("cover_hash") in self.cached_hash_map:
                        file_name = str(uuid.uuid4())
                        if song is False:
                            cover_path, cover_hash = helper_functions.download_file(url=j.get("file_info",{}).get("cover_url"),save_path=f"{self.CACHE_PATH}/{file_name}.png")
                            helper_functions.adjust_image_to_square(img_path=cover_path, mode=self.COVER_MODE)
                        else:
                            helper_functions.extract_cover_from_audio(input_file=self.song_hash_map[j.get("playlist_id")][j.get("track_id")],output_file=f"{self.CACHE_PATH}/{file_name}.png")
                        self.libraryInstance.set_track_data(playlist_id=i,track_id=j.get("playlist_id"),data={"file_info":{"cover_hash":helper_functions.hash_file(f"{self.CACHE_PATH}/{file_name}.png")}})

    def youtube_progress_callback(self,info,playlist_id,track_id):
        if info["status"] == "downloading":
            downloaded = info.get("downloaded_bytes", 0)
            total = info.get("total_bytes") or info.get("total_bytes_estimate")
            if total:
                percent = downloaded / total * 100
                self.progress_dict[playlist_id][id]["status_msg"] = "Downloading from Youtube"
                self.progress_dict[playlist_id][id]["progress_val"] = math.floor(percent)
                print(f"{percent:.1f}%  {downloaded}/{total} bytes")
            else:
                self.progress_dict[playlist_id][id]["status_msg"] ="Finished downloading"
                self.progress_dict[playlist_id][id]["progress_val"] = 100
                print(f"{downloaded} bytes downloaded")

        elif info["status"] == "finished":
            print("Download finished, now processing...")

    def download_track(self,library_uri:str,playlist_id:str,output_folder:str):
        random_uuid = str(uuid.uuid4())
        service = library_uri.split(":")[0]
        item_type = library_uri.split(":")[1]
        id = library_uri.split(":")[-1]
        self.progress_dict[playlist_id][id] = {"status_msg":"Starting.....","progress_val":100}
        try:
            if item_type == "track":
                if service == "youtube":
                    result_data = self.youtubeInstance.download_track(youtube_id=id,download_folder=self.TEMP_PATH,progress_hook=lambda inf:self.youtube_progress_callback(inf,playlist_id,id))
                    self.progress_dict[playlist_id][id] = {"status_msg": "Downloading cover", "progress_val": 50}
                    cover_path, cover_hash = helper_functions.download_file(url = result_data["cover_url"],save_path=f"{self.CACHE_PATH}/{random_uuid}.png")
                    self.progress_dict[playlist_id][id] = {"status_msg": "Finished", "progress_val": 100}
                    helper_functions.adjust_image_to_square(img_path=cover_path,mode=self.COVER_MODE)
                    self.progress_dict[playlist_id][id] = {"status_msg": "Transcoding media", "progress_val": 0}
                    filename = helper_functions.sanitize(helper_functions.template_decoder(template=self.FILENAME_TEMPLATE,data=result_data))
                    output_file,media_bitrate = helper_functions.transcode_audio(input_file=result_data["file_path"],output_path=output_folder,filename=filename,overwrite=True,out_codec=self.CODEC,quality=self.ENCODE_QUALITY)
                    helper_functions.edit_audio_metadata(input_file=output_file,data=result_data)
                    helper_functions.replace_image_in_track(input_file=output_file,input_cover=cover_path)
                    self.progress_dict[playlist_id][id] = {"status_msg": "Finished", "progress_val": 100}
                    print("Download complete!")
                    self.libraryInstance.set_track_data(playlist_id=playlist_id,track_id=library_uri,data=
                    {"success": True,
                     "release":result_data["release"],
                     "file_info":{
                        "cover_url":result_data.get("cover_url"),
                        "cover_mode":self.COVER_MODE,
                        "cover_hash": helper_functions.hash_file(cover_path),
                        "media_container": self.CODEC,
                        "media_bitrate": media_bitrate,
                        "media_hash": helper_functions.hash_file(output_file),
                        "length":result_data.get("length",0),
            }})
        except Exception as e:
            print(e)
            raise e
    def add_playlist_to_library(self, playlist_url:str):
        if "youtu" in playlist_url:
            playlist_id = playlist_url.split("/")[-1].split("?list=")[-1]
            library_uri = f"youtube:playlist:{playlist_id}"
            if helper_functions.check_network():
                playlist_data = self.youtubeInstance.get_playlist(youtube_id=playlist_id)
                print(playlist_data)
                self.libraryInstance.add_playlist(playlist_id=library_uri,data = {"title": playlist_data["title"],"author":""})
                return library_uri
            else:
                raise ConnectionError("No internet connection.")
    def sync_playlist(self,library_uri:str):
        service = library_uri.split(":")[0]
        item_type = library_uri.split(":")[1]
        id = library_uri.split(":")[-1]
        if item_type != "playlist":
            raise ValueError("Item is not a playlist.")
        if not check_network():
            raise ConnectionError("No internet connection.")
        if not self.libraryInstance.verify_library_path(library_uri):
            raise ValueError("Playlist does not exist.")
        if service == "youtube":
            yt_music_data = self.youtubeInstance.get_playlist(youtube_id=id)
            new_item_list = {f"youtube:track:{item['youtube_id']}": item for item in yt_music_data["tracks"]}
            new_item_id_list = [f"youtube:track:{item['youtube_id']}" for item in yt_music_data["tracks"]]
            existing_item_id_list = self.libraryInstance.get_playlist_items_ids(playlist_id=library_uri)
            positive, negative = helper_functions.get_difference(existing_item_id_list, new_item_id_list)
            for item_id in positive:
                song_data = {
                    "success": False,
                    "title": new_item_list[item_id]["title"],
                    "artist": [i for i in new_item_list[item_id]["artists"]],
                    "album": new_item_list[item_id].get("album", "Unknown album"),
                    "release": None,
                    "track_id": item_id,
                    "playlist_id": library_uri,
                }
                self.libraryInstance.add_track(playlist_id=library_uri,track_id=item_id, data=song_data)
            job_list = []
            output_folder = os.path.join(self.DOWNLOAD_FOLDER, helper_functions.sanitize(self.libraryInstance.get_playlist_full(library_uri).get('folder_name')))
            os.makedirs(output_folder, exist_ok=True)
            if not os.path.exists(os.path.join(output_folder,".id")):
                with open(os.path.join(output_folder,".id"), "w") as f:
                    json.dump({"id": library_uri}, f)

            for item in self.libraryInstance.get_playlist_items_data(library_uri):
                if item.get("success", False) == False:
                    job_list.append(
                        lambda passed_item=item: self.download_track(library_uri=passed_item["track_id"], playlist_id=library_uri,output_folder=output_folder)
                    )

            self.threadingInstance.submit_jobs(job_list)
            self.threadingInstance.wait_completion()
    def reload_config(self):
        self.set_constants()
        self.libraryInstance = library.Library(filepath=self.DOWNLOAD_FOLDER)
        self.threadingInstance = threader.QueueSystem(max_threads=self.MAX_THREADS)

if __name__ == "__main__":
    print("This isn't the place to launch the gui!")
    print("Do that from the main.py file!")
    print("Launching terminal test mode")
    backendInstance = Backend()
    while True:
        command = input(">>> ")
        if command == "add_playlist":
            backendInstance.add_playlist_to_library(playlist_url=input("Enter playlist url: "))
        if command == "exit" or command == "quit" or command == "q":
            break

