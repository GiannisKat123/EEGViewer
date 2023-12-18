import sys
# from PyQt5 import QtWidgets, QtCore
from qtpy import QtWidgets,QtCore
from qtpy.QtWidgets import QScrollArea,QHBoxLayout
from qtpy.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import pylsl
from test_matplotlib import EEGViewer
from receiver_data import ReceiveData

class Ui_MainWindow(object):
   def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("EEG VIEWER")
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        
        self.layout1 = QHBoxLayout()
        self.layout2 = QHBoxLayout()
        
        receiver = ReceiveData()
        streams = receiver.inlets
        self.eegViewer = EEGViewer(streams=streams,color_label='w',color_time_marker='r',color_per_plot=True,color_for_plots='b',background_plot_color='k',n_seconds_per_screen = 5)
        
        self.scrollbar = QScrollArea()
        # self.scrollbar.resize(800,600)
        self.scrollbar.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollbar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollbar.setWidgetResizable(True)
        self.scrollbar.setWidget(self.eegViewer.lay)
        self.scrollbar.show()
        
        
        self.titleLabel = QtWidgets.QLabel("Channel Selection")
        self.titleLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.titleLabel.setFixedHeight(100)
        
        self.checkboxPanel = QtWidgets.QWidget()
        self.checkboxPanel.setFixedHeight(1500)
        self.checkboxLayout = QtWidgets.QVBoxLayout(self.checkboxPanel)
        self.checkboxLayout.addWidget(self.titleLabel)
        
        
        self.scrollbar1 = QScrollArea()
        self.scrollbar1.setFixedWidth(200)
        self.scrollbar1.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollbar1.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollbar1.setWidgetResizable(True)
        self.scrollbar1.setWidget(self.checkboxPanel)
        self.scrollbar1.show()
    
        num_channels = self.eegViewer.plot_id  # Assuming this is the number of EEG channels
        self.checkboxes = []
        
        for i in range(num_channels):
            chk = QtWidgets.QCheckBox(self.eegViewer.channel_names[i],self.checkboxPanel)
            chk.setChecked(True)
            chk.toggled.connect(lambda checked, index=i: self.eegViewer.toggle_channel_visibility(index, checked))
            self.checkboxLayout.addWidget(chk)
            self.checkboxes.append(chk)
        
        MainWindow.setCentralWidget(self.centralWidget)
        self.centralWidget.setLayout(self.layout1)
        self.layout1.addLayout(self.layout2)
        self.layout1.addWidget(self.scrollbar)
        self.layout2.addWidget(self.scrollbar1)
        
        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())