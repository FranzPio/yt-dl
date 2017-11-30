import sys

import pytube
from PyQt5 import QtCore, QtWidgets


class Downloader(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str, str, int, tuple, bool)
    success = QtCore.pyqtSignal(int, int)
    progress = QtCore.pyqtSignal(int, int, int, int)
    pulse = QtCore.pyqtSignal(bool)

    last_downloaded = []

    def __init__(self, yt=None):
        super().__init__()
        self.yt = yt

        self.video_downloading = 0
        self.videos_total = 0

    def get_stream(self, video, extension, resolution):
        global stream_fsize
        for stream in video:
            if stream.subtype == extension and stream.resolution == resolution:
                stream_fsize = stream.filesize
                return stream

    def download_video(self, video, extension, resolution, destination=""):
        self.yt.register_on_progress_callback(self.on_progress)
        self.last_downloaded.clear()
        self.video_downloading = 1
        self.videos_total = 1
        successful_downloads = 0
        try:
            stream = self.get_stream(video, extension, resolution)
            stream.download(destination)
        except Exception:
            self.error.emit("Error", "An error occurred during the downloading. See below for details.",
                            QtWidgets.QMessageBox.Critical, sys.exc_info(), True)
        else:
            successful_downloads += 1
            self.last_downloaded.append(stream)
        self.success.emit(successful_downloads, self.videos_total)
        self.finished.emit()

    def download_playlist(self, video_list, extension, resolution, destination=""):
        # TODO: multi-threaded downloading -> playlists download faster
        self.last_downloaded.clear()
        self.videos_total = len(video_list)
        successful_downloads = 0
        for video in video_list:
            self.video_downloading += 1
            try:
                self.pulse.emit(True)
                yt = pytube.YouTube(video[1])
                yt.register_on_progress_callback(self.on_progress)
                video = yt.streams.filter(progressive=True).desc().all()
                stream = self.get_stream(video, extension, resolution)
                self.pulse.emit(False)
                if stream is None:
                    self.error.emit("Error", "Video #%s not available in the given resolution (%s).\n"
                                    "This is a bug that will be fixed...some day..."
                                    % (self.video_downloading, resolution), QtWidgets.QMessageBox.Critical, (), False)
                    continue
                else:
                    stream.download(destination)
            except Exception:
                self.error.emit("Error", "An error occurred during the downloading. See below for details.",
                                QtWidgets.QMessageBox.Critical, sys.exc_info(), True)
            else:
                successful_downloads += 1
                self.last_downloaded.append(stream)
        self.success.emit(successful_downloads, self.videos_total)
        self.finished.emit()

    def on_progress(self, stream, chunk, fhandle, bremain):
        # accessing stream.filesize, vdl, vtotal = bottleneck; fixed by declaring global vars
        global vdl, vtotal
        vdl = self.video_downloading
        vtotal = self.videos_total
        self.progress.emit(stream_fsize - bremain, stream_fsize, vdl, vtotal)
