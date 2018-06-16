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
import webbrowser
import zipfile
from datetime import datetime
from distutils.version import StrictVersion

from PyQt5 import QtCore, QtWidgets

from config import VERSION, IS_FROZEN, APP_PATH, ZIP_URL, RELEASES_URL, GITHUB_URL, YTDL_GUID


# TODO: support updating if application is frozen (.exe)
class Updater(QtCore.QObject):
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
            urllib.request.urlretrieve(ZIP_URL, self.zip_fpath, reporthook=self.on_progress)

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
            self.status_update.emit(self.tr("1 / 4\nChecking for newer release on Github..."))
            releases_raw = urllib.request.urlopen(RELEASES_URL).read()
            self.latest_release = json.loads(releases_raw.decode())[0]

            if self.check_update_need():
                self.status_update.emit(self.tr("2 / 4\nDetermining installation method..."))
                platform = self.os_asset_names[sys.platform]
                # arch = "x64" if platform.machine().endswith("64") else "x32"  # we don't have pkgs for different
                                                                                # architechtures yet
                if sys.platform == "win32" and self.setup_regkey_exists():
                    pkg_type = "setup"
                else:
                    if self.write_permission_granted(APP_PATH):
                        pkg_type = "portable"
                    else:
                        # see details about workaround below
                        pkg_type = "portable"
                        # self.error.emit(self.tr("Error"),
                        #                 self.tr("The application doesn't have write access to\n\"%s\", "
                        #                         "therefore it can't be updated automatically.") % APP_PATH,
                        #                 QtWidgets.QMessageBox.Warning, (), False)
                        # self.finished.emit()
                        # return

                asset = self.get_asset(platform, pkg_type)  # , arch)

                asset_url = asset["browser_download_url"]
                asset_name = asset["name"]
                # asset_ext = asset_name.split(".")[-1]
                # asset_size = round(asset["size"] / 1000000, 1)

                if pkg_type == "portable":
                    self.status_update.emit(self.tr("Automatic updating is not yet available for %s installations.")
                                            % pkg_type)
                    # => we can't just overwrite the running exe
                    #
                    # on Windows, we could download the setup as well + run in "portable mode"
                    # -> see https://stackoverflow.com/questions/8397863/how-to-create-installer-with-innosetup-which-should-not-register-the-application
                    #
                    # (temporary?) workaround: open asset url in webbrowser
                    webbrowser.open(asset_url)
                else:
                    self.status_update.emit(self.tr("3 / 4\nDownloading latest release (v%s)...") % self.new_version)
                    asset_path, headers = urllib.request.urlretrieve(asset_url,
                                                                     os.path.join(tempfile.gettempdir(), asset_name),
                                                                     reporthook=self.on_progress)

                    self.status_update.emit(self.tr("4 / 4\nInstalling update..."))
                    import ctypes
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", asset_path,
                                                        "/silent /closeapplications", None, 1)

                self.finished.emit()
            else:
                self.information.emit(self.tr("Info"), self.tr("There's no update available at the time!"),
                                      QtWidgets.QMessageBox.Information)
                self.finished.emit()

            # self.status_update.emit(self.tr("5 / 5\nCleaning up..."))
            # self.cleanup()
            #
            # self.information.emit(self.tr("Info"), self.tr("Updating is not yet supported for Windows executables."),
            #                       QtWidgets.QMessageBox.Information)
            # self.finished.emit()

    @staticmethod
    def extract_zipball(fpath, dst):
        with zipfile.ZipFile(fpath) as archive:
            archive.extractall(dst)

    @staticmethod
    def query_files(tree):
        queried_files = []
        for root, _, files in os.walk(tree):
            if not IS_FROZEN:
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

    def get_asset(self, *requirements):
        assets = self.latest_release["assets"]  # TODO: what if there are no assets in the latest release?
        for asset in assets:
            if all(requirement in asset["name"] for requirement in requirements):
                return asset
        raise FileNotFoundError(self.tr("Couldn't find a release compatible with your OS (%s).\n"
                                        "This shouldn't normally happen.")
                                % " ".join(requirements))

    @staticmethod
    def setup_regkey_exists():
        import winreg
        try:
            app_list = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE,
                                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", access=winreg.KEY_READ)
            ytdl_regkey = winreg.OpenKeyEx(app_list, YTDL_GUID)
        except (OSError, FileNotFoundError):
            return False
        else:
            return True

    @staticmethod
    def write_permission_granted(path):
        path_attrs = os.stat(path)
        return bool(path_attrs.st_mode & stat.S_IWUSR & stat.S_IXUSR)  # check for write + execute bit

    def copy_files(self, files, dst):
        try:
            for file in files:
                shutil.copy2(file, dst)
        except OSError:
            # no write permissions or some other weird OS-thingy
            self.error.emit(self.tr("Error"), self.tr("Apparently you don't have write permissions for \"%s\".") % dst,
                            QtWidgets.QMessageBox.Warning, sys.exc_info(), True)

    def cleanup(self):
        if not IS_FROZEN:
            shutil.rmtree(self.dst_folder)
            os.remove(self.zip_fpath)
        else:
            # os.remove(self.asset_path)
            pass

    def on_progress(self, chunks_transferred, chunk_size, bytes_total):
        bytes_transferred = chunks_transferred * chunk_size
        # print(bytes_transferred, "of", bytes_total, "...", end="\r")
        # sys.stdout.flush()
        self.progress.emit(bytes_transferred, bytes_total)
