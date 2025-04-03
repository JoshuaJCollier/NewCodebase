# Code for extracting visibilities from thermal camera images and comparing to theory
# Author:  Josh Collier
# Created: 31 Mar 2024

import numpy as np
import matplotlib.pyplot as plt
import sys

sys.path.insert(0, sys.path[0]+'\\..\\Toolbox')
import visibilityTools as visTools # type: ignore
import myTools as tools # type: ignore


def compVals(theory, exp, size, baseline_space, baselines): # baseline in m
    """ Function to print out a comparison of the theoretical and experimental values and their error
    """
    print('Theory vs exp @ {:.1f}um'.format(size*10**6))
    for i, baseline in enumerate(baselines):
        #print(baseline_space)
        baseline_index = tools.findNearest(baseline_space, baseline)
        theoretical = theory[baseline_index]
        experimental = exp[i]
        error = (np.abs(theoretical-experimental)/theoretical)*100
        print('For baseline of {:.1f}um, err: {:.2f}% (theory: {:.3f}, exp: {:.3f})'.format(baseline*10**6, error, theoretical, experimental))
    print()

def generateLEDtoSWIRData(): # This is data taken 14th Mar 2025, generates plot of experimental LED data vs theoretical
    """ Generates plot from data of LED pointing at SWIR camera from 1m away
    """
    plotTotal = 3
    background = 1000
    directory = 'C:\\Users\\josh\\OneDrive - UWA\\UWA\\PhD\\3. Data\\250314\\'
    LED_200 = '200um_source_baseline_{}.tiff'
    LED_500 = '500um_source_baseline_{}.tiff'
    LED_1000 = '1000um_source_baseline_{}.tiff'

    exp_200um = visTools.genExpCamVisSeries(200, directory, background, name='LED 200um', arr_x=[1,2,4,6], filename=LED_200, plotNumber=plotTotal)
    plotTotal+=8
    exp_500um = visTools.genExpCamVisSeries(500, directory, background, name='LED 500um', arr_x=[1,2,4,6], filename=LED_500, plotNumber=plotTotal)
    plotTotal+=8
    exp_1000um = visTools.genExpCamVisSeries(1000, directory, background, name='LED 1000um', arr_x=[1,2,4,6], filename=LED_1000, plotNumber=plotTotal)
    plotTotal+=8

    exp_200um[3] = 0.3901 # measured by hand for 6mm baseline (code didnt recognise it well)
    exp_500um[3] = 0.0841 # measured by hand for 6mm baseline (code didnt recognise it well)

    baseline_space = np.linspace(1*10**-9, 10*10**-3, 1000) # distance range in meters
    wavelength = 1450*10**-9 # wavelength of LED
    theory_200um = visTools.generateTheoreticalVisibility(sourcewidth=200*10**-6, dist=1, baseline_space=baseline_space, wavelength=wavelength)
    theory_500um = visTools.generateTheoreticalVisibility(sourcewidth=500*10**-6, dist=1, baseline_space=baseline_space, wavelength=wavelength)
    theory_1000um = visTools.generateTheoreticalVisibility(sourcewidth=1000*10**-6, dist=1, baseline_space=baseline_space, wavelength=wavelength)


    plt.figure(1)
    plt.plot([1,2,4,6], exp_200um, label='LED 200um exp', marker='o', linestyle='--', color='b')
    plt.plot([1,2,4,6], exp_500um, label='LED 500um exp', marker='o', linestyle='--', color='g')
    plt.plot([1,2,4,6], exp_1000um, label='LED 1000um exp', marker='o', linestyle='--', color='r')

    plt.plot(baseline_space*1000,theory_200um, label='200um theory', color='b')
    plt.plot(baseline_space*1000,theory_500um, label='500um theory', color='g')
    plt.plot(baseline_space*1000,theory_1000um, label='1000um theory', color='r')

    compVals(theory_200um, exp_200um, 200, baseline_space, [1e-3, 2e-3, 4.5e-3, 6e-3])
    compVals(theory_500um, exp_500um, 500, baseline_space, [1e-3, 2e-3, 4.5e-3, 6e-3])
    compVals(theory_1000um, exp_1000um, 1000, baseline_space, [1e-3, 2e-3, 4.5e-3, 6e-3])

    plt.ylim([0, 1])
    plt.legend()
    plt.xlabel('Baseline (mm)')
    plt.ylabel('Visibility')
    plt.title('Visibility vs Baseline (LED)')
    plt.show()

