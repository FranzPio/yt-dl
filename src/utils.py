from PyQt5 import QtWidgets


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
