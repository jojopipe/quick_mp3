import io
import tkinter
import requests
from tkinter.filedialog import askdirectory
from tkinter import ttk
from bs4 import BeautifulSoup
from pytube import YouTube
from PIL import Image, ImageTk
from urllib.parse import urlparse
import yt_dlp

window_size_modifier: float = 1
window_width: int = 1280
window_height: int= 720
save_dir: str = " "
save_dir_field: tkinter.Entry
format_select: ttk.Combobox
url_field: tkinter.Entry
title_label: tkinter.Label
thumb_label: tkinter.Label
status_label: tkinter.Label
video_title: str
valid_url: bool = False
sel_fol_button: tkinter.Button
dl_button: tkinter.Button

format_values = ["mp3", "m4a"]

def is_valid_youtube_url(url):
    if not url:
        return False
    try:
        parsed_url = urlparse(url)
    except Exception:  # Handle potential parsing errors
        return False

    host = parsed_url.hostname
    path = parsed_url.path
    query = parsed_url.query

    valid_hosts = [
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",  # Shortened URLs
        "www.youtu.be",
        "m.youtu.be",
    ]
    if host not in valid_hosts:
        return False

    # 2. Check path and query parameters for typical YouTube structures
    if host in ["youtube.com", "www.youtube.com", "m.youtube.com"]:
        if path == "/watch":  # Regular video URL
            if "v=" in query:  # Must have a 'v' parameter
                return True
        elif path.startswith("/embed/"):  # Embeded video
            return True
        elif path.startswith("/v/"):  # Flash video
            return True
        elif path == "/":  # Homepage
            return True

    elif host in ["youtu.be", "www.youtu.be", "m.youtu.be"]:  # Shortened URLs
        if path and path.startswith("/"):  # Must have a path after the domain
            return True

    return False


def position_window(window):
    global window_width
    global window_height
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    window_width = 768
    window_height = 432
    x = int(screen_width / 2 - window_width / 2)
    y = int(screen_height / 2 - window_height / 2)
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")

def folder_select_clicked():
    global save_dir
    save_dir = askdirectory(title="select directory to save to")
    if save_dir == "0":
        save_dir = " "
    if save_dir is None:
        return
    save_dir_field.config(state=tkinter.NORMAL)
    save_dir_field.delete(0, None)
    save_dir_field.insert(0, save_dir)
    save_dir_field.config(state="readonly")

def get_video_title():
    global video_title
    yt_url = url_field.get()
    r = requests.get(yt_url)
    soup = BeautifulSoup(r.text, features="html.parser")
    link = soup.find_all(name="title")[0]
    title = link.text
    title = title[:-10]
    video_title = title
    return title

def get_youtube_thumbnail():
    video_url = url_field.get()
    try:
        yt = YouTube(video_url)
        thumbnail_url = yt.thumbnail_url

        response = requests.get(thumbnail_url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        image_bytes = io.BytesIO(response.content)
        image = Image.open(image_bytes)
        return image
    except requests.exceptions.RequestException as e:
        print(f"Error downloading thumbnail: {e}")
        return None
    except Exception as e:  # Catch other potential errors (e.g., pytube errors)
        print(f"An error occurred: {e}")
        return None


def download():
    if not valid_url:
        return
    dl_button["state"] = "disabled"
    sel_fol_button["state"] = "disabled"
    format_select["state"] = "disabled"
    url_field["state"] = "disabled"
    status_label.config(text=f"downloading: \'{video_title}\'", fg='red')
    status_label.update()
    url = url_field.get()
    target_format = format_select.get()
    output_path = save_dir_field.get()
    options = {
        'format': 'bestaudio/best',  # Select best available audio format
        'audioformat': target_format,
        'outtmpl': f'{output_path}/%(title)s.{target_format}',  # Output file name template
        'extract_flat': True,  # extract all formats
        'keepvideo': False,  # Only keep the audio
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(options) as dl:
        #info_dict = dl.extract_info(url, download=False)  # Extract info first
        #old_file = dl.prepare_filename(info_dict) #Get the final filename
        dl.download([url])
    #os.remove(old_file)
    status_label.config(text=f"waiting for user...", fg='green')
    status_label.update()
    dl_button["state"] = "normal"
    sel_fol_button["state"] = "normal"
    format_select["state"] = "normal"
    url_field["state"] = "normal"

def url_text_changed(*unused):
    global title_label
    global thumb_label
    global valid_url
    if not is_valid_youtube_url(url_field.get()):
        valid_url = False
        print("invalid url")
        return
    valid_url = True
    print("valid url")
    title_label.config(text="loading...")
    title_label.update()
    thumb_label.config(text="thumbnail loading...")
    thumb_label.update()
    title = get_video_title()
    title_label.config(text=title)
    thumbnail = get_youtube_thumbnail()
    if thumbnail:
        # Resize if needed (optional)
        thumbnail = thumbnail.resize((213, 120), Image.LANCZOS)  # Example size

        photo = ImageTk.PhotoImage(thumbnail)  # Keep a reference to prevent garbage collection
        thumb_label.config(image=str(photo))
        thumb_label.image = photo  # Keep a reference! Very important!
    else:
        thumb_label.config(text="Thumbnail not available.")
    title_label.update()
    thumb_label.update()

def setup_ui():
    global save_dir_field
    global format_select
    global url_field
    global title_label
    global thumb_label
    global status_label
    global sel_fol_button
    global dl_button
    url_frame = tkinter.Frame()
    url_label = tkinter.Label(url_frame, text="youtube url: ")
    url_field = tkinter.Entry(url_frame, width=70)
    url_field.bind("<KeyRelease>", url_text_changed)
    folder_frame = tkinter.Frame()
    save_dir_label = tkinter.Label(folder_frame, text="save to: ")
    sel_fol_button = tkinter.Button(folder_frame, text="select...", command=folder_select_clicked)
    save_dir_field = tkinter.Entry(folder_frame, background="gray85", width=70)
    save_dir_field.config(state="readonly")
    convert_frame = tkinter.Frame()
    convert_label = tkinter.Label(convert_frame, text="convert to: ")
    format_select = ttk.Combobox(convert_frame, values=format_values, state="mp3")
    format_select.current(0)
    dl_button = tkinter.Button(text="download", command=download)

    title_label = tkinter.Label()
    thumb_label = tkinter.Label()

    status_label = tkinter.Label(text="waiting for user...", anchor="s", pady=40, fg='green')

    url_frame.pack(pady=5)
    url_label.pack(side="left")
    url_field.pack(side="right")
    folder_frame.pack(pady=5)
    save_dir_label.pack(side="left")
    save_dir_field.pack(side="left")
    sel_fol_button.pack(side="right", padx=5)
    convert_frame.pack(pady=5)
    convert_label.pack(side="left")
    format_select.pack(side="right")
    dl_button.pack()
    title_label.pack()
    thumb_label.pack()
    status_label.pack(side="bottom")

def ui_init():
    window = tkinter.Tk()
    window.title("quickly download and convert youtube videos")
    position_window(window)
    setup_ui()
    window.mainloop()

def main():
    ui_init()

if __name__ == "__main__":
    main()
