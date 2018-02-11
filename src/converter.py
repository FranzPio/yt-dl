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
    detection_success = QtCore.pyqtSignal(str, str)
    error = QtCore.pyqtSignal(str, str, int, tuple, bool)

    ENCODE_VBR = "-qscale:a"
    ENCODE_CBR = "-b:a"

    def __init__(self, path):
        super().__init__()
        self.path = os.path.normpath(path)

        self.ffmpeg = shutil.which("ffmpeg") or None
        self.ffprobe = shutil.which("ffprobe") or None

        self.audio_codec = None
        self.file_ext = None

    def convert_audio(self, file_ext, compression_method, quality):
        if self.ffmpeg:
            process = subprocess.Popen([self.ffmpeg,
                                        "-y",  # overwrite possibly existing files without asking
                                        "-i", self.path,
                                        compression_method, str(quality),  # VBR/CBR | value/bitrate
                                        ".".join(self.path.split(".")[:-1]) + file_ext],
                                       stderr=subprocess.PIPE, universal_newlines=True)
                                       # ffmpeg outputs info to stderr | needed because of its \r chars
            for line in process.stderr:
                print(line)
                # parsing to happen here (calculate progress, ETA based on file size / frame number / length ???)
        else:
            self.error.emit(self.tr("Error"),
                            self.tr("Couldn't find ffmpeg. Make sure it's installed and in your PATH."),
                            QtWidgets.QMessageBox.Warning, (), False)

    def extract_audio(self, audio_codec=None):
        if audio_codec is not None:
            try:
                self.audio_codec, self.file_ext = self._detect_audio_codec()
            except (FFprobeNotFoundError, FFprobeError) as error:
                print(error, "\n", sys.exc_info())
                self.error.emit(self.tr("Error"), str(error), QtWidgets.QMessageBox.Warning, sys.exc_info(), True)
                return
        else:
            self.audio_codec = audio_codec
            self.file_ext = self.codecs.get(audio_codec)

        if self.ffmpeg:
            subprocess.run([self.ffmpeg,
                            "-y",
                            "-i", self.path,
                            "-vn",
                            "-codec:a", "copy",
                            ".".join(self.path.split(".")[:-1]) + self.file_ext])
        else:
            self.error.emit(self.tr("Error"),
                            self.tr("Couldn't find ffmpeg. Make sure it's installed and in your PATH."),
                            QtWidgets.QMessageBox.Warning, (), False)

    def _detect_audio_codec(self):
        if self.ffprobe:
            process = subprocess.Popen([self.ffprobe,
                                        "-v", "error",
                                        "-select_streams", "a:0",
                                        "-show_entries", "stream=codec_name",
                                        "-print_format", "csv=p=0",
                                        self.path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stdout:
                audio_codec = stdout.decode("utf-8").strip()
                file_ext = self.codecs.get(audio_codec)
                return audio_codec, file_ext
            else:
                raise FFprobeError(stderr)
        else:
            raise FFprobeNotFoundError(self.tr("Couldn't find ffprobe. Make sure it's installed and in your PATH."))

    def get_audio_codec(self):
        try:
            audio_codec, file_ext = self._detect_audio_codec()
        except (FFprobeNotFoundError, FFprobeError) as error:
            self.error.emit(self.tr("Error"), str(error), QtWidgets.QMessageBox.Warning, sys.exc_info(), True)
        else:
            self.detection_success.emit(self.path, audio_codec)
        finally:
            self.finished.emit()
