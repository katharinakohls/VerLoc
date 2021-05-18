import pytest
import numpy as np

from verloc.localization import Localizer

def test_calc_estimate_distances(loc_object, location_estimate):
    est_dists = loc_object.calc_estimate_distances(location_estimate)

    assert est_dists.shape[0] == 10

def test_calc_mean_prop_time(loc_object):
    times = loc_object.calc_mean_prop_time()

    assert times.shape[0] == 10

def test_get_distance_error(loc_object, location_estimate):
    try:
        error = loc_object.get_distance_error(location_estimate)
        success = True
    except:
        success = False

    assert success == True

def test_error_rmse(loc_object, location_estimate):
    error = loc_object.get_distance_error(location_estimate)
    try:
        rmse = loc_object.error_rmse(error)
        success = True
    except:
        success = False
    assert success == True

def test_initial_guess(loc_object, reference_coordinates):
    initial_guess = loc_object.prepare_initial_guess()

    assert initial_guess == [47.025380777286514, 9.920191898361605]

def test_estimate_location(loc_object):
    try:
        location_estimate = loc_object.estimate_location()
        success = True
    except Exception as e:
        success = False
        print ('ERROR IN ESTIMATE: ', e)

    assert success == True
