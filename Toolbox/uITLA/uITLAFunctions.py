
import time
import struct
import os
import os.path
import sys
import threading
import serial

# ERROR CODES
ITLA_NOERROR=0x00
ITLA_EXERROR=0x01
ITLA_AEERROR=0x02
ITLA_CPERROR=0x03
ITLA_NRERROR=0x04
ITLA_CSERROR=0x05
ITLA_ERROR_SERPORT=0x01
ITLA_ERROR_SERBAUD=0x02

# REGISTER ADDRESSES
REG_Nop=0x00            # (read only) NOP / status
REG_Devtyp=0x01         # (read only, AEA) device type
REG_Mfgr=0x02           # (read only, AEA) manufacturer
REG_Model=0x03          # (read only, AEA) model ID
REG_Serial=0x04         # (read_only, AEA) serial number
REG_Release=0x06        # (read only, AEA) release info
REG_Gencfg=0x08         # general module configuration
REG_AeaEar=0x0B         # location accessed through AEA-EA and AEA-EAC
REG_Iocap=0x0D          # IO Capabilities
REG_Ear=0x10            # Location accessed through EA and EAC
REG_Dlconfig=0x14       # download configuration
REG_Dlstatus=0x15       # (read only) Download status
REG_Fpow=0x22           # threshold for output power FATAL condition
REG_Wpow=0x23           # threshold for output power warning condition
REG_Ffreq=0x24          # threshold for frequency FATAL condition
REG_Wfreq=0x25          # threshold for frequency warning condition
REG_Channel=0x30        # channel set-point
REG_Power=0x31          # power set point
REG_Resena=0x32         # device enable
REG_Grid=0x34           # grid
REG_Fcf1=0x35           # first channel frequency (THz part)
REG_Fcf2=0x36           # first channel frequency (GHz part)
REG_Oop=0x42            # (read only) optical output power
REG_Ctemp=0x43          # (read only) laser temperature (unsure if i have access)
REG_Opsl=0x50           # (read only) power lower limit device capability
REG_Opsh=0x51           # (read only) power upper limit device capability
REG_Lfl1=0x52           # (read only) frequency lower limit device capability (THz part)
REG_Lfl2=0x53           # (read only) frequency lower limit device capability (GHz*10)
REG_Lfh1=0x54           # (read only) frequency upper limit device capability (THz part)
REG_Lfh2=0x55           # (read only) frequency upper limit device capability (GHz*10)
REG_Currents=0x57       # (read only, AEA) device currents
REG_Temps=0x58          # (read only, AEA) device temperatures (gain chip & case)
REG_Ftf=0x62            # fine tune frequency
REG_Mode=0x90           # select low noise mode
                        #   0: standard operation (with dither signal)
                        #   1: no-dither operation
                        #   2: whisper-mode operation
REG_PW=0xE0             # password to enable laser
                        #   W: provide password to the laser
                        #   R: provide 16 bit integer that will help Pure Photonics to calculate the password for you
REG_Csweepsena=0xE5     # (write only) start or stop the clean sweep feature
                        #   0: stop
                        #   1: start
REG_Csweepamp=0xE4      # range for the clean sweep feature in GHz
REG_Cscanamp=0xE4
REG_Cscanon=0xE5
REG_Csweepon=0xE5
REG_Csweepoffset=0xE6   # provide the offset during the clean sweep in units of 0.1 GHz with an offset of 200 GHz
                        # calculate the offset as: (read-out -2000) * 0.1 GHz
REG_Cscanoffset=0xE6
REG_Cscansled=0xF0
REG_Cscanf1=0xF1
REG_Cscanf2=0xF2
REG_CjumpTHz=0xEA
REG_CjumpGHz=0xEB
REG_CjumpSled=0xEC
REG_Cjumpon=0xED
REG_Cjumpoffset=0xE6

# OPERATING MODES
MODE_Standard = 0
MODE_Nodither = 1
MODE_Whisper = 2

# CONSTANTS
READ = 0
WRITE = 1

# ERROR MESSAGES
error_messages = {
    '0' : 'OK flag (normal return status)',
    '1' : 'XE flag (execution error)',
    '2' : 'AEA flag (automatic extended addressing result being returned or ready to write)',
    '3' : 'CP flag (command not complete, pending)'
}

