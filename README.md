# VerLoc
This is the prototype implementation of VerLoc, a system that uses RTT measurements for the localization and verification of nodes in a network. VerLoc is designed to function in a fully decentralized network and without any central authority. Measurement tasks and results are stored in a central blockchain, and each node can verify the location information of other nodes based on this information.

We will shortly add a link to the arxiv version of the full paper that documents VerLoc.

## Components of the Prototype
### verloc
This is the core component. It provides a localization and a verification function and uses a set of node and timing data as input.

#### Localization
The localization uses multiple timing measurements and estimates the geographical location of a node. To this end, we use a minimization function that optimizes a location estimate for the target node from all given RTT measurements of the reference nodes.

The outout of the localization is the location estimate (lat,lon).

#### Verification
The verification predicts the country of the target node by defining the most likely target area from all reference RTT measurements. In contrast to the localization, where the goal is to estimate an exact location, the verification outputs the most likely country.

### blockchain
We implement an exemplary central block chain that keeps track of the network information, required input parameters like a random epoch beacon, and the measurement results of all scheduled RTT measurements in an epoch.

### input simulation
VerLoc assigns random measurement tasks for each epoch and all nodes of the network follow this schedule by conducting pairwise RTT measurements. We simulate this behavior in the prototype, i.e., we don't implement live measurements but provide a test input including node information (ID, location, country code, etc.) and the measurement results of sample epochs.

The given test input can be replaced by any other timing and network information in the same format.

## Setup
Each component runs individually and has its own ```requirements.txt``` and test cases. To run one of the components, you need to first select a directory and then install the requirements.

```
pip install -r requirements.txt
```