from qtpy.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGroupBox,
    QCheckBox,
    QWidget,
    QSizePolicy,
)

from qtpy.QtCore import (
    Qt,
    QSize,
)

from qtpy.QtGui import QIcon
from EEGViewer_plot_algo import Viewer

class Foldout(QWidget):
    
    def __init__(self, foldout_title: str = 'foldout', open = False):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        self.foldout_widget = QWidget()
        self.foldout_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.foldout_widget.setLayout(QHBoxLayout())
        
        self.foldout_button = QPushButton()
        self.foldout_button.setIcon(QIcon('resources/open_foldout.svg'))
        self.foldout_button.setIconSize(QSize(15,15))
        self.foldout_button.setCheckable(True)
        
        self.foldout_button.setChecked(open)
        self.foldout_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")
        
        def __toggle_foldout(checked: bool):
            if checked == True:
            # Show or hide the foldout
                self.foldout_button.setIcon(QIcon('resources/close_foldout.svg'))
            else:
                self.foldout_button.setIcon(QIcon('resources/open_foldout.svg'))
            
            self.container.setVisible(checked)
        
        self.foldout_button.toggled.connect(__toggle_foldout)
        
        self.foldout_widget.layout().addWidget(self.foldout_button)
        # title
        self.titleLabel = QLabel(foldout_title)
        self.foldout_widget.layout().addWidget(self.titleLabel)

        # container
        self.container = QWidget()
        self.container.setLayout(QVBoxLayout())
        self.container.setContentsMargins(25,0,0,0)
        
        self.layout().addWidget(self.foldout_widget)
        self.layout().addWidget(self.container)
        self.container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        __toggle_foldout(open)
        
    def add_to_foldout_widget(self, widget: QWidget):
        self.foldout_widget.layout().addWidget(widget)
