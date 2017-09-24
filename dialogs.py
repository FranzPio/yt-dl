from PyQt5 import QtCore, QtWidgets, QtGui
import sys
import os.path
import subprocess
import traceback
from updater import Update
from resources import *


LICENSE = None


def show_msgbox(title, msg, icon=QtWidgets.QMessageBox.NoIcon, detailed_text=None, is_traceback=False):
    msgbox = QtWidgets.QMessageBox()
    msgbox.setWindowTitle(title)
    msgbox.setIcon(icon)
    msgbox.setText(msg)
    if detailed_text:
        if is_traceback:
            msgbox.setDetailedText(str(detailed_text[0]) + "\n" + str(detailed_text[1]) + "\n\n"
                                   + "Traceback (most recent call last):\n"
                                   + "".join(traceback.format_tb(detailed_text[2])))
        else:
            msgbox.setDetailedText(detailed_text)
    msgbox.exec()


def show_license(parent=None):
    global LICENSE
    dlg = QtWidgets.QDialog(parent)
    dlg.resize(600, 600)
    dlg.setWindowTitle("License")

    vbox = QtWidgets.QVBoxLayout()
    hbox1 = QtWidgets.QHBoxLayout()
    hbox2 = QtWidgets.QHBoxLayout()

    txt_edit = QtWidgets.QTextEdit()
    txt_edit.setReadOnly(True)
    if LICENSE is None:
        try:
            with open("LICENSE") as lfile:
                LICENSE = lfile.read()
        except (FileNotFoundError, OSError):
            LICENSE = "LICENSE file couldn't be found/accessed.\nyt-dl used to be under the GNU GPL v3.\n" \
                      "Please update the application or visit https://github.com/FranzPio/yt-dl for more information."

    txt_edit.insertPlainText(LICENSE)
    text_cursor = txt_edit.textCursor()
    text_cursor.movePosition(QtGui.QTextCursor.Start)
    txt_edit.setTextCursor(text_cursor)

    close_btn = QtWidgets.QPushButton("&Close")
    close_btn.clicked.connect(dlg.close)

    hbox1.addWidget(txt_edit)
    hbox2.addWidget(close_btn)
    hbox2.setAlignment(QtCore.Qt.AlignRight)

    vbox.addLayout(hbox1)
    vbox.addLayout(hbox2)

    dlg.setLayout(vbox)
    dlg.exec()


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        try:
            with open("version") as vfile:
                self.version = "v" + vfile.read().strip()
        except (FileNotFoundError, OSError):
            self.version = "unknown version"

        self.init_ui()

    def init_ui(self):
        self.resize(400, 315)
        self.setFixedSize(400, 315)
        self.setWindowTitle("About")
        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()
        hbox3 = QtWidgets.QHBoxLayout()
        hbox4 = QtWidgets.QHBoxLayout()
        hbox5 = QtWidgets.QHBoxLayout()

        self.icon = QtGui.QPixmap(":/resources/youtube_icon_red.png").scaled(
            92, 92, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
        self.icon_lbl = QtWidgets.QLabel()
        self.icon_lbl.setPixmap(self.icon)

        hbox1.addWidget(self.icon_lbl)
        hbox1.setAlignment(QtCore.Qt.AlignCenter)

        self.title_lbl = QtWidgets.QLabel("yt-dl")
        big_font = self.title_lbl.font()
        big_font.setPointSize(20)
        big_font.setBold(True)
        self.title_lbl.setFont(big_font)

        hbox2.addWidget(self.title_lbl)
        hbox2.setAlignment(QtCore.Qt.AlignCenter)

        self.version_lbl = QtWidgets.QLabel(self.version)

        hbox3.addWidget(self.version_lbl)
        hbox3.setAlignment(QtCore.Qt.AlignCenter)

        self.description_lbl = QtWidgets.QLabel("An easy-to-use YouTube downloader (GUI),<br>"
                                                "created with PyQt5, pytube and beautifulsoup4.<br>"
                                                "Icon: composition of illustrations from "
                                                "<a href=\"https://icons8.com\">icons8.com</a>.<br>"
                                                "Github page: <a href=\"https://github.com/FranzPio/yt-dl\">"
                                                "https://github.com/FranzPio/yt-dl</a>")
        self.description_lbl.setTextFormat(QtCore.Qt.RichText)
        self.description_lbl.setOpenExternalLinks(True)
        self.description_lbl.setAlignment(QtCore.Qt.AlignCenter)

        hbox4.addWidget(self.description_lbl)
        hbox4.setAlignment(QtCore.Qt.AlignCenter)

        self.license_btn = QtWidgets.QPushButton("&License")
        self.license_btn.clicked.connect(lambda: show_license(self))

        self.about_qt_btn = QtWidgets.QPushButton("&About Qt")
        self.about_qt_btn.clicked.connect(lambda: QtWidgets.QMessageBox.aboutQt(self, "About Qt"))

        self.close_btn = QtWidgets.QPushButton("&Close")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setDefault(True)

        hbox5.addWidget(self.license_btn)
        hbox5.addWidget(self.about_qt_btn)
        hbox5.addStretch(1)
        hbox5.addWidget(self.close_btn)
        hbox5.setAlignment(QtCore.Qt.AlignCenter)

        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addLayout(hbox4)
        vbox.addSpacing(10)
        vbox.addLayout(hbox5)

        self.setLayout(vbox)


class UpdateDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.init_ui()
        self.start_update()

    def init_ui(self):
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        vbox = QtWidgets.QVBoxLayout()

        self.loading_indicator = QtWidgets.QLabel()
        self.spinning_wheel = QtGui.QMovie(":/resources/rolling.gif")
        self.spinning_wheel.setScaledSize(QtCore.QSize(32, 32))
        self.loading_indicator.setMovie(self.spinning_wheel)

        self.status_lbl = QtWidgets.QLabel()
        # self.update_dlg.status_lbl.setWordWrap(True)

        vbox.addWidget(self.loading_indicator)
        vbox.addWidget(self.status_lbl)
        self.setLayout(vbox)

    def start_update(self):
        self.spinning_wheel.start()

        self.updater = Update("https://github.com/FranzPio/yt-dl/zipball/master/")
        self.thread = QtCore.QThread()
        self.updater.moveToThread(self.thread)
        self.updater.finished.connect(self.close)
        self.updater.status_update.connect(self.status_lbl.setText)
        self.updater.success.connect(self.success)
        self.updater.error.connect(show_msgbox)
        self.updater.information.connect(show_msgbox)

        self.thread.started.connect(self.updater.check_for_updates)

        self.thread.start()

    def keyPressEvent(self, evt):
        if evt.key() == QtCore.Qt.Key_Escape:
            self.close()
        else:
            self.keyPressEvent(evt)

    def closeEvent(self, evt):
        self.thread.quit()
        self.thread.wait(100)
        if not self.thread.isFinished():
            self.thread.terminate()
            self.thread.wait(2000)
        self.close()

    def success(self):
        self.close()
        self.restart()

    @staticmethod
    def restart():
        QtWidgets.qApp.closeAllWindows()
        QtWidgets.qApp.quit()
        if hasattr(sys, "frozen"):
            filepath = sys.executable
        else:
            filepath = [sys.executable, os.path.abspath(__file__)]
        subprocess.run(filepath)
