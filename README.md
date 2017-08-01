# yt-dl
youtube-downloader (GUI) for Windows + Linux (+ macOS), created with PyQt5, pytube and beautifulsoup4

## Features
- download videos or playlists from YouTube
- mp4, webm, 3gp, flv supported (as of pytube version 6.4)
- (in future: convert downloaded video files, e.g. to mp3)

## Installation
- (if necessary) install Python (>= 3.5) from https://www.python.org/downloads/

#### Linux (Debian):
(extrapolate accordingly for other distros)
```
sudo apt install python3-pip
sudo pip3 install pytube PyQt5 beautifulsoup4 lxml
```
#### Windows:
in a cmd enter the following
(provided that python is in your PATH):
```
python -m pip install pytube PyQt5 beautifulsoup4 lxml
```
#### macOS:

idk...

## Launch
```
python3 main.py
```
or, respectively
```
python main.py
```
