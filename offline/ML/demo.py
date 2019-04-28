# -*- coding: utf-8 -*-
"""
Created on Wed Mar 28 17:35:17 2018

@author: Marley
"""
import numpy as np
import numpy.fft as fft
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

from sklearn import model_selection
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC

import pandas as pd


def epoch_data(data, window_length, overlap):
    arr = []
    i = 0
    while i + window_length < len(data):
        arr.append(data[i:i+window_length])
        i += overlap
    return np.array(arr)
def get_features(data_epochs, sampling_freq):
    num_epochs, win_length = data_epochs.shape
    Y = fft.fft(data_epochs)/win_length
    PSD = 2*np.abs(Y[0:int(win_length/2), :])
    f = sampling_freq/2*np.linspace(0, 1, int(win_length/2))
    # SPECTRAL FEATURES
    # Average of band powers
    # Delta <4
    ind_delta, = np.where(f < 4)
    meanDelta = np.mean(PSD[:, ind_delta], axis = -1)
    # Theta 4-8
    ind_theta, = np.where((f >= 4) & (f <= 8))
    meanTheta = np.mean(PSD[:, ind_theta], axis = -1)
    # Alpha 8-12
    ind_alpha, = np.where((f >= 8) & (f <= 12))
    meanAlpha = np.mean(PSD[:, ind_alpha], axis = -1)
    # Beta 12-30
    ind_beta, = np.where((f >= 12) & (f < 30))
    meanBeta = np.mean(PSD[:, ind_beta], axis=-1)
    feature_vector = np.array([meanDelta, meanTheta, meanAlpha,
                                     meanBeta]).T
    feature_vector = np.log10(feature_vector)
    return feature_vector
def draw_specgram(ch, fs_Hz, fig, i):
    NFFT = fs_Hz*2
    overlap = NFFT - int(0.25 * fs_Hz)
    spec_PSDperHz, spec_freqs, spec_t = mlab.specgram(np.squeeze(ch),
                                   NFFT=NFFT,
                                   window=mlab.window_hanning,
                                   Fs=fs_Hz,
                                   noverlap=overlap
                                   ) # returns PSD power per Hz
    # convert the units of the spectral data
    
    spec_PSDperBin = spec_PSDperHz * fs_Hz / float(NFFT)
    f_lim_Hz = [0, 60]   # frequency limits for plotting
    #plt.figure(figsize=(10,5))
    ax = fig.add_subplot(2,1,i)
    plt.pcolor(spec_t, spec_freqs, 10*np.log10(spec_PSDperBin))  # dB re: 1 uV
    plt.clim([-25,26])
    plt.xlim(spec_t[0], spec_t[-1]+1)
    plt.ylim(f_lim_Hz)
    plt.xlabel('Time (sec)')
    plt.ylabel('Frequency (Hz)')
    plt.show()
if __name__ == '__main__':
    fname_ec = '../data/EyesClosedNTXDemo.txt' 
    fname_eo = '../data/EyesOpenedNTXDemo.txt' 
    data_ec = np.loadtxt(fname_ec,
                      delimiter=',',
                      skiprows=7,
                      usecols=(1))
    data_eo = np.loadtxt(fname_eo,
                      delimiter=',',
                      skiprows=7,
                      usecols=(1))
    sampling_freq = 250
    window_size = int(3 * sampling_freq)
    window_overlap = int(0.5 * sampling_freq)
    fig = plt.figure()
    draw_specgram(data_eo, sampling_freq, fig, 1)
    draw_specgram(data_ec, sampling_freq, fig, 2)
    
    data_epochs_ec = epoch_data(data_ec, window_size, window_overlap)
    data_epochs_eo = epoch_data(data_eo, window_size, window_overlap)
    
    ec_features = get_features(data_epochs_ec, sampling_freq)
    eo_features = get_features(data_epochs_eo, sampling_freq)
    
    ec_features = np.hstack((ec_features, np.ones([ec_features.shape[0],1])))
    eo_features = np.hstack((eo_features, np.zeros([eo_features.shape[0],1])))
            
    X = np.vstack((ec_features, eo_features))[:,:-1]
    Y = np.vstack((ec_features, eo_features))[:,-1]
    validation_size = 0.20
    seed = 7
    X_train, X_validation, Y_train, Y_validation = model_selection.train_test_split(X, Y, test_size=validation_size, random_state=seed)
    
    # Test options and evaluation metric
    seed = 7
    scoring = 'accuracy'
    
    # Spot Check Algorithms
    models = []
    models.append(('LR', LogisticRegression()))
    models.append(('LDA', LinearDiscriminantAnalysis()))
    models.append(('KNN', KNeighborsClassifier()))
    models.append(('CART', DecisionTreeClassifier()))
    models.append(('NB', GaussianNB(var_smoothing=0.001)))
    models.append(('SVM', SVC()))
    # evaluate each model in turn
    results = []
    names = []
    
    for name, model in models:
    	kfold = model_selection.KFold(n_splits=10, random_state=seed)
    	cv_results = model_selection.cross_val_score(model, X_train, Y_train, cv=kfold, scoring=scoring)
    	results.append(cv_results)
    	names.append(name)
    	msg = "%s: %f (%f)" % (name, cv_results.mean(), cv_results.std())
    	print(msg)
    
    fname_eo_test = '../data/OpenBCI-RAW-2018-04-17_17-21-25.txt'
    fname_ec_test = '../data/Ganglion1minEyesOpen-1minEyesClosed.txt'
        
    eo_test = np.loadtxt(fname_eo_test,
                      delimiter=',',
                      skiprows=7,
                      usecols=(1))
    ec_test = np.loadtxt(fname_ec_test,
                      delimiter=',',
                      skiprows=sampling_freq*10,    # skip first 10 seconds (noisy)
                      usecols=(3))                  # channel 3 is at O1
    
    ec_test = ec_test[70*sampling_freq : 100*sampling_freq]             # grab seconds 70 to 100 
    
    fig = plt.figure()
    draw_specgram(eo_test, sampling_freq, fig, 1)
    draw_specgram(ec_test, sampling_freq, fig, 2)
    
    data_epochs_ec_test = epoch_data(ec_test, window_size, window_overlap)
    data_epochs_eo_test = epoch_data(eo_test, window_size, window_overlap)
    
    ec_test_features = get_features(data_epochs_ec_test, sampling_freq)
    eo_test_features = get_features(data_epochs_eo_test, sampling_freq)
    
    Y_eo_test = [0]*len(eo_test_features)
    Y_ec_test = [1]*len(ec_test_features)
    
    for name, model in models:
        model.fit(X_train, Y_train)
        ec_test_score = model.score(ec_test_features, Y_ec_test)
        eo_test_score = model.score(eo_test_features, Y_eo_test)
        validation_score = model.score(X_validation, Y_validation)
        msg = "%s: validation %f, test (closed) %f, test (open) %f" % (name, validation_score, ec_test_score, eo_test_score)
        print(msg)



