# Code for taking CSVs downloaded from moku:pro and processing them
# Author:  Josh Collier
# Created: 06 Nov 2024

# --- Imports ---
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

sys.path.insert(0, sys.path[0]+'\\..\\Toolbox')
import visibilityTools as visTools # type: ignore
import generalTools as tools # type: ignore

# --- Functions ---
def mokuProPhasemeter(curr_dir, filename):
    """ Plot phase time series data from csv file downloaded from moku pro

    Args:
        filename (str): File name.
        curr_dir (str): Directory of file.
    """
    phase_pandas = pd.read_csv(curr_dir+filename+'.csv', skiprows=9)

    inputA_phase = np.array(phase_pandas[' Input A Phase (cyc)']).astype("float64")
    inputB_phase = np.array(phase_pandas[' Input B Phase (cyc)']).astype("float64")
    time = np.array(phase_pandas['% Time (s)']).astype("float64")
    
    return inputA_phase, inputB_phase, time

def mokuProDataLogger(curr_dir, filename, display_time=False, figname=''):
    """ Takes csv file downloaded from Moku:Pro returns arrays

    Example(s):
        dataLoggerProcess("C:\\Users\\josh\\OneDrive - UWA\\UWA\\PhD\\3. Data\\Interference Data\\250122_Interference\\", "Interferometer250122_20250122_082257", cyc=5, freq=1, rate=1000, manual_offset=2, diff_trigger=0.5, roll=10, display_time=True, display_avg=True, figname="SNSPDs with modulated thorlabs")

    Args:
        curr_dir (str): Directory of file.
        filename (str): File name.
        display_time (bool, optional): Optional additional time series display. Defaults to False.
        figname (str, optional): Name of figure. Defaults to ''.
    """
    interference_pandas = pd.read_csv('{}{}.csv'.format(curr_dir, filename), skiprows=11) # skip comment as well
    
    inputA = np.array(interference_pandas[' Input A (V)']).astype("float64")
    inputB = np.array(interference_pandas[' Input B (V)']).astype("float64")
    inputC = np.array(interference_pandas[' Input C (V)']).astype("float64")
    inputD = np.array(interference_pandas[' Input D (V)']).astype("float64")
    time = np.array(interference_pandas['% Time (s)']).astype("float64")

    if display_time:
        plt.figure()
        plt.title('Interference Time Series {}'.format(figname))
        plt.plot(time, inputA)
        plt.plot(time, inputB)
        plt.plot(time, inputC)
        plt.plot(time, inputD)
        plt.legend(['Input A', 'Input B', 'Input C', 'Input D'])
        plt.xlabel('Time (s)')
        plt.ylabel('Signal Amplitude (V)')
    
    return inputA, inputB, inputC, inputD, time

def plotPhaseSeriesData(filename, curr_dir):
    """ Plot phase time series data from csv file downloaded from moku pro

    Args:
        filename (str): File name.
        curr_dir (str): Directory of file.
    """
    phase_data, None, phase_time = mokuProPhasemeter(curr_dir, filename)
    
    plt.figure()
    plt.title('Fibre Stretcher Time Series {}'.format(filename))
    plt.plot(phase_time, phase_data)
    
    plt.figure()
    plt.title('Fibre Stretcher Inteference Sim? {}'.format(filename))
    sinusoid = np.sin(phase_data)
    plt.plot(phase_time, sinusoid)

