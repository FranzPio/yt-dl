from PyQt5 import QtCore, QtWidgets
import os
import sys
import urllib.request
import time
from datetime import datetime
import zipfile
import shutil
from distutils.version import StrictVersion


# TODO: support updating if application is frozen (.exe)
class Update(QtCore.QObject):

    status_update = QtCore.pyqtSignal(str)
    success = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str, str, int, tuple, bool)
    information = QtCore.pyqtSignal(str, str, int)
    finished = QtCore.pyqtSignal()

    def __init__(self, url):
        super().__init__()
        self.url = url

    # TODO: split up this admittedly horrible-looking method (make it great again! ...sorry.)
    def check_for_updates(self):
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M")
        self.filename = "ytdlupdate_" + current_datetime + ".zip"
        self.status_update.emit("1 / 5\nFetching the latest version from Github...")
        # TODO: make this a progress bar (-> reporthook argument; pretty easy)
        urllib.request.urlretrieve(self.url, self.filename)
        self.status_update.emit("2 / 5\nExtracting ZIP archive...")
        with zipfile.ZipFile(self.filename) as archive:
            self.dst_folder = self.filename.split(".")[0]
            archive.extractall(self.dst_folder)
        self.status_update.emit("3 / 5\nVerifying files...")
        self.new_files = []
        # FIXME: apparently rolling.gif + youtube_icon.ico are still added to self.new_files...:/
        for root, _, files in os.walk(self.dst_folder):
            for file in files:
                if file not in ("rolling.gif", "youtube_icon.ico", "youtube_splash_screen.png",
                                "resources.qrc", "README.md"):
                    self.new_files.append(os.path.join(root, file))
        new_vfile = None
        for file in self.new_files:
            if file.endswith("version"):
                new_vfile = file
        try:
            self.app_path = os.path.dirname(os.path.realpath("version"))
            with open(new_vfile) as vfile1, open(os.path.join(self.app_path, "version")) as vfile2:
                new_version = vfile1.read().strip()
                old_version = vfile2.read().strip()
            if StrictVersion(new_version) > StrictVersion(old_version):
                self.status_update.emit("4 / 5\nCopying new files...")
                self.copy_files()
                self.status_update.emit("5 / 5\nCleaning up...")
                self.cleanup()
                self.information.emit("Info", "Updated successfully! (" + old_version + " -> " + new_version + ")\n"
                                      "The application will restart now for the update to take effect.",
                                      QtWidgets.QMessageBox.Information)
                time.sleep(5)
                self.success.emit()
            else:
                self.status_update.emit("5 / 5\nCleaning up...")
                self.cleanup()
                self.information.emit("Info", "There's no update available at the time!",
                                      QtWidgets.QMessageBox.Information)
        except FileNotFoundError:
            # "version" file doesn't exist in app_path
            if hasattr(sys, "frozen"):
                self.information.emit("Info", "Updating is not yet supported for Windows executables.",
                                      QtWidgets.QMessageBox.Information)
            else:
                # TODO: we can should an update anyway to fix this
                self.information.emit("Error", "Apparently, the local version file was deleted...\n"
                                      "Reinstalling the application could fix the problem.")
            self.cleanup()
            self.finished.emit()
            return

        except TypeError:
            # vfile1 is None (no new "version" file in zipball);
            # this probably won't ever happen since I won't delete the version file on Github,
            # but we should still throw some unexpected error warning here
            self.cleanup()
            self.finished.emit()
            pass

    def copy_files(self):
        try:
            for file in self.new_files:
                shutil.copy2(file, self.app_path)
        except OSError:
            # no write permissions or some other weird OS-thingy
            self.error.emit("Error", "Apparently you don't have write permissions for \"" + self.app_path + "\".",
                            QtWidgets.QMessageBox.Warning, sys.exc_info(), True)

    def cleanup(self):
        shutil.rmtree(self.dst_folder)
        os.remove(self.filename)
