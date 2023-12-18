from pylsl import StreamOutlet,StreamInfo,local_clock,proc_clocksync, proc_dejitter, proc_monotonize
import pylsl
import argparse
import time
import random
import numpy as np
from random import random as rand

channel_names = [f"Channel{i}" for i in range(0,32)]
channel_names1 = [f"CHannel_{i}" for i in range(0,10)]

start_time = local_clock()


time_for_sin = np.linspace(0, 0.05 , 102)

INIT_FREQ = 0.01  # Initial frequency in Hz
FREQ_INC = 1  # Frequency increment
AMPLITUDE = 1

channel_locations = [
    [-0.0307, 0.0949, -0.0047],
    [0.0307, 0.0949, -0.0047],
    [-0.0742,  4.54343962e-18,  0.0668],
    [0.0743, 4.54956286e-18, 0.0669],
    [0, 6.123234e-18, 0.1],
    [-0.0567, -0.0677,  0.0469],
    [0.0566, -0.0677,  0.0469],
    [8.74397815e-18, -0.0714,  0.0699],
    [-0.0307, -0.0949, -0.0047],
    [0.0307, -0.0949, -0.0047]
]

def create_random_data(n_chan,samples):
    print(samples)
    time_for_sin = np.linspace(0, 0.05 , samples)
    values = np.zeros((samples,n_chan),dtype=np.float32)
    for i in range(samples):
        for j in range(n_chan):
            values [i][j] = random.uniform(-1.0,1.0)

    # for i in range(n_chan): 
    #     values[:,i] = AMPLITUDE * np.sin(2 * np.pi * (INIT_FREQ + i * FREQ_INC) * time_for_sin)
                    
    return values

# def create_random_data1(n_chan,samples):
#     values = np.zeros((samples,n_chan),dtype=np.float64)
#     for i in range(samples):
#         for j in range(n_chan):
#             values [i][j] = random.randint(2,10)
#     return values

class EEGDataGeneratorOutlet(object):
    def __init__(self,name="EEG_data_stream",chunk_duration=1,sampling_freq=256,channels=channel_names,channels_locations=channel_locations):
        
        self.stream_name = name
        self.channels = channels
        self.channels_locations = channels_locations
        self.samp_freq = sampling_freq
        self.n_channels = len(self.channels)
        print(self.n_channels)
        
        self.chunk_duration = chunk_duration
        self.chunk_samples = int(self.samp_freq*self.chunk_duration)
        print("This stream will create random {} data for each of {} EEG channels".format(self.chunk_samples,self.n_channels))

        # self.time_vector = (np.arange(self.chunk_samples)+1)/self.samp_freq

        info = StreamInfo(name=self.stream_name,type="EEG",nominal_srate=self.samp_freq,channel_count=self.n_channels,channel_format="float32",source_id="myuid12334")

        chans = info.desc().append_child("channels")
        for label in self.channels:
            ch = chans.append_child('channel')
            ch.append_child_value("label",label)
            ch.append_child_value("unit",'microvolts')
        
        info.desc().append_child_value("manufacturer","Biosemi")
        cap = info.desc().append_child("cap")
        cap.append_child_value("name","ActiveTwo")
        cap.append_child_value("size","54")
        cap.append_child_value("labelscheme","10-20")

        self.eeg_outlet = StreamOutlet(info)
        print("Created an EEG type of outlet")
        # self.start_time = local_clock()
        
    # def update(self):
    #     timestamp = local_clock()
    #     data = create_random_data(n_chan=self.n_channels,samples=self.chunk_samples)
    #     print(timestamp,data.shape)
    #     self.eeg_outlet.push_chunk(x=data,timestamp=timestamp)
    #     time.sleep(0.05)

    def update(self):       
        mychunk_new = create_random_data(n_chan=self.n_channels,samples = self.chunk_samples)
        stamp = pylsl.local_clock()
        print(stamp,mychunk_new.shape)
        self.eeg_outlet.push_chunk(mychunk_new, stamp)
        # time.sleep(self.chunk_duration)
        time.sleep(self.chunk_duration)


# for irregural sampling rate: pylsl.IRREGULAR_RATE
# for regural sampling rate (EEG): 256

class MarkersGeneratorOutlet(object):
    phases = {
        'Start_of_trial': {'next':'1st_Image',"duration" : 10.0},
        '1st_Image': {'next':'2nd_Image',"duration" : 2.0},
        '2nd_Image': {'next':'3rd_Image',"duration" : 2.0},
        '3rd_Image': {'next':'Start_of_trial',"duration" : 1.0},
    }
    
    def __init__(self):
        stream_name = "Generated_Markers"
        stream_type = "Markers"
        outlet_info = StreamInfo(name=stream_name,type=stream_type,channel_count=1,\
                                nominal_srate=0,channel_format='string',source_id='centreoutmarkerhen1234')
        outlet_xml = outlet_info.desc()
        channels_xml = outlet_xml.append_child('channels')
        chan_xml = channels_xml.append_child('channel')
        chan_xml.append_child_value('label','EventMarkers')
        chan_xml.append_child_value('type','generated')
        self.outlet = StreamOutlet(outlet_info)
        print("Created outlet with name {} and type {}".format(stream_name, stream_type))
        
        self.next_transition = -1
        self.in_phase = '3rd_Image'
        self.trial_ix = 0
        # self.start_time = local_clock()
        
    def update(self):
        now = local_clock()
        # self.next_transition = now + self.phases[self.in_phase]['duration']
        if (now > self.next_transition):
            self.in_phase = self.phases[self.in_phase]['next']
            self.next_transition = now + self.phases[self.in_phase]['duration']
            
            out_string = "undefined"
            if self.in_phase == 'Start_of_trial':
                self.trial_ix +=1
                out_string = "NewTrial, trial_no: {}".format(self.trial_ix)
                timestamp = now - start_time
            elif self.in_phase == '1st_Image':      
                out_string = "1st_Image, trial_no: {}".format(self.trial_ix)
                timestamp = now - start_time
            elif  self.in_phase == '2nd_Image':    
                out_string = "2nd_Image, trial_no: {}".format(self.trial_ix)
                timestamp = now - start_time
            elif self.in_phase == "3rd_Image":
                out_string = "3rd_Image, trial_no: {}".format(self.trial_ix)
                timestamp = now - start_time
            # print("Marker outlet pushing string: {}".format(out_string))
            # print(timestamp)
            # print(self.next_transition)
            print(out_string,local_clock())
            self.outlet.push_sample([out_string,])
            
            return True
        return False

Markers_stream = MarkersGeneratorOutlet()
# EEG_stream1 = EEGDataGeneratorOutlet(name="EEG_stream1",chunk_duration=0.05,sampling_freq=2048,channels=channel_names,channels_locations=channel_locations)
EEG_stream2 = EEGDataGeneratorOutlet(name="EEG_stream2",chunk_duration=0.05,sampling_freq=256,channels=channel_names1,channels_locations=channel_locations)
# EEG_stream3 = EEGDataGeneratorOutlet(name="EEG_stream2",chunk_duration=0.05,sampling_freq=256,channels=channel_names1,channels_locations=channel_locations)

while True:
    Markers_stream.update()
    # EEG_stream1.update()
    EEG_stream2.update()
    # EEG_stream3.update()


    
    
    

