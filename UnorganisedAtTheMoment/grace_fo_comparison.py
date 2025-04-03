import numpy as np
import matplotlib.pyplot as plt

def plot_x_y(x, y_list, xscale='linear', yscale='linear', xaxis='x', yaxis='y', legend=False):
    """ Just quick plotting tool for debugging.
    """
    fig, ax = plt.subplots()
    for y in y_list:
        plt.plot(x, y)
    ax.set_yscale(yscale)
    ax.set_xscale(xscale)
    ax.set_title("{} vs {}".format(yaxis, xaxis))
    ax.set_xlabel(xaxis)
    ax.set_ylabel(yaxis)
    if legend:
        ax.legend(legend)
    plt.show()
    #input('Press enter to continue...')
    #plt.close()

no_freq_steps = 10000
laser_stab_bandwidth = 3e5

freq_space = np.logspace(-4, 8, no_freq_steps) # note, bound this by the limits of the integral
c4, c3, c2 = 0.5, 0, 2e-3
S_cavity = (c4/freq_space**4+c3/freq_space**3+c2/freq_space**2)[None, :] # not sure yet

# Free running laser and stabilised laser PSD
B, gamma, delta = laser_stab_bandwidth, 0.1, 10 # B is laser stab bandwidth
G_0 = (2*np.pi*B)**2 * (1+delta)/(1+gamma)
G_f = G_0*(1/(2*np.pi*1j*freq_space)**2)*(1j*freq_space+B*gamma)/(1j*freq_space+B*delta)
r3, r2, fc = 3e6, 3e2, 2e6
S_laser_free = (r3/(freq_space**3)) + (r2/(freq_space**2)) * (fc/(freq_space+fc))**2
S_laser_stab = S_cavity + np.abs(1/(1-G_f))**2 * S_laser_free

x = np.log10(freq_space)
#y = -0.0043*x**5 + 0.0158*x**4 + 0.0511*x**3 - 0.2149*x**2 - 0.8865*x - 0.2659 # first eq
y= -0.0306*x**3 + 0.0393*x**2 - 1.6446*x - 0.7316
y10 = np.where(freq_space < 10, 10**y, 0.00429*10**1/freq_space**1)

#y_from_paper = 0.001*x**5 + 0.0046*x**4 - 0.0422*x**3 - 0.0683*x**2 - 0.4827*x + 0.3217
y_from_paper = 0.001*x**5 + 0.0046*x**4 - 0.0422*x**3 - 0.0683*x**2 - 1.4827*x + 0.3217
y10_from_paper = np.where(freq_space < 10, 10**y_from_paper, 0.0542*10**1/freq_space**1)

legend = ['Stablised Laser (Bertania)', 'Free Running Laser (Bertania)', 'Grace FO (Rees2021)']
y_list = [S_laser_stab[0], S_laser_free, y10_from_paper**2]
#plot_x_y(freq_space, y_list, 'log', 'log', 'Frequency [Hz]', 'Frequency Noise [$Hz/\sqrt{Hz}$]', legend)
plot_x_y(freq_space, y_list, 'log', 'log', 'Frequency [Hz]', 'Frequency Noise [$Rad^2$/Hz]', legend)