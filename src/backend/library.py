from typing import Any, Optional
import json
import os
import tempfile
import time
import backend.helper_functions as helper_functions


class Library:
    DEFAULTS = {
        "createdOn": float(0),
        "playlists": {}
    }

    def __init__(self, filepath: str = None):

        if filepath is None:
            raise ValueError("No path was provided!")
        if not os.path.exists(filepath):
            raise FileNotFoundError("The filepath doesn't exist!")

        self.filepath = os.path.join(filepath, "library.json")

        self._library: dict[str, Any] = {}
        if not os.path.exists(self.filepath):
            self.DEFAULTS["createdOn"] = time.time()
            self._library = self.DEFAULTS.copy()
            self._save()
        else:
            self._load()
        self._backup()

    def _load(self) -> None:
        """Load configuration from disk. If corrupted, fallback to defaults."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self._library = json.load(f)
        except (json.JSONDecodeError, OSError):
            print("Original library corrupted! Attempting fallback to backup (leads to data loss)")

    def _backup(self) -> None:
        with open(self.filepath + ".backup", "w", encoding="utf-8") as f:
            json.dump(self._library, f, indent=4)

    def _save(self) -> None:
        """Safely save configuration to disk (atomic write when possible)."""
        if not self._library:
            raise BufferError("Config is empty and cannot be saved.")

        # Create temp file in the same directory to ensure same filesystem
        dirpath = os.path.dirname(os.path.abspath(self.filepath))
        tmp_fd, tmp_path = tempfile.mkstemp(dir=dirpath)
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(self._library, f, indent=4)
            try:
                os.replace(tmp_path, self.filepath)  # atomic within same FS
            except OSError as e:
                import errno, shutil
                if e.errno == errno.EXDEV:  # cross-device link error
                    shutil.move(tmp_path, self.filepath)
                else:
                    raise
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except FileNotFoundError:
                    pass
    def _get(self, path: str, default: Optional[Any] = None) -> Any:
        keys = path.split(".")
        value = self._library
        for k in keys:
            if not isinstance(value, dict) or k not in value:
                return default
            value = value[k]
        return value

    def _delete(self, path: str, write_to_file: Optional[bool] = True):
        keys = path.split(".")
        d = self._library
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict):
                raise KeyError(f"Invalid path: {'.'.join(keys)}")
            d = d[k]

        d.pop(keys[-1], None)
        if write_to_file:
            self._save()

    def _set(self, path: str, value: Any, write_to_file: Optional[Any] = False) -> None:
        """Set a config value by dotted path (e.g., 'appearance.mode')."""
        keys = path.split(".")
        d = self._library
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        if write_to_file:
            self._save()

    # --------------------------
    #   User facing functions
    # --------------------------

    def verify_library_path(self, playlist_id=None, song_id=None):
        exists = False
        if playlist_id:
            if self._get(f"playlists.{playlist_id}", None) is not None: exists = True
            if song_id:
                exists = False
                if self._get(f"playlists.{playlist_id}.items.{song_id}", None) is not None:
                    exists = True
        return exists

    # -----Track operations-----

    def get_track_full(self, playlist_id: str = None, track_id: str = None):
        if playlist_id and track_id:
            if not self.verify_library_path(playlist_id, track_id):
                raise ValueError("Library given does not exist!")
            return dict(self._get(path=f"playlists.{playlist_id}.items.{track_id}", default={}))
        else:
            raise ValueError("No library path was given!")

    def add_track(self, playlist_id: str = None, track_id: str = None, data: dict = None):
        if playlist_id and track_id:
            if not self.verify_library_path(playlist_id):
                raise ValueError("Playlist given does not exist!")
            if data.get("title", None) is not None and data.get("artist", None) is not None and data.get("album",None) is not None:
                data["success"] = False
                data["playlist_id"] = playlist_id
                data["track_id"] = track_id
                data["file_info"] = {}
                self._set(path=f"playlists.{playlist_id}.items.{track_id}", value=data)
                self._save()
            else:
                raise ValueError("Needed values weren't given!")
        else:
            raise ValueError("No library path was given!")

    def set_track_data(self, playlist_id: str = None, track_id: str = None, data: dict = None):
        if playlist_id and track_id:
            if not self.verify_library_path(playlist_id, track_id):
                raise ValueError("Library given does not exist!")
            for key in data:
                if key in self.get_track_full(playlist_id, track_id).keys():
                    self._set(path=f"playlists.{playlist_id}.items.{track_id}.{key}", value=data[key])
            self._save()
        else:
            raise ValueError("No library path was given!")

    def delete_track(self, playlist_id: str = None, track_id: str = None):
        if playlist_id and track_id:
            if not self.verify_library_path(playlist_id, track_id):
                raise ValueError("Library given does not exist!")
            self._delete(path=f"playlists.{playlist_id}.items.{track_id}")
            self._save()
        else:
            raise ValueError("No library path was given!")

    # ---Playlist operations---

    def get_playlist_full(self, playlist_id: str = None):
        if playlist_id:
            if not self.verify_library_path(playlist_id):
                raise ValueError("Library given does not exist!")
            return dict(self._get(path=f"playlists.{playlist_id}", default={}))
        else:
            raise ValueError("No library path was given!")

    def get_playlist_items_data(self, playlist_id: str = None):
        if playlist_id:
            if not self.verify_library_path(playlist_id):
                raise ValueError("Library given does not exist!")
            return_list = [self._get(path=f"playlists.{playlist_id}.items.{item}", default={}) for item in self._get(path=f"playlists.{playlist_id}.items", default={})]
            return return_list
        else:
            raise ValueError("No library path was given!")

    def get_playlist_items_ids(self, playlist_id: str = None):
        if playlist_id:
            if not self.verify_library_path(playlist_id):
                raise ValueError("Library given does not exist!")
            return list(dict(self._get(path=f"playlists.{playlist_id}.items", default={})).keys())
        else:
            raise ValueError("No library path was given!")

    def add_playlist(self, playlist_id: str = None, data: dict = None):
        if playlist_id and data:
            if self.verify_library_path(playlist_id):
                raise ValueError("Library id already exists!")
            if data.get("title") is None:
                raise ValueError("No title was given!")
            playlist_dict = {
                "title": str(data.get("title", "")),
                "folder_name": helper_functions.sanitize(str(data.get("title", ""))),
                "author": str(data.get("author", "")),
                "addedOn": time.time(),
                "blacklist": [],
                "items": {}
            }
            self._set(path=f"playlists.{playlist_id}", value=playlist_dict)
            self._save()
            return playlist_dict
        else:
            raise ValueError("No library path or data was given!")

    def set_playlist_data(self, playlist_id: str = None, data: dict = None):
        if playlist_id and data:
            if not self.verify_library_path(playlist_id):
                raise ValueError("The playlist given does not exist!")
            for key in data:
                if key in self.get_playlist_full(playlist_id).keys() and key not in ["items", "blacklist"]:
                    self._set(path=f"playlists.{playlist_id}.{key}", value=data[key])
            self._save()
        else:
            raise ValueError("No library path or data was given!")

    def get_playlist_blacklist(self, playlist_id: str = None):
        if playlist_id:
            if not self.verify_library_path(playlist_id):
                raise ValueError("Library given does not exist!")
            return list(self._get(path=f"playlists.{playlist_id}.blacklist", default=[]))
            self._save()
        else:
            raise ValueError("No library path was given!")

    def append_playlist_blacklist(self, playlist_id: str = None, item_id: str = None):
        if playlist_id and item_id:
            if not self.verify_library_path(playlist_id):
                raise ValueError("Library given does not exist!")
            if item_id in self.get_playlist_blacklist(playlist_id):
                raise ValueError("Item id already present in blacklist!")

            blacklist_array = self._get(f"playlists.{playlist_id}.blacklist", default=[])
            blacklist_array.append(item_id)
            self._set(path=f"playlists.{playlist_id}.blacklist", value=blacklist_array)
            self._save()

        else:
            raise ValueError("No playlist id or no item id was given!")

    def delete_playlist_blacklist(self, playlist_id: str = None, item_id: str = None):
        if playlist_id and item_id:
            if not self.verify_library_path(playlist_id):
                raise ValueError("Library given does not exist!")
            if not item_id in self.get_playlist_blacklist(playlist_id):
                raise ValueError("Item id is not present in blacklist!")
            out_array = []
            for index, item in enumerate(self._get(path=f"playlists.{playlist_id}.blacklist", default=[])):
                if item != item_id:
                    out_array.append(item)
            self._set(path=f"playlists.{playlist_id}.blacklist", value=list(out_array))
            self._save()
        else:
            raise ValueError("No playlist id or no item id was given!")

    def delete_playlist(self, playlist_id: str = None):
        if playlist_id:
            if not self.verify_library_path(playlist_id):
                raise ValueError("Library given does not exist!")
            self._delete(path=f"playlists.{playlist_id}")
            self._save()
        else:
            raise ValueError("No library path was given!")

    def get_playlists(self):
        return list(self._get(path=f"playlists", default=[]).keys())

    def __getitem__(self, key: str) -> Any:
        return self._library[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._library[key] = value

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._save()