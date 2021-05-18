import pytest
import numpy as np
from math import floor

from verloc.verification import Verifier

def test_crop_grid(ver_object):
    try:
        ver_object.sort_by_time()
        sort_success = True
    except:
        print ('Error in ver_object.sort_by_time():', e)
        sort_success = False
    assert sort_success == True

def test_lat_grid(ver_object):
    ver_object.sort_by_time()

    sorted_propagation = ver_object.get_sorted_propagation()
    grid_resolution = ver_object.get_grid_resolution()
    reference_locations = ver_object.get_reference_locations()

    distance_limit = sorted_propagation[0,0]
    reference_index = int(sorted_propagation[0,2])

    reference_location = reference_locations[reference_index]
    num_points = floor(distance_limit / grid_resolution)

    try:
        ver_object.compute_lat_grid(reference_location, num_points)
        lat_grid = ver_object.get_lat_grid()

        lat_grid_success = True
    except Exception as e:
        print ('Error in ver_object.get_lat_grid():', e)
        lat_grid_success = False

    assert lat_grid_success == True

def test_full_grid(ver_object):
    ver_object.sort_by_time()

    sorted_propagation = ver_object.get_sorted_propagation()
    grid_resolution = ver_object.get_grid_resolution()
    reference_locations = ver_object.get_reference_locations()

    distance_limit = sorted_propagation[0,0]
    reference_index = int(sorted_propagation[0,2])

    reference_location = reference_locations[reference_index]
    num_points = floor(distance_limit / grid_resolution)

    # FULL GRID
    try:
        ver_object.compute_lat_grid(reference_location, num_points)
        ver_object.compute_full_grid(num_points)
        full_grid_success = True
    except Exception as e:
        print ('Error in ver_object.compute_full_grid():', e)
        full_grid_success = False

    # CROPPING
    try:
        ver_object.crop_full_grid(reference_location, distance_limit, float('inf'))
        cropping_success = True
    except Exception as e:
        print ('Error in ver_object.crop_full_grid():', e)
        cropping_success = False

    assert cropping_success == True
    assert full_grid_success == True

def test_verify_location(ver_object):
    try:
        decision, time_dict = ver_object.verify_location()
        print ('TIMES')
        print (time_dict)
        verify_success = True
    except Exception as e:
        print ('Error in ver_object.verify_location():', e)
        verify_success = False

    assert verify_success == True
