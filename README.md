## TO-DO
- Implement CI/CD
- Implement tests
- Implement automatic document generation
- Minimal environment dependencies
- Comprehensive documentation
- Code formating

__________________
## Table of Contents

- [Introduction](#introduction)
- [Bridge description](#bridge-description)
  - [Location](#location)
  - [Structure](#structure)
  - [Materials](#materials)
- [Code dependencies](#code-dependencies)
- [Installation and use](#installation-and-use)
  - [Installation](#installation)
  - [Use](#use)
    - [Running the basic example](#running-the-basic-example)
    - [Modifying the settings](#modifying-the-settings)
    - [Adding custom functionalities](#adding-custom-functionalities)
- [Expected results](#expected-results)

# Introduction
The goal of **NibelungenbrueckeDemonstrator** is to provide a representative and repeatable workflow for the implementation of a stochastic [Digital Twin (DT)](https://en.wikipedia.org/wiki/Digital_twin) of the [Nibelungenbrücke in Worms (Germany)](https://de.wikipedia.org/wiki/Nibelungenbr%C3%BCcke_Worms). This repository has been developed by [_Bundesanstalt für Materialforschung und -prüfung (BAM)_](https://www.bam.de) in the context of the project "Data driven model adaptation for identifying stochastic digital twins of bridges", englobed in the funding initiative SPP 2388/1 100plus of the German Research Foundation (DFG). 

Nevertheless, due to its modular structure and user-oriented approach, this demonstrator can be used as the basis for implementing the workflow of any digital twin using a [Bayesian framework](https://en.wikipedia.org/wiki/Bayesian_inference). This repository abides by the principles of [FAIR](https://www.go-fair.org/fair-principles/) (Findable, Accessible, Interoperable and Reusable) scientific software.
# Bridge description
## Location
Located in the city of [Worms](https://en.wikipedia.org/wiki/Worms,_Germany) (Rheinlad-Palatinate), the Nibelungenbrücke connects it across the river Rhine with the cities of [Lampertheim](https://en.wikipedia.org/wiki/Lampertheim) and [Bürstadt](https://en.wikipedia.org/wiki/B%C3%BCrstadt) (Hesse).
It is the only road bridge between Mannheim in the south and Mainz in the north, which leads to the transit of 23000 vehicles every 24h on average.

The DT implemented in this repository focuses on the span closest to the west shore of the Rhein (Worms side) of the ["old" Nibelungenbrücke](https://structurae.net/en/structures/nibelungenbrucke). The measurements and dimensions of the bridge are provided by the organization of the SPP 2388/ 100plus program.

*INSERT PICTURES HERE?*
## Structure
The bridge is a [box girder bridge](https://en.wikipedia.org/wiki/Box_girder_bridge) built following the [balanced cantilever method](https://en.wikipedia.org/wiki/Cantilever_bridge). 

*INSERT CROSS-SECTION DRAWINGS HERE?*
## Materials
The bridge is built out of prestressed concrete for the deck and reinforced concrete for piers and abutments. This demonstrator implements a simulation of the deck, with the following material parameters:

*INSERT TABLE WITH MATERIAL PARAMETERS*
# Code dependencies
The following packages are required:
- [doit](https://pydoit.org/)
- [fenics-dolfinx](https://github.com/FEniCS/dolfinx)
- [gmsh](https://gmsh.info/)
- [h5py](https://www.h5py.org/)
- [probeye](https://github.com/BAMresearch/probeye)

For visualization, [paraview](https://www.paraview.org/) is recommended. These packages may require their own dependencies such as numpy, scipy, pandas, etc.

*INCLUDE MINIMUM VERSIONS*

# Installation and use
## Installation
From the root of the cloned repository, install the folder as a package using pip:
```
pip install .
```
Now the contents in `nibelungenbruecke` are available for their use in any Python script calling `import nibelungenbruecke`.

## Use
The NibelungenbrückeDemonstrator provides the following modules:
- **Geometry and mesh creation**: From a set of parameters, it creates the geometry of the Nibelungenbrücke and meshes it.
- **Synthetic data generation**: Generates a set of data a a given set of virtual sensor positions.
- **Data preprocessing**: Pre-processes the data by applying the transformations indicated and adapts it to a suitable format for the DT. (WIP)
- **Run inference procedure**: Applies Bayesian inference methods to obtain fitted distributions of a set of parameters based on provided data.
- **Query posterior predictive**: Predicts new data points at positions where it was not available based on the previously fitted parameters.
- **Results postprocessing**: Post-processes the results as requested by the user. (WIP)
- **Document generation**: Generates automatically the documentation with the obtained results. (WIP)

The demonstrator is implemented as a set of [doit](https://pydoit.org/) tasks run after each other. This workflow allows checking if one result is already present or not, and avoid running any task more than once. The script that controls this is [dodo.py](dodo.py). Input files must be located in the folder `input` and the results will be generated in `output` and `document`.
### Running the basic example
The basic example consists in the full workflow applied to the Nibelungenbrücke. It will be used the basic example on how to run and implement the necessary tasks. In this case, the objective is to fit the material parameters of the bridge section given a set of displacements under its own weight simulated using a FEM model.

To run the example from a clean installation, navigate to the root folder and run the command:
```
doit
```
This will run the full workflow and output results for the basic example in the results folder from `output`.

To activate or deactivate any of the tasks, toggle them at [input/settings/doit_parameters.json](input/settings/doit_parameters.json). Note: If the results are present already, the task manager will skip that task regardless.
### Modifying the settings
To customize the demonstrator, it suffices with modifying the settings files in [input/settings](input/settings/) with the desired ones. They new values parameters must be changed in the JSON files, which can be modified manually or programatically. Notice that these modifications impact only to the methods implemented in this repository.

Another probable requirement would be the analysis of a different set of sensors. To modify their characteristics and locations, change them in their definitions from [input/sensors](input/sensors/). Virtual sensors for synthetic data generation and inference follow currently a different sintaxis.

### Adding custom functionalities
To add easily new functionalities, NibelungenBruecke implements a set of base classes that allow for the new implementations to work seamlesly with the rest of the demonstrator. Current available options are:
- **Custom geometries**: simply deactivate the "generate model task" and indicate the path to the desired mesh
- **Custom data input**: analogously to custom geometries, deactivate the corresponding task and indicate the path to data accordingly. The data format and structure must be compatible with the inference model.
- **Custom synthetic generator model**: Derive a new class from `GeneratorModel` in a new file and save it to [nibelungenbruecke/scripts/data_generation](nibelungenbruecke/scripts/data_generation). Modify the settings' JSON file to point to this model as the generator.
- **Custom forward model**: Derive a new class from probeye's `ForwardModel` in a new file and save it to [nibelungenbruecke/scripts/inference](nibelungenbruecke/scripts/inference). Modify the settings' JSON file to point to this model as the generator.
- **Custom FEM boundary conditions**: The available boundary conditions are located at [nibelungenbruecke/scripts/utilities/boundary_conditions.py](nibelungenbruecke/scripts/utilities/boundary_conditions.py). Add new ones to the file and call them from the definition in the settings JSON file.
# Expected results
WIP
