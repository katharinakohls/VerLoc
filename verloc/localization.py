import numpy as np
from math import sqrt

from vincenty import vincenty

from colorama import Fore
from shapely import geometry

from scipy.linalg import norm
from scipy.optimize import minimize
from scipy.optimize import Bounds
from scipy.optimize import NonlinearConstraint

from propagation import Propagation

class Localizer():
    def __init__(self, my_times, their_times, reference_locations):
        # self.earth_bounds = Bounds([-90, -180], [90, 180])
        self.earth_bounds = Bounds([27.6375, -18.1706],[60.8444, 40.1797])
        # self.method = min_method

        # all of the following are static items that stay the same during the optimization
        self.my_times = my_times
        self.their_times = their_times
        self.reference_locations = reference_locations

        # will be set later on
        self.measured_distances = None
        self.mean_prop_time = None

    def prepare_initial_guess(self):
        try:
            ref_poly = geometry.Polygon(self.reference_locations)
            initial_guess = ref_poly.centroid.coords
        except:
            print (self.reference_locations)
            initial_guess = (0,0)

        # print ('Initial Guess:', list(initial_guess[0]))
        return list(initial_guess[0])

    def estimate_location(self):
        initial_guess = self.prepare_initial_guess()
        
        # method='TNC',
        location_estimate = minimize(self.error_rmse, x0=initial_guess, bounds=self.earth_bounds)

        print ('Localization finished with result', location_estimate.x)
        return location_estimate.x


    def calc_power(self, timing):
        return np.power(timing, sqrt(1))

    def calc_estimate_distances(self, location_estimate):
        estimate_distances = []
        for ref in self.reference_locations:
            # distance in km, WGS 84 reference ellipsoid
            dist = vincenty(location_estimate, ref) * 1000
            if dist != None:
                estimate_distances.append(dist)
            else:
                print ('Problem in calc_estimate_distances:', location_estimate, ref, dist)

        return np.array(estimate_distances)

    def calc_mean_prop_time(self):
        return np.add(self.my_times, self.their_times) / 2
        

    def get_distance_error(self, location_estimate):
        prop_model = Propagation('paper')

        # distance between current estimate and all reference locations
        estimate_distances = self.calc_estimate_distances(location_estimate)

        # apply propagation function to estimated distances
        estimate_speeds = np.array([prop_model.get_time(x) for x in estimate_distances])

        # print ('Estimate Distances:', estimate_distances)

        # average measured time of outgoing and incoming measurements
        self.mean_prop_time = self.calc_mean_prop_time()

        # print ('Mean Prop Time:', self.mean_prop_time)

        # ? how it should be
        # self.measured_distances = [prop_model.get_dist(x) for x in self.mean_prop_time]
        # ? following the matlab implementation
        self.measured_distances = self.mean_prop_time * estimate_speeds

        # print ('Measured Distances:', self.measured_distances)

        try:
            # difference between measured and estimated distances
            error = estimate_distances - self.measured_distances
        except ValueError as e:
            print (e)
        except TypeError as e:
            print ('MESSED UP IN ERROR THINGY')
            print (estimate_distances)
            print (self.measured_distances)

        return error

    def error_rmse(self, location_estimate):
        base_error = self.get_distance_error(location_estimate)

        # print ('Base Error:', base_error)

        # base_error and mean_prop_time need to be np.ndarray
        try:
            error = base_error * ( (1 / self.calc_power(self.mean_prop_time)) / norm( (1 / self.calc_power(self.mean_prop_time)), 1))
            rmse = sqrt(np.mean(np.power(error, 2)))
        except Exception as e:
            print (Fore.RED + 'ERROR {}: error or timing in the wrong format: error is {}, timing is {}'.format(e, type(base_error), type(mean_prop_time)))

        return rmse