def generateLEDtoInterferometerData():
    """ Generates plot from data of LED pointing at interferometer from 10cm away (0.01m away)
    """
    max_baseline = 0.5*10**-3 # baseline of interferometer in metres 
    min_baseline = 0.001*10**-3 # baseline of interferometer in metres 
    wavelength = 1450*10**-9 # wavelength of light in metres
    distance = 92*10**-3 # NOTE: as max distance approaches infinity, we get high visibility because we are looking at a point source?
    baseline_space = np.linspace(min_baseline, max_baseline, 1000) # distance range in metres
    
    theory_200um = visTools.generateTheoreticalVisibility(sourcewidth=200*10**-6, dist=distance, baseline_space=baseline_space, wavelength=wavelength)
    theory_500um = visTools.generateTheoreticalVisibility(sourcewidth=500*10**-6, dist=distance, baseline_space=baseline_space, wavelength=wavelength)
    theory_1000um = visTools.generateTheoreticalVisibility(sourcewidth=1000*10**-6, dist=distance, baseline_space=baseline_space, wavelength=wavelength)

    plt.plot(baseline_space*10**3,theory_200um, label='200um theory', color='blue')
    plt.plot(baseline_space*10**3,theory_500um, label='500um theory', color='orange')
    plt.plot(baseline_space*10**3,theory_1000um, label='1000um theory', color='green')
    
    exp_baseline_list = np.array([127, 2*127, 3*127])*10**-6
    scale = 5.6#8.11
    yaxis = -0.109 #-0.581
    offset = 0.02
    
    #scale, yaxis, offset = 1, 0, 0.02

    # x axis is changing baseline, y axis is changing source size
    # baseline   127um  254um  381um
    raw_data = [[0.210, 0.185, 0.155], # 200um
                [0.175, 0.125, 0.065], # 500um
                [0.120, 0.065, 0.050]] # 1000 um
    
    data = (np.array(raw_data)-offset)*scale+yaxis
    colour = ['blue', 'orange', 'green'] # one for each source size

    for i in range(len(raw_data)):
        for j in range(len(raw_data[i])):
            plt.plot(exp_baseline_list[j]*10**3,(raw_data[i][j]-offset)*scale+yaxis,color=colour[i], marker='o')

    compVals(theory_200um, raw_data[0], 200*10**-6, baseline_space, exp_baseline_list)
    compVals(theory_500um, raw_data[1], 500*10**-6, baseline_space, exp_baseline_list)
    compVals(theory_1000um, raw_data[2], 1000*10**-6, baseline_space, exp_baseline_list)
    
    for i, baseline in enumerate(exp_baseline_list):
        plt.axvline(x=baseline*10**3, color='r', linestyle='--')
        plt.text(baseline*10**3+0.005, 0.5, "{:.0f}$\\mu$m".format(baseline*10**6), rotation=90, verticalalignment='center')
        
    plt.title('Interferometer response to LED - scaled', fontsize=14) # - 5m 600um core MMF - 0.83m distance
    plt.xlabel('Baseline (mm)', fontsize=12)
    plt.ylabel('Visibility', fontsize=12)
    plt.ylim([0, 1])
    plt.legend(title='Source Size')
    plt.rcParams["figure.figsize"] = (14,12)
    plt.show()

generateLEDtoInterferometerData()
