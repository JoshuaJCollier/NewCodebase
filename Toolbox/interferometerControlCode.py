
# --- Imports ---
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import pandas as pd
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

# --- Internal imporst ---
from mokuProControl import *
from kinesisMotorControl import *
from uITLA.uITLAControl import *
from saving import *
from generalTools import movingAverage, findNearest
from visibilityTools import getVisibility

def quit(moku=None, motor=None, laser=None):
    """ Quits all provided devices

    Args:
        moku (_type_, optional): Moku object (from Moku:Pro). Defaults to None.
        motor (_type_, optional): Motor object (from Kinesis motor / KCube). Defaults to None.
        laser (_type_, optional): Laser object (from uITLA). Defaults to None.
    """
    if moku != None: quitMoku(moku)
    if motor != None: quitMotor(motor)
    if laser != None: turnOffLaser(laser)

def removeOutliers(data1, data2, exclusion=0.5):
    """ Removes outlier values from a pair of outputs (both sides of the output) from an interferometer

    Args:
        data1 (arr): Array of data out from an interferometer
        data2 (arr): Array of data out from the other arm of the interferometer
        exclusion (float, optional): Percentage buffer around the mean to not count as outliers (this should be able to be low). Defaults to 0.5.

    Returns:
        tuple: Both data outputs without their outliers, and also the middle point in the interference
    """
    data_sum = data1 + data2
    avg_tot = np.average(data_sum)
    
    avg1 = np.average(data1)
    data1[data_sum < avg_tot*(1-exclusion)] = avg1
    data1[data_sum > avg_tot*(1+exclusion)] = avg1
    
    avg2 = np.average(data2)
    data2[data_sum < avg_tot*(1-exclusion)] = avg2
    data2[data_sum > avg_tot*(1+exclusion)] = avg2

    data_mid = data1
    data_mid = np.abs(data1 - np.average(data1))
    total_len = len(data_mid)
    data_mid = movingAverage(data_mid, int(len(data_mid)/1000))
    mid = int(np.argmax(data_mid)*(total_len/len(data_mid)))
    return data1, data2, mid

def findVis(data, sigma=3):
    """ Find peaks and troughs of data set and then find the visibility from these

    Args:
        data (array): Data that you want to process

    Returns:
        tuple: Visibility, and the values used to get it
    """
    slc = gaussian_filter1d(data, sigma=sigma) # filter the peaks the remove noise,
    peaks = find_peaks(slc)[0] # [0] returns only locations 
    troughs = find_peaks(-slc)[0] # [0] returns only locations 

    max_pos = slc[peaks].argmax() # index of peaks that gives the index with the peak (very confusing I know)
    min_pos = findNearest(troughs, peaks[max_pos])
    
    max_val = data[peaks[max_pos]]
    
    if troughs[min_pos] > peaks[max_pos]:
        min_val = (data[troughs[min_pos]] + data[troughs[min_pos-1]])/2
        used_vals = [troughs[min_pos-1], peaks[max_pos], troughs[min_pos]]
    else:
        min_val = (data[troughs[min_pos]] + data[troughs[min_pos+1]])/2
        used_vals = [troughs[min_pos], peaks[max_pos], troughs[min_pos+1]]

    visibility = np.abs(getVisibility(max_val, min_val))
    return visibility, used_vals
        
