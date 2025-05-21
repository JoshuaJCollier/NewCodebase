import re
import time
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import pickle
import pandas as pd

from mokuProControl import *
from kinesisMotorControl import *
from uITLA.uITLAControl import *
from myTools import movingAverage

def quit(moku=None, motor=None, laser=None):
    if moku != None: quitMoku(moku)
    if motor != None: quitMotor(motor)
    if laser != None: turnOffLaser(laser)

def getMidPoint(data):
    data[data < 1e3] = np.average(data)
    data[data > 2e6] = np.average(data)
    data = np.abs(data - np.average(data))
    total_len = len(data)
    data = movingAverage(data, int(len(data)/1000))
    return int(np.argmax(data)*(total_len/len(data)))

def menloDataRun(uITLA = False): 
    myLaser = turnOnLaser() if uITLA else None # chuck this at the beginning any time there is a laser
    
    first_pos = 0e-3
    last_pos = 6e-3
    integration_time = 1
    total_time = 10
    osc = initialisePersistMokuPro(integration_time=integration_time)
    motor = initialiseMotor("26003312")
    moveMotor(motor, pos=first_pos, acc=1e-3, max_vel=1e-3, delay=0)
    motor.wait_move()
    print('Moving')
    moveMotor(motor, pos=last_pos, acc=1e-3, max_vel=last_pos/total_time, delay=0) # position in m, time in s
    dataList = []
    start = time.perf_counter()
    while (time.perf_counter()-start) < total_time:
        #print('Start {}th at {}s'.format(i, time.perf_counter()-start))
        dataList.append(osc.get_data(wait_complete=True))
    print('Finished {}s'.format(time.perf_counter()-start))
    
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

def snspdMeasure(saving=False, filename=''):    
    m, tfa, osc = initialisePersistMokuPro()
    motor = initialiseMotor("26003312")
    
    osc.enable_rollmode(False)
    osc.set_timebase(-1, 0, max_length=16384)
    
    # Initialisation
    first_pos = 0e-3
    last_pos = 6e-3
    total_time = 1000
    dataList = []
    data1 = np.array([])
    data2 = np.array([])
    
    # Move and record data
    print('Returning to start...')
    moveMotor(motor, pos=first_pos, acc=1e-3, max_vel=1e-3, delay=0)
    motor.wait_move() # Move to start
    print('At start. Now moving...')
    moveMotor(motor, pos=last_pos, acc=1e-3, max_vel=last_pos/total_time, delay=0) # position in m, time in s
    pbar = tqdm(desc='Progress', total = total_time)
    start = time.perf_counter()
    while (time.perf_counter()-start) < total_time:
        start_itt = time.perf_counter()
        #print('Start {}th at {}s'.format(i, time.perf_counter()-start))
        dataList.append(osc.get_data(wait_complete=True))
        pbar.update(time.perf_counter()-start_itt)
    pbar.close()
    print('Finished {}s'.format(time.perf_counter()-start))
    
    # Process data
    for i in range(len(dataList)):
        a = np.array(dataList[i]['ch1'])
        b = np.array(dataList[i]['ch2'])
        data1 = np.concatenate((data1, a)) # CH3 (green)
        data2 = np.concatenate((data2, b)) # CH4 (yellow)
    
    ch3_offset, ch4_offset = 0, 0
    count_to_signal = 100e-6 # 100e-6 is for 100uV / count
    signal_buckets = 1e-2 # 10ms buckets
    data1 = np.round((data1+ch3_offset)/(count_to_signal*signal_buckets)).astype(int)
    data2 = np.round((data2+ch4_offset)/(count_to_signal*signal_buckets)).astype(int)
    
    #min_allowed, max_allowed = 0, 1e6
    #data1 = data1[(min_allowed<data1)&(data1<max_allowed)]
    #data2 = data2[(min_allowed<data2)&(data2<max_allowed)]
    
    length = np.min([len(data1), len(data2)])
    averaging_no = int((length/total_time)*signal_buckets / 5) # total number of points / total time = data rate -> data rate * signal buckets = number of points that should be around the same, the 5 is just an extra offset value
    print('Averaging: {} points (from {} total points)'.format(averaging_no, len(data1)))
    
    dividable_len = int(length//averaging_no * averaging_no)
    data1 = np.average(data1[0:dividable_len].reshape(-1, averaging_no), axis=1)
    data2 = np.average(data2[0:dividable_len].reshape(-1, averaging_no), axis=1)
    
    length = np.min([len(data1), len(data2)])
    print('Final len: {}'.format(length))
    positions = np.linspace(first_pos, last_pos, length)*2e3 # Converted to mm path length added
    
    mid = getMidPoint(data1) #TODO: should probably change this to a rolling average
    positions = positions - positions[mid] # Finding the fringe peak
    
    osc.enable_rollmode(True)
    quit(moku=osc, motor=motor)
    
    if saving:
        #dbfile = open('{}.pkl'.format(filename), 'ab')
        #pickle.dump({'Outputs1':data1, 'Outputs2':data2, 'Positions':positions}, dbfile)
        all_outs = np.array([data1, data2, positions]).T
        headers = ['Output1', 'Output2', 'Positions']
        df = pd.DataFrame(all_outs, columns=headers)
        df.to_csv('{}.csv'.format(filename), header=True, sep=',')
    
    print('Plotting')
    plt.figure(0)
    plt.plot(positions, data1[:length], label='SNSPD 1') # the x2 for all these is because the beam is reflected
    plt.plot(positions, data2[:length], label='SNSPD 2')
    plt.xlabel('Path length difference')
    plt.ylabel('Counts')
    plt.title('Counts vs Position')
    plt.ylim([0, 2e6])
    plt.legend()
    plt.show()


snspdMeasure(saving=False, filename='testing')