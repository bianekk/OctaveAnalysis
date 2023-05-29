# https://qmlonline.kde.org/

import sys
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)


class Window(QDialog):
    def __init__(self):
        super().__init__(parent=None)
        self.setWindowTitle("Kawka")

        self.layout = QVBoxLayout()
        self.label = QLabel("Third octave analysis app")

        self.layout.addWidget(self.label)
        self.setLayout(self.layout)


if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec())