def menloDataRun(uITLA = False, first_pos=0e-3, last_pos=6e-3, integration_time=1, total_time=10): 
    # Initialise used devices
    myLaser = turnOnLaser() if uITLA else None # chuck this at the beginning any time there is a laser
    osc = initialiseMokuProOsc(integration_time=integration_time)
    motor = initialiseMotor("26003312")

    # Move to start position
    moveMotor(motor, pos=first_pos, acc=1e-3, max_vel=1e-3, delay=0)
    motor.wait_move()

    # Move to end position
    moveMotor(motor, pos=last_pos, acc=1e-3, max_vel=last_pos/total_time, delay=0) # position in m, time in s
    dataList = []
    start = time.perf_counter()
    while (time.perf_counter()-start) < total_time:
        dataList.append(osc.get_data(wait_complete=True))
    
    data1 = np.array([])
    data2 = np.array([])
    for i in range(len(dataList)):
        a = np.array(dataList[i]['ch3'])
        b = np.array(dataList[i]['ch4'])
        a, b = a[(-0.003<a)&(a<2)], b[(-0.003<b)&(b<2)]
        data1 = np.concatenate((data1, a)) # CH3 (green)
        data2 = np.concatenate((data2, b)) # CH4 (yellow)
    
    scaling = 1 # data1[0]/data2[0]
    ch3_offset, ch4_offset = 0.0021, 0.0011
    positions1 = np.linspace(first_pos, last_pos, len(data1))
    positions2 = np.linspace(first_pos, last_pos, len(data2))
    data1 = data1+ch3_offset
    data2 = data2+ch4_offset
    length = np.min([len(data1), len(data2)])
    
    diff = 0
    if np.average(data1) > np.average(data2):
        diff = data1[:length]-data2[:length]
    else:
        diff = data2[:length]-data1[:length]

    quit(moku=osc, motor=motor, laser=myLaser)

    plt.figure(0)
    plt.plot(positions1*2e3, data1, label='Output 1') # the x2 for all these is because the beam is reflected
    plt.plot(positions2*2e3, data2, label='Output 2')
    #plt.plot(positions2*2e3, diff, label='Output1 - Output2')
    #plt.plot((0.0001*times+start_pos)*2, outputs1/window_len, label='Output 1 - time*speed')
    #plt.plot((0.0001*times+start_pos)*2, outputs2/window_len, label='Output 2 - time*speed')
    plt.xlabel('Path length addition (mm)')
    plt.ylabel('Voltage (V)')
    plt.title('Voltage vs Position')
    plt.ylim([0, np.max([np.max(data1), np.max(data2)])*1.1])
    plt.legend()
    plt.show()
    
    print('Plot finished')

