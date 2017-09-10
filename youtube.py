from PyQt5 import QtCore, QtWidgets
import pytube, pytube.exceptions
import urllib.request, urllib.error
import bs4
import sys
import collections.abc


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
                                       ("3gp", "MPEG-4 Visual (.3gp)"),
                                       ("flv", "Sorenson H.263 (.flv)")])

    standard_formats = collections.OrderedDict([("mp4", ["360p", "720p"]),
                                                ("webm", ["360p"]),
                                                ("3gp", ["144p", "240p"])])

    finished = QtCore.pyqtSignal()
    videos_found = QtCore.pyqtSignal(list)
    playlist_found = QtCore.pyqtSignal(list)
    success = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str, str, int, tuple, bool)
    # critical_error = QtCore.pyqtSignal(str, tuple)  # later replace this by another argument passed in error.emit()
                                                      # (e.g. QtWidgets.QMessageBox.Critical)

    last_downloaded = []

    def __init__(self, page_url):
        super().__init__()
        self.page_url = page_url

    def find_videos(self):
        try:
            yt = pytube.YouTube(self.page_url)
            videos = yt.get_videos()
            if not videos:
                self.error.emit("Error", "No URL given. Enter a URL to continue.",
                                QtWidgets.QMessageBox.Warning, sys.exc_info(), True)
            else:
                self.success.emit()
                self.videos_found.emit(videos)
        except (ValueError, AttributeError, urllib.error.URLError, pytube.exceptions.PytubeError):
            try:
                yt = pytube.YouTube("https://" + self.page_url)
                videos = yt.get_videos()
                if not videos:
                    self.error.emit("Error", "No URL given. Enter a URL to continue.",
                                    QtWidgets.QMessageBox.Warning, sys.exc_info(), True)
                else:
                    self.success.emit()
                    self.videos_found.emit(videos)
            except (ValueError, AttributeError, urllib.error.URLError, pytube.exceptions.PytubeError):
                self.error.emit("Error", "Invalid url: no videos could be found. Check url for typos.",
                                QtWidgets.QMessageBox.Warning, sys.exc_info(), True)
            except pytube.exceptions.AgeRestricted:
                # the video could be age restricted OR we're maybe dealing with a playlist
                self.find_playlist("https://" + self.page_url)
            except Exception:
                self.error.emit("Error", "An unexpected error occurred. See below for details.",
                                QtWidgets.QMessageBox.Critical, sys.exc_info(), True)

        except (pytube.exceptions.CipherError, pytube.exceptions.ExtractorError):
            self.error.emit("Error", "An error occurred. Couldn't get video(s). Try another url.",
                            QtWidgets.QMessageBox.Warning, sys.exc_info(), True)
        except pytube.exceptions.AgeRestricted:
            # the video could be age restricted OR we're maybe dealing with a playlist
            self.find_playlist(self.page_url)
        except Exception:
            self.error.emit("Error", "An unexpected error occurred. See below for details.",
                            QtWidgets.QMessageBox.Critical, sys.exc_info(), True)
        finally:
            self.finished.emit()

    def find_playlist(self, url):
        page_html = urllib.request.urlopen(url).read()
        page_soup = bs4.BeautifulSoup(page_html, "lxml")

        playlist_html = page_soup.find_all(
            "a", attrs={"class": "pl-video-title-link yt-uix-tile-link yt-uix-sessionlink spf-link "})

        if not playlist_html:
            self.error.emit("Error", "This video is age-restricted. This is not supported by pytube as of version 6.4.",
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

    @staticmethod
    def download_video(video_list, extension="mp4", resolution=None, destination=""):
        raise NotImplementedError("Since this application is still under active development, not all features are "
                                  "available yet. Be patient!")

    @staticmethod
    def download_playlist(video_list, extension="mp4", resolution=None, destination=""):
        raise NotImplementedError("Since this application is still under active development, not all features are "
                                  "available yet. Be patient!")

    @staticmethod
    def _download_video(video_list, extension, resolution, destination=""):
        # TODO: "really" do it (put downloading into thread, emit signals, update progress bar etc.)
        YouTube.last_downloaded.clear()
        successful_downloads = 0
        errors = 0
        print("Downloading ", "1", "of", "1", "...", flush=True)
        try:
            for video in video_list:
                if video.extension == extension and video.resolution == resolution:
                    video.download(destination)
                    break
        except Exception:
            print("An error occurred:\n", sys.exc_info())
            errors += 1
        else:
            successful_downloads += 1
            YouTube.last_downloaded.append(video)

        print(successful_downloads, "of", "1", "videos were downloaded successfully.")
        if errors:
            print(errors, "errors occurred.")
        return

    @staticmethod
    def _download_playlist(video_list, extension, resolution, destination=""):
        YouTube.last_downloaded.clear()
        successful_downloads = 0
        errors = 0
        for index, video in enumerate(video_list):
            print("Downloading", index + 1, "of", len(video_list), "...", flush=True)
            try:
                yt = pytube.YouTube(video[1])
                video = yt.get(extension, resolution)
                video.download(destination)
            except pytube.exceptions.DoesNotExist:
                print("An error occurred:\nThe video isn't available in the given format / resolution."
                      "This happens due to a bug that will be fixed soon.\n", sys.exc_info())
                errors += 1
            except Exception:
                print("An error occurred:\n", sys.exc_info())
                errors += 1
            else:
                successful_downloads += 1
                YouTube.last_downloaded.append(video)

        print(successful_downloads, "of", len(video_list), "videos were downloaded successfully.")
        if errors:
            print(errors, "errors occurred.")
        return
