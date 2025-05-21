from pylablib.devices import Thorlabs

def initialiseMotor(serial_no='', verbose=False):
    device = 0
    if serial_no == '':
        allDevices= Thorlabs.list_kinesis_devices()
        print(allDevices)
        device = Thorlabs.KinesisMotor(allDevices[0][0], is_rack_system=False)
    else:
        device = Thorlabs.KinesisMotor(serial_no, is_rack_system=False)
    device.home()
    device.wait_for_home()    
    #print('Settings:', device.get_settings())
    #step_size = int(re.findall(r"step_size=(\d*)",str(step))[0])
    if verbose: 
        print('Homed')
        step_size = device.get_jog_parameters()[1]
        min_vel, acc, max_vel = device.get_velocity_parameters()
        scaling = 1e-4/step_size
        print('Device step: {}, acc: {:.4f} mm/s^2, min-vel: {:.4f} mm/s, max-vel: {:.4f} mm/s'.format(step_size, acc*scaling*1e3, min_vel*scaling*1e3, max_vel*scaling*1e3))
    
    return device

def moveMotor(device, pos, acc=0, max_vel=0, delay=0, verbose=False): # all in m
    # Getting current pos
    step_size = device.get_jog_parameters()[1]
    #step_size = int(re.findall(r"step_size=(\d*)",str(device.get_device_variable('jog_parameters')))[0])
    displacement_per_step = 1e-4/step_size
    if verbose:
        print('Start position: {:.5f} mm'.format(device.get_position()*1e3*displacement_per_step))
        print('Moving in {}ms'.format(delay))

    # Setting parameters
    if (acc != 0) and (max_vel != 0):
        device.setup_velocity(acceleration = acc/(displacement_per_step), max_velocity=max_vel/(displacement_per_step))
        device.setup_jog(acceleration = acc/(displacement_per_step), max_velocity=max_vel/(displacement_per_step))
        
        if verbose:
            min_vel, acc, max_vel = device.get_velocity_parameters()
            scaling = 1e-4/step_size # to m
            print('Device step: {}, acc: {:.4f} mm/s^2, min-vel: {:.4f} mm/s, max-vel: {:.4f} mm/s'.format(step_size, acc*scaling*1e3, min_vel*scaling*1e3, max_vel*scaling*1e3))
    
    # Moving
    device.move_to((pos)/displacement_per_step)

def getMotorPos(device, verbose=False):
    displacement_per_step = 1e-4/device.get_jog_parameters()[1] # 1e-4 is converting to m I think
    pos_in_m = device.get_position()*displacement_per_step
    if verbose: print('Position: {:.5f} mm'.format(pos_in_m*1e3))
    return pos_in_m

def motorBackAndForth(start=0e-3, end=6e-3, speed=0.004e-3):
    motor = initialiseMotor("26003312")
    var = True
    count = 0
    while var:
        moveMotor(motor, pos=start, acc=1e-3, max_vel=speed, delay=0)
        motor.wait_move()
        moveMotor(motor, pos=end, acc=1e-3, max_vel=speed, delay=0) # position in m, time in s
        motor.wait_move()
        count += 1
        print('Count: {}'.format(count))
        if count > 100:
            var = False
    
    quitMotor(motor)

def quitMotor(motor): # just making all quit functions consistent
    motor.close()