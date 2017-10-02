from PyQt5 import QtCore, QtWidgets, QtGui
import subprocess
import traceback
from utils import VERSION, ICONS8_URL, LOADINGIO_URL, GITHUB_URL, ZIP_URL, EXE
from updater import Update
import resources


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


def show_splash(parent=None, opacity=0.95, vfont_size=11, vfont_bold=True):
    pixmap = QtGui.QPixmap(":/youtube_splash_screen.png")
    splashie = QtWidgets.QSplashScreen(parent if parent else None, pixmap)
    big_font = splashie.font()
    big_font.setPointSize(vfont_size)
    big_font.setBold(vfont_bold)
    splashie.setFont(big_font)
    splashie.setWindowOpacity(opacity)
    if VERSION:
        splashie.showMessage("v" + VERSION, QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom, QtCore.Qt.white)
    splashie.show()
    return splashie


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
            lfile = QtCore.QFile(":/LICENSE")
            if not lfile.open(QtCore.QIODevice.ReadOnly | QtCore.QFile.Text):
                raise FileNotFoundError
            LICENSE = QtCore.QTextStream(lfile).readAll()
            lfile.close()
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
        self.init_ui()

    def init_ui(self):
        self.resize(420, 360)
        self.setFixedSize(420, 360)
        self.setWindowTitle("About")
        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()
        hbox3 = QtWidgets.QHBoxLayout()
        hbox4 = QtWidgets.QHBoxLayout()
        hbox5 = QtWidgets.QHBoxLayout()
        hbox6 = QtWidgets.QHBoxLayout()

        self.icon = QtGui.QPixmap(":/youtube_icon_red.png").scaled(
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

        self.version_lbl = QtWidgets.QLabel("v" + VERSION)

        hbox3.addWidget(self.version_lbl)
        hbox3.setAlignment(QtCore.Qt.AlignCenter)

        self.copyright_lbl = QtWidgets.QLabel("\u00A9 Franz Piontek, 2017")

        hbox4.addWidget(self.copyright_lbl)
        hbox4.setAlignment(QtCore.Qt.AlignCenter)

        self.desc_lbl = QtWidgets.QLabel("An easy-to-use YouTube downloader (GUI),<br>"
                                         "created with PyQt5, pytube and beautifulsoup4.<br>"
                                         "Icon: composition of illustrations from "
                                         "<a href=\"" + ICONS8_URL + "\">" + ICONS8_URL + "</a><br>"
                                         "Loading GIF: <a href=\"" + LOADINGIO_URL + "\">" + LOADINGIO_URL + "</a><br>"
                                         "Github page: <a href=\"" + GITHUB_URL + "\">" + GITHUB_URL + "</a>")
        self.desc_lbl.setTextFormat(QtCore.Qt.RichText)
        self.desc_lbl.setOpenExternalLinks(True)
        self.desc_lbl.setAlignment(QtCore.Qt.AlignCenter)

        hbox5.addWidget(self.desc_lbl)
        hbox5.setAlignment(QtCore.Qt.AlignCenter)

        self.license_btn = QtWidgets.QPushButton("&License")
        self.license_btn.clicked.connect(lambda: show_license(self))

        self.about_qt_btn = QtWidgets.QPushButton("&About Qt")
        self.about_qt_btn.clicked.connect(lambda: QtWidgets.QMessageBox.aboutQt(self, "About Qt"))

        self.close_btn = QtWidgets.QPushButton("&Close")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setDefault(True)

        hbox6.addWidget(self.license_btn)
        hbox6.addWidget(self.about_qt_btn)
        hbox6.addStretch(1)
        hbox6.addWidget(self.close_btn)
        hbox6.setAlignment(QtCore.Qt.AlignCenter)

        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addLayout(hbox5)
        vbox.addLayout(hbox4)
        vbox.addSpacing(5)
        vbox.addLayout(hbox6)

        self.setLayout(vbox)


class UpdateDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.init_ui()
        self.start_update()

    def init_ui(self):
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()

        self.loading_indicator = QtWidgets.QLabel()
        self.spinning_wheel = QtGui.QMovie(":/rolling.gif")
        self.spinning_wheel.setScaledSize(QtCore.QSize(32, 32))
        self.loading_indicator.setMovie(self.spinning_wheel)

        hbox1.addWidget(self.loading_indicator)

        self.status_lbl = QtWidgets.QLabel()
        # self.update_dlg.status_lbl.setWordWrap(True)

        hbox2.addWidget(self.status_lbl)

        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        self.setLayout(vbox)

    def start_update(self):
        self.spinning_wheel.start()

        self.updater = Update(ZIP_URL)
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
            QtWidgets.QDialog.keyPressEvent(self, evt)

    def closeEvent(self, evt):
        self.thread.quit()
        self.thread.wait(100)
        if not self.thread.isFinished():
            self.thread.terminate()
            self.thread.wait(2000)
        QtWidgets.QDialog.closeEvent(self, evt)

    def success(self):
        self.close()
        self.restart()

    @staticmethod
    def restart():
        QtWidgets.qApp.closeAllWindows()
        QtWidgets.qApp.quit()
        subprocess.run(EXE)
