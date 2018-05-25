import importlib.util
import json
import os
import platform
import shutil
import stat
import sys
import tempfile
import time
import urllib.request
import zipfile
from datetime import datetime
from distutils.version import StrictVersion

from PyQt5 import QtCore, QtWidgets

from config import VERSION, IS_FROZEN, APP_PATH, ZIP_URL, RELEASES_URL


# TODO: support updating if application is frozen (.exe)
class Update(QtCore.QObject):
    os_asset_names = {"win32": "win32", "darwin": "macos", "linux": "linux", "cygwin": "linux"}

    status_update = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal(int, int)
    success = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str, str, int, tuple, bool)
    information = QtCore.pyqtSignal(str, str, int)
    finished = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

    def check_for_updates(self):
        if not IS_FROZEN:
            current_datetime = datetime.now().strftime("%Y%m%d_%H%M")
            zip_fname = "yt-dl_update_" + current_datetime + ".zip"
            self.zip_fpath = os.path.join(tempfile.gettempdir(), zip_fname)

            self.status_update.emit(self.tr("1 / 5\nFetching the latest version from Github..."))
            urllib.request.urlretrieve(ZIP_URL, self.zip_fpath)

            self.status_update.emit(self.tr("2 / 5\nExtracting ZIP archive..."))
            self.dst_folder = ".".join(self.zip_fpath.split(".")[:-1])
            self.extract_zipball(self.zip_fpath, self.dst_folder)

            self.status_update.emit(self.tr("3 / 5\nVerifying files..."))
            self.new_files = self.query_files(self.dst_folder)

            if self.check_update_need():
                self.status_update.emit(self.tr("4 / 5\nCopying new files..."))
                self.copy_files(self.new_files, APP_PATH)

                self.status_update.emit(self.tr("5 / 5\nCleaning up..."))
                self.cleanup()

                self.information.emit(self.tr("Info"),
                                      self.tr("Updated successfully! (v%s -> v%s)\n"
                                              "The application will restart now for the update to take effect.")
                                      % (self.old_version, self.new_version),
                                      QtWidgets.QMessageBox.Information)
                time.sleep(4)
                self.success.emit()
            else:
                self.status_update.emit(self.tr("5 / 5\nCleaning up..."))
                self.cleanup()

                self.information.emit(self.tr("Info"), self.tr("There's no update available at the time!"),
                                      QtWidgets.QMessageBox.Information)
                self.finished.emit()
        else:
            # self.status_update.emit(self.tr("1 / 4\nChecking for newer release on Github..."))
            # releases_raw = urllib.request.urlopen(RELEASES_URL).read()
            # self.latest_release = json.loads(releases_raw.decode())[0]
            #
            # if self.check_update_need():
            #     self.status_update.emit(self.tr("2 / 4\nChecking for write permission..."))
            #     if self.check_write_permission(APP_PATH):
            #         # download the portable zip
            #         portable_required = True
            #     else:
            #         # download the installer + ShellExecuteEx it
            #         portable_required = False
            #
            #     try:
            #         asset = self.get_compatible_asset(portable_required)
            #     except FileNotFoundError as error:
            #         self.error.emit(self.tr("Error"), str(error), QtWidgets.QMessageBox.Warning, sys.exc_info(), True)
            #         self.finished.emit()
            #         return
            #
            #     asset_url = asset["browser_download_url"]
            #     asset_name = asset["name"]
            #     asset_ext = asset_name.split(".")[-1]
            #     asset_size = round(asset["size"] / 1000000, 1)
            #     print(asset_url, asset_ext, str(asset_size) + " MB", sep="\n")
            #
            #     self.status_update.emit(self.tr("2 / 4\nDownloading latest release (v%s)...") % self.new_version)
            #     asset_path, headers = urllib.request.urlretrieve(asset_url,
            #                                                      os.path.join(tempfile.gettempdir(), asset_name),
            #                                                      reporthook=self.on_progress)
            #     print(asset_path)
            # else:
            #     self.information.emit(self.tr("Info"), self.tr("There's no update available at the time!"),
            #                           QtWidgets.QMessageBox.Information)

            self.status_update.emit(self.tr("5 / 5\nCleaning up..."))
            self.cleanup()

            self.information.emit(self.tr("Info"), self.tr("Updating is not yet supported for Windows executables."),
                                  QtWidgets.QMessageBox.Information)
            self.finished.emit()

    @staticmethod
    def extract_zipball(fpath, dst):
        with zipfile.ZipFile(fpath) as archive:
            archive.extractall(dst)

    @staticmethod
    def query_files(tree):
        queried_files = []
        for root, _, files in os.walk(tree):
            if root.endswith("resources"):
                continue
            for file in files:
                queried_files.append(os.path.join(root, file))
        return queried_files

    def check_update_need(self):
        if not IS_FROZEN:
            for file in self.new_files:
                if file.endswith("config.py"):
                    break
            self.old_version = VERSION
            spec = importlib.util.spec_from_file_location("config", file)
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)
            self.new_version = config.VERSION
            if StrictVersion(self.new_version) <= StrictVersion(self.old_version):
                return False
            else:
                return True
        else:
            self.old_version = VERSION
            self.new_version = self.latest_release["name"].replace("v", "")
            if StrictVersion(self.new_version) <= StrictVersion(self.old_version):
                return False
            else:
                return True

    def _get_asset_requirements(self, portable):
        os = self.os_asset_names[sys.platform]
        install_mode = "portable" if portable else "setup"

        # there are no packages for different archs yet, so this won't work:
        # arch = "x64" if platform.machine().endswith("64") else "x32"
        return os, install_mode  #, arch

    def get_compatible_asset(self, portable):
        assets = self.latest_release["assets"]  # TODO: what if there are no assets in the latest release?
        requirements = self._get_asset_requirements(portable)
        for asset in assets:
            if all(requirement in asset["name"] for requirement in requirements):
                return asset
        raise FileNotFoundError(self.tr("Couldn't find a release compatible with your OS (%s).")
                                % " ".join(requirements))

    @staticmethod
    def check_write_permission(path):
        path_attrs = os.stat(path)
        return bool(path_attrs.st_mode & stat.S_IWUSR)

    def copy_files(self, files, dst):
        try:
            for file in files:
                shutil.copy2(file, dst)
        except OSError:
            # no write permissions or some other weird OS-thingy
            self.error.emit(self.tr("Error"), self.tr("Apparently you don't have write permissions for \"%s\".") % dst,
                            QtWidgets.QMessageBox.Warning, sys.exc_info(), True)

    def cleanup(self):
        shutil.rmtree(self.dst_folder)
        os.remove(self.zip_fpath)

    def on_progress(self, chunks_transferred, chunk_size, total_size):
        pass
