#!/usr/bin/env python3
import collections.abc
import functools
import os.path
import sys
import traceback

from PyQt5 import QtCore, QtWidgets, QtGui

from config import APP_PATH
from converter import FFmpeg
from dialogs import UpdateDialog, AboutDialog, show_msgbox, show_splash
from download import Downloader
from utils import LineEdit, ElidedLabel, FusionDarkPalette
from youtube import YouTube
import resources


def handle_uncaught_exception(exc_type, exc_obj, exc_tb):
    with open(os.path.join(APP_PATH, "yt-dl.log"), "a") as lfile:
        lfile.write(str(exc_type) + "\n" + str(exc_obj) + "\n\n" + "".join(traceback.format_tb(exc_tb)) +
                    "\n\n////\n\n")

    if issubclass(exc_type, Warning):
        return
    elif issubclass(exc_type, Exception):
        QtCore.QMetaObject.invokeMethod(window, "show_msgbox",
                                        QtCore.Q_ARG(str, QtCore.QCoreApplication.translate("handle_uncaught_exception",
                                                                                            "Error")),
                                        QtCore.Q_ARG(str, QtCore.QCoreApplication.translate("handle_uncaught_exception",
                                                                                            "An unexpected error occurred."
                                                                                            "See below for details.")),
                                        QtCore.Q_ARG(int, QtWidgets.QMessageBox.Critical),
                                        QtCore.Q_ARG(list, [exc_type, exc_obj, exc_tb]))
    else:
        traceback.print_exception(exc_type, exc_obj, exc_tb)
        sys.exit(1)


sys.excepthook = handle_uncaught_exception


