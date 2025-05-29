"""
GUI app to control the motorized polarizer and read power meter sensor from NeaSNOM microscope
Standalone app
@author: Gergely Németh
"""

#For the GUI
import sys
import yaml
import os

import pyqtgraph as pg
import numpy as np
from time import sleep
import asyncio

from PySide6 import QtWidgets
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QMessageBox, QWidget, QHBoxLayout, QFormLayout, QLineEdit, QSpinBox
from PySide6.QtCore import QTimer, QObject, QThread, Signal, Slot

from gui import LineEdit, ScanEditor

# import neaSDK
try:
    import nea_tools
    offline_mode = False
except:
    print("nea_tools module not found, working in offline mode")
    offline_mode = True

class neaSNOM():
    def __init__(self,path_to_dll,fingerprint):
        self.name = None
        self.connected = False
        self.context = None
        self.nea = None

    def connect_to_sensor(self,path_to_dll,fingerprint):
        if "nea_tools" not in sys.modules:
            print("nea_tools module was not found, missing SDK!")
            return False

        host = 'nea-server'
    
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(nea_tools.connect(host, fingerprint, path_to_dll))
        except ConnectionError:
            print("Could not connect!")
            return False

        try:
            from neaspec import context
            import Nea.Client.SharedDefinitions as nea
        except ModuleNotFoundError:
            raise ConnectionError('Connection refused or timeout. Retry to connect again.')
        else:
            self.connected = True
            print('\nConnected to SNOM.')

            self.context = context
            self.nea = nea

            return True
        
    def get_power(self):
        return self.context.Microscope.Py.EnergySensor
    
    def close(self):
        if self.connected:
            print('\nDisconnecting from neaServer!')
            nea_tools.disconnect()
            self.connected = False
        else:
            print("SNOM was not connected!")

## Worker class to handle computaionally heavy tasks in a separate thread
class Worker(QObject):
    progress = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self):
        super().__init__()

class AutoScanApp(QMainWindow):

    start_zero_adjust = Signal()

    offline_mode = True

    def __init__(self):
        super().__init__()

         # Set up UI
        self.setup_ui()
        
        self.snom_connected = False
        self.config = None
        self.settings = None
        self.read_config()
        self.read_settings()
        
        # Create the worker thread
        self.worker = Worker()
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()
        

    def setup_ui(self):

        self.setWindowTitle("My App")

        mainlayout = QHBoxLayout()
        mainlayout.setContentsMargins(0,0,0,0)
        mainlayout.setSpacing(20)

        editor = ScanEditor(self)
        mainlayout.addWidget(editor)

        container = QWidget()
        container.setLayout(mainlayout)
        self.setCentralWidget(container)

    def check_snom_config(self):
        if (self.config['fingerprint'] == 'CHANGEMEE') or (self.config['path_to_dll'] == r"CHANGEMEE"):
            msg = QMessageBox()
            msg.setWindowTitle("Configuration missing")
            msg.setText("You have to set up neaSNOM configuration before use")
            msg.setIcon(QMessageBox.Critical)
            msg.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
            buttonConnect = msg.button(QMessageBox.Ok)
            buttonConnect.setText('Ok')
            msg.setInformativeText("Click 'Ok' and set the parameters in the config.yaml file or click 'Cancel' to continue in offline mode")
            button = msg.exec()
            if button == QMessageBox.Ok:
                sys.exec()
            elif button == QMessageBox.Cancel:
                self.offline_mode = True

    def read_config(self):
        with open('config.yaml', 'r') as file:
            self.config = yaml.safe_load(file)

    def read_settings(self):
        with open('settings.yaml', 'r') as file:
            self.settings = yaml.safe_load(file)

    def write_settings(self):
        with open('settings.yaml', 'w') as file:
            yaml.dump(self.settings, file)

    def connect_sensor(self):
        objname = globals()[self.sensor_combobox.currentText()]
        self.powersensor = objname()
        self.worker.sensor = self.powersensor
        self.sensor_control_frame.setEnabled(True)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = AutoScanApp()
    ex.show()
    sys.exit(app.exec())