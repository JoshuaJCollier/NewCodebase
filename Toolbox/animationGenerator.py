# File for creating animations for slide deck for AIP
# Author:  Josh Collier
# Created: 18 Nov 2024

# --- Imports ---
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random

# --- Functions ---
def make_time_plot(noisy,noisefactor=1,directory='C:\\Users\\josh\\OneDrive - UWA\\UWA\\PhD\\7. Code\\Interference\\tmp'):
    """ Generate a plot of a sinusoid with amplitude and phase noise that is animated and saved as a gif

    Example(s):
        make_interference_plot(True, noisefactor=2)

    Args:
        noisy (Boolean): State if you want the plot to be noisy or not
        noisefactor (int, optional): Determines the magnitude of the noise. Defaults to 1.
        directory (str, optional): _description_. Defaults to 'C:\\Users\\josh\\OneDrive - UWA\\UWA\\PhD\\7. Code\\Interference\\tmp'.
    """
    fig, [ax1, ax2] = plt.subplots(1, 2, gridspec_kw={'width_ratios':[1,2]})
    plt.subplots_adjust(left=None, bottom=0.18, right=None, top=None, wspace=0.3, hspace=None)

    #ax.set_xlim(-4.5e6/divisor, 4.5e6/divisor)
    #ax.set_ylim(5e6/divisor, 8e6/divisor)
    ax1.set_title("Unit Circle")
    ax1.set_xlabel("$cos(\\theta)$")
    ax1.set_xticks([-1, -0.5, 0, 0.5, 1])
    ax1.set_ylabel("$sin(\\theta)$")
    ax1.set_yticks([-1, -0.5, 0, 0.5, 1])

    ax2.set_title("Sinusoid")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Amplitude")
    ax2.set_yticks([-1, -0.5, 0, 0.5, 1])

    fig.set_size_inches(16, 5)
    #fig.tight_layout()

    no_values = 100

    phase_arr = np.linspace(0, 2*np.pi, no_values)
    sin_space = np.zeros(100)

    ax1.plot(np.cos(phase_arr), np.sin(phase_arr), color='black')

    artists = []
    phase_noise = 0
    amp_noise = 0
    for i in range(no_values):
        current_phase = phase_arr[i]
        if noisy:
            phase_noise += (random.random()*0.2-0.1)*noisefactor
            current_phase += phase_noise
            amp_noise = (random.random()*0.2-0.1)*noisefactor
        sin_space = np.roll(sin_space, 1)
        
        sin_space[0] = np.sin(current_phase) * (1+amp_noise)
        
        container, = ax1.plot([0, np.cos(current_phase)], [0, np.sin(current_phase)], color='green') # this is the line on the unit circle
        container2, = ax1.plot([0, np.cos(current_phase)], [np.sin(current_phase), np.sin(current_phase)], color='blue', linestyle='dashed') # this is the x component on the unit circle
        container3, = ax1.plot([0, 0], [0, np.sin(current_phase)], color='red') # this is the y component on the unit circle
        container4, = ax1.plot(np.cos(current_phase), np.sin(current_phase), 'go')
        container5, = ax1.plot(0, np.sin(current_phase), 'ro')
        container6, = ax2.plot(phase_arr, sin_space, color='red')
        artists.append([container, container2, container3, container4, container5, container6])

    ani = animation.ArtistAnimation(fig=fig, artists=artists, interval=60)
    ani.save(filename="{}\\phase_animation_noisyIs{}.gif".format(directory, noisy), writer="pillow")
    print("Done - unit circle (noise={})".format(noisy))