class DownloadWindow(QtWidgets.QMainWindow):
    MODE_EXTRACT = 0
    MODE_CONVERT = 1

    STYLE_DEFAULT = 0
    STYLE_FUSION = 1
    STYLE_FUSION_DARK = 2

    def __init__(self):
        super().__init__()
        self.splashie = show_splash(self)
        QtCore.QTimer.singleShot(1200, self.show_window)

        self.threads_workers = collections.OrderedDict()

        self.videos = None
        self.playlist_videos = None
        self.video_formats = None
        self.destination = os.getcwd()
        self.postprocess_mode = None
        self.audio_codecs = {}

        self.init_ui()

    @QtCore.pyqtSlot(str, str, int, list)
    def show_msgbox(self, title, msg, icon, tb):
        show_msgbox(title, msg, icon, tb, True)

    def show_window(self):
        self.show()
        self.raise_()
        self.splashie.finish(self)

    def create_thread(self, WorkerClass, *args, **kwargs):
        worker = WorkerClass(*args, **kwargs)
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        self.threads_workers.update({thread: worker})

        return thread, worker

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

        self.setMinimumSize(self.sizeHint())
        self.setGeometry(QtWidgets.QStyle.alignedRect(QtCore.Qt.LeftToRight,
                                                      QtCore.Qt.AlignCenter,
                                                      self.minimumSize(),
                                                      QtWidgets.qApp.desktop().availableGeometry()))
        self.setWindowIcon(QtGui.QIcon(":/youtube_icon.ico"))
        self.setWindowTitle("yt-dl")

    def create_toolbar(self):
        exit_act = QtWidgets.QAction(self.tr("&Exit"), self)
        exit_act.setShortcut(QtCore.Qt.ControlModifier | QtCore.Qt.Key_Q)
        exit_act.triggered.connect(QtWidgets.qApp.quit)

        update_act = QtWidgets.QAction(self.tr("&Check for updates"), self)
        update_act.triggered.connect(self.update_dialog)

        about_act = QtWidgets.QAction(self.tr("&About"), self)
        about_act.triggered.connect(self.about_dialog)

        style_group = QtWidgets.QActionGroup(self)
        default_style_act = QtWidgets.QAction(self.tr("&Default"), self)
        default_style_act.triggered.connect(functools.partial(self.change_style, self.STYLE_DEFAULT))
        default_style_act.setCheckable(True)
        default_style_act.setChecked(True)
        style_group.addAction(default_style_act)

        fusion_style_act = QtWidgets.QAction(self.tr("&Fusion"), self)
        fusion_style_act.triggered.connect(functools.partial(self.change_style, self.STYLE_FUSION))
        fusion_style_act.setCheckable(True)
        style_group.addAction(fusion_style_act)

        dark_style_act = QtWidgets.QAction(self.tr("Fusion (d&ark theme)"), self)
        dark_style_act.triggered.connect(functools.partial(self.change_style, self.STYLE_FUSION_DARK))
        dark_style_act.setCheckable(True)
        style_group.addAction(dark_style_act)

        menu_bar = self.menuBar()
        actions_menu = menu_bar.addMenu(self.tr("&Actions"))
        actions_menu.addAction(exit_act)
        options_menu = menu_bar.addMenu(self.tr("&Options"))
        options_menu.addAction(default_style_act)
        options_menu.addAction(fusion_style_act)
        options_menu.addAction(dark_style_act)
        help_menu = menu_bar.addMenu(self.tr("&?"))
        help_menu.addAction(update_act)
        help_menu.addAction(about_act)
        return menu_bar

    def update_dialog(self):
        update_dlg = UpdateDialog(self)
        update_dlg.exec()

    def about_dialog(self):
        about_dlg = AboutDialog(self)
        about_dlg.exec()

    def change_style(self, new_style):
        current_style = QtWidgets.qApp.style().objectName()

        if new_style != current_style:
            if new_style == self.STYLE_DEFAULT:
                # TODO: maybe remove default style in future (at least on Windows)
                QtWidgets.qApp.setStyleSheet("")

                if sys.platform == "win32":
                    default_style = QtWidgets.QStyleFactory.create("windowsvista")  # stupid workaround needed :/
                else:
                    default_style = QtWidgets.QStyleFactory.create(QtWidgets.QStyleFactory.keys()[0])

                QtWidgets.qApp.setStyle(default_style)

                QtWidgets.qApp.setPalette(default_style.standardPalette())

                if sys.platform == "win32":
                    font = QtGui.QFont("Segoe UI", 9)
                else:
                    font = QtGui.QFont()
                    font.setFamily(font.defaultFamily())

                QtWidgets.qApp.setFont(font)

            elif new_style == self.STYLE_FUSION or new_style == self.STYLE_FUSION_DARK:
                # TODO: change background in palette of Fusion style
                #       (brownish background color in Qt 5.9 = ugly, but 5.10 not working with PyInstaller yet)
                #                                                    -> ugly windowsxp style, windowsvista not bundled

                # TODO: make change persistent (some hidden config file...)
                QtWidgets.qApp.setStyleSheet("")

                fusion_style = QtWidgets.QStyleFactory.create("fusion")
                QtWidgets.qApp.setStyle(fusion_style)

                font = QtGui.QFont("Fira Sans", 9)
                QtWidgets.qApp.setFont(font)

                if new_style == self.STYLE_FUSION_DARK and not current_style == self.STYLE_FUSION_DARK:
                    dark_style = FusionDarkPalette(QtWidgets.qApp)
                    dark_style.apply()
                else:
                    palette = fusion_style.standardPalette()
                    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0, 120, 215))
                    palette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Highlight, QtGui.QColor(240, 240, 240))
                    QtWidgets.qApp.setPalette(palette)

            self.setMinimumSize(self.sizeHint())
            self.resize(self.sizeHint())

    def create_url_box(self):
        url_box = QtWidgets.QGroupBox(self.tr("1. Enter URL"))

        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()
        hbox3 = QtWidgets.QHBoxLayout()

        url_box.url_ledit = LineEdit()
        url_box.url_ledit.setPlaceholderText(self.tr("URL of a YouTube video or playlist"))
        url_box.url_ledit.returnPressed.connect(lambda: self.get_videos_from_url(url_box.url_ledit.text()))
        url_box.get_videos_btn = QtWidgets.QPushButton(self.tr("Find videos..."))
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
        settings_box = QtWidgets.QGroupBox(self.tr("2. Select quality and format"))

        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()
        hbox3 = QtWidgets.QHBoxLayout()

        settings_box.continue_msg = QtWidgets.QLabel(self.tr("Click \"Find videos...\" to continue."))
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
        save_box = QtWidgets.QGroupBox(self.tr("3. Download videos"))

        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()
        hbox3 = QtWidgets.QHBoxLayout()
        hbox4 = QtWidgets.QHBoxLayout()

        save_box.continue_msg = QtWidgets.QLabel(self.tr("Click \"Find videos...\" to continue."))
        save_box.destination_lbl = ElidedLabel()
        save_box.destination_lbl.setElideMode(QtCore.Qt.ElideNone)
        save_box.destination_lbl.setText(self.tr("Click \"...\" to specify download destination."))
        save_box.destination_lbl.hide()
        save_box.fdialog_btn = QtWidgets.QPushButton()
        # TODO: nice folder icon instead of ugly dots
        save_box.fdialog_btn.setText(self.tr("..."))
        save_box.fdialog_btn.clicked.connect(self.choose_download_directory)
        save_box.fdialog_btn.hide()
        save_box.download_btn = QtWidgets.QPushButton(self.tr("DOWNLOAD"))
        save_box.download_btn.setDisabled(True)
        save_box.download_btn.clicked.connect(self.on_download_clicked)
        save_box.download_btn.hide()
        save_box.progress_bar = QtWidgets.QProgressBar()
        save_box.progress_bar.hide()
        save_box.progress_lbl = QtWidgets.QLabel()
        save_box.progress_lbl.hide()

        hbox1.addWidget(save_box.continue_msg)
        vbox.addLayout(hbox1)
        hbox2.addWidget(save_box.destination_lbl)
        hbox2.addSpacing(5)
        hbox2.addWidget(save_box.fdialog_btn)
        vbox.addLayout(hbox2)
        hbox3.addWidget(save_box.download_btn)
        vbox.addLayout(hbox3)
        hbox4.addWidget(save_box.progress_bar)
        hbox4.addSpacing(5)
        hbox4.addWidget(save_box.progress_lbl)
        vbox.addLayout(hbox4)

        save_box.setLayout(vbox)

        return save_box

    def choose_download_directory(self):
        dst_folder = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr("Choose download directory"), os.getcwd())
        if dst_folder:
            self.destination = dst_folder
            self.save_box.destination_lbl.setElideMode(QtCore.Qt.ElideMiddle)
            self.save_box.destination_lbl.setText(self.destination)
            self.save_box.download_btn.setEnabled(True)

    def update_progress(self, bytes_downloaded, stream_fsize, videos_downloaded, videos_total):
        self.save_box.progress_bar.setMaximum(stream_fsize)
        self.save_box.progress_bar.setFormat(self.tr("%s of %s MB") %
                                             (round(self.save_box.progress_bar.value() / 1000000, 1),
                                              round(self.save_box.progress_bar.maximum() / 1000000, 1)))
        self.save_box.progress_bar.setValue(bytes_downloaded)
        self.save_box.progress_lbl.setText(self.tr("(%s/%s)") % (videos_downloaded, videos_total))

    def toggle_progress_pulse(self, should_pulse):
        if should_pulse:
            self.save_box.progress_bar.setRange(0, 0)
        else:
            self.save_box.progress_bar.setRange(0, 1)

    def on_download_success(self, successful_downloads, videos_total):
        self.convert_box.extract_rbtn.setEnabled(True)
        self.convert_box.convert_rbtn.setEnabled(True)

        if videos_total - successful_downloads == 0:
            if videos_total == 1:
                show_msgbox(self.tr("Info"),
                            self.tr("Video downloaded successfully!"),
                            QtWidgets.QMessageBox.Information)
            else:
                show_msgbox(self.tr("Info"),
                            self.tr("All videos downloaded successfully!"),
                            QtWidgets.QMessageBox.Information)
        else:
            show_msgbox(self.tr("Info"),
                        self.tr("%s of %s videos downloaded successfully!") % (successful_downloads, videos_total),
                        QtWidgets.QMessageBox.Information)

    def on_download_clicked(self):
        extension = YouTube.uglify(self.settings_box.format_dropdown.currentText())
        resolution = YouTube.uglify(self.settings_box.resolution_dropdown.currentText())

        if len(self.url_box.videos_list_widget) < 1:
            return
        else:
            self.save_box.progress_bar.show()
            self.save_box.progress_bar.reset()
            self.save_box.progress_lbl.show()
            self.save_box.progress_lbl.clear()

            self.audio_codecs.clear()
            self.convert_box.extract_rbtn.setAutoExclusive(False)
            self.convert_box.convert_rbtn.setAutoExclusive(False)
            self.convert_box.extract_rbtn.setChecked(False)
            self.convert_box.convert_rbtn.setChecked(False)
            self.convert_box.extract_rbtn.setAutoExclusive(True)
            self.convert_box.convert_rbtn.setAutoExclusive(True)

            self.convert_box.extract_status.hide()
            self.convert_box.extract_rbtn.setDisabled(True)
            self.convert_box.convert_rbtn.setDisabled(True)
            self.convert_box.convert_btn.setDisabled(True)

            if len(self.url_box.videos_list_widget) == 1:
                if self.url_box.videos_list_widget.item(0).checkState() == QtCore.Qt.Checked:
                    thread, downloader = self.create_thread(Downloader, self.yt)

                    downloader.finished.connect(thread.quit)
                    downloader.success.connect(self.on_download_success)
                    downloader.error.connect(show_msgbox)
                    downloader.progress.connect(self.update_progress)
                    downloader.pulse.connect(self.toggle_progress_pulse)

                    thread.started.connect(functools.partial(
                        downloader.download_video, self.videos, extension, resolution, self.destination))
                    thread.finished.connect(lambda: print("finished!"))

                    thread.start()
            else:
                checked_videos = []
                for index, video in enumerate(self.playlist_videos):
                    if self.url_box.videos_list_widget.item(index).checkState() == QtCore.Qt.Checked:
                        checked_videos.append(video)
                if checked_videos:
                    thread, downloader = self.create_thread(Downloader)

                    downloader.finished.connect(thread.quit)
                    downloader.success.connect(self.on_download_success)
                    downloader.error.connect(show_msgbox)
                    downloader.progress.connect(self.update_progress)
                    downloader.pulse.connect(self.toggle_progress_pulse)

                    thread.started.connect(functools.partial(
                        downloader.download_playlist, checked_videos, extension, resolution, self.destination))
                    thread.finished.connect(lambda: print("finished!"))

                    thread.start()

    def create_convert_box(self):
        convert_box = QtWidgets.QGroupBox(self.tr("4. Post-processing"))

        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()
        hbox3 = QtWidgets.QHBoxLayout()
        hbox4 = QtWidgets.QHBoxLayout()
        # hbox5 = QtWidgets.QHBoxLayout()
        # hbox6 = QtWidgets.QHBoxLayout()

        convert_box.continue_msg = QtWidgets.QLabel(self.tr("Click \"Find videos...\" to continue."))

        convert_box.extract_rbtn = QtWidgets.QRadioButton()
        convert_box.extract_rbtn.setDisabled(True)
        convert_box.extract_rbtn.setText(self.tr("Extract audio only"))
        convert_box.extract_rbtn.clicked.connect(self.on_audio_mode_switched)
        convert_box.extract_rbtn.hide()

        convert_box.convert_rbtn = QtWidgets.QRadioButton()
        convert_box.convert_rbtn.setDisabled(True)
        convert_box.convert_rbtn.setText(self.tr("Convert audio"))
        convert_box.convert_rbtn.clicked.connect(self.on_audio_mode_switched)
        convert_box.convert_rbtn.hide()

        convert_box.loading_indicator = QtWidgets.QLabel()
        convert_box.loading_indicator.hide()
        convert_box.spinning_wheel = QtGui.QMovie(":/rolling.gif")
        convert_box.spinning_wheel.setScaledSize(QtCore.QSize(22, 22))

        convert_box.extract_status = QtWidgets.QLabel()
        convert_box.extract_status.hide()

        convert_box.audio_formats = QtWidgets.QComboBox()
        convert_box.audio_formats.hide()

        convert_box.convert_btn = QtWidgets.QPushButton(self.tr("CONVERT"))
        convert_box.convert_btn.clicked.connect(self.on_convert_clicked)
        convert_box.convert_btn.setDisabled(True)
        convert_box.convert_btn.hide()

        hbox1.addWidget(convert_box.continue_msg)
        vbox.addLayout(hbox1)
        hbox2.addWidget(convert_box.extract_rbtn)
        hbox2.addStretch(1)
        hbox2.addWidget(convert_box.convert_rbtn)
        hbox2.addStretch(1)
        vbox.addLayout(hbox2)
        hbox3.addSpacing(20)
        hbox3.addWidget(convert_box.loading_indicator)
        hbox3.addSpacing(5)
        hbox3.addWidget(convert_box.extract_status, 1)
        hbox3.addStretch(1)
        hbox3.addWidget(convert_box.audio_formats)
        vbox.addLayout(hbox3)
        vbox.addSpacing(5)
        hbox4.addWidget(convert_box.convert_btn)
        vbox.addLayout(hbox4)

        convert_box.setLayout(vbox)

        return convert_box

    def on_audio_mode_switched(self):
        if self.convert_box.extract_rbtn.isChecked() and Downloader.last_downloaded:
            self.postprocess_mode = self.MODE_EXTRACT
            self.convert_box.convert_btn.setText(self.tr("EXTRACT"))
            self.convert_box.loading_indicator.setMovie(self.convert_box.spinning_wheel)
            self.convert_box.loading_indicator.show()

            self.convert_box.extract_status.show()
            self.convert_box.extract_status.setText(self.tr("Detecting audio format..."))
            self.convert_box.spinning_wheel.start()

            self.detect_audio_format()
            self.convert_box.convert_btn.setEnabled(True)
        elif self.convert_box.convert_rbtn.isChecked() and Downloader.last_downloaded:
            self.postprocess_mode = self.MODE_CONVERT
            self.convert_box.convert_btn.setText(self.tr("CONVERT"))
            self.convert_box.convert_btn.setEnabled(True)

    def detect_audio_format(self):
        path_list = []
        for stream in Downloader.last_downloaded:
            path_list.append(os.path.join(self.destination, stream.default_filename))
        for path in path_list:
            thread, converter = self.create_thread(FFmpeg, path)

            converter.finished.connect(thread.quit)
            converter.detection_success.connect(self.format_detection_success)
            converter.error.connect(show_msgbox)

            thread.started.connect(converter.get_audio_codec)

            thread.start()

        last_thread = list(self.threads_workers.keys())[-1]
        while not last_thread.isFinished():
            QtWidgets.qApp.processEvents()
            last_thread.wait(20)

        self.display_formats()

    def format_detection_success(self, path, codec):
        # print("Codec:", codec, "[", path, "]")
        self.audio_codecs[path] = codec
        self.convert_box.spinning_wheel.stop()
        self.convert_box.loading_indicator.hide()

    def display_formats(self):
        unique_codecs = set(codec for codec in self.audio_codecs.values())
        description = self.tr("Audio format: ") if not len(unique_codecs) > 1 else self.tr("Audio formats: ")
        self.convert_box.extract_status.setText(description + ", ".join(unique_codecs).upper())

    def on_convert_clicked(self):
        if self.audio_codecs and self.postprocess_mode == self.MODE_EXTRACT:
            for index, (path, codec) in enumerate(self.audio_codecs.items()):
                print("Converting", index, "of", len(self.audio_codecs), "...")
                converter = FFmpeg(path)
                converter.extract_audio(codec)
            print("Finished (more or less) successfully.")
        elif self.audio_codecs and self.postprocess_mode == self.MODE_CONVERT:
            # path_list = []
            # for stream in Downloader.last_downloaded:
            #     path_list.append(os.path.join(self.destination, stream.default_filename))
            # for index, path in enumerate(path_list):
            #     print("Converting", index, "of", len(path_list), "...")
            #     converter = FFmpeg(path)
            #     converter.convert_audio(".mp3", converter.ENCODE_VBR)
            # print("Finished (more or less) successfully.")
            show_msgbox(self.tr("Sorry"), self.tr("This feature is not supported yet."), QtWidgets.QMessageBox.Warning)

    def get_videos_from_url(self, page_url=None):
        self.url_box.get_videos_btn.setDisabled(True)
        self.url_box.url_ledit.setDisabled(True)
        self.url_box.videos_list_widget.setDisabled(True)
        self.settings_box.format_dropdown.setDisabled(True)
        self.settings_box.resolution_dropdown.setDisabled(True)
        self.url_box.loading_indicator.setMovie(self.url_box.spinning_wheel)
        self.url_box.spinning_wheel.start()

        thread, youtube = self.create_thread(YouTube, page_url)

        youtube.finished.connect(thread.quit)
        youtube.video_found.connect(self.on_video_found)
        youtube.playlist_found.connect(self.on_playlist_found)
        youtube.success.connect(self.on_success)
        youtube.error.connect(show_msgbox)

        thread.started.connect(youtube.find_videos)
        thread.finished.connect(self.on_thread_finished)

        thread.start()

    def on_video_found(self, yt):
        video = yt.streams.filter(progressive=True).desc().all()
        # TODO: this doesn't have to be a QListWidget anymore since we can be sure to get only one video
        video_item = QtWidgets.QListWidgetItem()
        video_item.setText("1 - " + video[0].default_filename.split(".")[0])
        video_item.setFlags(video_item.flags() | QtCore.Qt.ItemIsUserCheckable)
        video_item.setCheckState(QtCore.Qt.Checked)
        self.url_box.videos_list_widget.addItem(video_item)
        self.url_box.videos_list_widget.show()

        self.video_formats = collections.OrderedDict()
        for format in YouTube.formats.keys():
            self.video_formats.update({format: []})
        for streams in video:
            self.video_formats[streams.subtype].append(streams.resolution)
        for format, resolution in list(self.video_formats.items()):
            if not resolution:
                self.video_formats.pop(format)

        for i in self.video_formats.keys():
            self.settings_box.format_dropdown.addItem(YouTube.prettify(i))
        for i in list(self.video_formats.values())[0]:
            self.settings_box.resolution_dropdown.addItem(YouTube.prettify(i))

        self.videos = video
        self.yt = yt

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

    def on_thread_finished(self):
        self.url_box.spinning_wheel.stop()
        self.url_box.loading_indicator.clear()
        self.url_box.get_videos_btn.setEnabled(True)
        self.url_box.url_ledit.setEnabled(True)
        self.url_box.videos_list_widget.setEnabled(True)
        self.settings_box.format_dropdown.setEnabled(True)
        self.settings_box.resolution_dropdown.setEnabled(True)
        self.resize(self.widget.sizeHint())
        # self.threads_workers.clear()

    def on_success(self):
        self.url_box.videos_list_widget.clear()
        self.settings_box.format_dropdown.clear()
        self.settings_box.resolution_dropdown.clear()

        self.settings_box.continue_msg.hide()
        self.settings_box.format_dropdown.show()
        self.settings_box.resolution_dropdown.show()
        self.save_box.continue_msg.hide()
        self.save_box.destination_lbl.show()
        self.save_box.fdialog_btn.show()
        self.save_box.download_btn.show()
        self.convert_box.continue_msg.hide()
        self.convert_box.extract_rbtn.show()
        self.convert_box.convert_rbtn.show()
        self.convert_box.convert_btn.show()


def startup():
    global window
    logfile = os.path.join(APP_PATH, "yt-dl.log")
    if os.path.isfile(logfile):
        os.remove(logfile)

    # QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_DisableWindowContextHelpButton)  # only works with Qt >=5.10
    app = QtWidgets.QApplication(sys.argv)

    if sys.platform == "win32":
        font = QtGui.QFont("Segoe UI", 9)
        app.setFont(font)

    QtGui.QFontDatabase.addApplicationFont(":/FiraSans-Regular.ttf")
    QtGui.QFontDatabase.addApplicationFont(":/FiraSans-Bold.ttf")

    locale = QtCore.QLocale.system().name()
    tr_list = []

    qt_tr = QtCore.QTranslator()
    qt_tr.load("qtbase_" + locale, QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath))
    tr_list.append(qt_tr)

    ytdl_tr = QtCore.QTranslator()
    ytdl_tr.load(":/lang_" + locale)
    tr_list.append(ytdl_tr)

    for tr in tr_list:
        if tr:
            app.installTranslator(tr)

    window = DownloadWindow()
    app.exec()


if __name__ == "__main__":
    startup()
