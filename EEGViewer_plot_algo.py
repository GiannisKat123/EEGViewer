import sys
# from PyQt5 import QtWidgets, QtCore
from qtpy import QtWidgets,QtCore
from qtpy.QtWidgets import QScrollArea
from qtpy.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import pylsl
from receiver_data import ReceiveData
from scipy.interpolate import interp1d
from scipy import signal

class EEGViewer(QtWidgets.QWidget):
    def __init__(self,streams:list,color_label:str='k',color_time_marker:str='r',color_per_plot:bool=True,color_for_plots:str='b',background_plot_color:str='k',color_for_markers:str='b',n_seconds_per_screen:int|float = 5):
        super(EEGViewer, self).__init__()

        ### Settings for viewer
        self.color_label = color_label
        self.color_time_marker = color_time_marker
        self.color_per_plot = color_per_plot
        self.color_for_plots = color_for_plots
        self.background_plot_color = background_plot_color
        self.n_seconds_per_screen = n_seconds_per_screen
        self.color_for_markers = color_for_markers
        
        self.streams = streams
        
        self.start_times = []
        
        self.start_index = 0
        self.flag_overflow = False
        self.plot_id = 0
        self.old_plot_id = 0
        self.sampling_freqs = []
        self.num_channels = []
        self.channel_names = []
        self.downsampled_factors = []
        self.time_marker_ts = []
        
        
        self.x = []
        self.y = []
        self.x = []
        self.current_plot_id = 0
        # Set up the layout
       
        ###-----------------------------------------------
        self.lay = pg.GraphicsLayoutWidget()
        self.lay.setFixedHeight(1500)
        self.lay.setFixedWidth(1700)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.lay)
        
        ###-----------------------------------------------
        
        # Create plot widgets for each channel
        self.streams_data = []
        self.streams_markers = []
        
        self.stream_plots = []
        self.stream_curves = []
        self.time_markers = []
        self.markers = []
        
        self.samples = []
        self.start_indexs = []
        
        for inlet,stream_id in self.streams:
            if inlet.inlet_type == "Markers":
                self.streams_markers.append(inlet)
        
            else:
                self.streams_data.append(inlet)
        
        for stream in self.streams_data:
            self.start_times.append(stream.time_created)
        
        for stream in self.streams_data:
            self.old_plot_id = self.plot_id
            curves = []
            time_markers = []
            self.samples.append(0)
            self.start_indexs.append(0)
            
            num_channels = stream.channel_count
            channel_names = stream.channels_names
            sampling_freq = stream.stream_Fs
            
            self.sampling_freqs.append(sampling_freq)
            self.num_channels.append(num_channels)
            
            for chan_id in channel_names:
                self.channel_names.append(chan_id)
            
            print(num_channels,channel_names,sampling_freq)
            
            for chan_id in range(num_channels):
                label = pg.LabelItem(channel_names[chan_id],color=self.color_label)
                self.lay.addItem(label, row=self.plot_id,col=0)
                self.lay.setBackground(self.background_plot_color)
                
                plotWidget = self.lay.addPlot(row=self.plot_id, col=1, sharex=self.stream_plots[0] if self.plot_id > 0 else None)

                time_marker = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(self.color_time_marker, width=5))
                plotWidget.addItem(time_marker)
                time_markers.append(time_marker)
                
                plotWidget.enableAutoRange('y', True)  # Enable autorange for y-axis
                plotWidget.hideAxis('left')  # Hide y-axis for clarity
                
                for marker_stream in self.streams_markers:
                    marker = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(self.color_for_markers, width=5))
                    plotWidget.addItem(marker)
                    self.markers.append(marker)
                
                if chan_id!=num_channels-1:
                    plotWidget.hideAxis('bottom')
                
                if self.color_per_plot:
                    curve = plotWidget.plot(pen=(self.plot_id, num_channels))
                else:
                    curve = plotWidget.plot(pen=self.color_for_plots)

                self.stream_plots.append(plotWidget)
                curves.append(curve)
                
                self.plot_id += 1
        
            # self.time_markers.append(time_marker)
            self.stream_curves.append(curves)  
            self.time_markers.append(time_markers)  
        
        # # Initialize data arrays
        for stream_id in range(len(self.streams_data)):
            self.y.append(np.zeros((int(self.sampling_freqs[stream_id] * self.n_seconds_per_screen),self.num_channels[stream_id])))
            self.x.append(np.linspace(0, self.n_seconds_per_screen, int(self.sampling_freqs[stream_id] * self.n_seconds_per_screen)))

        # Set up a timer for updates
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)  # Update interval in milliseconds
        self.start_time = pylsl.local_clock()
    
    def toggle_channel_visibility(self, channel_index, is_visible):
        """Toggle the visibility of the specified channel."""
        self.stream_plots[channel_index].setVisible(is_visible)
    
    def find_closest_id(self,x_axis,ts):
        print(len(x_axis))
        dif = 10e5
        for index in range(len(x_axis)):
            if abs(x_axis[index] - ts) < dif:
                dif = abs(x_axis[index] - ts)
            else:
                print(x_axis[index])
                return x_axis[index] 
                
    def update(self):
        self.current_plot_id = 0
        
        for stream_id in range(len(self.streams_data)):
        
            new_data,time_ = self.streams_data[stream_id].update()
            
            if time_:
                
                ts_after_overflow = 0        
                
                # if self.downsampled_factors[stream_id]!=1:
                #     transposed_data = np.transpose(new_data)
                    
                #     new_data = np.transpose(signal.decimate(transposed_data,self.downsampled_factors[stream_id]))
                    
                #     max_time = np.max(time_)
                #     min_time = np.min(time_)
                    
                #     time_ = np.linspace(min_time,max_time,new_data.shape[0])
                
                if self.samples[stream_id] + new_data.shape[0] >= self.sampling_freqs[stream_id] * self.n_seconds_per_screen:
                    self.flag_overflow = True
                    ts_after_overflow = int(self.sampling_freqs[stream_id] * self.n_seconds_per_screen - self.samples[stream_id])
            
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
                        self.current_plot_id += self.num_channels[stream_id]
                                    
                    else:
                        self.start_indexs[stream_id] = 0
                        self.samples[stream_id] = new_data.shape[0]
                        ts = self.x[stream_id][self.samples[stream_id]]
                        
                        self.y[self.start_indexs[stream_id]:self.samples[stream_id]] = new_data
                                                
                        for i in range(self.num_channels[stream_id]):
                            self.stream_curves[stream_id][i].setData(self.x[stream_id], self.y[stream_id][:,i])   
                            self.time_markers[stream_id][i].setValue(ts)
                            self.time_markers[stream_id].setValue(ts)
                            
                        self.start_indexs[stream_id] += self.samples[stream_id]
                        self.flag_overflow = False
                        self.current_plot_id += self.num_channels[stream_id]

                else:
                    self.samples[stream_id] += new_data.shape[0]
                    ts = self.x[stream_id][self.samples[stream_id]]
                    
                    self.y[stream_id][self.start_indexs[stream_id]:self.samples[stream_id]] = new_data
                    for i in range(self.num_channels[stream_id]):
                        self.time_markers[stream_id][i].setValue(ts)
                        self.stream_curves[stream_id][i].setData(self.x[stream_id], self.y[stream_id][:,i])   
                        
                    self.start_indexs[stream_id] = self.samples[stream_id]
                    self.current_plot_id += self.num_channels[stream_id]
              
        self.marker_current_id = 0     
        for stream_id in range(len(self.streams_markers)):    
            new_data,time_ = self.streams_markers[stream_id].update()
            if time_:
                self.time_marker_ts.append([])
                for i in range(len(self.streams_data)):
                    marker_ts = self.time_markers[i][0].getXPos()
                    for mark_id in range(self.marker_current_id,self.marker_current_id+self.num_channels[i]):
                        self.markers[mark_id].setValue(marker_ts)
                    self.marker_current_id += self.num_channels[i]
            