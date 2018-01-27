import collections.abc
import html.parser
import sys
import urllib.error
import urllib.request

import bs4
import pytube
import pytube.exceptions
from PyQt5 import QtCore, QtWidgets


class YouTube(QtCore.QObject):
    resolutions = collections.OrderedDict([("144p", "144p"), ("144p 15 fps", "144p15"), ("240p", "240p"),
                                           ("360p", "SD (360p)"), ("480p", "FWVGA (480p)"),
                                           ("720p", "HD (720p)"), ("720p HFR", "HD (720p60)"),
                                           ("1080p", "Full HD (1080p)"), ("1080p HFR", "Full HD (1080p60)"),
                                           ("1440p", "Quad HD (1440p)"), ("1440p HFR", "Quad HD (1440p60)"),
                                           ("2160p", "4K UHD (2160p)"), ("2160p HFR", "4K UHD (2160p60)"),
                                           ("2160p-2304p", "4K UHD (2160p-2304p)"),
                                           ("2160p-4320p", "4K UHD (2160p-4320p)")])

    formats = collections.OrderedDict([("mp4", "MPEG-4 AVC / H.264 (.mp4)"),
                                       ("webm", "VP9 (.webm)"),
                                       ("3gpp", "MPEG-4 Visual (.3gp)"),
                                       ("flv", "Sorenson H.263 (.flv)")])

    standard_formats = collections.OrderedDict([("mp4", ["360p", "720p"]),
                                                ("webm", ["360p"]),
                                                ("3gpp", ["144p", "240p"])])

    finished = QtCore.pyqtSignal()
    video_found = QtCore.pyqtSignal(pytube.YouTube)
    playlist_found = QtCore.pyqtSignal(list)
    success = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str, str, int, tuple, bool)

    last_downloaded = []

    def __init__(self, page_url=None):
        super().__init__()
        self.page_url = page_url

    def find_videos(self):
        try:
            if not self.page_url:
                self.error.emit(self.tr("Error"), self.tr("No URL given. Enter a URL to continue."),
                                QtWidgets.QMessageBox.Warning, (), True)
            else:
                yt = pytube.YouTube(self.page_url)
                self.success.emit()
                self.video_found.emit(yt)
        except (ValueError, AttributeError, urllib.error.URLError):
            try:
                yt = pytube.YouTube("https://" + self.page_url)
                self.success.emit()
                self.video_found.emit(yt)
            except pytube.exceptions.RegexMatchError:
                # this could be an invalid url OR we're maybe dealing with a playlist
                self.find_playlist("https://" + self.page_url)
            except (ValueError, AttributeError, urllib.error.URLError, pytube.exceptions.PytubeError):
                self.error.emit(self.tr("Error"), self.tr("Invalid url: no videos could be found. Check url for typos."),
                                QtWidgets.QMessageBox.Warning, sys.exc_info(), True)

        except pytube.exceptions.RegexMatchError:
            # this could be an invalid url OR we're maybe dealing with a playlist
            self.find_playlist(self.page_url)
        except pytube.exceptions.PytubeError:
            self.error.emit(self.tr("Error"), self.tr("An error occurred. Couldn't get video(s). Try another url."),
                            QtWidgets.QMessageBox.Warning, sys.exc_info(), True)
        finally:
            self.finished.emit()

    def find_playlist(self, url):
        page_html = urllib.request.urlopen(url).read()
        page_soup = bs4.BeautifulSoup(page_html, "html.parser")

        playlist_html = page_soup.find_all(
            "a", attrs={"class": "pl-video-title-link yt-uix-tile-link yt-uix-sessionlink spf-link "})

        if not playlist_html:
            self.error.emit(self.tr("Error"),
                            self.tr("This is not a playlist (or shitty youtube have changed their html again)."),
                            QtWidgets.QMessageBox.Warning, sys.exc_info(), True)
        else:
            videos = []
            for a in playlist_html:
                videos.append((a.string.strip(), "https://www.youtube.com" + a.get("href")))

            self.success.emit()
            self.playlist_found.emit(videos)

    @staticmethod
    def prettify(video_format):
        if video_format in YouTube.formats.keys():
            return YouTube.formats[video_format]
        elif video_format in YouTube.resolutions.keys():
            return YouTube.resolutions[video_format]

    @staticmethod
    def uglify(video_format):
        reversed_format_dict = collections.OrderedDict((value, key) for key, value in YouTube.formats.items())
        reversed_resolution_dict = collections.OrderedDict((value, key) for key, value in YouTube.resolutions.items())

        if video_format in reversed_format_dict.keys():
            return reversed_format_dict[video_format]
        elif video_format in reversed_resolution_dict.keys():
            return reversed_resolution_dict[video_format]
