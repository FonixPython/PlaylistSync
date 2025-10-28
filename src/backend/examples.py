import services.youtube as yt
import helper_functions
import uuid

yt_instance = yt.YouTube()
download_folder = "./"
filename_template = "$title$ - $artist$"
format = "mp3"


def download_song(url:str):
    if "youtu" in url:
        id = url.split("/")[-1].split("&")[0].split("=")[-1]
        result_data = yt_instance.download_track(youtube_id=id,download_folder=download_folder)
        cover_path, cover_hash = helper_functions.download_file(url = result_data["cover_url"],save_path=f"{download_folder}/{uuid.uuid4()}.png")
        helper_functions.adjust_image_to_square(img_path=cover_path,mode="crop")
        filename = helper_functions.sanitize(helper_functions.template_decoder(template=filename_template,data=result_data))
        output_file = helper_functions.transcode_audio(input_file=result_data["file_path"],output_path=download_folder,filename=filename,overwrite=True,out_codec=format,quality=10)
        helper_functions.edit_audio_metadata(input_file=output_file,data=result_data)
        helper_functions.replace_image_in_track(input_file=output_file,input_cover=cover_path)
        print("Download complete!")

download_song(url=input("Enter url: "))