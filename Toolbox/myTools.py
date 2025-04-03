# Josh's toolbox, just a massive list of tools that are used often between programs
# Author:  Josh Collier
# Created: 31 Mar 2025

# --- Imports ---
import numpy as np
from scipy.signal import butter, lfilter
import cv2


# --- Functions ---
def findNearest(array, value): # for array [3, 6, 8, 9], value 7, returns 1 or 2
    """ Finds the nearest value to the value provided in an array (returns the index of this)

    Args:
        array (array): Array you want to search through
        value (float): Value you are looking for

    Returns:
        int: Index of the value that is the closest
    """
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

def movingAverage(a, n=3):
    """ Returns a moving average

    Args:
        a (array): The array you want to average
        n (int, optional): Number of averaged steps. Defaults to 3.

    Returns:
        array: Moving averaged array
    """
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

def normaliseData(data):
    return data/np.average(data)

def normaliseDataTight(data):
    ''' data:   Set that we want normalised such that the max is 1 and the min is 0'''
    return (data-np.min(data))/np.max(data-np.min(data))

def wrapData(data, avg_rate, offset=0):
    """ Take a set of repeating pattern and sums each set of the pattern so that you can get the average of each pattern instance

    Args:
        data (_type_): The set that you want averaged / bucketted
        avg_rate (_type_): The number of steps between each repetition of the data so we can do our bucketting
        offset (int, optional): A number of offset, can be used if the start point isnt at 0. Defaults to 0.

    Returns:
        array: The set of data inputted by is now all instances of the pattern overlapped
    """

    wrapped = []
    for i in range(avg_rate):
        wrapped.append(np.sum(data[i+offset::avg_rate]))
        
    return np.array(wrapped)

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter(order, cutoff, fs=fs, btype='low', analog=False)
    y = lfilter(b, a, data)
    return y

def findNext(list_indexing, comparing):
    ''' Finds the next value in the list larger than a set value, returns the index'''
    for i in range(len(list_indexing)):
        if list_indexing[i] > comparing:
            return i

def findImageAvg(directory, filename, n=1):
    # image name: 'blank_'+str(i)+'.tiff'
    ''' Finds the average value of an image or list of images, note that this is for grey images'''
    if isinstance(filename,str):
        return np.average(np.asarray(cv2.imread(directory+filename, -1), dtype = np.float64))
    
    sum = 0
    for i in range(n):
        sum += np.average(np.asarray(cv2.imread(directory+filename[i], -1), dtype = np.float64)) # -1 is for grey
    return sum/n