def snspdMeasure(window_length=1e-3, saving=False, source_size='200um', dist='60mm', baseline='127um'):    
    m, tfa, osc = initialisePersistMokuPro(window_length=window_length)
    motor = initialiseMotor("26003312")
    
    osc.enable_rollmode(False)
    osc.set_timebase(-1, 0, max_length=16384)
    
    # Initialisation
    first_pos = 2.5e-3
    last_pos = 3.5e-3
    total_time = 1000
    dataList = []
    #motorPos = []
    #times = []
    data1 = np.array([])
    data2 = np.array([])
    
    # Move and record data
    print('Returning to start...')
    moveMotor(motor, pos=first_pos, acc=1e-3, max_vel=1e-3, delay=0)
    motor.wait_move() # Move to start
    #last_time = getMotorPos(motor)
    print('At start. Now moving...')
    moveMotor(motor, pos=last_pos, acc=1e-3, max_vel=(last_pos-first_pos)/total_time, delay=0) # position in m, time in s
    pbar = tqdm(desc='Progress', total = total_time)
    start = time.perf_counter()
    while (time.perf_counter()-start) < total_time:
        start_itt = time.perf_counter()
        #print('Start {}th at {}s'.format(i, time.perf_counter()-start))
        dataList.append(osc.get_data(wait_complete=True)) # WAS TRUE
        #curr_motor_pos = getMotorPos(motor)
        #motorPos.append(curr_motor_pos-last_time)
        instance_time = time.perf_counter()-start_itt
        #times.append(instance_time)
        pbar.update(instance_time)
    pbar.close()
    print('Finished motor pos = {:.3f}mm'.format(getMotorPos(motor)*1e3))
    print('Finished {}s'.format(time.perf_counter()-start))
    
    # Process data
    for i in range(len(dataList)):
        data1 = np.concatenate((data1, np.array(dataList[i]['ch1']))) # CH1 
        data2 = np.concatenate((data2, np.array(dataList[i]['ch2']))) # CH2
    
    if len(data1) > len(data2): data1 = data1[:len(data2)] # Find the shortest one and make that the standard
    else: data2 = data2[:len(data1)]
        
    ch3_offset, ch4_offset = 0, 0
    count_to_signal = 100e-6 # 100e-6 is for 100uV / count
    snspd_integration_time = window_length # 10ms buckets
    data1 = np.round((data1+ch3_offset)/(count_to_signal*snspd_integration_time)).astype(int)
    data2 = np.round((data2+ch4_offset)/(count_to_signal*snspd_integration_time)).astype(int)
    
    #min_allowed, max_allowed = 0, 1e6
    #data1 = data1[(min_allowed<data1)&(data1<max_allowed)]
    #data2 = data2[(min_allowed<data2)&(data2<max_allowed)]
    
    # total number of points / total time = data rate -> data rate * signal buckets = number of points that should be around the same, the 5 is just an extra offset value
    averaging_no = int((len(data1)/total_time)*snspd_integration_time / 5) 
    print('Averaging: {} points (from {} total points)'.format(averaging_no, len(data1)))
    
    dividable_len = int(len(data1)//averaging_no * averaging_no)
    data1 = np.average(data1[0:dividable_len].reshape(-1, averaging_no), axis=1)
    data2 = np.average(data2[0:dividable_len].reshape(-1, averaging_no), axis=1)
    
    modified_data1, modified_data2, mid_index = removeOutliers(data1, data2, exclusion=0.3)
    data1_vis, valsUsed1 = findVis(modified_data1, sigma=10)
    data2_vis, valsUsed2 = findVis(modified_data2, sigma=10)
    vis = np.max([data1_vis, data2_vis])
    
    print('Visibility from data1: {}, from data2: {}'.format(data1_vis, data2_vis))
    #measured_pos = np.array(motorPos)
    #pos_step = measured_pos[1:] - measured_pos[:-1]
    #pos_step = np.insert(pos_step, 0, measured_pos[0])
    #positions = pos_step / np.array(times) * (1000 / len(measured_pos)) # gives m / s, which is then normalised to 1000s in n steps
    #positions = positions*2*(10**3)
    
    #plt.plot(times, positions)
    #plt.show()
    
    positions = np.linspace(first_pos, last_pos, len(data1))*2e3 # Converted to mm path length added
    positions = positions - positions[mid_index] # Finding the fringe peak
    
    osc.enable_rollmode(True)
    quit(moku=osc, motor=motor)
    
    plot_params = "plt.setp(plt.gca(), xlabel='Path length difference (mm)', ylabel='Counts', ylim=[0, 1e6], title='Counts vs Position (outliers removed)')"
    if saving:
        all_outs = np.array([data1, data2, positions]).T
        headers = ['Output1 (cnt)', 'Output2 (cnt)', 'Positions (mm)']
        df = pd.DataFrame(all_outs, columns=headers) #df.to_csv('{}.csv'.format(filename), header=True, sep=',')
        metadata = generateMetadata('LED', source_size, dist, baseline, pol=0, parts={}, 
                                    params = {'plot params':plot_params, 'snspd integration (s)':snspd_integration_time, 'volt per count':count_to_signal, 
                                              'moku inputs':'DC 1Mohm 400mVpp', 'measured vis':{'ch1':float(data1_vis),'ch2':float(data2_vis)}, 
                                              'data runtime':total_time, 'data length':len(data1), 'start pos (m)': first_pos,
                                              'end pos(m)': last_pos})
        save('interferometer', df, metadata)
    
    print('Plotting')
    plt.figure(0)
    plt.plot(positions, modified_data1, label='SNSPD 1') # the x2 for all these is because the beam is reflected
    plt.plot(positions, modified_data2, label='SNSPD 2')
    plt.plot(positions[valsUsed1], data1[valsUsed1], marker='o', label='Vals Used 1')
    plt.plot(positions[valsUsed2], data2[valsUsed2], marker='o', label='Vals Used 2')
    plt.setp(plt.gca(), xlabel='Path length difference (mm)', ylabel='Counts', ylim=[0, 1e6], title='Counts vs Position (outliers removed)')
    #plt.xlabel('Path length difference')
    #plt.ylabel('Counts')
    #plt.title('Counts vs Position (outliers removed)')
    #plt.ylim([0, 1e6])
    plt.legend()
    plt.show()

def testingLoad(campaign, index):
    df, metadata = load(campaign, index)
    
    data1 = np.array(df['Output1 (cnt)'])
    data2 = np.array(df['Output2 (cnt)'])
    positions = np.array(df['Positions (mm)'])
    data1, data2, mid_index = removeOutliers(data1, data2, exclusion=0.3)
    positions = positions - positions[mid_index]
    data1_vis, valsUsed1 = findVis(data1, sigma=10)
    data2_vis, valsUsed2 = findVis(data2, sigma=10)
    
    print('Visibilities: {:.2f}%, {:.2f}%'.format(data1_vis*100, data2_vis*100))
    print('Plotting')
    plt.figure(0)
    
    #plt.plot(positions, gaussian_filter1d(data1, sigma=1), label='SNSPD 1 smoothed') # the x2 for all these is because the beam is reflected
    plt.plot(positions, data1, label='SNSPD 1') # the x2 for all these is because the beam is reflected
    plt.plot(positions, data2, label='SNSPD 2')
    plt.plot(positions[valsUsed1], data1[valsUsed1], marker='o', label='Vals Used 1')
    plt.plot(positions[valsUsed2], data2[valsUsed2], marker='o', label='Vals Used 2')
    plt.setp(plt.gca(), xlabel='Path length difference', ylabel='Counts', ylim=[0, 1e6], title='Counts vs Position (outliers removed)')
    plt.legend()
    plt.show()
    
#testingLoad('interferometer', 12)

snspdMeasure(window_length=1e-2, saving=True, source_size='1000um', baseline='127um')