def dataLoggerProcess(curr_dir, filename, cyc=5, freq=2, rate=2000, display_time=False, display_avg=False, manual_offset=1, diff_trigger=0.5, roll=0, figname=''):
    """ Takes csv file downloaded from Moku:Pro and processes it

    Example(s):
        dataLoggerProcess("C:\\Users\\josh\\OneDrive - UWA\\UWA\\PhD\\3. Data\\Interference Data\\250122_Interference\\", "Interferometer250122_20250122_082257", cyc=5, freq=1, rate=1000, manual_offset=2, diff_trigger=0.5, roll=10, display_time=True, display_avg=True, figname="SNSPDs with modulated thorlabs")

    Args:
        curr_dir (str): Directory of file.
        filename (str): File name.
        cyc (int, optional): Number of cycles per itteration. Defaults to 5.
        freq (int, optional): Frequency of ramp. Defaults to 2.
        rate (int, optional): Sampling rate. Defaults to 2000.
        display_time (bool, optional): Optional additional time series display. Defaults to False.
        display_avg (bool, optional): Optional additional averaging display. Defaults to False.
        manual_offset (int, optional): Data point offset. Defaults to 1.
        diff_trigger (float, optional): Trigger point. Defaults to 0.5.
        roll (int, optional): Number of values to rolling average. Defaults to 0.
        figname (str, optional): Name of figure, if unnamed will use filename. Defaults to ''.
    """
    if figname=='': figname=filename

    inputA, inputB, inputC, None, time = mokuProDataLogger(curr_dir, filename, figname=figname)
    
    baseline_at_freq = np.sin(time*freq*np.pi*freq*cyc)
    avg_rate = int(rate/freq) # sample rate divided by the number of cycles (x2 because vpp cycle is up and down) times freq to tell how many samples is in one interference cycle
    time_averaged = np.linspace(0, 2*np.pi*cyc, avg_rate)

    if display_time:
        norm_factor = (np.max(inputA+inputB)-np.min(inputA+inputB))/2
        offset = np.average(inputA+inputB)/2
        plt.figure()
        plt.title('Interference Time Series {}'.format(figname))
        plt.plot(time, inputA)
        plt.plot(time, inputB)
        plt.plot(time, inputC*norm_factor+offset)
        plt.plot(time, baseline_at_freq*norm_factor+offset)
        plt.legend(['Input A', 'Input B', 'Ramp', 'Sinusoid @ {}Hz'.format(freq*cyc)])
        plt.xlabel('Time (s)')
        plt.ylabel('Signal Amplitude (V)')
    
    if display_avg:
        indecies = [5, 10]
        plt.figure()
        print(np.diff(inputC))
        subset_indecies = np.where(np.diff(inputC) > diff_trigger)[0] 
        print(subset_indecies)
        vis_A_set, vis_B_set = [], []
        for i in range(len(subset_indecies)-1):
            pdA = inputA[subset_indecies[i]+manual_offset:subset_indecies[i+1]]
            pdB = inputB[subset_indecies[i]+manual_offset:subset_indecies[i+1]]
            ramp = inputC[subset_indecies[i]+manual_offset:subset_indecies[i+1]]*5.43*2*np.pi # 5.43 cyc/V
            
            if roll > 0:
                pdA = tools.movingAverage(pdA, n=roll)
                pdB = tools.movingAverage(pdB, n=roll)
                ramp = tools.movingAverage(ramp, n=roll)  
                
            if i in indecies:
                plt.plot(ramp, pdA) # was *1000 for SNSPD counts
                plt.plot(ramp, pdB) # was *1000 for SNSPD counts
            vis_A_set.append(visTools.getTimeSeriesVisibility(pdA))
            vis_B_set.append(visTools.getTimeSeriesVisibility(pdB))
        vis_A_avg = np.average(vis_A_set)
        vis_B_avg = np.average(vis_B_set)
        print("Visibility avg - PD A={:.2f}, PD B={:.2f}".format(vis_A_avg, vis_B_avg))
        print("Visibility max - PD A={:.2f}, PD B={:.2f}".format(np.max(vis_A_set), np.max(vis_B_set)))
        print("Visibility min - PD A={:.2f}, PD B={:.2f}".format(np.min(vis_A_set), np.min(vis_B_set)))

        plt.title('Interference {} - vis$_A$:{:.1f}%, vis$_B$:{:.1f}%'.format(figname, vis_A_avg*100, vis_B_avg*100))
        plt.xlabel('Phase Applied') # Was "Ramp Voltage"
        plt.ylabel("PDs Voltage") # 'SNSPD counts per 10ms'
        
        plt.legend(['PD A - 1', 'PD B - 1', 'PD A - 2', 'PD B - 2', 'PD A @ 4', 'PD B @ 4', 'PD A @ 5', 'PD B @ 5'])

