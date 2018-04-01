import collections.abc
import datetime
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
    codecs = collections.OrderedDict([("aac", ".m4a"),
                                      ("vorbis", ".ogg"),
                                      ("opus", ".opus"),
                                      ("mp3", ".mp3")])

    finished = QtCore.pyqtSignal()
    detection_success = QtCore.pyqtSignal(str, str)
    error = QtCore.pyqtSignal(str, str, int, tuple, bool)

    ENCODE_VBR = "-qscale:a"  # variable bitrate (VBR)
    #  option | avg. bitrate  ||  option | avg. bitrate
    #  =====================  ||  =====================
    #    9    |    65 kbps    ||    4    |   165 kbps
    #    8    |    85 kbps    ||    3    |   175 kbps
    #    7    |   100 kbps    ||    2    |   195 kbps
    #    6    |   115 kbps    ||    1    |   225 kbps
    #    5    |   130 kbps    ||    0    |   245 kbps

    ENCODE_CBR = "-b:a"  # constant bitrate (CBR)
    # bitrate in kbps, followed by a "k"

    default_quality = {ENCODE_VBR: "4", ENCODE_CBR: "160k"}

    def __init__(self, path):
        super().__init__()
        self.path = os.path.normpath(path)

        self.ffmpeg = shutil.which("ffmpeg") or None
        self.ffprobe = shutil.which("ffprobe") or None

        self.audio_codec = None
        self.file_ext = None

    def convert_audio(self, file_ext, compress_method=ENCODE_VBR, quality=None):
        if self.ffmpeg:
            if quality is None:
                quality = self.default_quality[compress_method]
            process = subprocess.Popen([self.ffmpeg,
                                        "-y",  # overwrite possibly existing files without asking
                                        "-i", self.path,
                                        compress_method, str(quality),
                                        ".".join(self.path.split(".")[:-1]) + file_ext],
                                       stderr=subprocess.PIPE, universal_newlines=True)

            for line in process.stderr:
                if not line.startswith("size="):
                    print(line)
                    # debug output; to be removed later on
                else:
                    fsize, duration, bitrate, speed = self._parse_output(line)

                    print(fsize, duration, bitrate, speed)
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

    @staticmethod
    def _parse_output(line):
        parsed_line = line
        for omit in (" ", "size", "time", "bitrate", "speed", "kB", "kbits/s", "x"):
            parsed_line = parsed_line.replace(omit, "")

        progress_list = parsed_line.strip("=\n").split("=")
        fsize_str, duration_str, bitrate_str, speed_str = progress_list

        fsize = int(fsize_str)
        duration = datetime.timedelta(hours=int(duration_str.split(":")[0]),
                                      minutes=int(duration_str.split(":")[1]),
                                      seconds=float(duration_str.split(":")[2]))
        bitrate = float(bitrate_str)
        speed = float(speed_str)

        return fsize, duration, bitrate, speed

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
