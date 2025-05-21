import uITLA.uITLAFunctions as uITLAFunctions

def turnOnLaser(power=13.5, wavelength=1552, verbose=False):
    laser = uITLAFunctions.ITLA('COM3',verbose=True)
    if verbose: print('Connected')

    if verbose: print(f'Temp: {laser.get_temperature()}')

    if verbose: print('Setting power to {power}')
    laser.set_power_dBm(power)

    if verbose: print('Setting frequency to {}THz (wavelength {}nm)'.format(3*10**8/(wavelength*10**3), wavelength))
    laser.set_wavelength_nm(wavelength)

    if verbose: print('Turning on')
    laser.turn_on()
    
    print('Laser on')

    return laser

def turnOffLaser(laser, verbose=False):
    if verbose: print('Turning off')
    laser.turn_off()

    if verbose: print('Disconnecting')
    laser.disconnect()

    print('Laser off')

def simpleLaserRun():
    myLaser = turnOnLaser()
    input('Press enter to turn off laser')
    turnOffLaser(myLaser)
    
#simpleLaserRun()