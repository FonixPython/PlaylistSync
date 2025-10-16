import os,json
from typing import Any, Optional
import tempfile


class Config:
    DEFAULTS = {
        "appearance": {
            "app_title": "Syncy",
            "app_icon": "./icon.ico",
            "mode": "dark",  # options: dark / light / system
            "color_theme": "dark-blue",
            "primary_roundness": 20,
            "secondary_roundness": 7,
            "saved_state": {
                "window_position": {"x": 100, "y": 100},
                "window_height": 800,
                "window_width": 700,
                "displayed_item_height": 80,
            },
        },
        "download_settings": {
            "final_codec": "mp3",  # ["mp3","opus","aac","wav"]
            "encode_quality": 0,   # 0 = best, 10 = worst
            "temp_path": ".TEMP",
            "cache_path": ".CACHE",
            "download_path": "./Music",
            "filename_template": "$title$ - $artist$",
            "cover_mode": "crop",  # crop, stretch
        },
        "api_keys": {"youtube_api_key": None},
    }

    def __init__(self, filepath: str = "./config.json") -> None:
        self.filepath = filepath
        self._config: dict[str, Any] = {}
        if not os.path.exists(self.filepath):
            self._config = self.DEFAULTS.copy()
            self.save()
        else:
            self.load()
            self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        """Ensure missing keys are added with default values."""
        def merge(defaults: dict, target: dict):
            for key, val in defaults.items():
                if key not in target:
                    target[key] = val
                elif isinstance(val, dict) and isinstance(target[key], dict):
                    merge(val, target[key])
        merge(self.DEFAULTS, self._config)

    def load(self) -> None:
        """Load configuration from disk. If corrupted, fallback to defaults."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except (json.JSONDecodeError, OSError):
            # fallback if corrupted
            self._config = self.DEFAULTS.copy()
            self.save()

    def save(self) -> None:
        """Safely save configuration to disk (atomic write)."""
        if not self._config:
            raise BufferError("Config is empty and cannot be saved.")
        tmp_fd, tmp_path = tempfile.mkstemp()
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
            os.replace(tmp_path, self.filepath)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def get(self, path: str, default: Optional[Any] = None) -> Any:
        """Get a config value by dotted path (e.g., 'appearance.mode')."""
        keys = path.split(".")
        value = self._config
        for k in keys:
            if not isinstance(value, dict) or k not in value:
                return default
            value = value[k]
        return value

    def set(self, path: str, value: Any,write_to_file:Optional[Any]=False) -> None:
        """Set a config value by dotted path (e.g., 'appearance.mode')."""
        keys = path.split(".")
        d = self._config
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        if write_to_file:
            self.save()

    def __getitem__(self, key: str) -> Any:
        return self._config[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._config[key] = value

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.save()
