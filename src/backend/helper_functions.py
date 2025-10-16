import requests
import ping3
import hashlib
import os
import re
import colorsys
import numpy as np
from PIL import Image
import imageio_ffmpeg as ffmpeg
import subprocess
from mutagen.oggopus import OggOpus
from mutagen.flac import Picture
from mutagen.easyid3 import EasyID3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.wave import WAVE
import eyed3
import base64


def check_network():
    is_online = ping3.ping("1.1.1.1")
    return is_online


def download_file(url: str, save_path: str):
    if check_network():
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return save_path, hash_file(save_path)
    return None, None

def hash_file(filename:str=None):
    if filename:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"No such file found at given path {filename}")
        BUF_SIZE = 65536
        md5 = hashlib.md5()
        with open(filename, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                md5.update(data)
        return md5.hexdigest()


def sanitize(s):
    return re.sub(r'[<>:"/\\|?*\']', '', s)


def template_decoder(template, data: dict = None, magic_char: str = "$"):
    if data is None: data = {}
    final, opened, opened_keyword = "", False, ""
    for char in template:
        if not opened:
            if char == magic_char:
                opened = True
            else:
                final += char
            continue
        if opened:
            if char == magic_char:
                opened = False
                final += str(data.get(opened_keyword, ''))
                opened_keyword = ""
            else:
                opened_keyword += char
            continue

    return re.sub(r'[<>:"/\\|?*\']', '', final).strip()


def adjust_image_to_square(img_path: str = None, mode="crop", image_size=(640, 640)):
    image = Image.open(img_path)
    width, height = image.size
    ratio = width / height
    if ratio == 1:
        return None
    if mode == "crop":
        left,right,top,bottom = 0,0,0,0
        if ratio > 1:  # wider than tall
            left = (width - height) // 2
            right = width - left
            top, bottom = 0, height
        elif ratio < 1:  # taller than wide
            top = (height - width) // 2
            bottom = height - top
            left, right = 0, width

        image = image.crop((left, top, right, bottom))
        image = image.resize(image_size)
        image.save(img_path)
    if mode == "extend":
        img_data = np.array(image)
        max_saturation = 0
        max_brightness = 0
        vibrant_color = (0, 0, 0)
        for row in img_data:
            for pixel in row:
                r, g, b = pixel
                h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
                if s > max_saturation and v > max_brightness:
                    max_saturation = s
                    max_brightness = v
                    vibrant_color = (r, g, b)
        new_size = max(width, height)
        new_img = Image.new("RGB", (new_size, new_size), vibrant_color)
        x_offset = (new_size - width) // 2
        y_offset = (new_size - height) // 2
        new_img.paste(image, (x_offset, y_offset))
        new_img = new_img.resize(image_size)
        new_img.save(img_path)


def transcode_audio(input_file: str = None, output_path: str = None, filename: str = None, overwrite: bool = False,
                    out_codec: str = None, quality: int = None):
    if input_file and output_path and filename:
        codec_map = {
            "mp3": ("libmp3lame", "mp3"),
            "aac": ("aac", "m4a"),
            "opus": ("libopus", "ogg"),
            "wav": ("pcm_s16le", "wav")
        }

        if out_codec is None:
            out_codec = "mp3"
        if out_codec not in codec_map.keys():
            raise ValueError(f"Invalid codec, {out_codec} is not supported!")
        if quality is None:
            quality = 10
        quality = min(quality, 10)
        quality = max(quality, 1)
        quality = int(quality)
        codec, container = codec_map[out_codec]

        if not os.path.exists(input_file):
            raise FileNotFoundError("Unable to find the input file!")
        output_file = os.path.join(output_path, sanitize(filename) + "." + container)
        if not os.path.exists(output_path):
            raise FileNotFoundError("Unable to find the output path!")
        if os.path.exists(output_file) and not overwrite:
            raise FileExistsError("Output path already exists!")

        ffmpeg_path = ffmpeg.get_ffmpeg_exe()
        command = [ffmpeg_path,
                   '-loglevel', 'quiet',
                   '-y',
                   '-i', input_file]
        MAX_MP3_BITRATE = 320
        MAX_OGG_BITRATE = 256
        MAX_M4A_BITRATE = 256

        MIN_AUDIO_BITRATE = 32
        media_bitrate = 256

        if container == "mp3":
            media_bitrate = f"{int(max(MIN_AUDIO_BITRATE, quality // 10 * MAX_MP3_BITRATE))}k"
        if container == "ogg":
            media_bitrate = f"{int(max(MIN_AUDIO_BITRATE, quality // 10 * MAX_OGG_BITRATE))}k"
        if container == "m4a":
            media_bitrate = f"{int(max(MIN_AUDIO_BITRATE, quality // 10 * MAX_M4A_BITRATE))}k"

        if container != "wav":
            command += ['-b:a', media_bitrate, ]

        command += [
            '-c:a', codec,
            output_file
        ]
        try:
            subprocess.run(command, check=True)
        except Exception as e:
            raise e
    else:
        raise ValueError("Input file, output path or filename is missing!")


def edit_audio_metadata(input_file: str = None, data: dict = None):
    _, ext = os.path.splitext(input_file)
    container = ext.lstrip(".").lower()
    if not container.lower() in ["mp3", "m4a", "ogg", "wav"]:
        raise ValueError("Non-supported file type was given!")
    if not os.path.exists(input_file):
        raise FileNotFoundError("Input file given does not exist!")
    if data is None:
        raise ValueError("No data was given!")

    if container == "mp3":
        audio_file = EasyID3(input_file)
        audio_file['title'] = str(
            data.get("title", None) if data.get("title", None) is not None else audio_file['title'])
        audio_file['artist'] = str(
            ",".join(data.get("artists", None)) if data.get("artists", None) is not None and data.get("artists",
                                                                                                      None) != [] else
            audio_file['artist'])
        audio_file['albumartist'] = str(
            ",".join(data.get("artists", None)) if data.get("artists", None) is not None and data.get("artists",
                                                                                                      None) != [] else
            audio_file['artist'])
        audio_file['album'] = str(
            data.get("album", None) if data.get("album", None) is not None else audio_file['album'])
        audio_file['date'] = str(
            data.get("release", None) if data.get("release", None) is not None else audio_file['date'])
        audio_file.save(v2_version=3)
    if container == "m4a":
        audio_file = MP4(input_file).tags
        audio_file["\xa9nam"] = str(
            data.get("title", None) if data.get("title", None) is not None else audio_file['\xa9nam'])
        audio_file["\xa9ART"] = str(
            ",".join(data.get("artists", None)) if data.get("artists", None) is not None and data.get("artists",
                                                                                                      None) != [] else
            audio_file['\xa9ART'])
        audio_file["\xa9alb"] = str(
            data.get("album", None) if data.get("album", None) is not None else audio_file['\xa9alb'])
        audio_file["\xa9day"] = str(
            data.get("release", None) if data.get("release", None) is not None else audio_file['\xa9day'])
        audio_file.save()
    if container == "ogg":
        audio_file = OggOpus(input_file)
        audio_file["TITLE"] = str(
            data.get("title", None) if data.get("title", None) is not None else audio_file['TITLE'])
        audio_file["ARTIST"] = str(
            ",".join(data.get("artists", None)) if data.get("artists", None) is not None and data.get("artists",
                                                                                                      None) != [] else
            audio_file['ARTIST'])
        audio_file["ALBUM"] = str(
            data.get("album", None) if data.get("album", None) is not None else audio_file['ALBUM'])
        audio_file["DATE"] = str(
            data.get("release", None) if data.get("release", None) is not None else audio_file['DATE'])
        audio_file.save()
    if container == "wav":
        audio_file = WAVE(input_file)
        audio_file["INAM"] = str(data.get("title", None) if data.get("title", None) is not None else audio_file['INAM'])
        audio_file["IART"] = str(
            ",".join(data.get("artists", None)) if data.get("artists", None) is not None and data.get("artists",
                                                                                                      None) != [] else
            audio_file['IART'])
        audio_file["IPRD"] = str(data.get("album", None) if data.get("album", None) is not None else audio_file['IPRD'])
        audio_file["ICRD"] = str(
            data.get("release", None) if data.get("release", None) is not None else audio_file['ICRD'])
        audio_file.save()

    return data


def replace_image_in_track(input_file, input_cover):
    if not os.path.exists(input_file):
        raise FileNotFoundError("Input file does not exist!")
    if not os.path.exists(input_cover):
        raise FileNotFoundError("Cover image does not exist!")

    _, ext = os.path.splitext(input_file)
    container = ext.lstrip(".").lower()
    if container not in ["mp3", "ogg", "m4a"]:
        raise ValueError("Unsupported file type!")

    _, cover_ext = os.path.splitext(input_cover)
    cover_ext = cover_ext.lstrip(".").lower()
    if cover_ext in ["jpg", "jpeg"]:
        mime = "image/jpeg"
        mp4_format = MP4Cover.FORMAT_JPEG
    elif cover_ext == "png":
        mime = "image/png"
        mp4_format = MP4Cover.FORMAT_PNG
    else:
        raise ValueError("Cover image must be JPEG or PNG!")

    with open(input_cover, "rb") as f:
        cover_data = f.read()

    try:
        if container == "mp3":
            audio = eyed3.load(input_file)
            if audio.tag is None:
                audio.initTag()
            audio.tag.images.remove(u'')
            audio.tag.images.set(3, cover_data, mime, "Cover")
            audio.tag.save()

        elif container == "ogg":
            audio = OggOpus(input_file)
            pic = Picture()
            pic.data = cover_data
            pic.type = 3
            pic.mime = mime
            audio["METADATA_BLOCK_PICTURE"] = [base64.b64encode(pic.write()).decode("ascii")]
            audio.save()

        elif container == "m4a":
            audio = MP4(input_file)
            audio["covr"] = [MP4Cover(cover_data, imageformat=mp4_format)]
            audio.save()

        return True

    except Exception as e:
        raise RuntimeError(f"Failed to replace cover: {e}")