class ITLA:
    def __init__(self,port,baudrate=9600,verbose=True):
        self.latestregister=0
        self.tempport=0
        self.raybin=0
        self.queue=[]
        self.maxrowticket=0
        self._error=ITLA_NOERROR
        self.seriallock=0
        self.conn = []
        self.verbose = False

        self.connect(port,baudrate)

        self.max_power = self.get_max_power()
        self.min_power = self.get_min_power()

        self.verbose = verbose

# Connect and disconnect
    def connect(self,port: str,baudrate=9600):
        '''
        Function:
            Establish serial connection with the ITLA at the maximum possible baud rate
        Inputs:
            Port to connect, initial baud rate
        Outputs:
            Errors if present
        '''
        reftime=time.process_time()
        self.conn = serial.Serial(port,baudrate, timeout=1)

        baudrate2=4800
        while baudrate2<115200:
            self.ITLA(REG_Nop,0,0)
            if self.last_error() != ITLA_NOERROR:
                #go to next baudrate
                if baudrate2==4800:baudrate2=9600
                elif baudrate2==9600: baudrate2=19200
                elif baudrate2==19200: baudrate2=38400
                elif baudrate2==38400:baudrate2=57600
                elif baudrate2==57600:baudrate2=115200
                self.conn.close()
                self.conn = serial.Serial(port,baudrate2 , timeout=1)            
            else:
                return
        self.conn.close()
        return(ITLA_ERROR_SERBAUD)
    
    def disconnect(self) -> None:
        '''
        Function:
            Close the serial connection with the ITLA
        '''
        self.conn.close()
    
    
# Basic operations
    def stripString(self,input):
        outp=''
        input=str(input)
        teller=0
        while teller<len(input) and ord(input[teller])>47:
            outp=outp+input[teller]
            teller=teller+1
        return(outp)

    def last_error(self) -> int:
        return(self._error)

    def SerialLock(self):
        return self.seriallock

    def SerialLockSet(self):
        self.seriallock
        self.queue
        self.seriallock=1
        
    def SerialLockUnSet(self):
        self.seriallock
        self.queue
        self.seriallock=0
        self.queue.pop(0)
    
    def serial_number(self):
        register = REG_Serial
        return self.ITLA(register,0,READ)

    def wait_until_no_operation(self):
        '''
        Function:
            Monitor the NOP register and halt operations until it is clear
        Returns:
            NOP register
        '''
        register = REG_Nop
        data = []
        
        while data != 16:
            print('\nWaiting for operation to complete')
            time.sleep(5)
            data = self.ITLA(register,0,0)
        print('\nOperation completed')
        return data
        
