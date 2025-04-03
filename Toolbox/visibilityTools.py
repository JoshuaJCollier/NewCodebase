# Visibility toolbox, tools used for visibility specifically
# Author:  Josh Collier
# Created: 31 Mar 2025
# Notes: All docstrings up to date as 03 Apr 2025

# --- Imports ---
import cv2
import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
from scipy.signal import savgol_filter, find_peaks
from scipy.special import j0, j1
from scipy.ndimage import gaussian_filter1d
import sys
import myTools as tools

# --- Functions ---
def getVisibility(max, min):
    """ Return visibility based on max and min

    Args:
        max (float): Peak value
        min (float): Trough value

    Returns:
        float: visibility
    """
    return (max-min)/(max+min)

def getTimeSeriesVisibility(data):
    """ Finds visibility of a time series of values, by getting the max and min

    Args:
        data (array): Array of values over time

    Returns:
        float: visibility
    """
    return getVisibility(np.max(data),np.min(data))

def generateTheoreticalVisibility(baseline_space=np.linspace(0, 1*10**-3, 1000), wavelength=1550*10**-9, sourcewidth=500*10**-6, dist=1.0):
    """ Generates visibility curve expected for a source of a fixed width at a fixed distance for a range of baselines

    Example(s):
    theory200um = generate_vis(sourcewidth=200*10**-6, dist=distance, baseline_space=baseline_space)
    theory500um = generate_vis(sourcewidth=500*10**-6, dist=distance, baseline_space=baseline_space)
    theory1000um = generate_vis(sourcewidth=1000*10**-6, dist=distance, baseline_space=baseline_space)
    
    Args:
        baseline_space (array, optional): Baseline space of the generated visibility curve, in m. Defaults to np.linspace(0, 1*10**-3, 1000).
        wavelength (float, optional): Wavelength of light being viewed, in m. Defaults to 1550*10**-9.
        sourcewidth (float, optional): Size of the source at the object plane, in m. Defaults to 500*10**-6.
        dist (float, optional): Distance from object plane to imaging plane, in m. Defaults to 1.

    Returns:
        array: Visibility curve, for each value of the baseline_space
    """
    d, a, L = baseline_space, sourcewidth, dist # These are just so that the names are consistent with the equation while having good intuition for what they are
    visibility = 2*j1(np.pi*d*a/(L*wavelength))/(np.pi*d*a/(L*wavelength)) # visibility of uniform circular disk
    return abs(visibility)

def getExperimentalCameraVisibility(path, plotting=False, background=1000, plotNumber=0):
    """ Find visibility from image of interference

    Args:
        path (str, optional): Path to image.
        plotting (bool, optional): Plots some intermediate curves. Defaults to False.
        background (int, optional): Average background noise. Defaults to 1000.
        plotNumber (int, optional): Total plot number, used to manage many plots. Defaults to 0.

    Returns:
        float: visibility
    """
    image = cv2.imread(path, -1)
    image_floats = np.asarray(image,dtype = np.float64)
    
    # a bunch of noise in the image
    sigma = [1, 1]
    image_floats_smoothed = sp.ndimage.filters.gaussian_filter(image_floats, sigma, mode='constant')
    target_slice = np.sum(image_floats_smoothed.T, axis=0).argmax() #(ymax - ymin) / 2 + ymin # get the middle of the fringe blob

    sobely = cv2.Sobel(image,cv2.CV_64F,2,0,ksize=5) # get the horizontal derivative
    sobely = cv2.blur(sobely,(7,7)) # make the peaks a little smoother

    slc = sobely[int(target_slice), :]
    #slc[slc < 0] = 0
    
    slc = gaussian_filter1d(-slc, sigma=1) # filter the peaks the remove noise,
    peaks = find_peaks(slc)[0] # [0] returns only locations 
    troughs = find_peaks(-slc)[0] # [0] returns only locations 

    image_floats = image_floats - background
    image_floats[image_floats <= 0] = 0 
    image_floats = gaussian_filter1d(image_floats, sigma=0.1)

    if np.max(slc[troughs]) > np.max(slc[peaks]):
        temp = troughs 
        troughs = peaks
        peaks = temp
        
    #print(image_floats[int(target_slice), peaks])
    #print(max_pos)
    max_pos = slc[peaks].argmax()
    max_val = image_floats[int(target_slice), peaks[max_pos]]
    min_pos = tools.findNearest(troughs, peaks[max_pos])
    min_val = 0
    used_vals=[]
    if troughs[min_pos] > peaks[max_pos]:
        min_val = (image_floats[int(target_slice), troughs[min_pos]] + image_floats[int(target_slice), troughs[min_pos-1]])/2
        used_vals = [troughs[min_pos-1], peaks[max_pos], troughs[min_pos]]
    else:
        min_val = (image_floats[int(target_slice), troughs[min_pos]] + image_floats[int(target_slice), troughs[min_pos+1]])/2
        used_vals = [troughs[min_pos], peaks[max_pos], troughs[min_pos+1]]

    visibility = max(getVisibility(max_val, min_val), getVisibility(min_val, max_val))
   
    if plotting:
        plt.figure(plotNumber)
        plt.imshow(sobely, cmap='gray') #show the derivative (troughs are very visible)
        plt.plot([0, image.shape[1]], [target_slice, target_slice], 'r-')
        plt.title("horizontal derivative (red line indicating slice taken from image)")

        plt.figure(plotNumber+1)
        plt.plot(slc) 
        plt.plot(image_floats[int(target_slice),:]) 
        plt.plot(peaks, slc[peaks], 'ro', label='peaks')
        plt.plot(troughs, slc[troughs], 'go', label='troughs')
        plt.plot(used_vals, slc[used_vals], 'bx', label='used')
        plt.plot(used_vals, image_floats[target_slice, used_vals], 'b+', label='used')
        plt.title(path)
        plt.legend()
    
    return visibility

