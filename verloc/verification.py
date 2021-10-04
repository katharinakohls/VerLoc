import time
import sys
import geopy
import geopy.distance

import numpy as np
import pandas as pd
import geopandas as gpd

from math import pow, floor
from statistics import median
from scipy import constants
from vincenty import vincenty
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from propagation import Propagation

class Verifier():
    def __init__(self, my_times, their_times, schedule, reference_locations, me):

        self.my_times = my_times
        self.their_times = their_times
        self.schedule = schedule
        self.reference_locations = reference_locations
        self.light_speed = lambda x: (2/3) * constants.speed_of_light * x
        self.me = me
        # self.light_speed = lambda x: constants.speed_of_light * x

        self.world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
        self.europe = self.world[self.world['continent'] == 'Europe']
        self.eu_polygons = {row['name']: row['geometry'] for index, row in self.europe.iterrows()}
        self.countries = [row['name'] for index, row in self.europe.iterrows()]

        self.cropped_grid = []
        
        self.grid_resolution = 50000 # in meters, original implementation 10000

    def get_grid_resolution(self):
        return self.grid_resolution
    def get_reference_locations(self):
        return self.reference_locations
    def get_sorted_propagation(self):
        return self.sorted_propagation
    def get_cropped_grid(self):
        return self.cropped_grid
    def get_filtered_grid(self):
        return self.filtered_grid
    def get_normalized_diffs(self):
        return self.normalized_diffs
    def get_lat_grid(self):
        return self.lat_grid
    def get_decision(self):
        return self.decision

    def sort_by_time(self):
        # returns a 2D np array with avg time in col 0 and reference index in col 1
        average_propagation = np.add(self.my_times, self.their_times) / 2
        if len(average_propagation) > 0:
            # ! idx is only a counter, the node index is in the second column
            indexed_propagation = np.array([[self.light_speed(x), self.schedule[idx], idx] for idx, x in enumerate(average_propagation)])
            self.sorted_propagation = indexed_propagation[indexed_propagation[:,0].argsort()]

            return True
        else:
            self.sorted_propagation = None
            return False


    def compute_grid(self, center_point, bearing, point_range):
        partial_grid = []
        for i in point_range:
            d = geopy.distance.geodesic(meters = self.grid_resolution * i)
            grid_point = d.destination(point=center_point, bearing=bearing)
            partial_grid.append((grid_point.latitude, grid_point.longitude))

        return partial_grid

    def compute_lat_grid(self, reference_location, num_points):
        lat_grid = []
        center = geopy.Point(reference_location)

        lat_grid.extend(self.compute_grid(center, 0, range(num_points,0,-1)))
        lat_grid.append(reference_location)
        lat_grid.extend(self.compute_grid(center, 180, range(1,num_points+1)))

        self.lat_grid = lat_grid

    def compute_full_grid(self, num_points):
        lat_lon_grid = []
        for lat_point in self.lat_grid:
            center = geopy.Point(lat_point)

            lat_lon_grid.extend(self.compute_grid(center, -90, range(num_points,0,-1)))
            lat_lon_grid.append(lat_point)
            lat_lon_grid.extend(self.compute_grid(center, 90, range(1,num_points+1)))

        self.lat_lon_grid = lat_lon_grid
        self.cropped_grid = lat_lon_grid

    def crop_full_grid(self, target_location, distance_limit, area_memory):
        # compute distances between all grid points and center point
        distances = [vincenty(target_location, (x[0], x[1]))*1000 for x in self.lat_lon_grid]

        # crop away all points that are too far away
        # print ('Before:', len(self.lat_lon_grid))
        cropped_grid = [self.lat_lon_grid[idx] for idx, x in enumerate(distances) if x <= distance_limit]
        # print ('After:', cropped_grid)

        cropped_area = (len(cropped_grid) * pow((0.5*self.grid_resolution), 2)) / 1000000
        
        if cropped_area < area_memory:
            self.lat_lon_grid = cropped_grid
            self.cropped_area = cropped_area

    def crop_to_land(self):
        land_cropped = []
        for point in self.lat_lon_grid:
            p = Point(point[1], point[0])

            for index, row in self.world.iterrows():
                if row['geometry'].contains(p):
                    land_cropped.append(point)

        self.lat_lon_grid = land_cropped

    def weight_cropped_area(self):
        prop = Propagation('paper')
        
        diffs = []
        for elem in self.sorted_propagation:
            # distances from reference to all points in the grid

            if len(self.lat_lon_grid) > 0:
                try:
                    distances = np.array([vincenty(self.reference_locations[int(elem[2])], (x[0], x[1])) * 1000 for x in self.lat_lon_grid])
                    try:
                        speeds = np.array([prop.get_time(x) for x in distances])
                        times = distances / speeds
                    except:
                        times = 0
                except Exception as e:
                    print ('weight_cropped_area failed:', e)
            else:
                times = 0

            differences = (np.absolute(times - np.array(self.my_times[int(elem[2])])) + np.absolute(times - np.array(self.their_times[int(elem[2])]))) / 2
            diffs.append(differences)

        try:
            mean_diffs = np.mean(np.array(diffs) / np.amax(diffs), axis=0)
            min_mean = np.amin(mean_diffs)
            span_mean = np.amax(mean_diffs) - min_mean
            normalized_diffs = (mean_diffs - min_mean) / span_mean
            inverted_diffs = 1 - normalized_diffs
            self.normalized_diffs = inverted_diffs
            # self.normalized_diffs = 1 - mean_diffs
        except:
            self.normalized_diffs = [0]

    def decide_country(self):
        country_weights = {x: [] for x in self.countries}

        merged_grid = np.array([[x[0], x[1], self.normalized_diffs[idx]] for idx, x in enumerate(self.lat_lon_grid)])
        sorted_by_weight = merged_grid[merged_grid[:,2].argsort()] #! ascending, do we want that?

        # median_weight = median(self.normalized_diffs)
        # filtered_grid = [x for x in sorted_by_weight if x[2] >= median_weight] #! do it without
        
        # ---------------------------

        # for elem in enumerate(filtered_grid):
        for elem in enumerate(sorted_by_weight):
            p = Point(elem[1][1], elem[1][0])
            weight = elem[1][2]

            for country in self.eu_polygons:
                if self.eu_polygons[country].contains(p):
                    country_weights[country].append(weight)
        # ---------------------------

        weight_memory = 0
        filtered_country_weights = {x: country_weights[x] for x in country_weights if len(country_weights[x]) > 0}
        country_weight_dict = {}
        for country in filtered_country_weights:
            try:
                # w = sum(country_weights[country]) / len(country_weights[country])
                w = sum(country_weights[country])
                country_weight_dict[country] = [w]

                if w > weight_memory:
                    decision = country
                    weight_memory = w
            except:
                pass

        self.filtered_grid = merged_grid
        self.decision = decision
        self.country_weights = country_weight_dict

        self.ctr_results = pd.DataFrame.from_dict(country_weight_dict)
        self.ctr_results.to_csv('mp/{}_country_weights.csv'.format(self.me.node_id), sep=',', index=False)

    def verify_location(self):
        sort_success = self.sort_by_time()
        if sort_success:
            try:
                # early stop helpers
                area_memory = float('inf')
                stuck_counter = 0

                initial_round = True
                for i in range(1,len(self.sorted_propagation)):
                    try:
                        reference_index = int(self.sorted_propagation[i,2])
                        distance_limit = self.sorted_propagation[i,0]

                        if initial_round:
                            ref_loc = self.reference_locations[reference_index]

                            if ref_loc != self.me.get_location():
                            
                                num_points = floor(distance_limit / self.grid_resolution)

                                self.compute_lat_grid(ref_loc, num_points)
                                self.compute_full_grid(num_points)
                                # self.crop_full_grid(ref_loc, distance_limit, area_memory)
                                # ! use target as center and not the reference
                                self.crop_full_grid(self.me.get_location(), distance_limit, area_memory)

                                initial_round = False
                        else:
                            # all other rounds
                            new_ref_loc = self.reference_locations[reference_index]
                            if new_ref_loc != ref_loc:
                                try:
                                    self.crop_full_grid(self.me.get_location(), distance_limit, area_memory)
                                
                                    if self.cropped_area >= area_memory:
                                        stuck_counter = stuck_counter + 1

                                    area_memory = self.cropped_area

                                    # ? can be adjusted for performance
                                    if stuck_counter >= 5:
                                        break
                                except :
                                    break

                            ref_loc = new_ref_loc
                    except:
                        break
            except:
                pass

            self.weight_cropped_area()

            try:
                self.decide_country()
                dec = self.decision
            except Exception as e:
                print ('Decision failure', e)
                self.filtered_grid = []
                dec = -1
        else:
            print ('Sort failure')
            self.filtered_grid = []
            dec = -1

        return dec, self.filtered_grid