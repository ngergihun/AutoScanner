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
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QMessageBox, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox, QPushButton
from PySide6.QtCore import QTimer, QObject, QThread, Signal, Slot

import gui
from gui import LineEdit, ScanEditor

import numpy as np
import logging

logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.info('Starting AutoScanApp')

# import neaSDK
try:
    import nea_tools
    offline_mode = False
except:
    logger.warning("nea_tools module not found, working in offline mode")
    offline_mode = True

class neaSNOM():
    def __init__(self,path_to_dll,fingerprint):

        self.name = None
        self.connected = False
        self.context = None
        self.nea = None
        self.scan_parameters = None

    def connect(self,path_to_dll,fingerprint):
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

            # global nea_tools
            # import nea_tools

            global scan
            from nea_tools.logic import scan
            # from nea_tools import database, plotter
            # from nea_tools.utils.colors import COLORS,CMAPS
            global approach_sample
            from nea_tools.logic.approach import approach_sample

        except ModuleNotFoundError:
            raise ConnectionError('Connection refused or timeout. Retry to connect again.')
        else:
            self.connected = True

            self.context = context
            self.nea = nea

            return True
        
    def spawn_parameters(self):
        if self.connected:
            self.scan_parameters = self.context.Logic.DefaultScanParameters.Spawn()

    def close(self):
        if self.connected:
            logger.debug('\nDisconnecting from neaServer!')
            nea_tools.disconnect()
            self.connected = False
        else:
            logger.debug("SNOM was not connected!")

## Worker class to handle computaionally heavy tasks in a separate thread
class Worker(QObject):

    progress = Signal(str)
    finished = Signal()
    error = Signal(str)

    parameters = {}

    def __init__(self, snom):
        super().__init__()

        self.snom = snom
        self.newscan = None

    def print_params(self):
        logger.info("Current parameters: %s", self.parameters)

    def create_measurement(self):
        if self.parameters is not None:
            try:
                p = self.snom.context.Logic.DefaultScanParameters.Spawn()
                return scan.Whitelight(Name = "Test Scan", 
                                PhysicalOffsetX=self.parameters["scan"]["PhysicalOffsetX"], 
                                PhysicalOffsetY=self.parameters["scan"]["PhysicalOffsetY"],
                                PhysicalSizeX=self.parameters["scan"]["PhysicalSizeX"],
                                PhysicalSizeY=self.parameters["scan"]["PhysicalSizeY"],
                                TargetResolutionWidth=self.parameters["scan"]["TargetResolutionWidth"],
                                TargetResolutionHeight=self.parameters["scan"]["TargetResolutionHeight"],
                                Angle=self.parameters["scan"]["Angle"], 
                                TargetMillisecondsPerPixel=self.parameters["scan"]["TargetMillisecondsPerPixel"],
                                LaserSourceTargetWavelength=p.LaserSourceTargetWavelength,
                                PhysicalRangeM=(665.5,665.5))
            except Exception as e:
                logger.error("Error creating scan object: %s", e)
                return None
        else:
            logger.error("Could not configure scan object.")
            return None

    def run_measurement(self):
        logger.info("Starting measurement with parameters: %s", self.parameters)
        newscan = self.create_measurement()
        if newscan is not None:
            approach_sample(0.8)
            with newscan as wl:
                wl.scan()
                logger.debug("Measurement started, waiting for scan to finish...")
                wl.wait_for_scan()
                logger.debug("Scan finished, downloading data...")
                data = wl.data[f"M1A"]
                logger.info(f"Data type: {type(data)}, Data shape: {np.shape(data)}")
                np.savetxt("TestSave", data)

