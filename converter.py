from PyQt5 import QtCore
import subprocess
import shutil
import os
import sys
import collections.abc


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

    ffmpeg = shutil.which("ffmpeg") or None
    ffprobe = shutil.which("ffprobe") or None

    finished = QtCore.pyqtSignal()
    success = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.path = os.path.normpath(path)

        self.audio_codec = None
        self.file_ext = None

    def convert_audio(self):
        pass

    def extract_audio(self):
        try:
            self.get_audio_codec()
        except FFprobeNotFoundError as error:
            print(error, "\n", sys.exc_info())
            self.error.emit(error, sys.exc_info())
        except FFprobeError as error:
            print(error, "\n", sys.exc_info())
            self.error.emit(error, sys.exc_info())
        else:
            subprocess.run([self.ffmpeg,
                            "-i", self.path,
                            "-vn",
                            "-acodec", "copy",
                            self.path.split(".")[0] + self.file_ext])

    def get_audio_codec(self):
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
                error = stderr
                raise FFprobeError(error)
        else:
            error = "Couldn't find ffprobe. Make sure it's installed and in your PATH."
            raise FFprobeNotFoundError(error)
