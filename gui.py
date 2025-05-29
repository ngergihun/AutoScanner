
from PySide6 import QtWidgets
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QMessageBox, QWidget, QHBoxLayout, QFormLayout, QLineEdit, QSpinBox, QComboBox
from PySide6.QtCore import QTimer, QObject, QThread, Signal, Slot

class AnyOrEmptyValidator(QtGui.QValidator):

    def __init__(self, parent, allow_empty, bottom, top, default_text):
        super().__init__(parent)
        self.allow_empty = allow_empty
        self.default_text = default_text
        self.dv.setLocale(QtCore.QLocale.c())
        self.setBottom(bottom)
        self.setTop(top)

    def setDefault(self, s):
        self.default_text = s

    def setBottom(self, b):
        self.dv.setBottom(b)

    def setTop(self, t):
        self.dv.setTop(t)

    def validate(self, s, pos):
        if self.allow_empty and len(s) == 0:
            return (QtGui.QValidator.Acceptable, s, pos)
        if "," in s:
            return (QtGui.QValidator.Invalid, s, pos)
        else:
            return self.dv.validate(s, pos)

class FloatOrEmptyValidator(AnyOrEmptyValidator):

    def __init__(self, parent, allow_empty=False, bottom=float("-inf"), top=float("inf"),
                 default_text=""):
        self.dv = QtGui.QDoubleValidator(parent)
        self.valid_type = float
        super().__init__(parent, allow_empty=allow_empty, bottom=bottom, top=top,
                         default_text=default_text)

class LineEdit(QLineEdit):
    def __init__(self, bottom, top, *args, **kwargs):
        super(LineEdit, self).__init__(*args, **kwargs)
        self.validator = FloatOrEmptyValidator(self, allow_empty=False, bottom=bottom, top=top)
        self.setValidator(self.validator)
        self.textChanged.connect(self.new_text)
        self.returnPressed.connect(self.check_validator)
        self.ntext = None

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == QtCore.Qt.Key_Return and not self.hasAcceptableInput():
            self.check_validator()

    def new_text(self, text):
        if self.hasAcceptableInput():
            self.ntext = text

    def check_validator(self):
        try:
            if float(self.text()) > self.validator.dv.top():
                self.setText(str(self.validator.dv.top()))
            elif float(self.text()) < self.validator.dv.bottom():
                self.setText(str(self.validator.dv.bottom()))
        except:
            mssg = QMessageBox.about(self, "Error", "Input can only be a number")
            self.setText(self.ntext)

class ScanEditor(QWidget):
    name = "Rotate phase"
    qualname = "orangecontrib.snom.phase_rotation_test"

    edited = Signal()

    parameters = {}

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        default_center = 50.0
        
        form = QFormLayout()

        # For center position of the scanner
        cxedit = LineEdit(bottom=0.0, top=100.0)
        cxedit.setText(str(default_center))
        cyedit = LineEdit(bottom=0.0, top=100.0)
        cyedit.setText(str(default_center))
        scanner_center_widget = QWidget()
        scanner_center_widget.setLayout(QHBoxLayout())
        scanner_center_widget.layout().addWidget(cxedit)
        scanner_center_widget.layout().addWidget(QLabel("x"))
        scanner_center_widget.layout().addWidget(cyedit)

        form.addRow("Scanner Center Position", scanner_center_widget)

        # For scan area
        axedit = LineEdit(bottom=0.0, top=100.0)
        axedit.setText(str(1.0))
        ayedit = LineEdit(bottom=0.0, top=100.0)
        ayedit.setText(str(1.0))
        scan_area_widget = QWidget()
        scan_area_widget.setLayout(QHBoxLayout())
        scan_area_widget.layout().addWidget(axedit)
        scan_area_widget.layout().addWidget(QLabel("x"))
        scan_area_widget.layout().addWidget(ayedit)

        form.addRow("Scan Area", scan_area_widget)

        # For pixel area
        pxedit = QSpinBox()
        pxedit.setRange(1, 10000)
        pxedit.setValue(100)
        pyedit = QSpinBox()
        pyedit.setRange(1, 10000)
        pyedit.setValue(100)
        pixel_area_widget = QWidget()
        pixel_area_widget.setLayout(QHBoxLayout())
        pixel_area_widget.layout().addWidget(pxedit)
        pixel_area_widget.layout().addWidget(QLabel("x"))
        pixel_area_widget.layout().addWidget(pyedit)

        form.addRow("Pixel Area", pixel_area_widget)

        self.setLayout(form)