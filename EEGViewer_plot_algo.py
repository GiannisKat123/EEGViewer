import sys
# from PyQt5 import QtWidgets, QtCore
from qtpy import QtWidgets,QtCore,QtGui
from qtpy.QtWidgets import QScrollArea
from qtpy.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import pylsl
from receiver_data import ReceiveData
from scipy.interpolate import interp1d
from scipy import signal
from dataclasses import dataclass

@dataclass
class ViewerConfigs():
    color_label: str = 'w'
    color_time_marker: str = 'r'
    color_per_plot: bool = True
    color_for_plots: str = 'b'
    color_for_markers: str = 'b'
    n_seconds_per_screen: int|float = 5
    background_plot_color: str = 'k'
    

class Viewer(QtWidgets.QWidget):
    def __init__(self,streams:list):
        super(Viewer, self).__init__()
        
        self.configs = ViewerConfigs()
        
        self.streams = streams
        
        self.flag_overflow = False
        self.plot_id = 0
        self.sampling_freqs = []
        self.num_channels = []
        self.channel_names = []
        self.time_marker_ts = []
        
        self.x = []
        self.y = []
        self.x_marker_axis = []
        self.y_marker_axis = []
        self.timestamps_from_streams = []
        # Set up the layout

        self.streams_data = []
        self.streams_markers = []
        
        self.stream_plots = []
        self.stream_curves = []
        self.time_markers1 = []
        self.markers = dict()
        
        self.samples = []
        self.start_indexs = []
        self.labels = []
        
        self.initial_plots = []
        
        
        ###-----------------------------------------------
        self.lay = pg.GraphicsLayoutWidget()
        self.lay.setFixedHeight(1500)
        self.lay.setFixedWidth(1700)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.lay)
        
        self.overlayed_window = pg.GraphicsLayoutWidget(self.lay)
        self.overlayed_window.setFixedHeight(1500)
        self.overlayed_window.setFixedWidth(1700)
        self.overlayed_window.setBackground(None)
        self.overlayed_window.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        # self.lay.addViewBox().setMouseEnabled(x=False, y=False)
        
        label = pg.LabelItem("PSEUDOLABEL",color=self.configs.background_plot_color)
        self.overlayed_window.addItem(label, row=0,col=0)
        
        ###-----------------------------------------------
        
        # Create plot widgets for each channel

        for inlet,stream_id in self.streams:
            if inlet.inlet_type == "Markers":
                self.streams_markers.append(inlet)
            else:
                self.streams_data.append(inlet)
        
        self.plotWidget1 = self.overlayed_window.addPlot(row=0, col=1)
        self.plotWidget1.hideAxis('left')
        self.plotWidget1.setYRange(0, 0.99, padding=0)
        self.plotWidget1.hideAxis('bottom')
        self.plotWidget1.getViewBox().setMouseEnabled(x=False, y=False)
    
        for marker_stream in range(len(self.streams_markers)):
            marker1 = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(self.configs.color_for_markers, width=5))
            marker1.setValue(0)
            # self.label_marker = pg.InfLineLabel(marker1,text='Label Bitch',movable=False,anchor=(0,5, 0),position=0.81)
            self.plotWidget1.addItem(marker1)
            self.markers[marker_stream] = marker1
        
        for stream in self.streams_data:
            
            curves = []
            self.samples.append(0)
            self.start_indexs.append(0)
            
            num_channels = stream.channel_count
            channel_names = stream.channels_names
            sampling_freq = stream.stream_Fs
            
            self.sampling_freqs.append(sampling_freq)
            self.num_channels.append(num_channels)
            
            self.x_marker_axis.append(np.linspace(0,self.configs.n_seconds_per_screen,int(sampling_freq * self.configs.n_seconds_per_screen)))
            self.y_marker_axis.append(np.ones((int(sampling_freq * self.configs.n_seconds_per_screen),)))
        
            time_marker1 = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(self.configs.color_time_marker, width=5))
            self.plotWidget1.addItem(time_marker1)
            self.time_markers1.append(time_marker1)
            
            curve = self.plotWidget1.plot(pen='k')
            curve.setData(self.x_marker_axis[-1],self.y_marker_axis[-1])
            
            for chan_id in channel_names:
                self.channel_names.append(chan_id)
            
            print(num_channels,channel_names,sampling_freq)
            
            for chan_id in range(num_channels):
                label = pg.LabelItem(channel_names[chan_id],color=self.configs.color_label)
                self.labels.append(label)
                
                self.lay.addItem(label, row=self.plot_id,col=0)
                self.lay.setBackground(self.configs.background_plot_color)
                
                plotWidget = self.lay.addPlot(row=self.plot_id, col=1, sharex=self.stream_plots[0] if self.plot_id > 0 else None)
                
                plotWidget.enableAutoRange('y', True)  # Enable autorange for y-axis
                plotWidget.hideAxis('left')  # Hide y-axis for clarity
                
                if chan_id!=num_channels-1:
                    plotWidget.hideAxis('bottom')
                
                if self.configs.color_per_plot:
                    curve = plotWidget.plot(pen=(self.plot_id, num_channels))
                else:
                    curve = plotWidget.plot(pen=self.configs.color_for_plots)

                self.stream_plots.append(plotWidget)
                curves.append(curve)
                
                self.plot_id += 1
            self.stream_curves.append(curves)  
        
        self.initial_plots = self.stream_plots
        
        # # Initialize data arrays
        for stream_id in range(len(self.streams_data)):
            self.y.append(np.zeros((int(self.sampling_freqs[stream_id] * self.configs.n_seconds_per_screen),self.num_channels[stream_id])))
            self.x.append(np.linspace(0, self.configs.n_seconds_per_screen, int(self.sampling_freqs[stream_id] * self.configs.n_seconds_per_screen)))

        # Set up a timer for updates
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)  # Update interval in milliseconds
        self.start_time = pylsl.local_clock()
    
    def toggle_channel_visibility(self, channel_index, is_visible):
        """Toggle the visibility of the specified channel."""
        # self.stream_plots[channel_index].setVisible(is_visible)
        
        print("PUSHED THE BUTTONN BOIIIIIIIIII")
        print(is_visible)
        print(channel_index)
        
        if is_visible == False:
            self.lay.removeItem(self.labels[channel_index])
            self.lay.removeItem(self.stream_plots[channel_index])
        else:
            self.lay.addItem(self.labels[channel_index],row = channel_index,col = 0)
            self.lay.addItem(self.stream_plots[channel_index],row = channel_index,col = 1)
        
    def find_index_in_stream(self,x_axis,ts):
        dif = 10e5
        for index in range(len(x_axis)):
            # print(abs(x_axis[index] - ts),dif)
            if abs(x_axis[index] - ts) < dif and index==len(x_axis)-1:
                print(abs(x_axis[index] - ts))
                return index
            
            elif abs(x_axis[index] - ts) < dif:
                dif = abs(x_axis[index] - ts)
            
            elif abs(x_axis[index] - ts) > dif:
                print(abs(x_axis[index] - ts))
                return index
                
    def update(self):
        self.timestamps_from_streams = []
        
        marker_samples = self.samples
        
        for stream_id in range(len(self.streams_data)):
        
            new_data,time_ = self.streams_data[stream_id].update()
            
            if time_:
                self.timestamps_from_streams.append(time_)
                
                ts_after_overflow = 0        
                
                if self.samples[stream_id] + new_data.shape[0] >= self.sampling_freqs[stream_id] * self.configs.n_seconds_per_screen:
                    self.flag_overflow = True
                    ts_after_overflow = int(self.sampling_freqs[stream_id] * self.configs.n_seconds_per_screen - self.samples[stream_id])
            
                if self.flag_overflow == True:
                    if ts_after_overflow > 0:
                        self.samples[stream_id] += ts_after_overflow
                        
                        self.y[stream_id][self.start_indexs[stream_id]:self.samples[stream_id]] = new_data[:ts_after_overflow]
                                                
                        for i in range(self.num_channels[stream_id]):
                            self.stream_curves[stream_id][i].setData(self.x[stream_id], self.y[stream_id][:,i])
                        self.start_indexs[stream_id] = 0
                        self.samples[stream_id] = new_data.shape[0] - ts_after_overflow
                                                
                        self.y[stream_id][self.start_indexs[stream_id]:self.samples[stream_id]] = new_data[ts_after_overflow:]
                        self.flag_overflow = False
                        self.start_indexs[stream_id] += self.samples[stream_id]
                                    
                    else:
                        self.start_indexs[stream_id] = 0
                        self.samples[stream_id] = new_data.shape[0]
                        ts = self.x[stream_id][self.samples[stream_id]]
                        
                        self.time_markers1[stream_id].setValue(ts)  
                        
                        self.y[self.start_indexs[stream_id]:self.samples[stream_id]] = new_data
                                                
                        for i in range(self.num_channels[stream_id]):
                            self.stream_curves[stream_id][i].setData(self.x[stream_id], self.y[stream_id][:,i])   
                        
                        self.start_indexs[stream_id] += self.samples[stream_id]
                        self.flag_overflow = False

                else:
                    self.samples[stream_id] += new_data.shape[0]
                    ts = self.x[stream_id][self.samples[stream_id]]
                    
                    self.time_markers1[stream_id].setValue(ts)
                    
                    self.y[stream_id][self.start_indexs[stream_id]:self.samples[stream_id]] = new_data
                    for i in range(self.num_channels[stream_id]):
                        self.stream_curves[stream_id][i].setData(self.x[stream_id], self.y[stream_id][:,i])   
                    
                    self.start_indexs[stream_id] = self.samples[stream_id]
              
        self.marker_current_id = 0     
        for stream_id in range(len(self.streams_markers)):    
            new_data,time_ = self.streams_markers[stream_id].update()
            if time_:
                text_label = new_data[0][0].split(',')[0]
                if not self.timestamps_from_streams:
                    self.time_marker_ts.append(time_[0])
                else:
                    if not self.time_marker_ts:
                        for i in range(len(self.timestamps_from_streams)):
                            marker_ts_index = self.find_index_in_stream(x_axis=self.timestamps_from_streams[i],ts=time_[0])
                            # self.markers[stream_id].setValue(self.x_marker_axis[i][marker_samples[i] + marker_ts_index])
                            
                            self.plotWidget1.removeItem(self.markers[stream_id])
                            
                            marker = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(self.configs.color_for_markers, width=5))
                            marker.setValue(self.x_marker_axis[i][marker_samples[i] + marker_ts_index])
                            self.plotWidget1.addItem(marker)
                            self.markers[stream_id] = marker
                            label_marker = pg.InfLineLabel(marker,text=text_label,movable=False,anchor=(0,5, 0),position=0.81)     

                            
                    else:
                        self.time_marker_ts.append(time_[0])
                        for i in range(len(self.timestamps_from_streams)):
                            marker_ts_index = self.find_index_in_stream(x_axis=self.timestamps_from_streams[i],ts=self.time_marker_ts[0])
                            self.markers[stream_id].setValue(self.x_marker_axis[i][marker_samples[i] + marker_ts_index])
                            # self.label_marker = pg.InfLineLabel(self.markers[stream_id],text=text_label,movable=False,anchor=(0.5, 0),position=0.5)
                            
                            self.plotWidget1.removeItem(self.markers[stream_id])
                            
                            marker = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(self.configs.color_for_markers, width=5))
                            marker.setValue(self.x_marker_axis[i][marker_samples[i] + marker_ts_index])
                            self.plotWidget1.addItem(marker)
                            self.markers[stream_id] = marker
                            label_marker = pg.InfLineLabel(marker,text=text_label,movable=False,anchor=(0,5, 0),position=0.81)     

                            del self.time_marker_ts[0]

        self.timestamps_from_streams = []   
            
