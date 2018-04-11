import subprocess
import traceback

from PyQt5 import QtCore, QtWidgets, QtGui

from config import VERSION, ICONS8_URL, LOADINGIO_URL, GITHUB_URL, GPL_URL, ZIP_URL, EXE
from updater import Update
from utils import get_download_window

license_txt = None


def show_msgbox(title, msg, icon=QtWidgets.QMessageBox.NoIcon, details=None, is_traceback=False):
    msgbox = QtWidgets.QMessageBox(parent=get_download_window())
    msgbox.setWindowTitle(title)
    msgbox.setIcon(icon)
    msgbox.setText(msg)
    if details:
        if is_traceback:
            msgbox.setDetailedText("".join(traceback.format_exception(*details)))
        else:
            msgbox.setDetailedText(details)
    msgbox.exec()


def show_splash(pixmap, parent=None, opacity=0.97, vfont="Fira Sans", vfont_size=11, vfont_bold=True):
    splashie = QtWidgets.QSplashScreen(parent, pixmap, QtCore.Qt.WindowStaysOnTopHint)
    font = QtGui.QFont(vfont) if vfont else splashie.font()
    font.setPointSize(vfont_size)
    font.setBold(vfont_bold)
    splashie.setFont(font)
    splashie.setWindowOpacity(opacity)
    if VERSION:
        splashie.showMessage("v" + VERSION, QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom, QtCore.Qt.red)
    splashie.show()
    return splashie


def show_license(lfile, fallback_msg="", is_html=False, parent=None):
    global license_txt
    dlg = QtWidgets.QDialog(parent, QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint
                            | QtCore.Qt.WindowMinMaxButtonsHint | QtCore.Qt.WindowCloseButtonHint)
    dlg.resize(600, 600)
    dlg.setWindowTitle(QtCore.QCoreApplication.translate("show_license", "License"))

    vbox = QtWidgets.QVBoxLayout()
    hbox1 = QtWidgets.QHBoxLayout()
    hbox2 = QtWidgets.QHBoxLayout()

    if license_txt is None:
        if lfile.open(QtCore.QIODevice.ReadOnly | QtCore.QFile.Text):
            license_txt = QtCore.QTextStream(lfile).readAll()
            lfile.close()
        else:
            license_txt = fallback_msg

    if is_html:
        txt_edit = QtWidgets.QTextBrowser()
        txt_edit.setReadOnly(True)
        txt_edit.setHtml(license_txt)
        txt_edit.setOpenExternalLinks(True)
    else:
        txt_edit = QtWidgets.QTextEdit()
        txt_edit.setReadOnly(True)
        txt_edit.insertPlainText(license_txt)

    text_cursor = txt_edit.textCursor()
    text_cursor.movePosition(QtGui.QTextCursor.Start)
    txt_edit.setTextCursor(text_cursor)

    close_btn = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("show_license", "&Close"))
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
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        vbox = QtWidgets.QVBoxLayout()
        hbox1 = QtWidgets.QHBoxLayout()
        hbox2 = QtWidgets.QHBoxLayout()
        hbox3 = QtWidgets.QHBoxLayout()
        hbox4 = QtWidgets.QHBoxLayout()
        hbox5 = QtWidgets.QHBoxLayout()
        hbox6 = QtWidgets.QHBoxLayout()
        hbox7 = QtWidgets.QHBoxLayout()

        self.icon = QtGui.QPixmap(":/ytdl_icon.png").scaled(
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

        self.desc_lbl = QtWidgets.QLabel(self.tr("An easy-to-use YouTube downloader (GUI),<br>"
                                                 "created with PyQt5, pytube and beautifulsoup4.<br>"
                                                 "Loading GIF: <a href=\"{1}\">{1}</a><br>"
                                                 "Github page: <a href=\"{2}\">{2}</a>")
                                         .format(ICONS8_URL, LOADINGIO_URL, GITHUB_URL))
        self.desc_lbl.setTextFormat(QtCore.Qt.RichText)
        self.desc_lbl.setOpenExternalLinks(True)
        self.desc_lbl.setAlignment(QtCore.Qt.AlignCenter)

        hbox4.addWidget(self.desc_lbl)
        hbox4.setAlignment(QtCore.Qt.AlignCenter)

        self.copyright_lbl = QtWidgets.QLabel("\u00A9 Franz Piontek, 2017")

        hbox5.addWidget(self.copyright_lbl)
        hbox5.setAlignment(QtCore.Qt.AlignCenter)

        self.license_note_lbl = QtWidgets.QLabel(self.tr("This program is free software: you can redistribute it "
                                                         "and/or<br>modify it under the terms of the GNU General "
                                                         "Public License as<br>published by the Free Software "
                                                         "Foundation, either version 3 of<br>the License, or "
                                                         "(at your option) any later version.<br>"

                                                         "This program is distributed in the hope that it will be "
                                                         "useful, but<br>WITHOUT ANY WARRANTY; without even the "
                                                         "implied warranty<br>of MERCHANTABILITY or FITNESS FOR A "
                                                         "PARTICULAR PURPOSE.<br>"
                                                         "See the GNU General Public License for more details<br>"
                                                         "(click \"License\" or visit <a href=\"{0}\">{0}</a>).")
                                                 .format(GPL_URL))
        self.license_note_lbl.setTextFormat(QtCore.Qt.RichText)
        self.license_note_lbl.setOpenExternalLinks(True)
        self.license_note_lbl.setAlignment(QtCore.Qt.AlignCenter)
        font = self.license_note_lbl.font()
        font.setPointSize(font.pointSize() - 2)
        self.license_note_lbl.setFont(font)

        hbox6.addWidget(self.license_note_lbl)
        hbox6.setAlignment(QtCore.Qt.AlignCenter)

        self.license_btn = QtWidgets.QPushButton(self.tr("&License"))
        lfile = QtCore.QFile(":/LICENSE.html")
        fallback_msg = self.tr("LICENSE file couldn't be found/accessed.\nyt-dl used to be "
                               "under the GNU GPL v3.\n"
                               "Please update the application or visit "
                               "https://github.com/FranzPio/yt-dl for more information.")
        self.license_btn.clicked.connect(lambda: show_license(lfile, fallback_msg, is_html=True, parent=self))

        self.about_qt_btn = QtWidgets.QPushButton(self.tr("&About Qt"))
        self.about_qt_btn.clicked.connect(lambda: QtWidgets.QMessageBox.aboutQt(self, self.tr("About Qt")))

        self.close_btn = QtWidgets.QPushButton(self.tr("&Close"))
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setDefault(True)

        hbox7.addWidget(self.license_btn)
        hbox7.addWidget(self.about_qt_btn)
        hbox7.addStretch(1)
        hbox7.addWidget(self.close_btn)
        hbox7.setAlignment(QtCore.Qt.AlignCenter)

        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addLayout(hbox4)
        vbox.addSpacing(5)
        vbox.addLayout(hbox5)
        vbox.addSpacing(7)
        vbox.addLayout(hbox6)
        vbox.addSpacing(12)
        vbox.addLayout(hbox7)

        self.setLayout(vbox)

        self.resize(self.sizeHint())
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle(self.tr("About"))


class UpdateDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.FramelessWindowHint)
        self.init_ui()
        self.start_update()

    def init_ui(self):
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
