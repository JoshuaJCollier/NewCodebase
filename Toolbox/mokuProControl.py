from moku.instruments import MultiInstrument, TimeFrequencyAnalyzer, WaveformGenerator, Oscilloscope, Datalogger

# Just oscilliscope
def initialiseMokuProOsc(ip='10.42.0.55', integration_time = 1):
    osc = Oscilloscope(ip, force_connect=True, platform_id=4)
    print('Connected')
    osc.set_frontend(3, impedance="50Ohm", coupling="DC", range='400mVpp') # input from SNSPD for TFA direct
    osc.set_frontend(4, impedance="50Ohm", coupling="DC", range='400mVpp') # input from SNSPD for TFA direct
    print('Frontend set')
    osc.set_acquisition_mode(mode='Precision')
    osc.set_timebase(-integration_time, 0, max_length=16384)
    print('Timebase set')
    print('Current sample rate: {}Sa/s'.format(osc.get_samplerate()['sample_rate']))
    print(osc.get_timebase())
    #osc.set_trigger(source='External', level=1e-3)
    return osc

# Persist from current state (so that the TFA can pass counts to the osc, this isnt possible without persist)
def initialisePersistMokuPro(window_length=1e-3):
    m = MultiInstrument(ip='10.42.0.55', force_connect=True, platform_id=4, persist_state=True)
    tfa = m.set_instrument(1, TimeFrequencyAnalyzer)
    osc = m.set_instrument(2, Oscilloscope) 
    
    #connections = [dict(source="Input1", destination="Slot1InA"),
    #            dict(source="Input2", destination="Slot1InB"),
    #            dict(source="Slot1OutA", destination="Slot2InA"),
    #            dict(source="Slot1OutB", destination="Slot2InB"),
    #            dict(source="Slot2OutA", destination="Output4")]
    #m.set_connections(connections=connections)
    #m.set_output(4, "14dB")
    m.set_frontend(1, impedance="1MOhm", coupling="DC", attenuation='0dB') # input from SNSPD for MIM
    m.set_frontend(2, impedance="1MOhm", coupling="DC", attenuation='0dB') # input from SNSPD for MIM
    
    tfa.set_acquisition_mode('Windowed', window_length=window_length)
    osc.set_acquisition_mode(mode='Precision')
    
    #wg.generate_waveform(1, "Ramp", amplitude=1, frequency=1, offset=0.5, symmetry=0)
    
    return m, tfa, osc

def quitMoku(moku):
    moku.relinquish_ownership()