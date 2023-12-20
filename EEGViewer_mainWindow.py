import sys
# from PyQt5 import QtWidgets, QtCore
from qtpy import QtWidgets,QtCore,QtGui
from qtpy.QtWidgets import (
    QScrollArea,
    QHBoxLayout,
    QCheckBox,
    QGroupBox,
    QWidget,
    QVBoxLayout,
    QSizePolicy,
)
from PyQt5.QtGui import QPalette, QColor,QColorConstants,QRgba64
from qtpy.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import pylsl
from EEGViewer_plot_algo import Viewer
from receiver_data import ReceiveData, Inlet
import time
from checkbox import Foldout


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("EEG VIEWER")
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        
        self.layout1 = QHBoxLayout()
        self.layout2 = QHBoxLayout()
        
        receiver = ReceiveData()
        streams = receiver.inlets
        self.eegViewer = Viewer(streams=streams)
        
        self.plot_scrollarea = QScrollArea()
        self.plot_scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.plot_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.plot_scrollarea.setWidgetResizable(True)
        self.plot_scrollarea.setWidget(self.eegViewer.lay)
        
        self.streams_scrollarea = QtWidgets.QScrollArea()
        self.streams_scrollarea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.streams_scrollarea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.streams_scrollarea.setWidgetResizable(True)
        self.streams_scrollarea.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        
        
        self.setup_stream_list(streams)
        MainWindow.setCentralWidget(self.centralWidget)
        self.centralWidget.setLayout(self.layout1)
        
        self.layout1.addLayout(self.layout2)
        self.layout1.addWidget(self.plot_scrollarea)
        self.layout2.addWidget(self.streams_scrollarea)
    
    def setup_stream_list(self, streams):
        channels_widget = QWidget()
        channels_widget.setLayout(QVBoxLayout())
        channels_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.streams_scrollarea.setWidget(channels_widget)

        print(streams)
        for stream in streams:
            stream: Inlet = stream[0]
            stream_foldout = Foldout(stream.inlet_name)
            show_stream_widget = QCheckBox()
            # connect show stream
            stream_foldout.add_to_foldout_widget(show_stream_widget)
            
            for i in range(stream.channel_count):
                channel_name = stream.channels_names[i]
                channel_check = QCheckBox(channel_name)
                stream_foldout.container.layout().addWidget(channel_check)
                # channel_check.toggled.connect
                # connect channel check
            
            channels_widget.layout().addWidget(stream_foldout)
            
            # channels_widget.layout().addStretch()
            
            

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
