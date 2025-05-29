
from PySide6 import QtWidgets
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QMessageBox, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox, QComboBox, QSizePolicy
from PySide6.QtCore import QTimer, QObject, QThread, Signal, Slot

from PySide6.QtCore import Qt, QPointF, Property
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QRadialGradient
from PySide6.QtWidgets import QAbstractButton

# Taken from https://github.com/nlamprian/pyqt5-led-indicator-widget
class LedIndicator(QAbstractButton):
    scaledSize = 1000.0

    def __init__(self, parent=None):
        QAbstractButton.__init__(self, parent)

        self.setMinimumSize(24, 24)
        self.setCheckable(True)

        # Green
        self.on_color_1 = QColor(0, 255, 0)
        self.on_color_2 = QColor(0, 192, 0)
        self.off_color_1 = QColor(0, 28, 0)
        self.off_color_2 = QColor(0, 128, 0)

    def resizeEvent(self, QResizeEvent):
        self.update()

    def paintEvent(self, QPaintEvent):
        realSize = min(self.width(), self.height())

        painter = QPainter(self)
        pen = QPen(Qt.black)
        pen.setWidth(1)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(realSize / self.scaledSize, realSize / self.scaledSize)

        gradient = QRadialGradient(QPointF(-500, -500), 1500, QPointF(-500, -500))
        gradient.setColorAt(0, QColor(224, 224, 224))
        gradient.setColorAt(1, QColor(28, 28, 28))
        painter.setPen(pen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(0, 0), 500, 500)

        gradient = QRadialGradient(QPointF(500, 500), 1500, QPointF(500, 500))
        gradient.setColorAt(0, QColor(224, 224, 224))
        gradient.setColorAt(1, QColor(28, 28, 28))
        painter.setPen(pen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(0, 0), 450, 450)

        painter.setPen(pen)
        if self.isChecked():
            gradient = QRadialGradient(QPointF(-500, -500), 1500, QPointF(-500, -500))
            gradient.setColorAt(0, self.on_color_1)
            gradient.setColorAt(1, self.on_color_2)
        else:
            gradient = QRadialGradient(QPointF(500, 500), 1500, QPointF(500, 500))
            gradient.setColorAt(0, self.off_color_1)
            gradient.setColorAt(1, self.off_color_2)

        painter.setBrush(gradient)
        painter.drawEllipse(QPointF(0, 0), 400, 400)

    @Property(QColor)
    def onColor1(self):
        return self.on_color_1

    @onColor1.setter
    def onColor1(self, color):
        self.on_color_1 = color

    @Property(QColor)
    def onColor2(self):
        return self.on_color_2

    @onColor2.setter
    def onColor2(self, color):
        self.on_color_2 = color

    @Property(QColor)
    def offColor1(self):
        return self.off_color_1

    @offColor1.setter
    def offColor1(self, color):
        self.off_color_1 = color

    @Property(QColor)
    def offColor2(self):
        return self.off_color_2

    @offColor2.setter
    def offColor2(self, color):
        self.off_color_2 = color

# Copy-modified from orange-spectroscopy
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
# Copy-modified from orange-spectroscopy
class FloatOrEmptyValidator(AnyOrEmptyValidator):

    def __init__(self, parent, allow_empty=False, bottom=float("-inf"), top=float("inf"),
                 default_text=""):
        self.dv = QtGui.QDoubleValidator(parent)
        self.valid_type = float
        super().__init__(parent, allow_empty=allow_empty, bottom=bottom, top=top,
                         default_text=default_text)
# Copy-modified from orange-spectroscopy
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

def is_macstyle():
    style = QApplication.style()
    style_name = style.metaObject().className()
    return style_name == 'QMacStyle'

def _is_horizontal(orientation):
    return (orientation == Qt.Horizontal or
            orientation == 'horizontal' or
            not orientation)

def setLayout(widget, layout):
    """
    Set the layout of the widget.

    If `layout` is given as `Qt.Vertical` or `Qt.Horizontal`, the function
    sets the layout to :obj:`~QVBoxLayout` or :obj:`~QVBoxLayout`.

    :param widget: the widget for which the layout is being set
    :type widget: QWidget
    :param layout: layout
    :type layout: `Qt.Horizontal`, `Qt.Vertical` or instance of `QLayout`
    """
    if not isinstance(layout, QtWidgets.QLayout):
        if _is_horizontal(layout):
            layout = QtWidgets.QHBoxLayout()
        else:
            layout = QtWidgets.QVBoxLayout()
    widget.setLayout(layout)

def widgetBox(widget, box=None, orientation=Qt.Vertical, margin=None, spacing=None,
              **misc):
    """
    Construct a box with vertical or horizontal layout, and optionally,
    a border with an optional label.

    If the widget has a frame, the space after the widget is added unless
    explicitly disabled.

    :param widget: the widget into which the box is inserted
    :type widget: QWidget or None
    :param box: tells whether the widget has a border, and its label
    :type box: int or str or None
    :param orientation: orientation of the box
    :type orientation: `Qt.Horizontal`, `Qt.Vertical` or instance of `QLayout`
    :param sizePolicy: The size policy for the widget (default: None)
    :type sizePolicy: :obj:`~QSizePolicy`
    :param margin: The margin for the layout. Default is 7 if the widget has
        a border, and 0 if not.
    :type margin: int
    :param spacing: Spacing within the layout (default: 4)
    :type spacing: int
    :return: Constructed box
    :rtype: QGroupBox or QWidget
    """
    if box:
        b = QtWidgets.QGroupBox(widget)
        if isinstance(box, str):
            b.setTitle(" " + box.strip() + " ")
            if is_macstyle() and widget and widget.layout() and \
                    isinstance(widget.layout(), QtWidgets.QVBoxLayout) and \
                    not widget.layout().isEmpty():
                misc.setdefault('addSpaceBefore', True)
        if margin is None:
            margin = 4
    else:
        b = QtWidgets.QWidget(widget)
        b.setContentsMargins(0, 0, 0, 0)
        if margin is None:
            margin = 0
    setLayout(b, orientation)
    if spacing is not None:
        b.layout().setSpacing(spacing)
    b.layout().setContentsMargins(margin, margin, margin, margin)
    miscellanea(b, None, widget, **misc)
    return b

