import pytest
from verloc.propagation import Propagation

@pytest.mark.parametrize('speed_func', ['2/3c', '1/3c', 'paper'])
def test_constant_speed(prop_object):
    
    time = prop_object.get_time(1000)

    assert time != None

def test_paper_propagation():
    prop_object = Propagation('paper')

    assert prop_object.get_time(1000) == 10463934.94608847