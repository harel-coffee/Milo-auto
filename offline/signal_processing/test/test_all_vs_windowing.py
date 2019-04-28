#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 15:46:32 2019

@author: jenisha
"""

"""
Testing filtering on all data vs 2 window at a time

"""

import numpy as np
import pandas as pd
from copy import deepcopy

import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

from scipy.signal import butter, ellip, cheby1, cheby2, lfilter, freqs,iirfilter,stft

import numpy.fft as fft


class Test_Filtering():
    def __init__(self, path, name_channels=["C3", "C1", "Cp3", "Cp1", "Cp2", "Cp4", "C2", "C4"]):
        self.path = path
        self.sample_rate = 250 #Default sampling rate for OpenBCI
        self.name_channel = name_channels

    def load_data_BCI(self,interval = (500,1000), list_channels=[1, 2, 3, 4, 5, 6, 7, 8]):
        """
        list_channels=[2, 7, 1, 8, 4, 5, 3, 6])
        name_channels=["C1", "C2", "C3", "C4", "Cp1", "Cp2", "Cp3", "Cp4"]
        Load the data from OpenBCI txt file

        Input:
            list_channel: lists of channels to use
        
        """
        self.number_channels = len(list_channels)
        self.list_channels = list_channels
        
        # load raw data into numpy array
        self.raw_eeg_data = np.loadtxt(self.path, 
                                       delimiter=',',
                                       skiprows=7,
                                       usecols=list_channels)

        #expand the dimmension if only one channel             
        if self.number_channels == 1:
            self.raw_eeg_data = np.expand_dims(self.raw_eeg_data, 
                                                          axis=1)
    def epoch_data(self, data,mode="1", window_length = 2, overlap=125):
            """
            Separates the data into several windows
            
            Input:
                - data: data to seperate into windows
                - mode: whether the windows are of same length (mode 1) or different lengths (mode 2)
                - window_length: length of the window in s
                - overlap: overlap in the previous window
            
            """
            array_epochs = []
            i = 0
            self.window_size_hz = int(window_length * self.sample_rate)
            
            if mode == "1":
                while(i  < len(data) ):
                    array_epochs.append(data[i:i+self.window_size_hz ])
                    i = i + self.window_size_hz 
                
    
                if i is not len(data) - 1:
                    array_epochs.append(data[i:len(data)])
    
                self.epoch = array_epochs
            
            if mode == "2":
                while i + self.window_size_hz < len(data):
                    array_epochs.append(data[i:i + self.window_size_hz])
                    i += overlap
                self.num_epochs = i + 1
               

            return np.array(array_epochs)
            
    
    def initial_preprocessing(self, bp_lowcut =1, bp_highcut =70, bp_order=2,
                          notch_freq_Hz  = [60.0, 120.0], notch_order =2):
       """
       Filters the data by applying
       - A zero-phase Butterworth bandpass was applied from 1 – 70 Hz. 
       - A 60-120 Hz notch filter to suppress line noise
      
       
       Input:
           - bp_ lowcut: lower cutoff frequency for bandpass filter
           - bp_highcut: higher cutoff frequency for bandpass filter
           - bp_order: order of bandpass filter
           - notch_freq_Hz: cutoff frequencies for notch fitltering
           - notch_order: order of notch filter

        
        """
       self.nyq = 0.5 * self.sample_rate #Nyquist frequency
       self.low = bp_lowcut / self.nyq
       self.high = bp_highcut / self.nyq
       
       
       #Butter
       b_bandpass, a_bandpass = butter(bp_order, [self.low , self.high],
                                       btype='band', analog=True)
       
       
       self.bp_filtered_eeg_data = np.apply_along_axis(lambda l: lfilter(b_bandpass, a_bandpass ,l),0,
                                                      self.raw_eeg_data)
       
       self.corrected_epoched_eeg_data = []
       self.corrected_epoched_eeg_data_psd =[]
       
       for raw in self.raw_eeg_data.T:  
           epoched = self.epoch_data(raw,mode="1",window_length = 2,overlap=0)
           epoch_filtered = []
           epoch_filtered_psd = np.zeros(251)
           
           for epoch in epoched:
               filtered = lfilter(b_bandpass, a_bandpass ,epoch)
               epoch_filtered.extend(filtered[1::])
  
               psd,_ = mlab.psd(np.squeeze(filtered),
                           NFFT=500,
                           Fs=250)

               if len(filtered) == 500:
                   epoch_filtered_psd= np.vstack((epoch_filtered_psd,psd))
           
        
           self.corrected_epoched_eeg_data.append(epoch_filtered)
  
           epoch_filtered_psd = np.delete(epoch_filtered_psd, (0), axis=0)
           epoch_filtered_psd_mean = np.mean(epoch_filtered_psd, axis=0)
           self.corrected_epoched_eeg_data_psd.append(epoch_filtered_psd_mean)
           
  
       self.corrected_eeg_data = self.corrected_epoched_eeg_data 

           
           
                

    def plots(self, num_channels=8):
        """
       
        Plot the raw and filtered data of a channel as well as their spectrograms
        
        Input:
            - channel: channel whose data is to plot
        
        """

        fig, axs = plt.subplots(8,2)
        fig2, axs2 = plt.subplots(8,2)
        axs,axs2 = axs.ravel(),axs2.ravel()
        

        t_sec = np.array(range(0, self.raw_eeg_data[:,0].size)) / self.sample_rate
        i = 0
        for idx, channel in enumerate(range(num_channels)):  
            #fig.suptitle(self.name_channel[channel])   

            axs[i].plot(self.bp_filtered_eeg_data[1:,channel])
            axs[i].set_title(str(self.name_channel[channel])+'_All')
            
            psd,freqs = mlab.psd(np.squeeze(self.bp_filtered_eeg_data[1:,channel]),
                           NFFT=500,
                           Fs=250)
            
            axs2[i].plot(freqs,psd)
            axs2[i].set_title(str(self.name_channel[channel])+'_All')
            axs2[i].set_ylim(0,0.01)

            
            i = i + 1

            axs[i].plot(self.corrected_eeg_data[channel][::])
            axs[i].set_title(str(self.name_channel[channel])+'_Epoched')
            
            self.psd2,self.freqs2 = mlab.psd(np.squeeze(self.corrected_eeg_data[channel][::]),
                           NFFT=500,
                           Fs=250)
            
            axs2[i].plot(self.freqs2,self.corrected_epoched_eeg_data_psd[channel])
            axs2[i].set_title(str(self.name_channel[channel])+'_Epoched')
            axs2[i].set_ylim(0,0.01)

            
            i = i + 1

        
        plt.show()              
                
plt.close('all')            
path='/Users/jenisha/Desktop/NeuroTechX-McGill-2019/offline/data/March_11/'
fname= path +  '1_JawRest_JawRightClench_10s.txt'

test4 = Test_Filtering(fname)
test4.load_data_BCI()
test4.initial_preprocessing(bp_lowcut =5, bp_highcut =20, bp_order=2)
test4.plots()  



           
           