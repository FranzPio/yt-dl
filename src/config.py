import os.path
import sys

VERSION = "0.13"
IS_FROZEN = hasattr(sys, "frozen")

if IS_FROZEN:
    FILE = sys.executable
    EXE = sys.executable
else:
    FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "main.py")
    EXE = [sys.executable, FILE]

APP_PATH = os.path.dirname(FILE)

ZIP_URL = "https://github.com/FranzPio/yt-dl/zipball/master/"
GITHUB_URL = "https://github.com/FranzPio/yt-dl"
ICONS8_URL = "https://icons8.com"
LOADINGIO_URL = "https://loading.io"

# TODO: youtube_icon_red.ico needs to be extracted from resources.py, saved to some icon location and path inserted here
DESKTOP_FILE_TEXT = "[Desktop Entry]\n" \
                    + "Name=yt-dl\n" \
                    + "GenericName=YouTube downloader\n" \
                    + "GenericName[de]=YouTube downloader\n" \
                    + "Comment=Easy-to-use YouTube downloader\n" \
                    + "Exec=%s\n" % " ".join(EXE) \
                    + "Icon=/home/franz/PycharmProjects/yt-dl/resources/youtube_icon_red.ico\n" \
                    + "Terminal=false\n" \
                    + "Type=Application\n" \
                    + "StartupNotify=false\n" \
                    + "Categories=Network;\n"
