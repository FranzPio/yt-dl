import collections.abc
import datetime
import os
import shutil
import subprocess
import sys

from PyQt5 import QtCore, QtWidgets


def sexagesimal_to_timedelta(time_str):
    timedelta = datetime.timedelta(hours=int(time_str.split(":")[0]),
                                   minutes=int(time_str.split(":")[1]),
                                   seconds=float(time_str.split(":")[2].split(".")[0]))  # leave out milliseconds;
    return timedelta                                                                     # seem to be inaccurate anyway


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

    ENCODE_VBR = "-qscale:a"  # variable bitrate (VBR)
    ENCODE_CBR = "-b:a"  # constant bitrate (CBR)

    default_quality = {ENCODE_VBR: "4", ENCODE_CBR: "160k"}

    vbr_bitrates = collections.OrderedDict([("45-85", "9"), ("70-105", "8"), ("80-120", "7"), ("100-130", "6"),
                                            ("120-150", "5"), ("140-185", "4"), ("150-195", "3"), ("170-210", "2"),
                                            ("190-250", "1"), ("220-260", "0")])

    cbr_bitrates = collections.OrderedDict([("8", "8k"), ("16", "16k"), ("32", "32k"), ("40", "40k"), ("48", "48k"),
                                            ("64", "64k"), ("80", "80k"), ("96", "96k"), ("112", "112k"),
                                            ("128", "128k"), ("160", "160k"), ("192", "192k"), ("224", "224k"),
                                            ("256", "256k"), ("320", "320k")])

    compress_methods = collections.OrderedDict([
        (QtCore.QCoreApplication.translate("FFmpeg", "VBR (variable bitrate)"), ENCODE_VBR),
        (QtCore.QCoreApplication.translate("FFmpeg", "CBR (constant bitrate)"), ENCODE_CBR)])

    finished = QtCore.pyqtSignal()
    detection_success = QtCore.pyqtSignal(str, str)
    error = QtCore.pyqtSignal(str, str, int, tuple, bool)
    progress = QtCore.pyqtSignal(datetime.timedelta, datetime.timedelta, int, int)

    def __init__(self, path):
        super().__init__()
        self.path = os.path.normpath(path)

        self.ffmpeg = shutil.which("ffmpeg") or None
        self.ffprobe = shutil.which("ffprobe") or None

        self.audio_codec = None
        self.file_ext = None

    def convert_audio(self, file_ext, compress_method=ENCODE_VBR, quality=None, vconv=1, vtotal=1):
        if self.ffmpeg:
            if quality is None:
                quality = self.default_quality[compress_method]
            process = subprocess.Popen([self.ffmpeg,
                                        "-y",  # overwrite possibly existing files without asking
                                        "-i", self.path,
                                        compress_method, str(quality),
                                        ".".join(self.path.split(".")[:-1]) + file_ext],
                                       stderr=subprocess.PIPE, universal_newlines=True)

            total_duration = self._get_stream_duration("a:0")

            for line in process.stderr:
                if not self.thread().isInterruptionRequested():
                    if not line.startswith("size="):
                        continue
                        # print(line, end="")
                        # debug output; to be removed later on
                    else:
                        kb_conv, duration, bitrate, speed = self._parse_progress_output(line)
                        # print(str(duration), "of", str(total_duration), " | ",
                        #       vconv, "/", vtotal, " | ",
                        #       bitrate, " | ",
                        #       speed)

                        self.progress.emit(duration, total_duration, vconv, vtotal)
                else:
                    if sys.platform == "win32":
                        subprocess.run(["TASKKILL", "/F", "/T", "/PID", str(process.pid)])
                    else:
                        process.terminate()
                    break
            self.finished.emit()
        else:
            self.error.emit(self.tr("Error"),
                            self.tr("Couldn't find ffmpeg. Make sure it's installed and in your PATH."),
                            QtWidgets.QMessageBox.Warning, (), False)

    def extract_audio(self, audio_codec=None, vconv=1, vtotal=1):
        if audio_codec is None:
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
            process = subprocess.Popen([self.ffmpeg,
                                        "-y",
                                        "-i", self.path,
                                        "-vn",
                                        "-codec:a", "copy",
                                        ".".join(self.path.split(".")[:-1]) + self.file_ext],
                                       stderr=subprocess.PIPE, universal_newlines=True)

            total_duration = self._get_stream_duration("a:0")

            for line in process.stderr:
                if not self.thread().isInterruptionRequested():
                    if not line.startswith("size="):
                        continue
                        # print(line, end="")
                        # debug output; to be removed later on
                    else:
                        kb_conv, duration, bitrate, speed = self._parse_progress_output(line)
                        # print(str(duration), "of", str(total_duration), " | ",
                        #       vconv, "/", vtotal, " | ",
                        #       bitrate, " | ",
                        #       speed)

                        self.progress.emit(duration, total_duration, vconv, vtotal)
                else:
                    if sys.platform == "win32":
                        subprocess.run(["TASKKILL", "/F", "/T", "/PID", str(process.pid)])
                    else:
                        process.terminate()
                    break
            self.finished.emit()
        else:
            self.error.emit(self.tr("Error"),
                            self.tr("Couldn't find ffmpeg. Make sure it's installed and in your PATH."),
                            QtWidgets.QMessageBox.Warning, (), False)

    def _get_stream_duration(self, stream):
        if self.ffprobe:
            process = subprocess.Popen([self.ffprobe,
                                        "-v", "error",
                                        "-select_streams", stream,
                                        "-show_entries", "stream=duration",
                                        "-sexagesimal",
                                        "-print_format", "csv=p=0",
                                        self.path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stdout:
                stream_duration = sexagesimal_to_timedelta(stdout.decode("utf-8").strip())
                return stream_duration
            else:
                raise FFprobeError(stderr)
        else:
            raise FFprobeNotFoundError(self.tr("Couldn't find ffmpeg. Make sure it's installed and in your PATH."))

    def _get_stream_size(self, stream, size_wanted):
        if self.ffmpeg:
            process = subprocess.Popen([self.ffmpeg,
                                        "-i", self.path,
                                        "-map", stream,
                                        "-codec", "copy",
                                        "-f", "null",
                                        "-"], stderr=subprocess.PIPE, universal_newlines=True)
            for line in process.stderr:
                print(line)
                if not line.startswith("video:"):
                    continue
                else:
                    file_info = line
                    stream_size_kb = self._parse_file_info(file_info)[size_wanted]
                    return stream_size_kb
        else:
            raise FFmpegNotFoundError(self.tr("Couldn't find ffmpeg. Make sure it's installed and in your PATH."))

    @staticmethod
    def _parse_file_info(line):
        parsed_line = line
        for omit in (" ", "kB", "video", "audio", "subtitle", "other", "streams", "global", "headers", "muxing",
                     "overhead"):
            parsed_line = parsed_line.replace(omit, "")

        parsed_line = parsed_line.replace("unknown", "0")

        info_list = parsed_line.strip(":\n").split(":")
        vsize_kb, asize_kb, ccsize_kb, other_size_kb, headers_size_kb, overhead_size_kb = (int(i) for i in info_list)

        return {"video": vsize_kb, "audio": asize_kb, "subtitle": ccsize_kb, "other streams": other_size_kb,
                "global headers": headers_size_kb, "muxing overhead": overhead_size_kb}

    @staticmethod
    def _parse_progress_output(line):
        parsed_line = line
        for omit in (" ", "size", "time", "bitrate", "speed", "kB", "kbits/s", "x"):
            parsed_line = parsed_line.replace(omit, "")

        progress_list = parsed_line.strip("=\n").split("=")
        # kb_conv_str, duration_str, bitrate_str, speed_str = progress_list
        #
        # kb_conv = int(kb_conv_str)
        # duration = sexagesimal_to_timedelta(duration_str)
        # bitrate = float(bitrate_str)
        # speed = float(speed_str)

        # TODO: investigate: above didn't seem to work on Ubuntu 16.04, probably due to an older version of ffmpeg in the sources
        #       -> workaround below
        kb_conv = int(progress_list[0])
        duration = sexagesimal_to_timedelta(progress_list[1])
        bitrate = float(progress_list[2])
        speed = 0

        return kb_conv, duration, bitrate, speed

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
