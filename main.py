try:
    from kalman import Kalman
    rootdir = '/home/marcos/projects/python_implementations/'
except ModuleNotFoundError:
    import sys
    sys.path.append('../')
    from kalman import Kalman
    rootdir = '/home/marcos/projects/python_implementations/'

import matplotlib.pyplot as plt

def example6():
    """This example is the implementation of
    `Example 6 - Estimating the temperature of the liquid in a tank`
    from `https://www.kalmanfilter.net/kalman1d.html`.

    This is a 1-D example of the Kalman filter.

    In this example, system matrixes and initial values are:
        F = [[1]],
        G = None
        H = [[1]]
        x = [10]
        P = [[100]]

    The process noise and measurement uncertainty are constant:
        Q = [[0.0001]]
        R = [[0.1**2]]
        
    The measurements are:
        49.95, 49.967, 50.1, 50.106, 49.992,
        49.819, 49.933, 50.007, 50.023, 49.99
    and the true values are:
        49.979, 50.025, 50, 50.003, 49.994,
        50.002, 49.999, 50.006, 49.998, 49.991
    """
    ## Setup
    F = [[1.]]
    G = None
    H = [[1.]]
    x = [10.]
    P = [[10000]]
    Q = [[0.0001]]
    R = [[0.1**2]]
    zs = [49.95, 49.967, 50.1, 50.106, 49.992,
          49.819, 49.933, 50.007, 50.023, 49.99]
    
    ## Filt
    kf = Kalman(F, G, H)
    kf.x = x
    kf.P = P
    x_kalman = []
    P_kalman = []
    K_kalman = []
    for z in zs:
        kf.predict(Q=Q)
        kf.update([z], R)
        x_kalman.append(kf.x[0])
        P_kalman.append(kf.P[0, 0])
        K_kalman.append(kf.K[0, 0])
        
    ## Plot
    idx = range(1, len(zs)+1)
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.plot(idx, [49.979, 50.025, 50, 50.003, 49.994,
                  50.002, 49.999, 50.006, 49.998, 49.991],
            'gd-', label='True values')
    ax.plot(idx, zs, 'bs-', label='Measurements')
    ax.plot(idx, x_kalman, 'ro-', label='Estimates')
    ax.legend()
    ax.grid()
    ax.set_xlabel('Measurement number')
    ax.set_ylabel(r'Temperature ($\degree$ C)')
    fig.suptitle('Liquid Temperature')
    fig.savefig(f'{rootdir}example6-1.svg')

    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.plot(idx, P_kalman, 'ro-')
    ax.grid()
    ax.set_xlabel('Measurement number')
    ax.set_ylabel('Estimate uncertainty')
    fig.suptitle('Estimate uncertainty')
    fig.savefig(f'{rootdir}example6-2.svg')

    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    ax.plot(idx, K_kalman, 'k')
    ax.grid()
    ax.set_xlabel('Measurement number')
    ax.set_ylabel('Kalman gain')
    fig.suptitle('Kalman gain')
    fig.savefig(f'{rootdir}example6-3.svg')

if __name__ =="__main__":
    example6()