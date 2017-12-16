from PyQt5 import QtCore, QtWidgets, QtGui


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
