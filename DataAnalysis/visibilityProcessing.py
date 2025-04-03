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
    directory = 'C:\\Users\\josh\\OneDrive - UWA\\UWA\\PhD\\3. Data\\250314\\'

    exp_200um = visTools.genExpCamVisSeries(200, directory, background_light=1000, name='LED 200um', arr_x=[1,2,4,6], filename='200um_source_baseline_{}.tiff', plotNumber=plotTotal)
    exp_500um = visTools.genExpCamVisSeries(500, directory, background_light=1000, name='LED 500um', arr_x=[1,2,4,6], filename='500um_source_baseline_{}.tiff', plotNumber=plotTotal+8)
    exp_1000um = visTools.genExpCamVisSeries(1000, directory, background_light=1000, name='LED 1000um', arr_x=[1,2,4,6], filename='1000um_source_baseline_{}.tiff', plotNumber=plotTotal+16)

    # MANUALLY EDITTED POINTS (code didnt recognise it well)
    exp_200um[3] = 0.3901 
    exp_500um[3] = 0.0841

    exp = [exp_200um, exp_500um, exp_1000um]

    baseline_space = np.linspace(1*10**-9, 10*10**-3, 1000) # distance range in meters
    source_sizes = np.array([200, 500, 1000]) # in um
    wavelength = 1450*10**-9 # wavelength of LED    
    colours = ['blue', 'green', 'red']
    exp_baselines = np.array([1e-3, 2e-3, 4.5e-3, 6e-3])

    plt.figure(1)
    for i in range(3):
        theory = visTools.generateTheoreticalVisibility(sourcewidth=200*10**-6, dist=1, baseline_space=baseline_space, wavelength=wavelength)
        plt.plot(exp_baselines*10**3, exp[i], label='{}um exp'.format(source_sizes[i]), marker='o', linestyle='--', color=colours[i])
        plt.plot(baseline_space*1000, theory, label='{}um theory'.format(source_sizes[i]), color=colours[i])
        compVals(theory, exp[i], source_sizes[i], baseline_space, exp_baselines)

    tools.plotParams(title='Visibility vs Baseline (LED)', xlabel='Baseline (mm)', ylabel='Visibility', ylim=[0, 1], legend='Source size')
    plt.show()

def generateLEDtoInterferometerData():
    """ Generates plot from data of LED pointing at interferometer from 10cm away (0.01m away)
    """
    # Theory constants
    wavelength = 1450*10**-9 # wavelength of light in metres
    distance = 92*10**-3 # NOTE: as max distance approaches infinity, we get high visibility because we are looking at a point source?
    baseline_space = np.linspace(0.001*10**-3, 0.5*10**-3, 1000) # distance range in metres    
    exp_baseline_list = np.array([127, 2*127, 3*127])*10**-6 # in m
    source_sizes = np.array([200, 500, 1000]) # in um
    
    # baseline   127um  254um  381um   ------ these are manually recorded values
    raw_data = [[0.210, 0.185, 0.155], # 200um source
                [0.175, 0.125, 0.065], # 500um source
                [0.120, 0.065, 0.050]] # 1000 um source
    scale, yaxis, offset = 5.6, -0.109, 0.02
    data = (np.array(raw_data)-offset)*scale+yaxis    
    colour = ['blue', 'green', 'red'] # one for each source size

    for i in range(3):
        theory = visTools.generateTheoreticalVisibility(sourcewidth=source_sizes[i]*10**-6, dist=distance, baseline_space=baseline_space, wavelength=wavelength)
        plt.plot(baseline_space*10**3, theory, label='{}um theory'.format(source_sizes[i]), color=colour[i]) # theoretical plot
        plt.plot(exp_baseline_list*10**3, data[i], color=colour[i], marker='o', linestyle='--') # experimental plot
        plt.axvline(x=exp_baseline_list[i]*10**3, color='r', linestyle='--') # vertical line for each baseline
        plt.text(exp_baseline_list[i]*10**3+0.005, 0.5, "{:.0f}$\\mu$m".format(exp_baseline_list[i]*10**6), rotation=90, verticalalignment='center') # text for vertical lines
        compVals(theory, raw_data[i], source_sizes[i]*10**-6, baseline_space, exp_baseline_list) # comparison printing
        
    tools.plotParams(title='Interferometer response to LED - scaled', xlabel='Baseline (mm)', ylabel='Visibility', ylim=[0, 1], legend='Source size')
    plt.show()

generateLEDtoInterferometerData()