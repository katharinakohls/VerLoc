# VerLoc
This is the prototype implementation of VerLoc, a system that uses RTT measurements for the localization and verification of nodes in a network. VerLoc is designed to function in a fully decentralized network and without any central authority. Measurement tasks and results are stored in a central blockchain, and each node can verify the location information of other nodes based on this information.

A preliminary version of the paper can be found [here](https://arxiv.org/abs/2105.11928).

## Components of the Prototype
### FetchAndParse.py
To be found in ```parser/```; loads the network data and measurement results and parses them into the representation we later use in the localization.

All data is written to ```parser/static_data/```; we currently use a world city database ```parser/worldcities.csv``` to match the self-reported location strings with a geographical location. This will be replaced in a future version, where we plan on using GeoIP information.

### Localization.py
To be found in ```verloc/```; provides the location estimate.

The localization uses multiple timing measurements and estimates the geographical location of a node. To this end, we use a minimization function that optimizes a location estimate for the target node from all given RTT measurements of the reference nodes.

The output of the localization is the location estimate (lat,lon).

VerLoc assigns random measurement tasks for each epoch and all nodes of the network follow this schedule by conducting pairwise RTT measurements. We simulate this behavior in the prototype, i.e., we don't implement live measurements but provide a test input including node information (ID, location, country code, etc.) and the measurement results of sample epochs.

### Verification.py
To be found in ```verloc/```; provides the zone verification. At the moment this is not fully functional.

The verification predicts the country of the target node by defining the most likely target area from all reference RTT measurements. In contrast to the localization, where the goal is to estimate an exact location, the verification outputs the most likely country.

### Other components
- Blockchain: We implement an exemplary central block chain that keeps track of the network information, required input parameters like a random epoch beacon, and the measurement results of all scheduled RTT measurements in an epoch.
- Simulation input: The given test input can be replaced by any other timing and network information in the same format.

## Setup
Each component runs individually and has its own ```requirements.txt``` and test cases. To run one of the components, you need to first select a directory and then install the requirements.

```
pip install -r requirements.txt
```

## High-Level Description

### Localization for 1 Node A
- Goal: Estimate a location (lat, lon) where we expect the node
- Input: All timing measurements involving A
  - We know the claimed locations of all reference nodes
  - We know the claimed location of node A
  - We can translate the measured time into distance by applying a *propagation model* speed = distance / time
- Output: Estimated location (lat, lon)
- Concept: Find the solution with the least error for all timing [measurements](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)
  - Distances: Get the distances between claimed location of A and all reference claimed locations
  - Error: Compare timing-based distances with expected distances (distance between two points on a sphere)
  - Apply and error function to weight the error
  - Minimize the error for all measurements, use the least error solution as location estimate
  - Compare the estimate with the claimed location

### Weighted target area for 1 Node A
- Goal: Compute a target grid, assign a weight to each point, visualize the highest weight area
- Input: All timing measurements involving A
  - We know the claimed locations of all reference nodes
  - We know the claimed location of node A
  - We can translate the measured time into distance by applying assuming the *speed of light*
- Output: Grid with locations, each location has a weight
- Concept: Define a starting grid, then cut off areas to narrow down the search space, finally weight each point in the grid
  - Sort all measured timings, begin with the shortest
  - Translate the timing into a distance, draw a circle around A that covers everything that can be reached in this time
  - Make this area a grid, the granularity of the grid defines how precise everything will be but also how much overhead we'll have (1km versus 100km versus ...)
  - Go to the next reference in the list, draw a circle around the reference, only keep the intersection between the initial circle and the new circle.
  - Repeat for the next references in the list, continue until there are no improvements anymore (improvement = grid shrinks)
  - For each point in the grid and for each reference compare the measured distance (time -> distance using the propagation model) with the actual distance between the grid point and the reference.
  Example: If the grid has 100 points and we have 5 references, we would do this 5 * 100 times
  - Use the difference to weight each point in the grid. The weights describe how likely it would have been to reach the point. Weights can be colorized, a higher weight/lower error area will differ from other areas
