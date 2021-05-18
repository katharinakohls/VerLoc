import pytest
import numpy as np
from math import floor

from verloc.performance_eval import LocalizationPerformance

def test_compute_location_error(loc_performance_object):
    loc_performance_object.compute_location_error()

    loc_error = loc_performance_object.get_location_error()

    assert len(loc_error) == 10

def test_compare_countries(loc_performance_object):
    loc_performance_object.compare_countries()
    cc_acc = loc_performance_object.get_cc_accuracy()

    assert cc_acc > 0
