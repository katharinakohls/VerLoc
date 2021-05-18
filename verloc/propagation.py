import numpy as np

from math import exp
from scipy import constants
from pynverse import inversefunc

class Propagation():
    # ! units of distance and time
    def __init__(self, speed_func):

        if speed_func == '2/3c':
            speed = ((2/3) * constants.speed_of_light) / 1000
            self.time_func = lambda x: x / speed

        elif speed_func == '1/3c':
            speed = ((1/3) * constants.speed_of_light) / 1000
            self.time_func = lambda x: x / speed

        elif speed_func == 'paper':
            # ! The empirical speed function uses meters as input
            self.time_func = lambda x: 5.817e+07 * exp(1.645e-07*x) -4.785e+07 * exp(-2.812e-06*x)

    def get_time(self, x):
        try:
            time = self.time_func(x)
        except Exception as e:
            print ('Failed in Propagation time_func:', e, 'x=', x)
            time = 0
        return time

        