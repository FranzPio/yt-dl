#!/usr/bin/env python3
import collections.abc
import os.path
import sys

from PyQt5 import QtCore, QtWidgets, QtGui

from converter import FFmpeg
from dialogs import UpdateDialog, AboutDialog, show_msgbox, show_splash
from youtube import YouTube


class DownloadWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.splashie = show_splash(self)
        QtCore.QTimer.singleShot(1200, self.show_window)

        self.videos = None
        self.playlist_videos = None
        self.video_formats = None

        self.init_ui()

    def show_window(self):
        self.show()
        self.splashie.finish(self)

    def init_ui(self):
        self.toolbar = self.create_toolbar()

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
        self.move(QtWidgets.qApp.desktop().screen().rect().center() - self.rect().center())
        self.setWindowIcon(QtGui.QIcon(":/youtube_icon.ico"))
        self.setWindowTitle("yt-dl")

    def create_toolbar(self):
        exit_action = QtWidgets.QAction("&Exit", self)
        exit_action.setShortcut(QtCore.Qt.ControlModifier | QtCore.Qt.Key_Q)
        exit_action.triggered.connect(QtWidgets.qApp.quit)

        update_action = QtWidgets.QAction("&Check for updates", self)
        update_action.triggered.connect(self.update_dialog)

        about_action = QtWidgets.QAction("&About", self)
        about_action.triggered.connect(self.about_dialog)

        menu_bar = self.menuBar()
        actions_menu = menu_bar.addMenu("&Actions")
        actions_menu.addAction(exit_action)
        help_menu = menu_bar.addMenu("&?")
        help_menu.addAction(update_action)
        help_menu.addAction(about_action)
        return menu_bar

    def update_dialog(self):
        update_dlg = UpdateDialog(self)
        update_dlg.exec()

    def about_dialog(self):
        about_dlg = AboutDialog(self)
        about_dlg.exec()

    def create_url_box(self):
        url_box = QtWidgets.QGroupBox("1. Enter URL")

        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()
        hbox3 = QtWidgets.QHBoxLayout()

        url_box.url_ledit = QtWidgets.QLineEdit()
        url_box.url_ledit.setPlaceholderText("URL of a YouTube video or playlist")
        url_box.get_videos_btn = QtWidgets.QPushButton("Find videos...")
        url_box.get_videos_btn.setDefault(True)
        url_box.get_videos_btn.clicked.connect(lambda: self.get_videos_from_url(url_box.url_ledit.text()))
        url_box.loading_indicator = QtWidgets.QLabel()
        url_box.spinning_wheel = QtGui.QMovie(":/rolling.gif")
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
        for i in self.video_formats[format]:
            self.settings_box.resolution_dropdown.addItem(YouTube.prettify(i))

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
        save_box.download_btn = QtWidgets.QPushButton("DOWNLOAD")
        save_box.download_btn.clicked.connect(self.on_download_clicked)
        save_box.download_btn.hide()

        hbox1.addWidget(save_box.continue_msg)
        vbox.addLayout(hbox1)
        hbox2.addWidget(save_box.destination_lbl)
        vbox.addLayout(hbox2)
        hbox3.addWidget(save_box.download_btn)
        vbox.addLayout(hbox3)

        save_box.setLayout(vbox)

        return save_box

    def on_download_clicked(self):
        extension = YouTube.uglify(self.settings_box.format_dropdown.currentText())
        resolution = YouTube.uglify(self.settings_box.resolution_dropdown.currentText())

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
                    checked_videos.append(video)
            if checked_videos:
                YouTube._download_playlist(checked_videos, extension, resolution)
            else:
                return

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

    @staticmethod
    def on_convert_clicked():
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

        self.yt = YouTube(page_url)
        self.thread = QtCore.QThread()
        self.yt.moveToThread(self.thread)
        self.yt.finished.connect(self.thread.quit)
        self.yt.videos_found.connect(self.on_videos_found)
        self.yt.playlist_found.connect(self.on_playlist_found)
        self.yt.success.connect(self.on_success)
        self.yt.error.connect(show_msgbox)

        self.thread.started.connect(self.yt.find_videos)
        self.thread.finished.connect(self.on_thread_finished)

        self.thread.start()

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

        for i in self.video_formats.keys():
            self.settings_box.format_dropdown.addItem(YouTube.prettify(i))
        for i in list(self.video_formats.values())[0]:
            self.settings_box.resolution_dropdown.addItem(YouTube.prettify(i))

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
        for i in self.video_formats.keys():
            self.settings_box.format_dropdown.addItem(YouTube.prettify(i))
        for i in list(self.video_formats.values())[0]:
            self.settings_box.resolution_dropdown.addItem(YouTube.prettify(i))

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


def startup():
    app = QtWidgets.QApplication(sys.argv)
    # locale = QtCore.QLocale.system().name()
    # qtTranslator = QtCore.QTranslator()
    # translations_path = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath)
    # if qtTranslator.load("qtbase_" + locale, translations_path):
    #     app.installTranslator(qtTranslator)
    # else:
    #     print("[PyNEWS] Error loading Qt language file for", locale, "language!")
    window = DownloadWindow()
    app.exec_()


if __name__ == "__main__":
    startup()
