from PyQt5 import QtCore, QtWidgets, QtGui
import time
import sys
import traceback
import collections.abc
from youtube import YouTube


# TODO: about window or something of the like that
#       - credits icons8.com (and loading.io, although CC0) for the yt icon (/ the spinning wheel)
#       - gives license information (GPL v3)

class DownloadWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        time.sleep(0.7)  # a little time for splashie to be shown (otherwise it just blinks up for a nanosecond...)

        self.video_formats = None

        self.init_ui()
        self.show()

        splashie.finish(self)

    def init_ui(self):
        self.url_box = self.create_url_box()
        self.settings_box = self.create_settings_box()
        # self.settings_box.quality_dropdown.show()
        # self.settings_box.format_dropdown.show()
        # self.settings_box.continue_msg.hide()
        self.save_box = self.create_save_box()
        # convert_box = self.create_convert_box()

        big_vbox = QtWidgets.QVBoxLayout()
        big_vbox.addWidget(self.url_box)
        big_vbox.addSpacing(15)
        big_vbox.addWidget(self.settings_box)
        big_vbox.addSpacing(15)
        big_vbox.addWidget(self.save_box)
        # big_vbox.addSpacing(15)
        # big_vbox.addWidget(convert_box)

        widget = QtWidgets.QWidget()
        widget.setLayout(big_vbox)
        self.setCentralWidget(widget)

        self.setWindowIcon(QtGui.QIcon("youtube_icon.ico"))

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
        url_box.spinning_wheel = QtGui.QMovie("rolling.gif")
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
        hbox4 = QtWidgets.QHBoxLayout()

        save_box.continue_msg = QtWidgets.QLabel("Click \"Find videos...\" to continue.")
        save_box.destination_lbl = QtWidgets.QLabel("(saving to current directory)")
        save_box.destination_lbl.hide()
        save_box.download_btn = QtWidgets.QPushButton("DOWNLOAD")
        save_box.download_btn.clicked.connect(self.on_download_clicked)
        save_box.download_btn.hide()
        save_box.loading_indicator = QtWidgets.QLabel()
        save_box.spinning_wheel = QtGui.QMovie("rolling.gif")
        save_box.spinning_wheel.setScaledSize(QtCore.QSize(26, 26))
        save_box.note_lbl = QtWidgets.QLabel("NOTE: This is a TEMPORARY solution just to make it work.")
        save_box.note_lbl.setWordWrap(True)
        save_box.note_lbl.hide()

        hbox1.addWidget(save_box.continue_msg)
        vbox.addLayout(hbox1)
        hbox2.addWidget(save_box.destination_lbl)
        vbox.addLayout(hbox2)
        hbox3.addWidget(save_box.download_btn)
        hbox3.addSpacing(5)
        hbox3.addWidget(save_box.loading_indicator)
        vbox.addSpacing(5)
        vbox.addLayout(hbox3)
        hbox4.addWidget(save_box.note_lbl)
        vbox.addSpacing(5)
        vbox.addLayout(hbox4)

        save_box.setLayout(vbox)

        return save_box

    def on_download_clicked(self):
        extension = YouTube.uglify(self.settings_box.format_dropdown.currentText())
        resolution = YouTube.uglify(self.settings_box.resolution_dropdown.currentText())
        # self.save_box.loading_indicator.setMovie(self.save_box.spinning_wheel)
        # self.save_box.spinning_wheel.start()
        # TODO: later only download those videos actually checked in the QListWidget
        YouTube._download(self.videos, extension, resolution)
        # self.save_box.spinning_wheel.stop()
        # self.save_box.loading_indicator.stop()

    @staticmethod
    def create_convert_box():
        convert_box = QtWidgets.QGroupBox("4. Convert downloaded file")

        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()

        convert_box.continue_msg = QtWidgets.QLabel("This feature is not yet available.")

        hbox1.addWidget(convert_box.continue_msg)
        vbox.addLayout(hbox1)

        convert_box.setLayout(vbox)

        return convert_box

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
        yt.error.connect(self.on_error)

        thread.started.connect(yt.find_videos)
        thread.finished.connect(self.on_thread_finished)

        thread.start()

    def on_videos_found(self, videos):
        self.url_box.videos_list_widget.clear()
        self.settings_box.format_dropdown.clear()
        self.settings_box.resolution_dropdown.clear()

        for video_info in videos:
            video_item = QtWidgets.QListWidgetItem()
            video_item.setText(str(video_info["index"]) + " - " + video_info["title"])
            video_item.setFlags(video_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            video_item.setCheckState(QtCore.Qt.Checked)
            self.url_box.videos_list_widget.addItem(video_item)
            self.url_box.videos_list_widget.show()

            for i in video_info["formats"]:
                print(i.resolution)

            # TODO: find a *nice* solution to properly handle single videos / playlists
            # seems "pytube.YouTube.get_videos()" returns "pytube.models.Video" objects (-> video_info["formats"])
            # which already have attributes title (= "filename"), format (= "extension") + quality (= "resolution"),
            # even contain the "real" URL of the actual video
            # and have a "download" method providing on_progress "signals" that could be used to update a progress bar.

            # problem: it takes too long to get Video objects for every playlist member at once,
            #          although it works for single videos (and is necessary to display available formats / resolutions)
            #          (those nested dicts are ugly af and unnecessary...)
            #          how should "on_success" differentiate between a single video (Video object) and playlist members?

            # solution: data has to be stored differently (obviously a list won't do...objects? -> wrap Video class)
            #           OR (even better) split up "success" signal into e.g. "playlist_success" and "video_success"
            #           that have different slots handling those different data types differently.
            #           (actually no QListWidget is needed for a single video -> could be changed with this approach)

        self.video_formats = collections.OrderedDict()
        for format in YouTube.formats.keys():
            self.video_formats.update({format: []})
            for video in videos[0]["formats"]:
                if format in str(video):
                    for resolution in YouTube.resolutions.keys():
                        if resolution in str(video):
                            self.video_formats[format].append(resolution)

        for format, resolution in self.video_formats.items():
            if not resolution:
                self.video_formats.pop(format)

        prettified_formats = YouTube.prettify(self.video_formats)
        self.settings_box.format_dropdown.addItems(prettified_formats.keys())
        self.settings_box.resolution_dropdown.addItems(list(prettified_formats.values())[0])

        self.settings_box.continue_msg.hide()
        self.settings_box.format_dropdown.show()
        self.settings_box.resolution_dropdown.show()
        self.save_box.continue_msg.hide()
        self.save_box.destination_lbl.show()
        self.save_box.download_btn.show()
        self.save_box.note_lbl.show()

        self.videos = videos

    def on_playlist_found(self, videos):
        self.url_box.videos_list_widget.clear()
        self.settings_box.format_dropdown.clear()
        self.settings_box.resolution_dropdown.clear()

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

        self.settings_box.continue_msg.hide()
        self.settings_box.format_dropdown.show()
        self.settings_box.resolution_dropdown.show()
        self.save_box.continue_msg.hide()
        self.save_box.destination_lbl.show()
        self.save_box.download_btn.show()
        self.save_box.note_lbl.show()

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

    def on_error(self, error_msg, error_info):
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


# class DownloadWizard(QtWidgets.QWizard):
#
#     WELCOME_PAGE, URL_PAGE, SETTINGS_PAGE = 0, 1, 2
#
#     def __init__(self):
#         super().__init__()
#         self.amount_videos = None
#
#         self.setPage(self.WELCOME_PAGE, WelcomePage(self))
#         self.setPage(self.URL_PAGE, URLPage(self))
#         self.setPage(self.SETTINGS_PAGE, SettingsPage(self))
#         # self.setStartId(0)
#
#         self.setWindowTitle("youtube-downloader [BETA]")
#         self.setWindowIcon(QtGui.QIcon("youtube_icon.ico"))
#         self.setWizardStyle(self.ModernStyle)
#
#         # side_widget = QtWidgets.QWidget()  # only needed for self.AeroStyle (doesn't display watermark)
#         # vbox = QtWidgets.QVBoxLayout()
#         # pixmap = QtGui.QPixmap("youtube.png")
#         # pixmap_label = QtWidgets.QLabel()
#         # pixmap_label.setPixmap(pixmap)
#         # vbox.addWidget(pixmap_label)
#         # side_widget.setLayout(vbox)
#         # self.setSideWidget(side_widget))
#
#         if sys.platform == "win32":
#             # self.setWizardStyle(self.AeroStyle)
#             self.setOption(QtWidgets.QWizard.ExtendedWatermarkPixmap)
#             self.setFixedSize(590, 348)
#         else:
#             self.setFixedSize(645, 397)
#         self.show()
#         # print(self.frameSize())
#
#
# class WelcomePage(QtWidgets.QWizardPage):
#     def __init__(self, parent):
#         super().__init__()
#
#         self.setTitle("Welcome to youtube-downloader!")
#         # self.setPixmap(QtWidgets.QWizard.BackgroundPixmap, QtGui.QPixmap("youtube_banner.png"))
#         # -> only used with self.MacStyle
#         # self.setPixmap(QtWidgets.QWizard.LogoPixmap, QtGui.QPixmap("youtube_banner.png"))
#         # -> only used when using self.setSubTitle() -> shows banner with this logo
#         # self.setPixmap(QtWidgets.QWizard.BannerPixmap, QtGui.QPixmap("youtube_banner.png"))
#         # -> only used when using self.setSubTitle() -> shows banner with this background
#         self.setPixmap(QtWidgets.QWizard.WatermarkPixmap, QtGui.QPixmap("youtube_banner.png"))
#
#         # copyright note: YouTube® and the YouTube logo are registered trade marks of Google Inc.,
#         #                 a subsidiary of Alphabet Inc.
#
#         vbox = QtWidgets.QVBoxLayout()format_dict
#         welcome_text = QtWidgets.QLabel("This wizard makes downloading your favorite YouTube video "
#                                         "or playlist really easy.\n\n\n"
#                                         "You are free to choose between different format and quality settings,\n"
#                                         "or even convert a downloaded video to an audio file.\n\n\n\n"
#                                         "Click \"Next\" to continue.\n\n\n")
#                                         # "Although this program is currently in beta, "
#                                         # "you can already have a lot of fun with it.\n"
#                                         # "Feel free to reach out if you have any questions or suggestions "
#                                         # "on how to make youtube-downloader better.\n"
#                                         # "I appreciate your feedback!")
#         welcome_text.setWordWrap(True)
#         vbox.addWidget(welcome_text)
#         self.setLayout(vbox)
#
#
# class URLPage(QtWidgets.QWizardPage):
#     def __init__(self, parent):
#         super().__init__()
#
#         self.parent = parent
#         self.setTitle("1. Enter a URL")
#         self.setPixmap(QtWidgets.QWizard.WatermarkPixmap, QtGui.QPixmap("youtube_banner.png"))
#         vbox = QtWidgets.QVBoxLayout()
#         hbox1 = QtWidgets.QHBoxLayout()
#         hbox2 = QtWidgets.QHBoxLayout()
#         hbox3 = QtWidgets.QHBoxLayout()
#         url_line_edit = QtWidgets.QLineEdit()
#         url_line_edit.setPlaceholderText("video or playlist URL")
#         self.registerField("url*", url_line_edit)
#         instruction_text = QtWidgets.QLabel("Enter a valid URL of a YouTube video or playlist.\n"
#                                             "(youtube-downloader will automatically detect what it is)")
#         warning_text = QtWidgets.QLabel("NOTE: Currently you can't download age-restricted videos!\n"
#                                         "(this isn't supported by pytube as of version 6.3.0)")
#         hbox1.addWidget(instruction_text)
#         vbox.addLayout(hbox1)
#         vbox.addSpacing(20)
#         hbox2.addWidget(url_line_edit)
#         vbox.addLayout(hbox2)
#         vbox.addSpacing(45)
#         hbox3.addWidget(warning_text)
#         vbox.addLayout(hbox3)
#         self.setLayout(vbox)
#
#     def validatePage(self):
#         global yt_page
#         url = self.field("url")
#         yt_page = YouTube(url)
#         if yt_page.find_videos():
#             self.parent.amount_videos = len(yt_page.video_list)
#             return True
#         else:
#             return False
#
#
# class SettingsPage(QtWidgets.QWizardPage):
#     def __init__(self, parent):
#         global yt_page
#         super().__init__()
#
#         self.parent = parent
#         self.setTitle("2. Select format and quality")
#         self.setPixmap(QtWidgets.QWizard.WatermarkPixmap, QtGui.QPixmap("youtube_banner.png"))
#         vbox = QtWidgets.QVBoxLayout()
#         hbox1 = QtWidgets.QHBoxLayout()
#         sorry_text = QtWidgets.QLabel(str(self.parent.amount_videos) + " videos were found.\n\n"
#                                       "[...]\n\noh no...\n\nSeems QWizard is shit and\n"
#                                       "I'll have to delete everything I've achieved today and redo it...\n\nUgh...:(")
#         hbox1.addWidget(sorry_text)
#         vbox.addLayout(hbox1)
#         self.setLayout(vbox)


# class Worker(QtCore.QObject):
#
#     finished = QtCore.pyqtSignal()
#     status_updated = QtCore.pyqtSignal(str)
#
#     def very_long_and_important_calculation(self):
#         for i in range(5):
#             time.sleep(1)
#             # self.status_updated.emit("calculating " + str(i) + " / 5...")
#
#         self.finished.emit()
#
#     def print_videos_that_were_found(self):
#         return "great vids"
#
#     # code to be in main GUI thread:
#     # (help from https://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt)
#     #
#     # objThread = QThread()
#     #
#     # obj = TestThread()
#     # obj.moveToThread(objThread)
#     # obj.finished.connect(objThread.quit)
#     #
#     # objThread.started.connect(obj.very_long_and_important_calculation)
#     # objThread.finished.connect(obj.print_videos_that_were_found)
#     #
#     # objThread.start()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    pixmap = QtGui.QPixmap("youtube_splash_screen.png")
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
