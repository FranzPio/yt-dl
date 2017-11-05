import collections.abc
import os
import shutil
import subprocess
import sys

from PyQt5 import QtCore, QtWidgets


class FFmpegError(Exception):
    pass


class FFmpegNotFoundError(FFmpegError):
    pass


class FFprobeError(Exception):
    pass


class FFprobeNotFoundError(FFprobeError):
    pass


# TODO: set ID3 tags from title / video thumbnail as cover
class FFmpeg(QtCore.QObject):
    codecs = collections.OrderedDict([("aac", ".aac"),
                                      ("vorbis", ".ogg"),
                                      ("opus", ".opus"),
                                      ("mp3", ".mp3")])

    finished = QtCore.pyqtSignal()
    success = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str, str, int, tuple, bool)

    def __init__(self, path):
        super().__init__()
        self.path = os.path.normpath(path)

        self.ffmpeg = shutil.which("ffmpeg") or None
        self.ffprobe = shutil.which("ffprobe") or None

        self.audio_codec = None
        self.file_ext = None

    def convert_audio(self):
        pass

    def extract_audio(self):
        try:
            self.get_audio_codec()
        except FFprobeNotFoundError as error:
            print(error, "\n", sys.exc_info())
            self.error.emit("Error", str(error), QtWidgets.QMessageBox.Warning, sys.exc_info(), True)
        except FFprobeError as error:
            print(error, "\n", sys.exc_info())
            self.error.emit("Error", str(error), QtWidgets.QMessageBox.Critical, sys.exc_info(), True)
        else:
            subprocess.run([self.ffmpeg,
                            "-i", self.path,
                            "-vn",
                            "-acodec", "copy",
                            self.path.split(".")[0] + self.file_ext])

    def get_audio_codec(self):
        # TODO: testing (stdout decoding seems ewwww...)
        if self.ffprobe:
            process = subprocess.Popen([self.ffprobe,
                                        "-v", "error",
                                        "-select_streams", "a:0",
                                        "-show_entries", "stream=codec_name",
                                        "-print_format", "csv=p=0",
                                        self.path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stdout:
                self.audio_codec = stdout.decode("utf-8").strip()  # does that work on Windows?! (stdout encoding different?)
                self.file_ext = self.codecs.get(self.audio_codec)
            else:
                raise FFprobeError(stderr)
        else:
            raise FFprobeNotFoundError("Couldn't find ffprobe. Make sure it's installed and in your PATH.")