class AutoScanApp(QMainWindow):

    offline_mode = False

    def __init__(self):
        super().__init__()
        
        self.snom_connected = False
        self.config = None
        self.settings = None
        self.read_config()
        
        # Create the worker thread
        self.worker = Worker(snom=None)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        # Set up UI
        self.setup_ui()
        
    def setup_ui(self):

        self.setWindowTitle("Auto Step Scanner App")

        mainlayout = QVBoxLayout()
        mainlayout.setContentsMargins(0,0,0,0)
        # mainlayout.setSpacing(10)

        self.scan_editor = ScanEditor(self)
        self.ifg_editor = gui.InterferometerEditor(self)
        self.info = gui.InfoDisplay(self)

        self.connect_widget = QWidget()
        self.connect_widget.setLayout(QHBoxLayout())
        self.connect_button = QPushButton("Connect")
        self.connect_led = gui.LedIndicator()
        self.connect_widget.layout().addWidget(self.connect_button)
        self.connect_widget.layout().addWidget(self.connect_led)
        self.connect_button.clicked.connect(self.connect_snom)

        self.start_measurement_button = QPushButton("Start Measurement")
        self.start_measurement_button.clicked.connect(self.worker.run_measurement)
        self.start_measurement_button.setEnabled(False)

        self.ifg_editor.edited.connect(self.on_parameters_changed)
        self.ifg_editor.edited.emit(self.ifg_editor.parameters)

        self.scan_editor.edited.connect(self.on_parameters_changed)
        self.scan_editor.edited.emit(self.scan_editor.parameters)

        mainlayout.addWidget(self.scan_editor)
        mainlayout.addWidget(self.ifg_editor)
        mainlayout.addWidget(self.info)
        mainlayout.addWidget(self.connect_widget)
        mainlayout.addWidget(self.start_measurement_button)

        container = QWidget()
        container.setLayout(mainlayout)
        self.setCentralWidget(container)

    def on_parameters_changed(self):
        self.set_info_display()
        self.send_parameters_to_worker()

        logger.debug("Parameters changed, info display and worker parameters updated")

    def set_info_display(self):
        self.info.set_scan_parameters(self.scan_editor.parameters)
        self.info.set_ifg_parameters(self.ifg_editor.parameters)

        logger.debug("Info display updated with current parameters")

    def send_parameters_to_worker(self):
        self.worker.parameters = {
            'scan': self.scan_editor.parameters,
            'ifg': self.ifg_editor.parameters
        }
        logger.info("Parameters sent to worker")

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
            all_settings = yaml.safe_load(file)
            print(all_settings)

    def write_settings(self):
        with open('settings.yaml', 'w') as file:
            yaml.dump([self.scan_editor.parameters, self.ifg_editor.parameters], file)

    def connect_snom(self):
        self.check_snom_config()
        if self.offline_mode:
            logger.warning("Working in offline mode, no SNOM connection")
            return
        else:
            if not self.snom_connected:
                if self.worker.snom is None:
                    self.worker.snom = neaSNOM(self.config['path_to_dll'], self.config['fingerprint'])
                
                if self.worker.snom.connect(self.config['path_to_dll'], self.config['fingerprint']):
                    if self.worker.snom.connected == True:
                        self.snom_connected = True
                        self.connect_led.setChecked(True)
                        self.connect_button.setText("Disconnect")
                        logger.info("Connected to SNOM")
                else:
                    logger.error("Failed to connect to SNOM")
                    self.connect_led.setChecked(False)
                    self.connect_button.setText("Connect")
                    QMessageBox.critical(self, "Connection Error", "Failed to connect to SNOM. Check your configuration.")
            else:
                self.worker.snom.close()
                self.snom_connected = False
                self.connect_led.setChecked(False)
                self.connect_button.setText("Connect")

            self.start_measurement_button.setEnabled(self.snom_connected)


    def closeEvent(self, event):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QtWidgets.QMessageBox.question(self, 'Message', quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()

            if self.worker.snom is not None:
                try:
                    self.worker.snom.close()
                    logger.info("SNOM connection closed before program exit!")
                except:
                    logger.error(f'{self.worker.snom} could NOT be closed upon program exit!')

            if self.worker_thread.isRunning():
                self.worker_thread.quit()
                self.worker_thread.wait()
                logger.info("Worker thread closed before program exit!")
            logger.info("Exiting AutoScanApp! Bye-bye!")

        else:
            event.ignore()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = AutoScanApp()
    ex.show()
    sys.exit(app.exec())