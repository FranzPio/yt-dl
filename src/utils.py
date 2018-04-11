import json
import os.path

from PyQt5 import QtCore, QtWidgets, QtGui


# probably buffer / queue changes since writing to disk might not be fast enough (???)
class SettingsFile:
    def __init__(self, fpath):
        self.path = fpath
        self.file = None

    def __enter__(self):
        if os.path.exists(self.path):
            self.file = open(self.path, "r+")
        else:
            self.file = open(self.path, "w+")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def clear(self):
        open(self.path, "w").close()
        self.file = open(self.path, "r+")

    def readall(self):
        if os.path.getsize(self.path) > 0:
            return json.load(self.file)
        else:
            return {}

    def read(self, key):
        sdict = self.readall()
        try:
            return sdict[key]
        except KeyError:
            return None

    def write(self, **kwargs):
        sdict = self.readall()
        sdict.update(kwargs)
        self.clear()
        json.dump(sdict, self.file)


def get_main_window(class_name):
    toplevel_widgets = QtWidgets.qApp.topLevelWidgets()
    for widget in toplevel_widgets:
        if widget.__class__.__name__ == class_name:
            return widget
    return None


def get_download_window():
    return get_main_window("DownloadWindow")


def setup_palette(color, widget_list=None, color_role=QtGui.QPalette.Highlight):
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Active, color_role, color)
    if widget_list:
        for widget in widget_list:
            QtWidgets.qApp.setPalette(palette, widget)
    else:
        QtWidgets.qApp.setPalette(palette)


class FusionDarkPalette(QtGui.QPalette):
    # adapted from https://stackoverflow.com/a/45634644

    WHITE = QtGui.QColor(255, 255, 255)
    BLUE = QtGui.QColor(42, 130, 218)
    RED = QtGui.QColor(180, 0, 0)
    # YT_RED = QtGui.QColor(255, 0, 0)

    LIGHTER_GRAY = QtGui.QColor(127, 127, 127)
    LIGHT_GRAY = QtGui.QColor(80, 80, 80)
    MEDIUM_GRAY = QtGui.QColor(66, 66, 66)
    GRAY = QtGui.QColor(53, 53, 53)
    DARK_GRAY = QtGui.QColor(42, 42, 42)
    DARKER_GRAY = QtGui.QColor(35, 35, 35)
    ULTRA_DARK_GRAY = QtGui.QColor(20, 20, 20)

    def __init__(self, QApplication, *args):
        super().__init__(*args)

        self.app = QApplication

        self.setColor(QtGui.QPalette.Window,                                   self.GRAY)
        self.setColor(QtGui.QPalette.WindowText,                               self.WHITE)
        self.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText,      self.LIGHTER_GRAY)
        self.setColor(QtGui.QPalette.Base,                                     self.DARK_GRAY)
        self.setColor(QtGui.QPalette.AlternateBase,                            self.MEDIUM_GRAY)
        self.setColor(QtGui.QPalette.ToolTipBase,                              self.WHITE)
        self.setColor(QtGui.QPalette.ToolTipText,                              self.WHITE)
        self.setColor(QtGui.QPalette.Text,                                     self.WHITE)
        self.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text,            self.LIGHTER_GRAY)
        self.setColor(QtGui.QPalette.Dark,                                     self.DARKER_GRAY)
        self.setColor(QtGui.QPalette.Shadow,                                   self.ULTRA_DARK_GRAY)
        self.setColor(QtGui.QPalette.Button,                                   self.GRAY)
        self.setColor(QtGui.QPalette.ButtonText,                               self.WHITE)
        self.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText,      self.LIGHTER_GRAY)
        self.setColor(QtGui.QPalette.BrightText,                               self.RED)
        self.setColor(QtGui.QPalette.Link,                                     self.BLUE)
        self.setColor(QtGui.QPalette.Highlight,                                self.BLUE)
        # self.setColor(QtGui.QPalette.Highlight,                                self.YT_RED)
        self.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight,       self.LIGHT_GRAY)
        self.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Highlight,       self.LIGHT_GRAY)
        self.setColor(QtGui.QPalette.HighlightedText,                          self.WHITE)
        self.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.HighlightedText, self.LIGHTER_GRAY)

    def apply(self):
        self.app.setPalette(self)
        self.app.setStyleSheet("QToolTip { color: #ffffff; background-color: #232323;  border: 1px solid white; }")


class LineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected = False

    def mousePressEvent(self, QMouseEvent):
        super().mousePressEvent(QMouseEvent)
        if not self.selected:
            self.selectAll()
            self.selected = True
        else:
            self.deselect()
            self.selected = False


class ElidedLabel(QtWidgets.QLabel):
    def __init__(self, text=None, parent=None, elide_mode=QtCore.Qt.ElideMiddle):
        super().__init__(parent)

        self.elide_mode = elide_mode
        self.last_text = None
        self.last_width = None

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.setText(text)

    def setElideMode(self, elide_mode):
        self.elide_mode = elide_mode

    # adapted from https://forum.qt.io/topic/24530/solved-shortening-a-label/3
    def minimumSizeHint(self):
        if self.elide_mode != QtCore.Qt.ElideNone:
            # TODO: tweak sizeHint
            # -> text should expand if user increases window size,
            #    but don't automatically adapt window size to label width on UI update!
            #    (somehow calculate minimumSizeHint + sizeHint with font metrics???)
            fm = self.fontMetrics()
            size = QtCore.QSize(fm.width("..."), fm.height())
            return size
        else:
            size = QtWidgets.QLabel.minimumSizeHint(self)
            return QtCore.QSize(size.width() + 13, size.height())

    # adapted from https://www.mimec.org/blog/status-bar-and-elided-label
    def paintEvent(self, QPaintEvent):
        painter = QtGui.QPainter(self)
        self.drawFrame(painter)

        rect = self.contentsRect()
        rect.adjust(self.margin(), self.margin(), -self.margin(), -self.margin())

        elided_text = painter.fontMetrics().elidedText(self.text(), self.elide_mode, rect.width())

        style_option = QtWidgets.QStyleOption()
        style_option.initFrom(self)

        self.style().drawItemText(painter, rect, self.alignment(), style_option.palette, self.isEnabled(),
                                  elided_text, self.foregroundRole())
