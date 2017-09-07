from PyQt5 import QtCore, QtWidgets, QtGui
import time
import sys
import os.path
import traceback
import collections.abc
from youtube import YouTube
from converter import FFmpeg
import resources


# copyright note: YouTube® is a registered trade mark of Google Inc., a subsidiary of Alphabet Inc.

# TODO: about window or something of the like that
#       - credits icons8.com (and loading.io, although CC0) for the yt icon (/ the spinning wheel)
#       - gives license information (GPL v3)

class DownloadWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        time.sleep(0.7)  # a little time for splashie to be shown (otherwise it just blinks up for a nanosecond...)

        self.videos = None
        self.playlist_videos = None
        self.video_formats = None

        self.init_ui()
        self.show()

        splashie.finish(self)

    def init_ui(self):
        self.url_box = self.create_url_box()
        self.settings_box = self.create_settings_box()
        self.save_box = self.create_save_box()
        self.convert_box = self.create_convert_box()

        big_vbox = QtWidgets.QVBoxLayout()
        big_vbox.addWidget(self.url_box)
        big_vbox.addSpacing(15)
        big_vbox.addWidget(self.settings_box)
        big_vbox.addSpacing(15)
        big_vbox.addWidget(self.save_box)
        big_vbox.addSpacing(15)
        big_vbox.addWidget(self.convert_box)

        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(big_vbox)
        self.setCentralWidget(self.widget)

        self.setMinimumSize(395, 400)
        self.setWindowIcon(QtGui.QIcon(":/resources/youtube_icon.ico"))

    def create_url_box(self):
        url_box = QtWidgets.QGroupBox("1. Enter URL")

        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()
        hbox3 = QtWidgets.QHBoxLayout()

        url_box.url_ledit = QtWidgets.QLineEdit()
        url_box.url_ledit.setPlaceholderText("url of a YouTube video or playlist")
        url_box.get_videos_btn = QtWidgets.QPushButton("Find videos...")
        url_box.get_videos_btn.setDefault(True)
        url_box.get_videos_btn.clicked.connect(lambda: self.get_videos_from_url(url_box.url_ledit.text()))
        url_box.loading_indicator = QtWidgets.QLabel()
        url_box.spinning_wheel = QtGui.QMovie(":/resources/rolling.gif")
        url_box.spinning_wheel.setScaledSize(QtCore.QSize(26, 26))
        # url_box.loading_indicator.setMovie(url_box.spinning_wheel)
        url_box.videos_list_widget = QtWidgets.QListWidget()
        url_box.videos_list_widget.hide()

        # retain_size = QtWidgets.QSizePolicy(url_box.loading_indicator.sizePolicy())
        # retain_size.setRetainSizeWhenHidden(True)
        # url_box.loading_indicator.setSizePolicy(retain_size)

        hbox1.addWidget(url_box.url_ledit)
        vbox.addLayout(hbox1)
        hbox2.addWidget(url_box.get_videos_btn)
        hbox2.addSpacing(5)
        hbox2.addWidget(url_box.loading_indicator)
        vbox.addLayout(hbox2)
        hbox3.addWidget(url_box.videos_list_widget)
        vbox.addLayout(hbox3)
        url_box.setLayout(vbox)

        return url_box

    def create_settings_box(self):
        settings_box = QtWidgets.QGroupBox("2. Select quality and format ")

        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()
        hbox3 = QtWidgets.QHBoxLayout()

        settings_box.continue_msg = QtWidgets.QLabel("Click \"Find videos...\" to continue.")
        settings_box.format_dropdown = QtWidgets.QComboBox()
        settings_box.format_dropdown.activated[str].connect(self.on_format_changed)
        settings_box.format_dropdown.hide()
        settings_box.resolution_dropdown = QtWidgets.QComboBox()
        settings_box.resolution_dropdown.hide()

        hbox1.addWidget(settings_box.continue_msg)
        vbox.addLayout(hbox1)
        hbox2.addWidget(settings_box.format_dropdown)
        vbox.addLayout(hbox2)
        hbox3.addWidget(settings_box.resolution_dropdown)
        vbox.addLayout(hbox3)

        settings_box.setLayout(vbox)

        return settings_box

    def on_format_changed(self, new_format):
        self.settings_box.resolution_dropdown.clear()
        format = YouTube.uglify(new_format)
        resolutions = self.video_formats[format]
        self.settings_box.resolution_dropdown.addItems(YouTube.prettify(resolutions))

    def create_save_box(self):
        save_box = QtWidgets.QGroupBox("3. Choose download destination")

        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()
        hbox3 = QtWidgets.QHBoxLayout()

        # TODO: don't just save it anywhere, but open a QFileDialog to select the desired download destination
        save_box.continue_msg = QtWidgets.QLabel("Click \"Find videos...\" to continue.")
        save_box.destination_lbl = QtWidgets.QLabel("video(s) will be saved to current working directory\n"
                                                    "NOTE: This is a TEMPORARY solution just to make it work.")
        save_box.destination_lbl.setWordWrap(True)
        save_box.destination_lbl.hide()
        # save_box.destination_ledit = QtWidgets.QLineEdit()
        # save_box.destination_ledit.setReadOnly(True)
        # save_box.destination_ledit.hide()
        save_box.download_btn = QtWidgets.QPushButton("DOWNLOAD")
        save_box.download_btn.clicked.connect(self.on_download_clicked)
        save_box.download_btn.hide()
        # save_box.loading_indicator = QtWidgets.QLabel()
        # save_box.spinning_wheel = QtGui.QMovie(":/resources/rolling.gif")
        # save_box.spinning_wheel.setScaledSize(QtCore.QSize(26, 26))

        hbox1.addWidget(save_box.continue_msg)
        vbox.addLayout(hbox1)
        # hbox2.addWidget(save_box.destination_ledit)
        hbox2.addWidget(save_box.destination_lbl)
        vbox.addLayout(hbox2)
        hbox3.addWidget(save_box.download_btn)
        # hbox3.addSpacing(5)
        # hbox3.addWidget(save_box.loading_indicator)
        # vbox.addSpacing(5)  # apparently, the spacing is there regardless of whether the hboxes are hidden or not...:(
        vbox.addLayout(hbox3)

        save_box.setLayout(vbox)

        return save_box

    def on_download_clicked(self):
        extension = YouTube.uglify(self.settings_box.format_dropdown.currentText())
        resolution = YouTube.uglify(self.settings_box.resolution_dropdown.currentText())
        # self.save_box.loading_indicator.setMovie(self.save_box.spinning_wheel)
        # self.save_box.spinning_wheel.start()

        if len(self.url_box.videos_list_widget) < 1:
            return
        elif len(self.url_box.videos_list_widget) == 1:
            if self.url_box.videos_list_widget.item(0).checkState() == QtCore.Qt.Checked:
                YouTube._download_video(self.videos, extension, resolution)
            else:
                return
        else:
            checked_videos = []
            for index, video in enumerate(self.playlist_videos):
                if self.url_box.videos_list_widget.item(index).checkState() == QtCore.Qt.Checked:
                    checked_videos.append(self.playlist_videos[index])
            if checked_videos:
                YouTube._download_playlist(checked_videos, extension, resolution)
            else:
                return

        # self.save_box.spinning_wheel.stop()
        # self.save_box.loading_indicator.stop()

    def create_convert_box(self):
        convert_box = QtWidgets.QGroupBox("4. (not really) Convert downloaded file")

        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()
        hbox3 = QtWidgets.QHBoxLayout()

        convert_box.continue_msg = QtWidgets.QLabel("Click \"Find videos...\" to continue.")
        convert_box.experimental_msg = QtWidgets.QLabel("EXPERIMENTAL: extract audio to file,"
                                                        "\nconsole window recommended (for now)"
                                                        "\n(ffprobe + ffmpeg are required for this)")
        convert_box.experimental_msg.hide()
        convert_box.convert_btn = QtWidgets.QPushButton("CONVERT")
        convert_box.convert_btn.clicked.connect(self.on_convert_clicked)
        convert_box.convert_btn.hide()

        hbox1.addWidget(convert_box.continue_msg)
        vbox.addLayout(hbox1)
        hbox2.addWidget(convert_box.experimental_msg)
        vbox.addLayout(hbox2)
        hbox3.addWidget(convert_box.convert_btn)
        vbox.addLayout(hbox3)

        convert_box.setLayout(vbox)

        return convert_box

    def on_convert_clicked(self):
        if YouTube.last_downloaded:
            path_list = []
            for video in YouTube.last_downloaded:
                path_list.append(os.path.abspath(video.filename + "." + video.extension))
            # TODO: put this in threads (GUI freezes) or use ffmpeg's async interface (but idk how that works...)
            #       (+ error slots, progress indicator,...)
            for index, path in enumerate(path_list):
                print("Converting", index, "of", len(path_list), "...")
                converter = FFmpeg(path)
                converter.extract_audio()
            print("Finished (more or less) successfully.")

    def get_videos_from_url(self, page_url=None):
        # sys.excepthook = lambda *args: print(args)
        self.url_box.get_videos_btn.setDisabled(True)
        self.url_box.url_ledit.setDisabled(True)
        self.url_box.videos_list_widget.setDisabled(True)
        self.settings_box.format_dropdown.setDisabled(True)
        self.settings_box.resolution_dropdown.setDisabled(True)
        self.url_box.loading_indicator.setMovie(self.url_box.spinning_wheel)
        self.url_box.spinning_wheel.start()

        self.threads_workers = {}
        yt = YouTube(page_url)
        thread = QtCore.QThread()
        self.threads_workers.update({"thread": thread, "worker": yt})
        yt.moveToThread(thread)
        yt.finished.connect(thread.quit)
        yt.videos_found.connect(self.on_videos_found)
        yt.playlist_found.connect(self.on_playlist_found)
        yt.success.connect(self.on_success)
        yt.error.connect(self.on_error)

        thread.started.connect(yt.find_videos)
        thread.finished.connect(self.on_thread_finished)

        thread.start()

    def on_videos_found(self, videos):
        # TODO: this doesn't have to be a QListWidget anymore since we can be sure to get only one video
        video_item = QtWidgets.QListWidgetItem()
        video_item.setText("1 - " + videos[0].filename)
        video_item.setFlags(video_item.flags() | QtCore.Qt.ItemIsUserCheckable)
        video_item.setCheckState(QtCore.Qt.Checked)
        self.url_box.videos_list_widget.addItem(video_item)
        self.url_box.videos_list_widget.show()

        self.video_formats = collections.OrderedDict()
        for format in YouTube.formats.keys():
            self.video_formats.update({format: []})
        for video in videos:
            self.video_formats[video.extension].append(video.resolution)
        for format, resolution in self.video_formats.items():
            if not resolution:
                self.video_formats.pop(format)

        prettified_formats = YouTube.prettify(self.video_formats)
        self.settings_box.format_dropdown.addItems(prettified_formats.keys())
        self.settings_box.resolution_dropdown.addItems(list(prettified_formats.values())[0])

        self.videos = videos

    def on_playlist_found(self, videos):
        for index, video_info in enumerate(videos):
            video_item = QtWidgets.QListWidgetItem()
            video_item.setText(str(index + 1) + " - " + video_info[0])
            video_item.setFlags(video_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            video_item.setCheckState(QtCore.Qt.Checked)
            self.url_box.videos_list_widget.addItem(video_item)
            self.url_box.videos_list_widget.show()

        self.video_formats = YouTube.standard_formats
        prettified_formats = YouTube.prettify(self.video_formats)
        self.settings_box.format_dropdown.addItems(prettified_formats.keys())
        self.settings_box.resolution_dropdown.addItems(list(prettified_formats.values())[0])

        self.playlist_videos = videos

        # TODO: as QListWidget + settings box have been updated, "yt.get_videos()" could silently be called in a thread
        #       and in the background create a list of "pytube.models.Video" objects
        #       whose file size (+ extension / resolution) the QListWidget could be updated with when thread finishes

    def on_thread_finished(self):
        self.url_box.spinning_wheel.stop()
        self.url_box.loading_indicator.clear()
        self.url_box.get_videos_btn.setEnabled(True)
        self.url_box.url_ledit.setEnabled(True)
        self.url_box.videos_list_widget.setEnabled(True)
        self.settings_box.format_dropdown.setEnabled(True)
        self.settings_box.resolution_dropdown.setEnabled(True)
        self.resize(self.widget.sizeHint())

    def on_success(self):
        self.url_box.videos_list_widget.clear()
        self.settings_box.format_dropdown.clear()
        self.settings_box.resolution_dropdown.clear()

        self.settings_box.continue_msg.hide()
        self.settings_box.format_dropdown.show()
        self.settings_box.resolution_dropdown.show()
        self.save_box.continue_msg.hide()
        self.save_box.destination_lbl.show()
        self.save_box.download_btn.show()
        self.convert_box.continue_msg.hide()
        self.convert_box.experimental_msg.show()
        self.convert_box.convert_btn.show()

    def on_error(self, error_msg, error_info):
        # TODO: rename to something less "slot-sounding" as this is a quite convenient method being used elsewhere too
        error_msgbox = QtWidgets.QMessageBox()
        error_msgbox.setWindowTitle("Error")
        error_msgbox.setIcon(QtWidgets.QMessageBox.Warning)
        # error_msgbox.setText("An error occured.")
        error_msgbox.setText(error_msg)
        error_msgbox.setDetailedText(str(error_info[0]) + "\n" + str(error_info[1]) + "\n\n"
                                     + "Traceback (most recent call last):\n"
                                     + "".join(traceback.format_tb(error_info[2])))
        error_msgbox.exec()
        # print(error_msg, "\n", error_info, sep="")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    pixmap = QtGui.QPixmap(":/resources/youtube_splash_screen.png")
    splashie = QtWidgets.QSplashScreen(pixmap)
    splashie.show()
    app.processEvents()
    # locale = QtCore.QLocale.system().name()
    # qtTranslator = QtCore.QTranslator()
    # translations_path = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath)
    # if qtTranslator.load("qtbase_" + locale, translations_path):
    #     app.installTranslator(qtTranslator)
    # else:
    #     print("[PyNEWS] Error loading Qt language file for", locale, "language!")
    window = DownloadWindow()
    app.exec_()
