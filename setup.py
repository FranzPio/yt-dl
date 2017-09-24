import sys
from cx_Freeze import setup, Executable
import os
import shutil


build_exe_options = {"excludes": ["tkinter"]}

setup(name = "youtube-downloader",
      version = "0.9",
      description = "Easy-to-use YouTube downloader (GUI).",
      options = {"build_exe": build_exe_options},
      executables = [Executable("main.py", base="Win32GUI" if sys.platform == "win32" else None)])


# ============= SHRINKING SIZE OF FROZEN APP =============
# Watch out, we might need something that is deleted here.
# ========================================================

shutil.rmtree("build/exe.win32-3.5/PyQt5/Qt")
shutil.rmtree("build/exe.win32-3.5/PyQt5/uic")
shutil.rmtree("build/exe.win32-3.5/distutils/command")
os.remove("build/exe.win32-3.5/platforms/qoffscreen.dll")
os.remove("build/exe.win32-3.5/platforms/qminimal.dll")

os.remove("build/exe.win32-3.5/PyQt5\pylupdate.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QAxContainer.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtBluetooth.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtDBus.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtDesigner.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtHelp.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtLocation.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtMultimedia.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtMultimediaWidgets.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtNetwork.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtNfc.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtOpenGL.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtPositioning.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtPrintSupport.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtQml.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtQuick.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtQuickWidgets.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtSensors.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtSerialPort.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtSql.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtTest.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtWebChannel.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtWebEngine.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtWebEngineCore.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtWebEngineWidgets.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtWebSockets.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtWinExtras.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtXml.pyd")
os.remove("build/exe.win32-3.5/PyQt5\QtXmlPatterns.pyd")
os.remove("build/exe.win32-3.5/PyQt5\_QOpenGLFunctions_2_0.pyd")
os.remove("build/exe.win32-3.5/PyQt5\_QOpenGLFunctions_2_1.pyd")
os.remove("build/exe.win32-3.5/PyQt5\_QOpenGLFunctions_4_1_Core.pyd")