def _addSpace(widget, space):
    """
    A helper function that adds space into the widget, if requested.
    The function is called by functions that have the `addSpace` argument.

    :param widget: Widget into which to insert the space
    :type widget: QWidget
    :param space: Amount of space to insert. If False, the function does
        nothing. If the argument is an `int`, the specified space is inserted.
        Otherwise, the default space is inserted by calling a :obj:`separator`.
    :type space: bool or int
    """
    if space:
        if type(space) == int:  # distinguish between int and bool!
            separator(widget, space, space)
        else:
            separator(widget)


def separator(widget, width=None, height=None):
    """
    Add a separator of the given size into the widget.

    :param widget: the widget into whose layout the separator is added
    :type widget: QWidget
    :param width: width of the separator
    :type width: int
    :param height: height of the separator
    :type height: int
    :return: separator
    :rtype: QWidget
    """
    sep = QtWidgets.QWidget(widget)
    if widget is not None and widget.layout() is not None:
        widget.layout().addWidget(sep)
    size = separator_size(width, height)
    sep.setFixedSize(*size)
    return sep


def separator_size(width=None, height=None):
    if is_macstyle():
        width = 2 if width is None else width
        height = 2 if height is None else height
    else:
        width = 4 if width is None else width
        height = 4 if height is None else height
    return width, height


def miscellanea(control, box, parent, *,
                addToLayout=True, stretch=0, sizePolicy=None,
                disabled=False, tooltip=None, disabledBy=None,
                addSpaceBefore=False, **kwargs):
    """
    Helper function that sets various properties of the widget using a common
    set of arguments.

    The function
    - sets the `control`'s attribute `box`, if `box` is given and `control.box`
    is not yet set,
    - attaches a tool tip to the `control` if specified,
    - disables the `control`, if `disabled` is set to `True`,
    - adds the `box` to the `parent`'s layout unless `addToLayout` is set to
    `False`; the stretch factor can be specified,
    - adds the control into the box's layout if the box is given (regardless
    of `addToLayout`!)
    - sets the size policy for the box or the control, if the policy is given,
    - adds space in the `parent`'s layout after the `box` if `addSpace` is set
    and `addToLayout` is not `False`.

    If `box` is the same as `parent` it is set to `None`; this is convenient
    because of the way complex controls are inserted.

    Unused keyword arguments are assumed to be properties; with this `gui`
    function mimic the behaviour of PyQt's constructors. For instance, if
    `gui.lineEdit` is called with keyword argument `sizePolicy=some_policy`,
    `miscallenea` will call `control.setSizePolicy(some_policy)`.

    :param control: the control, e.g. a `QCheckBox`
    :type control: QWidget
    :param box: the box into which the widget was inserted
    :type box: QWidget or None
    :param parent: the parent into whose layout the box or the control will be
        inserted
    :type parent: QWidget
    :param addSpaceBefore: the amount of space to add before the widget
    :type addSpaceBefore: bool or int
    :param disabled: If set to `True`, the widget is initially disabled
    :type disabled: bool
    :param addToLayout: If set to `False` the widget is not added to the layout
    :type addToLayout: bool
    :param stretch: the stretch factor for this widget, used when adding to
        the layout (default: 0)
    :type stretch: int
    :param tooltip: tooltip that is attached to the widget
    :type tooltip: str or None
    :param disabledBy: checkbox created with checkBox() function
    :type disabledBy: QCheckBox or None
    :param sizePolicy: the size policy for the box or the control
    :type sizePolicy: QSizePolicy
    """
    if 'addSpace' in kwargs:
        kwargs.pop('addSpace')
    for prop, val in kwargs.items():
        method = getattr(control, "set" + prop[0].upper() + prop[1:])
        if isinstance(val, tuple):
            method(*val)
        else:
            method(val)
    if disabled:
        # if disabled==False, do nothing; it can be already disabled
        control.setDisabled(disabled)
    if tooltip is not None:
        control.setToolTip(tooltip)
    if box is parent:
        box = None
    elif box and box is not control and not hasattr(control, "box"):
        control.box = box
    if box and box.layout() is not None and \
            isinstance(control, QtWidgets.QWidget) and \
            box.layout().indexOf(control) == -1:
        box.layout().addWidget(control)
    if disabledBy is not None:
        disabledBy.disables.append(control)
        disabledBy.makeConsistent()
    if sizePolicy is not None:
        if isinstance(sizePolicy, tuple):
            sizePolicy = QSizePolicy(*sizePolicy)
        if box:
            box.setSizePolicy(sizePolicy)
        control.setSizePolicy(sizePolicy)
    if addToLayout and parent and parent.layout() is not None:
        _addSpace(parent, addSpaceBefore)
        parent.layout().addWidget(box or control, stretch)

class ScanEditor(QWidget):
    name = "Rotate phase"
    qualname = "orangecontrib.snom.phase_rotation_test"

    edited = Signal()

    parameters = {}

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        default_center = 50.0

        layout = QVBoxLayout()
        self.setLayout(layout)
        form = QFormLayout()
        box = widgetBox(self, "Basic settings", orientation=form)

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