def make_interference_plot(noisy, noisefactor=1, directory = 'C:\\Users\\josh\\OneDrive - UWA\\UWA\\PhD\\7. Code\\Interference\\tmp'):
    """ Genereates a plot of interference between two sinusoids, and saves it as an animation.
    
    Example(s):
        make_time_plot(False)
        make_time_plot(True, noisefactor=2)

    Args:
        noisy (Boolean): State if you want the plot to be noisy or not
        noisefactor (int, optional): Determines the magnitude of the noise. Defaults to 1.
        directory (str, optional): _description_. Defaults to 'C:\\Users\\josh\\OneDrive - UWA\\UWA\\PhD\\7. Code\\Interference\\tmp'.
    """
    #fig, [[ax1, ax2], ax3] = plt.subplots_mosaic([['upper left', 'right'],['lower left', 'right']],layout="constrained")
    fig, [ax1, ax2] = plt.subplots(2, 1, gridspec_kw={'height_ratios':[1,1]})

    ax1.set_xlim(0, 4*np.pi)
    #ax.set_ylim(5e6/divisor, 8e6/divisor)
    ax1.set_title("Sinusoids")
    ax1.set_xlabel("Phase (rad)")
    ax1.set_ylabel("Amplitude")
    #ax1.legend(['Sinusoid FFT', 'Sinusoid Offset FFT', 'Sinusoid Offset Noisy FFT'])

    ax2.set_title("Interference")
    ax2.set_xlabel("Phase (rad)")
    ax2.set_ylabel("Amplitude")

    fig.set_size_inches(10, 6)
    fig.tight_layout()

    no_values = 1000

    phase_arr = np.linspace(0, 2*np.pi*10, no_values+1)[0:-1]
    interference = np.zeros(no_values)
    
    phase_noise = np.random.rand(no_values)*(0.2-0.1)*noisefactor
    for i in range(no_values):
        phase_noise = np.roll(phase_noise, -1)
        phase_noise[-1] = (random.random()*0.2-0.1)*noisefactor
    amp_noise = np.random.rand(no_values)*(0.2-0.1)*noisefactor
    
    artists = []
    interference_over_phase = []
    interference_over_phase_noisy = []
    for i in range(no_values):
        if noisy:
            phase_noise = np.roll(phase_noise, -1)
            phase_noise[-1] = (random.random()*0.2-0.1)*noisefactor
            amp_noise = np.roll(phase_noise, -1)
            amp_noise[-1] = (random.random()*0.2-0.1)*noisefactor
            
        sin = np.cos(phase_arr)
        sin_offset_nonoise = np.cos(np.roll(phase_arr,i))
        
        
        
        sin_offset = np.cos(np.roll(phase_arr,i) + np.cumsum(phase_noise))*(1+amp_noise)

        interference = np.roll(interference, 1)
        interference[0] = sin[0] + sin_offset[0]
        container, = ax1.plot(phase_arr, sin, color='blue') # static sinusoid
        container2, = ax1.plot(phase_arr, sin_offset_nonoise, color='green') # sweeping sin
        container3, = ax1.plot(phase_arr, sin_offset, color='red') # sweeping sin

        #container3, = ax2.plot(interference, color='green')
        container4, = ax2.plot(np.abs(np.fft.fft(sin/2+sin_offset_nonoise/2))[0:int(no_values/10)]/500, color='green')
        container5, = ax2.plot(np.abs(np.fft.fft(sin/2+sin_offset/2))[0:int(no_values/10)]/500, color='red')
        
        interference_over_phase.append(np.real(np.fft.fft(sin/2+sin_offset_nonoise/2))[10]/500)
        interference_over_phase_noisy.append(np.real(np.fft.fft(sin/2+sin_offset/2))[10]/500)
        
        artists.append([container, container2, container3, container4, container5])

    print('Animating...')
    ani = animation.ArtistAnimation(fig=fig, artists=artists, interval=int(3000/no_values))
    ani.save(filename="{}\\interference_noisyIs{}.gif".format(directory, noisy), writer="pillow")
    #print("Done - interference (final phase offset: {}))".format(phase_noise))
    
    plt.figure()
    plt.plot(phase_arr,interference_over_phase, color='green')
    plt.plot(phase_arr,interference_over_phase_noisy, color='red')
    plt.xlim(0, 4*np.pi)
    plt.xlabel("Phase")
    plt.ylabel("Interference Amplitude")
    plt.rcParams['font.size'] = 20
    plt.show()
    

