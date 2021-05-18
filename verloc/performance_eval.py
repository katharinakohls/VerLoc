import reverse_geocode
import numpy as np
import seaborn as sns
import geopandas as gpd
import matplotlib.pyplot as plt

from shapely.geometry import Point
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib import cm
from vincenty import vincenty
from statistics import median

class LocalizationPerformance():
    def __init__(self, physical_locations, estimated_locations):
        self.physical_locations = physical_locations
        self.estimated_locations = estimated_locations

        self.physical_countries = reverse_geocode.search(self.physical_locations)
        self.estimated_countries = reverse_geocode.search(self.estimated_locations)

    def get_location_error(self):
        return self.location_error
    def get_cc_accuracy(self):
        return self.cc_accuracy

    def prepare_summary(self):
        self.compute_location_error()
        self.compare_countries()

        print ('##########################################################################')
        print ('Localization Performance\n------------------------')
        print ('Median Location Error:\t{}'.format(median(self.location_error)))
        print ('Relative CC Accuracy: \t{}'.format(self.cc_accuracy))
        print ('Results plotted to:   \t{}'.format('2021-verloc-prototype/visualization/'))

        self.plot_localization()
        self.plot_location_error()

        print ('Plotted {}'.format('location_error.pdf'))
        print ('Plotted {}'.format('estimates.pdf'))
        print ('##########################################################################')
                
    def compute_location_error(self):
        loc_error = []

        for idx, phy in enumerate(self.physical_locations):
            est = self.estimated_locations[idx]
            try:
                err = vincenty(phy, est)
            except:
                err = -1
            loc_error.append(err)
        self.location_error = loc_error

    def compare_countries(self):
        country_comparison = []
        for idx, elem in enumerate(self.physical_countries):
            phy_cc = elem['country_code']
            est_cc = self.estimated_countries[idx]['country_code']

            if phy_cc == est_cc:
                country_comparison.append(1)
            else:
                country_comparison.append(0)

        self.cc_accuracy = sum(country_comparison) / len(country_comparison)


    def plot_location_error(self):
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        sns.set_theme()
        ax = sns.histplot(self.location_error, kde=True, ax=ax)

        plt.savefig('/home/kk/Documents/Repos/2021-verloc-prototype/visualization/location_error.pdf')


    def plot_localization(self):
        real_locations = {'geometry': []}
        esti_locations = {'geometry': []}

        for idx, phy in enumerate(self.physical_locations):
            est = self.estimated_locations[idx]
            try:
                real_locations['geometry'].append(Point(float(phy[1]), float(phy[0])))
                esti_locations['geometry'].append(Point(float(est[1]), float(est[0])))

            except:
                pass

        phy_points = gpd.GeoDataFrame(real_locations, geometry=real_locations['geometry'])
        est_points = gpd.GeoDataFrame(esti_locations, geometry=esti_locations['geometry'])

        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

        fig, ax = plt.subplots(1, 1, figsize=(10, 10))

        world.boundary.plot(ax=ax, edgecolor='slategray', linewidth=1)
        est_points.plot(ax=ax, color='xkcd:crimson', markersize=10, alpha=0.4)
        phy_points.plot(ax=ax, color='black', markersize=10, alpha=0.4)

        # [27.6375, -18.1706],[60.8444, 40.1797]
        # zoom in on Europe
        # TODO automatic focus
        ax.set_xlim([-18.1706, 40.1797])
        ax.set_ylim([27.6375, 60.8444])

        plt.savefig('/home/kk/Documents/Repos/2021-verloc-prototype/visualization/estimates.pdf')

class VerificationPerformance():
    def __init__(self, verification_results, physical_locations):
        self.verification_results = verification_results
        self.physical_locations = physical_locations

        if physical_locations != 0:
            self.physical_countries = reverse_geocode.search(self.physical_locations)

    def prepare_summary(self):
        self.compare_countries()

        print ('##########################################################################')
        print ('Verification Performance\n------------------------')
        print ('Relative CC Accuracy: \t{}'.format(self.cc_accuracy))
        print ('##########################################################################')

    def compare_countries(self):
        country_comparison = []
        ver_countries = []
        for idx, elem in enumerate(self.physical_countries):
            phy_cc = elem['country']
            ver_cc = self.verification_results[idx]

            ver_countries.append((phy_cc, ver_cc))

            if phy_cc == ver_cc:
                country_comparison.append(1)
            else:
                country_comparison.append(0)

        print (ver_countries)
        self.cc_accuracy = sum(country_comparison) / len(country_comparison) 

    # must be called in node repetition
    def plot_map(self, cropped_grid, target_location, index):

        grid = {'geometry': []}
        weights = []
        for elem in cropped_grid:
            grid['geometry'].append(Point(elem[1], elem[0]))
            weights.append(elem[2])

        grid_points = gpd.GeoDataFrame(grid, geometry=grid['geometry'])
        grid_points['weight'] = weights

        target = {'geometry': [Point(target_location[1], target_location[0])]}
        target_point = gpd.GeoDataFrame(target, geometry=target['geometry'])

        fig, ax = plt.subplots(1, 1, figsize=(10, 10))

        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

        world.boundary.plot(ax=ax, edgecolor='slategray', linewidth=1)
        grid_points.plot(ax=ax, c=grid_points['weight'], markersize=10, alpha=0.4)
        target_point.plot(ax=ax, color='black', markersize=10)

        # [27.6375, -18.1706],[60.8444, 40.1797]
        ax.set_xlim([-18.1706, 40.1797])
        ax.set_ylim([27.6375, 60.8444])

        plt.savefig('/home/kk/Documents/Repos/2021-verloc-prototype/visualization/mass_decision_{}.pdf'.format(index)) 