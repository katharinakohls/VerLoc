from math import exp
from scipy import constants
from vincenty import vincenty

class ConfidenceScorer():
    def __init__(self, node):
        ref_locations = node.get_ref_locations()
        my_location = node.get_location()

        distances = []
        for ref_loc in ref_locations:
            distances.append(vincenty(my_location, ref_loc) * 1000)

        self.distances = distances
        self.my_times = node.get_my_measurements()
        self.their_times = node.get_their_measurements()
        
        lower_bound_function = lambda x: (5.934e+07 * exp(1.742e-07*x) -4.529e+07 * exp(-2.564e-06*x)) / 1000

        self.grace_factor = 0.2
        self.lower_bound_speed = [(lower_bound_function(x) - lower_bound_function(x) * self.grace_factor) for x in distances]
        self.upper_bound_speed = ((2/3) * constants.speed_of_light) / 1000
        

    def compute_confidence(self):
        # distances between from and to node

        node_confidence = []
        fast_violations = []
        slow_violations = []
        for idx, dist in enumerate(self.distances):
            my_speed = (dist / self.my_times[idx]) / 1000
            their_speed = (dist / self.their_times[idx]) / 1000

            lower = self.lower_bound_speed[idx]

            if my_speed > lower and my_speed < self.upper_bound_speed and their_speed > lower and their_speed < self.upper_bound_speed:
                node_confidence.append(1)
            else:
                node_confidence.append(0)

            if my_speed > self.upper_bound_speed or their_speed > self.upper_bound_speed:
                fast_violations.append(1)
            else:
                fast_violations.append(0)

            if my_speed < lower or their_speed < lower:
                slow_violations.append(1)
            else:
                slow_violations.append(0)

        try:
            node_conf = sum(node_confidence) / len(node_confidence)
        except:
            node_conf = 0

        try:
            fast_viol = sum(fast_violations) / len(fast_violations)
        except:
            fast_viol = 0
        
        try:
            slow_viol = sum(slow_violations) / len(slow_violations)
        except:
            slow_viol = 0

        return node_conf, fast_viol, slow_viol