def genExpCamVisSeries(size, directory, background_light=1000, name='', filename='', arr_x=[1, 2, 3, 4, 5, 6], plotNumber=0, plotting=False):
    """ Generate experimental camera visibility from a series of images

    Args:
        size (int): Source size (in um)
        directory (str): Directory of files
        background_light (int, optional): Average background noise. Defaults to 1000.
        name (str, optional): Simple name used for some printing. Defaults to ''.
        filename (str, optional): File naming scheme that is used, if not set, uses size str. Defaults to ''.
        arr_x (list, optional): Array of baselines. Defaults to [1, 2, 3, 4, 5, 6].
        plotNumber (int, optional): Number of plots total. Defaults to 0.
        plotting (bool, optional): Passes through, for excess intermediate plotting. Defaults to False.

    Returns:
        array: Array of visibilities, one for each baseline
    """
    arr_y = []
    for i in range(len(arr_x)):
        path = ''
        if filename!='': path = directory+filename.format(arr_x[i])
        else: path = directory+str(size)+'um_'+str(arr_x[i])+'.tiff'
        arr_y.append(getExperimentalCameraVisibility(path, plotting=plotting, plotNumber=i*2+plotNumber, background=background_light))
    
    if name == '': name = '{}um'.format(size)
    print(name+' = {}'.format(arr_y))

    return arr_y

def generateVisibilityPlot(title='',baseline_space=np.linspace(0, 1*10**-3, 1000), wavelength=1550*10**-9, sourcewidth=500*10**-6, dist=1.0):
    """ This is just a wrapper for the function generateVisibility to turn it into a plot quickly

    Example(s):
        generateVisibilityPlot(title='200um', sourcewidth=1000*10**-6, dist=distance, baseline_space=baseline_space)
    
    Args:
        baseline_space (array, optional): Baseline space of the generated visibility curve, in m. Defaults to np.linspace(0, 1*10**-3, 1000).
        wavelength (float, optional): Wavelength of light being viewed, in m. Defaults to 1550*10**-9.
        sourcewidth (float, optional): Size of the source at the object plane, in m. Defaults to 500*10**-6.
        dist (float, optional): Distance from object plane to imaging plane, in m. Defaults to 1.
    """
    plt.plot(baseline_space*10**3, generateTheoreticalVisibility(baseline_space=baseline_space, wavelength=wavelength, sourcewidth=sourcewidth, dist=dist), label='200um')
    plt.title(title, fontsize=14) 
    plt.xlabel('Baseline (mm)', fontsize=12)
    plt.ylabel('Visibility', fontsize=12)
    plt.ylim([0, 1])
    plt.legend(title='Source Size')
    plt.rcParams["figure.figsize"] = (6,6)

def generateVerticleLines(exp_baseline_list):
    """ Generates a series of verticle lines to add to the plot based on experimental baselines, with text

    Args:
        exp_baseline_list (array): Array of baselines used in experiment, in m
    """
    for i, baseline in enumerate(exp_baseline_list):
        plt.axvline(x=baseline*10**3, color='r', linestyle='--')
        plt.text(baseline*10**3+0.005, 0.5, "{:.0f}$\\mu$m".format(baseline*10**6), rotation=90, verticalalignment='center')

def estimateSourceWidth(baseline, distance, data, wavelength = 1550*10**(-9)):
    """ Determining beam diameter from visibility calcs

    Args:
        baseline (float): Baseline in imaging plane
        distance (float): Distance to source
        data (array): Time series of data
        wavelength (float, optional): Wavelength of light used. Defaults to 1550*10**(-9).

    Returns:
        float: Source width (maybe)
    """
    # our determination of the beam diameter from the visibility calcs used the expression
    gamma = getTimeSeriesVisibility(data) # for equal brightness sources
    print("Gamma:",gamma)
    sigma_d = np.sqrt((-baseline**2)/2*np.log(gamma))
    sigma_y = wavelength*distance/(2*np.pi*sigma_d)
    
    return sigma_y # standard deviation of source