# Transmitting and receiving methods
    def checksum(self,byte0,byte1,byte2,byte3):
        '''
        Function:
            Compute the checksum for error detection
        Inputs:
            Bytes being prepared to be passed to the serial connection
        Outputs:
            Checksum bit        
        '''
        bip8=(byte0&0x0f)^byte1^byte2^byte3   # & means AND, ^ means XOR
        bip4=((bip8&0xf0)>>4)^(bip8&0x0f)     # >> moves bits to the left, << moves to the right
        return bip4
        
    def send_command(self,byte0,byte1,byte2,byte3) -> None:  # these are all ints
        '''
        Function:
            Send data to the ITLA
        Inputs:
            Four bytes
        '''
        msg = bytearray([byte0,byte1,byte2,byte3])
        self.conn.write(msg)

    def receive_response(self):
        '''
        Function:
            Receives a response from the ITLA
        Outputs:
            Four bytes
        '''
        reftime=time.process_time()
        while self.conn.inWaiting()<4:
            if time.process_time()>reftime+0.25:
                _error=ITLA_NRERROR
                return(0xFF,0xFF,0xFF,0xFF)
            time.sleep(0.0001)
        try:
            byte0=ord(self.conn.read(1))
            byte1=ord(self.conn.read(1))
            byte2=ord(self.conn.read(1))
            byte3=ord(self.conn.read(1))
        except:
            print(f'problem with serial communication. queue[0] = {self.queue}')
            byte0=0xFF
            byte1=0xFF
            byte2=0xFF
            byte3=0xFF
        if self.checksum(byte0,byte1,byte2,byte3)==byte0>>4:
            self._error=byte0&0x03
            return(byte0,byte1,byte2,byte3)
        else:
            self._error=ITLA_CSERROR
            return(byte0,byte1,byte2,byte3)

    def decode_response(self,response):
        '''
        Function:
            Decode the response sent by the ITLA
        Inputs:
            4-byte string sent from the ITLA
        Outputs:
            Data bits returned from the ITLA
        '''
        byte0 = response[0]
        byte1 = response[1]
        byte2 = response[2]
        byte3 = response[3]
        error_message = byte0 & 3  # extract bits 25 and 24
        if self.verbose:
            print('\nReceived')
            print(f'byte0: {hex(byte0)}, byte1: {hex(byte1)}, byte2: {hex(byte2)}, byte3: {hex(byte3)}')

        if error_message == 1: # execution error
            print('Execution Error. Disconnected.')
            self.turn_off()
            self.disconnect()
            
        return 256*byte2 + byte3   

    def ITLA(self,register: int,data: int,rw: int):
        '''
        Function:
            Prepare and send data to the ITLA
        Inputs:
            register address, data, read/write
        Outputs:
            The data returned by the ITLA (last two bytes)
        '''
        lock=threading.Lock()
        lock.acquire()
        rowticket=self.maxrowticket+1
        self.maxrowticket=self.maxrowticket+1
        self.queue.append(rowticket)
        lock.release()
        while self.queue[0] != rowticket:
            rowticket=rowticket
        if rw==0: # read
            byte2=int(data/256) # take the integer (0-65355) and extract the top two bits in hexidecimal
            byte3=int(data-byte2*256) # extract the last two hexidecimal bits of the integer
            byte0 = int(self.checksum(0,register,byte2,byte3))*16 # checksum for error calculations
            self.latestregister=register
            if self.verbose:
                print('\nWriting the following command:')
                print(f'byte0: {hex(byte0)}, byte1: {hex(register)}, byte2: {hex(byte2)}, byte3: {hex(byte3)}')
            self.send_command(byte0,register,byte2,byte3)
            response = self.receive_response()
            self.decode_response(response)
            b0 = response[0]
            b1 = response[1]
            b2 = response[2]
            b3 = response[3]
            if (b0&0x03)==0x02: # check if bits 24 and 25 are 0x02 (flag for AEA)
                response=self.AEA(b2*256+b3)
                if self.verbose:
                    print(f'\nVerbose string: {response}')
                lock.acquire()
                self.queue.pop(0)
                lock.release()
                return response
            lock.acquire()
            self.queue.pop(0)
            lock.release()
            return 256*b2 + b3
        else: # write
            byte2=int(data/256)
            byte3=int(data-byte2*256)
            byte0 = int(self.checksum(1,register,byte2,byte3))*16+1
            if self.verbose:
                print('\nWriting the following command:')
                print(f'byte0: {hex(byte0)}, byte1: {hex(register)}, byte2: {hex(byte2)}, byte3: {hex(byte3)}')
            self.send_command(byte0,register,byte2,byte3)
            response = self.receive_response()
            self.decode_response(response)
            lock.acquire()
            self.queue.pop(0)
            lock.release()
            return 256*response[2] + response[3]
            
    def AEA(self,bytes: int) -> str:
        '''
        Function:
            During automatic extended addressing, the data is stored in 
            register REG_AeaEar and the data is extracted serially as a
            string
        Inputs: 
            Number of bytes
        Outputs:
            String of data pulled from AEA register
        '''
        outp=''
        while bytes>0: # bytes is the number of bytes to pull from the register, it is not the information itself
            self.send_command(int(self.checksum(0,REG_AeaEar,0,0))*16,REG_AeaEar,0,0) # pull from AEA register
            test=self.receive_response()
            outp = outp + chr(test[2]) # record the data bits of the pull as a string and concatenate
            outp = outp + chr(test[3])
            bytes = bytes - 2 # decrement the bytes remaining by two
        return outp

