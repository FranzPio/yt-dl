import sys
import os.path

VERSION = "0.9.5"
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
