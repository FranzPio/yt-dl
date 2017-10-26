# yt-dl
easy-to-use YouTube downloader (GUI), created with PyQt5, pytube and beautifulsoup4

### Features
- download videos or playlists from YouTube
- mp4, webm, 3gp, flv supported
- extract audio from downloaded video files

### To do
- support pytube v7 or switch to youtube-dl
- convert audio to e.g. mp3
- bundle ffmpeg or automatically download + install it

[...]

### Installation
#### Source:
(extrapolate accordingly for other distros)
```
sudo apt install python3-pip python3-bs4
sudo pip3 install -U pytube PyQt5 beautifulsoup4 lxml
```
to launch, type
```
python3 main.py
```
(given that the files are in your working directory)
#### Windows:
execute `yt-dl_x.x.x_setup.exe` and follow the instructions