# Laser characteristic methods
    def set_power_dBm(self,power: int):
        '''
        Function:
            Set the power of the laser in dBm
        Inputs:
            Power in dBm
        '''
        data = 100*power  # data to send to the laser
        register = REG_Power
        if data >= self.min_power and data <= self.max_power: # check if power is in allowed range
            self.ITLA(register,data,WRITE)
            return
        raise RuntimeError('Invalid choice for power %s dBm' % power)

    def get_power_dBm(self):
        '''
        Function:
            Return the laser diode set power in dBm
        Outputs:
            Set laser diode power
        '''
        register = REG_Power
        return self.ITLA(register,0,READ)/100

    
    def set_wavelength_nm(self,wavelength: float) -> None:
        '''
        Function:
            Set the laser wavelength
        Inputs:
            Wavelength (in nm)
        '''
        self.set_frequency_THz(3e5/wavelength)

    def get_wavelength_nm(self) -> float:
        '''
        Function:
            Get the laser wavelength 
        Outputs:
            Laser frequency (in nm)
        '''
        return 3e5/self.get_frequency_THz()
    
    def set_frequency_THz(self,frequency: float) -> None:
        '''
        Function:
            Set the laser frequency 
        Inputs:
            Frequency (in THz)
        '''
        if frequency <= 196.25 and frequency >= 191.5:
            # frequency is divided into two registers, one to record the 
            # THZ component and one to record the GHz component, the THz
            # is set by an integer corresponding to the number of THZ 
            # but the GHz component is 10 * GHz. e.g. If the frequency is
            # 193.4873, 193 should be written to the THz register and 
            # 4873 to the GHz register 

            THz_register = REG_Fcf1
            GHz_register = REG_Fcf2
            data_THz = int(frequency)
            data_GHz = int(10000*(frequency-data_THz))
            self.ITLA(THz_register,data_THz,WRITE)
            self.ITLA(GHz_register,data_GHz,WRITE)
            return
        raise RuntimeError('Invalid choice for frequency : %s' % frequency)

    def get_frequency_THz(self) -> float:
        '''
        Function:
            Return the frequency of the laser in THz
        Outputs:
            Frequency of the laser in THz
        '''
        THz_register = REG_Fcf1
        GHz_register = REG_Fcf2
        data_THz = self.ITLA(THz_register,0,READ)
        data_GHz = self.ITLA(GHz_register,0,READ)
        return data_THz + data_GHz/10000      
        
    def get_temperature(self) -> int:
        '''
        Function:
            Return the current temperature (monitored by the temperature alarm
            encoded as deg(C)*100)
        Outputs:
            Current temperature
        '''
        register = REG_Ctemp
        return self.ITLA(register,0,READ)
    
    def get_max_power(self) -> int:
        '''
        Function:
            Return the maximum allowed temperature
        Outputs:
            Maximum output power in 100*dBm
        '''
        register = REG_Opsh
        return self.ITLA(register,0,READ)

    def cleanMode(self, mode :int):
        '''
        Function:
            Change between dither mode and whisper mode.
        Inputs:
            Mode: 0 = Dither, 1 or 2 = Whisper'''
        register = REG_Mode
        if mode in [MODE_Standard, MODE_Nodither, MODE_Whisper]:
            self.ITLA(register,mode,WRITE)
            return
        raise RuntimeError('Invalid choice for mode: %s' % mode)
    
    def get_min_power(self) -> int:
        '''
        Function:
            Return the minimum allowed temperature
        Outputs:
            Minimum output power in 100*dBm
        '''
        register = REG_Opsl
        return self.ITLA(register,0,READ)
    
    def turn_on(self) -> None:
        '''
        Function:
            Turn on the laser diode
        '''
        register = REG_Resena
        data = 8
        self.ITLA(register,data,WRITE)
        self.wait_until_no_operation() # laser takes significant time to turn on

    def turn_off(self) -> None:
        '''
        Function:
            Turn off the laser diode
        '''
        register = REG_Resena
        data = 0
        self.ITLA(register,data,WRITE)
        self.wait_until_no_operation()



