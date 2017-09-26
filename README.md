# yt-dl
easy-to-use YouTube downloader (GUI), created with PyQt5, pytube and beautifulsoup4

## Features
- download videos or playlists from YouTube
- mp4, webm, 3gp, flv supported (as of pytube version 6.4)
- extract audio from downloaded video files
- (in future: convert audio to e.g. mp3)

## Installation
- (if necessary) install Python (>= 3.5) from https://www.python.org/downloads/

#### Linux (Debian):
(extrapolate accordingly for other distros)
```
sudo apt install python3-pip python3-bs4
sudo pip3 install -U pytube PyQt5 beautifulsoup4 lxml
```
#### Windows:
in a cmd enter the following
(provided that python is in your PATH):
```
python -m pip install -U pytube PyQt5 beautifulsoup4 lxml
```
#### macOS:

honestly, idk...

## Launch
```
python3 main.py
```
or, respectively
```
python main.py
```
