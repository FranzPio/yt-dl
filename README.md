# yt-dl
easy-to-use YouTube downloader (GUI), created with PyQt5, pytube and beautifulsoup4

### Features
- download videos or playlists from YouTube
- mp4, webm, 3gp, flv supported
- extract audio from downloaded video files

### To do
- entirely support pytube v7 (e.g. resolutions >= 1080p)
- convert audio to e.g. mp3
- bundle ffmpeg or automatically download + install it (needed to combine yt's separate audio / video streams)
- set ID3 tags to files (e.g. title, creator, thumbnail)

[...]

### Installation
#### Windows:
download [`yt-dl_x.x.x_setup.exe`](https://github.com/FranzPio/yt-dl/releases), execute it and follow the instructions

#### Source:
(extrapolate accordingly for non-Debian distros)
##### Install dependencies
```
sudo apt install python3-pip python3-setuptools python3-bs4
sudo pip3 install -U pytube PyQt5 beautifulsoup4
```
##### (optional) Fix appearance
on some systems using the distro's PyQt package results in an improved appearance, e.g. on Debian this can be done as follows:
```
pip3 uninstall PyQt5 sip
sudo apt install python3-pyqt5
```
##### Clone repo
```
git clone https://github.com/FranzPio/yt-dl && cd yt-dl/src
```
##### Launch application
```
python3 main.py
```
