import reverse_geocode
import numpy as np
import pandas as pd
import seaborn as sns
import geopandas as gpd
import matplotlib.pyplot as plt

from shapely.geometry import Point
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib import cm
from vincenty import vincenty
from statistics import median

class LocalizationPerformance():
    def __init__(self, physical_locations, estimated_locations, loc_computations, confidence_results, process_id):
        self.physical_locations = physical_locations
        self.estimated_locations = estimated_locations
        self.confidence_scores = confidence_results
        self.comutation_timing = loc_computations
        self.process_id = process_id

        self.physical_countries = reverse_geocode.search(self.physical_locations)
        self.estimated_countries = reverse_geocode.search(self.estimated_locations)

    def get_location_error(self):
        return self.location_error
    def get_cc_accuracy(self):
        return self.cc_accuracy
                
    def compute_location_error(self):
        loc_error = {'location_error': [], 'confidence': [], 'slow': [], 'fast': [], 'comp': []}

        conf = list(self.confidence_scores['score'])
        fast = list(self.confidence_scores['fast'])
        slow = list(self.confidence_scores['slow'])

        for idx, phy in enumerate(self.physical_locations):
            est = self.estimated_locations[idx]
            try:
                err = vincenty(phy, est)
            except:
                err = -1

            loc_error['location_error'].append(err)
            loc_error['confidence'].append(conf[idx])
            loc_error['slow'].append(slow[idx])
            loc_error['fast'].append(fast[idx])
            loc_error['comp'].append(self.comutation_timing[idx])

        self.location_error = pd.DataFrame.from_dict(loc_error)
        self.location_error.to_csv('mp/{}_location_error_r40.csv'.format(self.process_id), sep=',', index=False)

    def write_stats(self):
        self.compute_location_error()
        self.compare_countries()

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
        sns.set_theme()

        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        ax = sns.histplot(self.location_error['location_error'], kde=True, ax=ax)
        plt.savefig('../visualization/location_error.pdf')

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

        plt.savefig('../visualization/estimates.pdf')

    def plot_confidences(self):
        sns.set_theme()

        # non_confident = loc_error_df[loc_error_df['confidence'] < 0.2]
        # yes_confident = loc_error_df[loc_error_df['confidence'] >= 0.2]

        self.confidence_scores['fast'] = 1 - self.confidence_scores['fast']
        self.confidence_scores['slow'] = 1 - self.confidence_scores['slow']

        melted_confidences = pd.melt(self.confidence_scores, id_vars=['node'], value_vars=['score', 'fast', 'slow'])
        
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        sns.displot(data=melted_confidences, x="value", hue="variable", kind="kde")
        plt.savefig('../visualization/confidence_comparison.pdf')

        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        sns.scatterplot(data=self.location_error, x="location_error", y="confidence")
        plt.savefig('../visualization/location_confidence.pdf')

        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        ax = sns.histplot(self.location_error['confidence'], kde=True, ax=ax)
        # plt.axvline([0.1, 0.1], [0,100])
        # plt.axvline([0.2, 0.2], [0,100])
        # plt.axvline([0.3, 0.3], [0,100])
        plt.savefig('../visualization/confidences.pdf')


        threshold = 0.06
        self.location_error['decision'] = 'reject'
        self.location_error.loc[(self.location_error['confidence'] >= threshold), 'decision'] = 'accept'

        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        sns.displot(data=self.location_error, x="location_error", hue="decision", kind="kde")
        plt.savefig('../visualization/confidence_decision.pdf')

class VerificationPerformance():
    def __init__(self, verification_results, physical_locations, process_id):
        self.verification_results = verification_results
        self.physical_locations = physical_locations
        self.process_id = process_id
        self.physical_countries = physical_locations

    def prepare_summary(self):
        self.compare_countries()

        print ('##########################################################################')
        print ('Verification Performance\n------------------------')
        print ('Relative CC Accuracy: \t{}'.format(self.cc_accuracy))
        print ('##########################################################################')

    def compare_countries(self):
        ver_results = {'phy': [], 'ver': []}
        country_comparison = []
        for idx, elem in enumerate(self.physical_countries):
            phy_cc = elem
            ver_cc = self.verification_results[idx]

            ver_results['phy'].append(phy_cc)
            ver_results['ver'].append(ver_cc)

            if phy_cc == ver_cc:
                country_comparison.append(1)
            else:
                country_comparison.append(0)

        try:
            self.cc_accuracy = sum(country_comparison) / len(country_comparison)
            self.ver_results = pd.DataFrame.from_dict(ver_results)
            self.ver_results.to_csv('mp/{}_verification_fixed.csv'.format(self.process_id), sep=',', index=False)
            print ('mp/{}_verification_fixed.csv'.format(self.process_id))
        except:
            pass

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

        plt.savefig('../visualization/mass_decision_{}.pdf'.format(index)) 